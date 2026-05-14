# Lab 5: Storage — DynamoDB, Access Patterns, and the Persistence Layer

**Block 3 (in class) + out-of-class work**
**Due:** See course syllabus

---

## The Scenario

NovaSpark's status endpoint is live and the serverless compute layer is understood. The remaining gap is obvious: every request goes in, nothing stays. The moment the Lambda function returns, the data is gone.

> **Janet:** "Before we build the order API, I want a design document. Not code — a document. What is the order object? What are the fields? What is the key? How do we look things up? We've been burned before by building first and thinking second."

> **Linda:** "And while you're at it — what happens if the database goes down? What's our recovery story? I want RTO and RPO in writing."

> **Ben:** "I just need to be able to call GET /orders/{id} and get an order back. One route. That's Lab 5."

Janet's ask is Part 1: design the data model before writing a line of code. Linda's ask is D6: the RTO/RPO analysis. Ben's ask is Parts 2 and 3: build and verify it.

---

## What This Lab Does — and Does Not Do

After Lab 5, your stack looks like this:

| Route | Status |
|-------|--------|
| `GET /status` | ✅ Live (from Lab 4, unchanged) |
| `GET /orders/{id}` | ✅ Live (new this lab) |
| `POST /orders` | — Not yet live |
| `GET /orders` | — Not yet live |
| `PATCH /orders/{id}` | — Not yet live |
| `DELETE /orders/{id}` | — Not yet live |

The full async pipeline — POST /orders to SQS, processor Lambda, full CRUD — comes in Lab 6 and the final project. This lab's scope is intentionally narrow: provision the table, connect Lambda to it, and verify that a direct read works.

There is no POST route yet, which means you will seed a test record directly through the DynamoDB console rather than through the API. That is not a workaround — it is the correct way to verify a read path before the write path exists.

---

## Lab 4 Prediction Check

Before doing anything else, open your Lab 4 D6 submission. You made a specific prediction about the Hellerstein et al. limitation most relevant to synchronous DynamoDB writes and a measurable latency outcome.

Keep that prediction in front of you. Part 3 of this lab asks you to evaluate it.

---

## Before You Deploy: Read the Code First

Open `__main__.py` and `app/handler.py` and read them fully before running any commands.

For each TODO in both files, be able to answer:
- What does this resource or code change accomplish?
- Why is it placed where it is (module level vs. inside the handler)?
- What would break if it were implemented incorrectly or omitted?

**Specific things to annotate before you start:**

1. Why `billing_mode="PAY_PER_REQUEST"` rather than `PROVISIONED` — and what the cost tradeoff is at NovaSpark's current traffic level versus at scale
2. Why `TABLE_NAME` is injected as an environment variable rather than hardcoded in handler.py (connect this to Lab 4's `ENVIRONMENT` and `SERVICE` variables — same principle)
3. Why `boto3.resource("dynamodb")` belongs at module level, not inside `lambda_handler` — use your Lab 4 `env_create_time` observations as the supporting argument
4. What `response.get("Item")` returns when the item does not exist — and why that is handled with a 404 rather than a Python exception
5. What `event["pathParameters"]["id"]` contains and where API Gateway populates it from

> **Common gotcha — `{"error": "Internal server error"}` on GET routes**
>
> boto3's DynamoDB resource returns numeric attributes (like `quantity`) as Python `Decimal` objects, not plain `int`. The standard `json.dumps` cannot serialize `Decimal` and raises a `TypeError`, which your `except` block catches and converts to a 500.
>
> Fix this by adding a custom encoder to your handler:
>
> ```python
> import decimal
>
> class DecimalEncoder(json.JSONEncoder):
>     def default(self, obj):
>         if isinstance(obj, decimal.Decimal):
>             return int(obj) if obj % 1 == 0 else float(obj)
>         return super().default(obj)
> ```
>
> Then pass `cls=DecimalEncoder` to every `json.dumps` call that serializes DynamoDB items:
>
> ```python
> json.dumps(order, cls=DecimalEncoder)
> json.dumps({"orders": orders, "count": len(orders)}, cls=DecimalEncoder)
> ```
>
> The encoder is already included in the provided `orders/handler.py` template. If you see 500s on GET routes, check that you are using `cls=DecimalEncoder` in your `json.dumps` calls.

---

## Part 1: Data Model Design (D1)

**This is due before you touch the code.** Janet's rule: design document first, implementation second.

---

### The NovaSpark Order Object

The project roadmap specifies the order data model. Your task is to produce a written design document that justifies the choices — not just lists them. A design document that describes what you built without explaining why provides no value to the team that has to live with the decisions.

**The order data model:**

```json
{
  "order_id":   "a3f1c2d4-7e8b-4f9a-b2c1-3d4e5f6a7b8c",
  "item":       "widget",
  "quantity":   3,
  "status":     "received",
  "created_at": "2026-05-06T14:32:00",
  "updated_at": "2026-05-06T14:32:00"
}
```

**Status lifecycle:** `received → processing → shipped` (or `cancelled` at any point)

> **A note on `updated_at`:** the field is part of the full data model spec but Lab 5 does not exercise it — there is no write path yet, so the seeded test record will simply carry the same timestamp in both fields. Lab 6 introduces the `POST /orders` route (which sets the initial `updated_at`) and the project extensions introduce `PATCH /orders/{id}` (which updates it on every status change). Design for the complete lifecycle now in D1 — the implementation catches up to the spec incrementally.

---

### D1 Deliverable: Data Model Design Document

Write a structured design document covering the following four sections. Maximum 1 page total.

**Primary Key Selection**

- What is the partition key? Why `order_id` and not `item` or `status`?
- What is the cardinality? (High, medium, or low — and why does that matter for DynamoDB performance?)
- Could a composite key (PK + SK) add value here? For which access patterns?

**Attributes**

- For each field in the data model: what type is it in DynamoDB (`S`, `N`, `BOOL`, etc.)? What is it used for?
- `created_at` and `updated_at` are ISO 8601 strings rather than Unix timestamps. Name one advantage and one disadvantage of that choice.
- `status` takes one of four values: `received`, `processing`, `shipped`, `cancelled`. What constraint does DynamoDB not enforce that a relational database would?

**Access Patterns**

Identify all three access patterns the full API will require and map each to a DynamoDB operation:

| API Route | DynamoDB Operation | Notes |
|-----------|-------------------|-------|
| `GET /orders/{id}` | | |
| `GET /orders` (list all) | | |
| `GET /orders?status=received` | | |

For the third pattern — filtering by status — explain the tradeoff between a DynamoDB `Scan` with a `FilterExpression` versus adding a Global Secondary Index. At what scale does that tradeoff flip?

**ADD Connection**

Identify which section(s) of your Architecture Design Document this data model feeds. Name the specific design decision (PK selection, billing mode, or access pattern tradeoff) you will defend most explicitly in the ADD, and why it is defensible.

> This document is an input to ADD Section 3 (Component Decisions — storage) and Section 5 (Operational Considerations). Students who complete D1 carefully will find those ADD sections largely write themselves.

---

## Part 2: Deploy the Table

Confirm your environment is ready: [`SETUP.md`](SETUP.md)

Complete TODO 1 through TODO 4 in `__main__.py`, then complete TODO A and TODO B in `handler.py`. Do not proceed to `pulumi up` until all four `__main__.py` TODOs are addressed — the template will fail without them.

```bash
export PULUMI_CONFIG_PASSPHRASE=""
pulumi up
```

Review the preview carefully before confirming. You should see resources queued for creation including:

- 1 Lambda function (novaSpark-orders-fn)
- 1 DynamoDB table (novaspark-orders)
- 1 API Gateway HTTP API
- 1 API Gateway integration
- 2 API Gateway routes (GET /status + GET /orders/{id})
- 1 API Gateway stage
- 1 Lambda permission
- Stack outputs including `table_name`

> **If you see fewer than 2 routes:** TODO 3 in `__main__.py` is not complete. Stop and add the GET /orders/{id} route before confirming.

> **If deploy fails with `KeyError: 'TABLE_NAME'`:** TODO 2 is not complete, or the Lambda environment variables block does not include `TABLE_NAME`. Stop and fix `__main__.py`.

**D2 deliverable:** Screenshot of the completed `pulumi up` output. It must show the DynamoDB table in the created resources list **and** `table_name` in the stack outputs section at the bottom.

Confirm the table exists in the console: **DynamoDB → Tables → novaspark-orders**

---

## Part 3: Seed a Record and Test

There is no POST route yet. To test GET /orders/{id}, you need a record in the table. Put it there directly.

---

### Step 3.1 — Complete the Handler TODOs

Before seeding or testing, complete TODO C and TODO D in `handler.py`. Then redeploy:

```bash
pulumi up
```

The update should modify only the Lambda function (new handler code). All other resources remain unchanged.

---

### Step 3.2 — Seed a Test Record

In the AWS console: **DynamoDB → Tables → novaspark-orders → Explore table items → Create item**

Switch to JSON view and paste this item:

```json
{
  "order_id": "test-order-001",
  "item": "widget",
  "quantity": 3,
  "status": "received",
  "created_at": "2026-05-06T14:32:00",
  "updated_at": "2026-05-06T14:32:00"
}
```

Click **Create item**.

**D3 deliverable:** Screenshot of the DynamoDB console showing the seeded item in the table item list. The `order_id` value `test-order-001` must be visible.

---

### Step 3.3 — Test a Successful Retrieval (D4)

```bash
ORDERS_URL=$(pulumi stack output orders_base_url)
curl "$ORDERS_URL/test-order-001"
```

You should receive a 200 response with the full order object:

```json
{
  "order_id": "test-order-001",
  "item": "widget",
  "quantity": 3,
  "status": "received",
  "created_at": "2026-05-06T14:32:00",
  "updated_at": "2026-05-06T14:32:00"
}
```

If you receive a `502 Bad Gateway` instead: open CloudWatch Logs for the Lambda function and look for a Python traceback. The most common causes are:
- `KeyError: 'TABLE_NAME'` — TODO 2 in `__main__.py` not complete
- `AttributeError: module 'handler' has no attribute 'table'` — TODO B not complete (boto3 client not initialized at module level)
- `NameError: name 'dynamodb' is not defined` — TODO A not complete (boto3 not imported)

**D4 deliverable:** Screenshot of the `curl` command and the 200 JSON response. The full order object including all fields must be visible.

---

### Step 3.4 — Test a 404 (D5)

```bash
curl "$ORDERS_URL/does-not-exist"
```

You should receive a 404 response:

```json
{"error": "Order does-not-exist not found"}
```

If you receive a 500 or 502 instead: your `handle_get_order_by_id` implementation is not handling the case where `response.get("Item")` returns `None`. Review TODO D — the check for `item is None` must return a 404 response, not raise an exception.

**D5 deliverable:** Screenshot of the `curl` command and the 404 JSON response.

---

### Step 3.5 — Lab 4 Prediction Evaluation

Open CloudWatch Logs for the Lambda function. Find the REPORT line for your D4 invocation.

Compare the `Duration` you observe against the prediction you wrote in Lab 4 D6:
- What Init Duration did you observe on the first invocation after `pulumi up`?
- What warm Duration did you observe on subsequent invocations?
- How much of the warm Duration is DynamoDB I/O versus handler overhead?

This is not a separate deliverable — but D6 asks you to engage with these numbers directly. Take note of them now while the data is in front of you.

---

## Part 4: RTO/RPO Analysis (D6)

DynamoDB's durability and availability guarantees are not things you configure — they are properties of the service you are choosing to rely on. Understanding what you get for free, and what you do not, is an architectural responsibility.

**D6 deliverable:** Maximum 1 page addressing the following four questions.

---

### 1. What DynamoDB Provides by Default

DynamoDB stores data redundantly across three Availability Zones in the region. This is the foundation of its durability claim: a single AZ failure does not cause data loss.

Answer: What is DynamoDB's documented durability SLA? What availability SLA does it offer for standard tables? (Check the AWS documentation — these are specific percentages, not approximations.)

---

### 2. RTO and RPO Definitions and NovaSpark's Numbers

Define both terms in the context of the NovaSpark orders table:

- **RPO (Recovery Point Objective):** In the worst case — a DynamoDB service disruption ending right now — how much order data could NovaSpark lose? Justify your answer using DynamoDB's replication model.
- **RTO (Recovery Time Objective):** If a DynamoDB service disruption occurred affecting novaspark-orders, what would NovaSpark's engineering team need to do to restore order API service? How long would that reasonably take?

---

### 3. Point-in-Time Recovery

DynamoDB offers Point-in-Time Recovery (PITR) as an optional feature. It is not enabled in your Pulumi template.

Answer: What does PITR provide that DynamoDB's default replication does not? For NovaSpark's current stage, is enabling PITR worth the cost? What event would change your recommendation? Write the Pulumi attribute that would enable it (one line — include it in your D6 answer).

---

### 4. ADD Alignment

This analysis feeds ADD Section 5 (Operational Considerations). Name the specific failure mode you consider most likely for NovaSpark's order table at current scale, and one mitigation you would recommend in the ADD.

> Linda's question — "what's our recovery story?" — is exactly what the RTO/RPO analysis answers. The ADD's Reliability pillar section should cite your D6 analysis directly.

---

## Context Paragraph

See [`context-paragraph-prompt.md`](context-paragraph-prompt.md) for the full prompt, examples, and grading scale.

Include your context paragraph in your submission PDF after D6.

The Block 2 seminar discussion of DeCandia et al. ("Dynamo: Amazon's Highly Available Key-Value Store") is the primary source for your context paragraph. The three discussion questions from the seminar — where the AP/CP tradeoff is visible today, what it means for NovaSpark, and what changed when Amazon productized Dynamo — should inform your paragraph.

---

## Submission Checklist

Before submitting, confirm you have all of the following in your PDF in this order:

- [ ] D1 — Data model design document (four sections: PK selection, attributes, access patterns, ADD connection)
- [ ] D2 — `pulumi up` output (DynamoDB table in created resources + `table_name` in stack outputs)
- [ ] D3 — DynamoDB console screenshot showing seeded `test-order-001` item
- [ ] D4 — `curl GET /orders/test-order-001` returning 200 with full order JSON
- [ ] D5 — `curl GET /orders/does-not-exist` returning 404 with error JSON
- [ ] D6 — RTO/RPO analysis (four sections, max 1 page)
- [ ] CP — Context paragraph (150–250 words, grounded in DeCandia et al.)

Push `__main__.py` and `app/handler.py` to your course repo. Then run `pulumi destroy` to clean up.

---

## Looking Ahead to Lab 6

Lab 6 extends the stack you built today into the full async order pipeline. The DynamoDB table stays exactly as-is — the access pattern design you wrote in D1 is now load-bearing. What changes structurally:

- An **SQS queue** sits between the API and the database
- A **second Lambda function** — the *processor* — is triggered by SQS messages and writes orders to DynamoDB
- The existing orders Lambda gains a `POST /orders` route that publishes to SQS and returns `202 Accepted`
- The remaining routes (`GET /orders`, `PATCH`, `DELETE`) are stubbed as `501` and become extension work in the final project

Your current `app/handler.py` becomes the **orders** handler in Lab 6 — keep it intact. The processor will be a separate file with its own deployment package. The Lab 6 guide will walk through the restructure; the design move you should already be thinking about now is *why* the write path is async rather than synchronous. The Block 2 reading for Lab 6 (Vogels on eventual consistency) speaks directly to that decision.

ADD-wise: today you produced inputs to Section 3 (storage component decision) and Section 5 (RTO/RPO). Lab 6 produces the messaging component decision and the failure-mode analysis for the async pipeline. By the time the ADD is due in Week 7, four labs will have fed it.
