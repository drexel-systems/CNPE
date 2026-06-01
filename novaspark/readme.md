# k8s-order — NovaSpark Order API (Kubernetes Edition)

A containerized, Kubernetes-native implementation of the NovaSpark Order API.
Same async architecture, same 202-Accepted semantics, different runtime: Go, NATS, Redis, and k3s instead of Lambda, SQS, and DynamoDB.

---

## Architecture Overview

```
  Client (curl / Postman)
         │
         │  HTTP  POST   /orders          → 202 Accepted (async)
         │        GET    /orders/:id      → 200 / 404
         │        GET    /orders          → 200
         │        PATCH  /orders/:id      → 200 (update status)
         │        DELETE /orders/:id      → 200 (soft delete)
         ▼
  ┌──────────────────┐
  │   Traefik        │  ← built into k3s, no extra install
  │   (Ingress)      │    routes orders.local → order-api Service
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │   order-api      │  ← Golang + Gin  (2 replicas)
  │   :8080          │
  └────────┬─────────┘
           │
           │  POST /orders
           │  publishes JSON payload
           │  returns 202 immediately
           ▼
  ┌──────────────────┐
  │   NATS           │  ← subject: orders.new
  │   (JetStream)    │    at-least-once delivery
  └────────┬─────────┘
           │
           │  subscribes to orders.new
           │  one message per order
           ▼
  ┌──────────────────┐
  │  order-worker    │  ← Golang  (1 replica)
  │                  │    unmarshals → sets status: processing
  └────────┬─────────┘
           │
           │  SET order:{id}  (JSON)
           │  SADD orders     (ID index)
           ▼
  ┌──────────────────┐
  │   Redis          │  ← key-value store
  │   :6379          │    order:{id} → JSON record
  └──────────────────┘
           ▲
           │  GET order:{id}
           │  SMEMBERS orders
           │
  ┌────────┴─────────┐
  │   order-api      │  ← read path for GET routes
  └──────────────────┘
```

All five components run as pods inside the `orders` namespace on a single k3s node.

---

## How This Compares to the AWS NovaSpark Project

The architecture is intentionally the same shape as the serverless version built in class.
The engineering decisions — async submission, 202 semantics, decoupled worker, key-value storage — carry over exactly. Only the runtime changes.

| Concern               | AWS (class project)              | Kubernetes (this project)         |
|-----------------------|----------------------------------|-----------------------------------|
| **API runtime**       | Python Lambda                    | Go / Gin container                |
| **Ingress**           | API Gateway (managed)            | Traefik Ingress (in-cluster)      |
| **Async broker**      | SQS (managed queue)              | NATS JetStream (in-cluster)       |
| **Worker runtime**    | Python Lambda (SQS trigger)      | Go container (NATS subscriber)    |
| **Storage**           | DynamoDB (managed, serverless)   | Redis (in-cluster, ephemeral)     |
| **IaC / deploy**      | Pulumi (Python)                  | kubectl + Makefile                |
| **Scale to zero**     | Yes — Lambda idles for free      | No — pods always running          |
| **Cold start**        | Yes — first invocation pays      | No — container is already up      |
| **Ops overhead**      | Near-zero (fully managed)        | You own the cluster               |
| **Cost at low scale** | ~$0 (free tier)                  | Fixed VM cost regardless of load  |
| **Cost at high scale**| Per-invocation pricing adds up   | Fixed node cost; scales via replicas |

**The key insight:** the async pattern, the 202/GET consistency window, and the decoupled worker are not AWS-specific ideas. They are architectural patterns that appear in every serious distributed system. NATS and SQS solve the same problem differently. The tradeoffs shift — managed vs. self-operated, pay-per-use vs. fixed cost, zero-ops vs. full control — but the reasoning that leads you to an async queue is identical in both stacks.

---

## Go API Design

The API service (`api/`) is structured as a proper Go package layout rather than a single `main.go`. This reflects idiomatic Go design for a small-but-real service.

### Package structure

```
api/
├── main.go              ← wire-up only: connect deps, inject, start server
├── models/
│   └── order.go         ← domain types: Order, request structs, valid statuses
├── store/
│   └── redis.go         ← Store interface + RedisStore implementation
└── handlers/
    └── orders.go        ← HTTP handlers as methods on a Handler struct
```

Each package has a single, clear responsibility. `main.go` is intentionally thin — it creates real connections, wires the pieces together, and starts the server. Business logic lives in `handlers`. Data access lives in `store`. Shared types live in `models`.

---

### Dependency injection via a Handler struct

The central Go design decision is the `Handler` struct in `handlers/orders.go`:

```go
type Handler struct {
    store store.Store
    nc    *nats.Conn
}

func New(s store.Store, nc *nats.Conn) *Handler {
    return &Handler{store: s, nc: nc}
}

func (h *Handler) RegisterRoutes(r *gin.Engine) {
    r.POST("/orders",     h.SubmitOrder)
    r.GET("/orders",      h.ListOrders)
    r.GET("/orders/:id",  h.GetOrder)
    r.PATCH("/orders/:id", h.UpdateOrder)
    r.DELETE("/orders/:id", h.DeleteOrder)
}
```

Each route is a method on `Handler`, not a standalone function. This means every handler has access to its dependencies (`store`, `nc`) through the receiver — no package-level globals, no `init()` tricks. `main.go` creates the real implementations and passes them in:

```go
s  := store.New(redisAddr)
nc, _ := nats.Connect(natsURL)
h  := handlers.New(s, nc)
h.RegisterRoutes(r)
```

The practical benefit: you can test any handler in isolation by passing a fake store that implements the interface. No Redis cluster, no NATS server needed in tests.

---

### The Store interface

The `store` package defines both the interface and the Redis implementation:

```go
type Store interface {
    Get(ctx context.Context, id string) (*models.Order, error)
    List(ctx context.Context) ([]models.Order, error)
    Save(ctx context.Context, order *models.Order) error
    Ping(ctx context.Context) error
}
```

`Handler` depends on `store.Store` (the interface), not `*store.RedisStore` (the concrete type). This is a core Go principle: accept interfaces, return concrete types. It means the storage backend can be swapped — in-memory map for tests, Redis for production — without touching a single line of handler code.

The sentinel error pattern is used for "not found":

```go
var ErrNotFound = fmt.Errorf("order not found")
```

Handlers check for it explicitly with `errors.Is(err, store.ErrNotFound)` and return 404. Any other error returns 500. This is cleaner than returning `(nil, nil)` for missing records and forces callers to handle the distinction.

---

### PATCH and DELETE — the write path

Both operations follow the same read-modify-write pattern:

1. `Get` the existing order from Redis (returns 404 if missing)
2. Modify the field(s)
3. `Save` it back via a Redis pipeline (`SET` + `SADD` atomically)

**PATCH** updates `status` to one of the valid values defined in `models.ValidStatuses`:

```go
var ValidStatuses = map[string]bool{
    "processing": true,
    "shipped":    true,
}
```

`"received"` is excluded (set on creation only). `"cancelled"` is excluded (reserved for soft-delete via DELETE). The handler returns 400 with a descriptive error if anything else is submitted.

**DELETE** is a soft delete — it sets `status: "cancelled"` and writes the record back. The order is never removed from Redis. This preserves the audit trail: `GET /orders/:id` after a DELETE still returns the order, just with `status: "cancelled"`. Same design decision as the NovaSpark AWS version, which keeps `status: cancelled` records in DynamoDB rather than hard-deleting them.

---

## Prerequisites — Ubuntu Install Guide

### 1. System packages

```bash
sudo apt-get update && sudo apt-get install -y \
    curl \
    git \
    jq \
    make \
    ca-certificates \
    gnupg \
    lsb-release
```

### 2. Docker

```bash
# Add Docker's official GPG key and repository
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin

# Allow your user to run Docker without sudo
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker run --rm hello-world
```

### 3. Go

```bash
# Install Go 1.22 (adjust version as needed)
curl -OL https://go.dev/dl/go1.22.4.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.22.4.linux-amd64.tar.gz
rm go1.22.4.linux-amd64.tar.gz

# Add to PATH — add these lines to ~/.bashrc or ~/.zshrc
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# Verify
go version
```

### 4. kubectl

```bash
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

# Verify
kubectl version --client
```

### 5. k3s (Kubernetes cluster)

k3s is a fully conformant, lightweight Kubernetes distribution. A single command installs the server and starts the cluster.

```bash
# Install k3s
curl -sfL https://get.k3s.io | sh -

# Copy the kubeconfig to your user's home directory
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

# Verify the cluster is up
kubectl get nodes
```

Expected output:
```
NAME     STATUS   ROLES           AGE   VERSION
your-vm  Ready    control-plane   30s   v1.3x.x+k3s1
```

> **Note:** k3s includes Traefik as its built-in ingress controller and a lightweight
> containerd runtime. No additional ingress install is needed.

---

## Clone and Build

```bash
git clone <your-repo-url> k8s-order
cd k8s-order
```

---

## Kubernetes Manifests — `k8s/`

Six YAML files, applied in order by `make deploy`. Each file is described below.

---

### `namespace.yaml` — Isolation boundary

```
k8s/namespace.yaml
```

Creates the `orders` namespace. Every other resource in this project lives inside it. Namespaces in Kubernetes are the equivalent of an AWS account boundary within a cluster — they isolate resources, allow per-namespace RBAC policies, and make teardown clean (`kubectl delete namespace orders` removes everything at once).

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: orders
```

---

### `redis.yaml` — Backing store (Deployment + Service)

```
k8s/redis.yaml
```

Two resources in one file: a `Deployment` and a `Service`.

**Deployment** declares the desired state: one pod running `redis:7-alpine`. Kubernetes ensures that pod is always running — if it crashes, the scheduler starts a replacement automatically. The `resources` block sets CPU/memory `requests` (what the scheduler guarantees) and `limits` (the hard cap).

**Service** gives Redis a stable in-cluster DNS name: `redis.orders.svc.cluster.local:6379`. Without a Service, pods get random IPs that change on restart. The API and worker reference Redis by this DNS name via the `REDIS_ADDR` environment variable — the same principle as injecting `TABLE_NAME` as a Lambda environment variable rather than hardcoding an ARN.

> **Demo note:** This Redis instance has no `PersistentVolumeClaim` — data is lost if the pod restarts. Sufficient for a demo; production would use a `StatefulSet` with a volume.

---

### `nats.yaml` — Message broker (Deployment + Service)

```
k8s/nats.yaml
```

Same pattern as Redis: a `Deployment` + `Service` pair.

**Deployment** runs `nats:2.10-alpine` with the `--jetstream` flag, enabling durable message storage and at-least-once delivery. Without JetStream, NATS is pure fire-and-forget — messages sent while the worker is restarting are silently dropped. JetStream is the feature that closes the gap with SQS's durability guarantee.

**Service** exposes two ports:
- `4222` — the client port, used by the API and worker to connect
- `8222` — the HTTP monitoring endpoint (`http://orders.local:8222` shows live server stats)

The API connects to `nats://nats.orders.svc.cluster.local:4222` via the `NATS_URL` env var.

---

### `api.yaml` — Gin HTTP API (Deployment + Service)

```
k8s/api.yaml
```

**Deployment** runs two replicas of `k8s-order-api:latest`. Two replicas means:
- If one pod is killed or restarted, the other continues serving traffic with no downtime
- Kubernetes load-balances across both replicas through the Service

`imagePullPolicy: Never` tells Kubernetes not to pull from a registry — use the image already loaded into containerd via `make import`. Without this, the cluster would try to pull from Docker Hub and fail with `ErrImagePullBackOff`.

Two probes are configured on each pod:

| Probe | Path | Behaviour |
|-------|------|-----------|
| `readinessProbe` | `GET /orders` | Pod only receives traffic once this returns 200. Prevents routing to a pod that is still connecting to NATS/Redis on startup. |
| `livenessProbe`  | `GET /orders` | If this fails repeatedly, Kubernetes restarts the pod. Catches hung processes that are alive but not serving. |

**Service** of type `ClusterIP` gives the Deployment a stable internal IP and DNS name (`order-api.orders.svc.cluster.local:80`). The Traefik Ingress routes external traffic to this Service — the Service load-balances across the two API pods.

---

### `worker.yaml` — Go worker (Deployment only)

```
k8s/worker.yaml
```

A `Deployment` with one replica and **no Service**. The worker has no inbound HTTP traffic — it pulls messages from NATS. A Service would create an unnecessary endpoint with nothing listening on it.

The worker connects outbound to both NATS and Redis using the same in-cluster DNS names as the API. The `NATS_URL` and `REDIS_ADDR` env vars are the only configuration it needs — no hardcoded addresses anywhere in the codebase, same 12-factor config principle as the Lambda version.

The worker's `main.go` uses `MaxReconnects(-1)`, which means it retries NATS connections forever on failure. This is important in Kubernetes: pod startup order is not guaranteed, so the worker may start before NATS is fully ready. Infinite reconnect means it heals itself without needing an `initContainer` or `depends_on` logic.

---

### `ingress.yaml` — External access via Traefik

```
k8s/ingress.yaml
```

An `Ingress` resource tells Traefik how to route external HTTP traffic into the cluster. Without an Ingress, the API Service is only reachable inside the cluster.

```yaml
spec:
  ingressClassName: traefik
  rules:
    - host: orders.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: order-api
                port:
                  number: 80
```

This rule says: any request arriving at Traefik with `Host: orders.local` should be forwarded to the `order-api` Service on port 80. Traefik picks this up automatically — no Traefik restart or config file edit needed. This is the Kubernetes Ingress contract: the controller watches for `Ingress` resources and reconfigures itself.

The `traefik.ingress.kubernetes.io/router.entrypoints: web` annotation pins routing to the HTTP (port 80) entrypoint. Remove it if you add TLS.

**How the full routing chain works:**

```
curl http://orders.local/orders
  → VM port 80
  → Traefik (kube-system namespace)
  → Ingress rule matches host: orders.local
  → order-api Service (orders namespace, port 80)
  → one of the two order-api pods (port 8080)
  → Gin handler
```

---

## Makefile Reference

### First deploy

```bash
make up
```

### After a code change (cluster already running)

```bash
make redeploy-api     # rebuilt API only — most common
make redeploy-worker  # rebuilt worker only
make redeploy         # rebuild both
```

These targets rebuild the image, import it into k3s's containerd, and trigger a rolling restart. With two API replicas, pods are replaced one at a time — zero downtime.

### All targets

| Target                | What it does                                                                    |
|-----------------------|---------------------------------------------------------------------------------|
| `make deps`           | `go mod tidy` for both services — required before first build                   |
| `make build`          | Builds both Docker images                                                        |
| `make import`         | Imports both images into k3s containerd via `k3s ctr images import`             |
| `make deploy`         | Applies all six Kubernetes manifests; waits for rollout                         |
| `make up`             | Full first-deploy: `deps → build → import → deploy`                            |
| `make redeploy`       | Rebuild both images, import, rolling restart both deployments                   |
| `make redeploy-api`   | Rebuild API image only, import, rolling restart `order-api`                     |
| `make redeploy-worker`| Rebuild worker image only, import, rolling restart `order-worker`               |
| `make logs-api`       | Tail logs from all `order-api` pods                                             |
| `make logs-worker`    | Tail logs from the `order-worker` pod                                           |
| `make teardown`       | Delete the entire `orders` namespace and everything in it                       |

---

## Get the Cluster IP

```bash
kubectl get nodes -o wide
```

Look for `INTERNAL-IP` in the output:

```
NAME     STATUS   ROLES           AGE   VERSION   INTERNAL-IP      ...
your-vm  Ready    control-plane   2d    v1.35.x   192.168.139.65   ...
```

Use that IP in all curl commands below, or add it to your local `/etc/hosts` for the clean hostname:

```bash
echo "192.168.139.65  orders.local" | sudo tee -a /etc/hosts
```

---

## Testing with curl

### Check pod health first

```bash
kubectl get pods -n orders
```

All pods should show `Running` before testing:
```
NAME                            READY   STATUS    RESTARTS
nats-xxxx                       1/1     Running   0
redis-xxxx                      1/1     Running   0
order-api-xxxx                  1/1     Running   0
order-api-yyyy                  1/1     Running   0
order-worker-xxxx               1/1     Running   0
```

---

### Submit an order — POST /orders

Returns `202 Accepted` immediately. The order is queued in NATS; the worker
persists it to Redis asynchronously.

```bash
curl -s -X POST http://orders.local/orders \
  -H "Content-Type: application/json" \
  -d '{"item":"widget","quantity":3}' | jq .
```

Response:
```json
{
  "order_id": "a3f1c2d4-...",
  "status": "received",
  "message": "order queued for processing"
}
```

---

### Retrieve an order — GET /orders/:id

Wait a moment after the POST — the worker processes asynchronously. A 404
immediately after a POST is normal and illustrates the consistency window.

```bash
curl -s http://orders.local/orders/<order_id> | jq .
```

Response:
```json
{
  "order_id": "a3f1c2d4-...",
  "item": "widget",
  "quantity": 3,
  "status": "processing",
  "created_at": "2026-06-01T15:04:05Z",
  "updated_at": "2026-06-01T15:04:05Z"
}
```

---

### List all orders — GET /orders

```bash
curl -s http://orders.local/orders | jq .
```

---

### Update an order status — PATCH /orders/:id

Valid status values: `processing`, `shipped`. `received` is set on creation; `cancelled` is reserved for DELETE.

```bash
curl -s -X PATCH http://orders.local/orders/<order_id> \
  -H "Content-Type: application/json" \
  -d '{"status":"shipped"}' | jq .
```

Response:
```json
{
  "order_id": "a3f1c2d4-...",
  "item": "widget",
  "quantity": 3,
  "status": "shipped",
  "created_at": "2026-06-01T15:04:05Z",
  "updated_at": "2026-06-01T15:04:10Z"
}
```

Invalid status returns `400 Bad Request`:
```bash
curl -s -X PATCH http://orders.local/orders/<order_id> \
  -H "Content-Type: application/json" \
  -d '{"status":"launched"}' | jq .
# {"error": "invalid status — must be one of: processing, shipped"}
```

---

### Soft-delete an order — DELETE /orders/:id

The record is **not removed** — `status` is set to `cancelled` and the order remains in Redis. The audit trail is preserved.

```bash
curl -s -X DELETE http://orders.local/orders/<order_id> | jq .
```

Response:
```json
{
  "order_id": "a3f1c2d4-...",
  "item": "widget",
  "quantity": 3,
  "status": "cancelled",
  "created_at": "2026-06-01T15:04:05Z",
  "updated_at": "2026-06-01T15:04:15Z"
}
```

The order still appears in `GET /orders` and `GET /orders/:id` after deletion — with `status: cancelled`. This is intentional: deleting an order doesn't erase the business event, it records that it was cancelled.

---

### Full order lifecycle in one script

```bash
# 1. Submit
ORDER=$(curl -s -X POST http://orders.local/orders \
  -H "Content-Type: application/json" \
  -d '{"item":"widget","quantity":3}' | jq -r .order_id)
echo "Created: $ORDER"

# 2. Retrieve (give the worker a moment)
sleep 1
curl -s http://orders.local/orders/$ORDER | jq .

# 3. Advance status
curl -s -X PATCH http://orders.local/orders/$ORDER \
  -H "Content-Type: application/json" \
  -d '{"status":"shipped"}' | jq .status

# 4. Soft delete
curl -s -X DELETE http://orders.local/orders/$ORDER | jq .status

# 5. Confirm record survives
curl -s http://orders.local/orders/$ORDER | jq '{id: .order_id, status: .status}'
```

---

### Watch the async handoff in real time

Open two terminals side by side:

```bash
# Terminal 1 — watch the worker
make logs-worker
```

```bash
# Terminal 2 — fire requests
curl -s -X POST http://orders.local/orders \
  -H "Content-Type: application/json" \
  -d '{"item":"sprocket","quantity":10}' | jq .
```

The worker log will print `order <id> persisted` within milliseconds of the API
returning 202. The gap between the POST response and the worker log line is the
NATS round-trip — the async pipeline made visible.

---

### Testing without /etc/hosts (using Host header directly)

If you have not added `orders.local` to `/etc/hosts`, pass the hostname as a header:

```bash
curl -s -X POST http://192.168.139.65/orders \
  -H "Host: orders.local" \
  -H "Content-Type: application/json" \
  -d '{"item":"widget","quantity":1}' | jq .

curl -s http://192.168.139.65/orders \
  -H "Host: orders.local" | jq .
```

---

## Kubernetes Resilience Demo

The API ships two chaos endpoints specifically for demonstrating Kubernetes
self-healing in lecture. Both accept GET and POST so they can be triggered
from a browser or curl.

| Endpoint | Behaviour |
|---|---|
| `GET /crash` or `POST /crash` | Hard crash — `os.Exit(1)` with no log output. Simulates a catastrophic unexpected failure (OOM kill, segfault, unhandled signal). |
| `GET /panic` or `POST /panic` | Deliberate shutdown — logs a forensic message then exits. Simulates the application detecting a state it cannot safely recover from and choosing to stop rather than corrupt data. |

In both cases Kubernetes detects the non-zero exit code, restarts the
container, and the readiness probe (`GET /orders`) gates traffic until the
pod passes. The caller receives a connection reset / EOF because the process
dies before writing an HTTP response — that's intentional and realistic.

### Running the demo

Open two terminals side by side:

```bash
# Terminal 1 — watch pod lifecycle in real time
kubectl get pods -n orders -w
```

```bash
# Terminal 2 — trigger a crash
curl -X POST http://192.168.139.65/crash
# (connection will reset — that's expected)
```

Watch Terminal 1: the pod drops to `0/1`, Kubernetes restarts it, and it
returns to `1/1 Running` within a few seconds as the readiness probe clears.

### Crash vs Panic — the log difference

After a restart, check the logs from the **previous** container instance:

```bash
# See logs from the container that just died
kubectl logs -n orders -l app=order-api --previous
```

After `/crash` — the log ends abruptly with no final message. The last line
will be a normal request log entry. Nothing told you it was coming.

After `/panic` — the log ends with the forensic message:
```
PANIC: application entered an unrecoverable state — detected fatal inconsistency,
forcing shutdown for safety. Review recent orders for data integrity issues.
```

This is the key distinction to highlight in lecture: a crash gives you nothing,
a deliberate panic gives operators a breadcrumb. Real-world services use
structured logging (JSON) here so the message is queryable in CloudWatch,
Datadog, etc.

### CrashLoopBackOff — the bonus teaching moment

If you trigger `/crash` several times in quick succession, Kubernetes applies
exponential backoff and the pod enters `CrashLoopBackOff`:

```bash
kubectl get pods -n orders
# NAME                            READY   STATUS             RESTARTS   AGE
# order-api-7d6f9b8c4-xk2pq      0/1     CrashLoopBackOff   5          3m
```

This is intentional Kubernetes behaviour — it is not giving up, it is
throttling restarts to avoid thrashing. Leave it alone for a minute or two
and the pod will self-heal once the backoff timer expires. No manual
intervention needed.

---

## Troubleshooting

**Images not found (`ErrImageNeverPull` or `ImagePullBackOff`)**
```bash
# Re-import images into k3s
make import
kubectl rollout restart deployment/order-api    -n orders
kubectl rollout restart deployment/order-worker -n orders
```

**Permission denied on `~/.kube/config.lock`**
```bash
sudo rm ~/.kube/config.lock
sudo chown -R $USER:$USER ~/.kube
```

**Pod stuck in `CrashLoopBackOff`**
```bash
kubectl describe pod <pod-name> -n orders
kubectl logs <pod-name> -n orders
```

**Ingress not routing (connection refused)**
```bash
# Verify Traefik is running
kubectl get pods -n kube-system | grep traefik

# Verify the ingress was created
kubectl get ingress -n orders
```
