##
## k8s-order — NovaSpark Order API (Kubernetes edition)
## Gin API → NATS → Go worker → Redis
##
## First deploy:
##   make up              # deps + build + import + apply manifests
##
## After a code change:
##   make redeploy        # rebuild both images, import, rolling restart
##   make redeploy-api    # rebuild API only (most common)
##   make redeploy-worker # rebuild worker only
##
## Other:
##   make deps        # go mod tidy for both services
##   make build       # build Docker images
##   make import      # import images into k3s containerd
##   make deploy      # apply all k8s manifests (first deploy or manifest changes)
##   make hosts       # add / update orders.local in /etc/hosts
##   make logs-api    # tail API pod logs
##   make logs-worker # tail worker pod logs
##   make teardown    # delete everything from the cluster
##

API_IMAGE    := k8s-order-api:latest
WORKER_IMAGE := k8s-order-worker:latest
NAMESPACE    := orders

.PHONY: deps build import deploy up \
        redeploy redeploy-api redeploy-worker \
        logs-api logs-worker hosts teardown

## ── Dependencies ─────────────────────────────────────────────────────────────

deps:
	cd api    && go mod tidy
	cd worker && go mod tidy

## ── Build Docker images ──────────────────────────────────────────────────────

build: deps
	docker build -t $(API_IMAGE)    ./api
	docker build -t $(WORKER_IMAGE) ./worker

## ── Import images into k3s ───────────────────────────────────────────────────
## k3s uses containerd, not the Docker daemon. Images built with Docker
## must be explicitly imported — they don't share a registry by default.

import:
	docker save $(API_IMAGE)    | sudo k3s ctr images import -
	docker save $(WORKER_IMAGE) | sudo k3s ctr images import -

## ── Deploy to k3s ────────────────────────────────────────────────────────────

deploy:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/redis.yaml
	kubectl apply -f k8s/nats.yaml
	kubectl apply -f k8s/api.yaml
	kubectl apply -f k8s/worker.yaml
	kubectl apply -f k8s/ingress.yaml
	@echo ""
	@echo "Waiting for rollout..."
	kubectl rollout status deployment/order-api    -n $(NAMESPACE)
	kubectl rollout status deployment/order-worker -n $(NAMESPACE)
	@echo ""
	@echo "Done. Add to /etc/hosts on the client machine:"
	@echo "  <VM_IP>  orders.local"
	@echo ""
	@echo "Test with:"
	@echo "  curl -s -X POST http://orders.local/orders -H 'Content-Type: application/json' -d '{\"item\":\"widget\",\"quantity\":3}'"

## ── One-shot: build + import + deploy ────────────────────────────────────────

up: build import deploy

## ── Redeploy after a code change ─────────────────────────────────────────────
## Use these when manifests haven't changed — no need to re-apply YAML.
## k8s detects the new image via a rolling restart, replacing pods one at a time
## so traffic is never interrupted (zero-downtime for the API's 2 replicas).

## Rebuild and restart everything
redeploy: build import
	kubectl rollout restart deployment/order-api    -n $(NAMESPACE)
	kubectl rollout restart deployment/order-worker -n $(NAMESPACE)
	kubectl rollout status  deployment/order-api    -n $(NAMESPACE)
	kubectl rollout status  deployment/order-worker -n $(NAMESPACE)

## Rebuild and restart API only (most common — worker rarely changes)
redeploy-api:
	docker build -t $(API_IMAGE) ./api
	docker save $(API_IMAGE) | sudo k3s ctr images import -
	kubectl rollout restart deployment/order-api -n $(NAMESPACE)
	kubectl rollout status  deployment/order-api -n $(NAMESPACE)

## Rebuild and restart worker only
redeploy-worker:
	docker build -t $(WORKER_IMAGE) ./worker
	docker save $(WORKER_IMAGE) | sudo k3s ctr images import -
	kubectl rollout restart deployment/order-worker -n $(NAMESPACE)
	kubectl rollout status  deployment/order-worker -n $(NAMESPACE)

## ── Logs ─────────────────────────────────────────────────────────────────────

logs-api:
	kubectl logs -n $(NAMESPACE) -l app=order-api --tail=50 -f

logs-worker:
	kubectl logs -n $(NAMESPACE) -l app=order-worker --tail=50 -f

## ── /etc/hosts ───────────────────────────────────────────────────────────────
## Adds or updates the orders.local → <cluster-IP> entry in /etc/hosts.
## Run once after first deploy (or after your VM gets a new IP).

hosts:
	@bash setup-hosts.sh

## ── Teardown ─────────────────────────────────────────────────────────────────

teardown:
	kubectl delete namespace $(NAMESPACE) --ignore-not-found
