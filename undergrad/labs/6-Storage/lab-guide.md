# Lab 6: Storage Backend — DynamoDB Integration

**Course:** Cloud Native Platform Engineering
**Paired lecture:** 6u — Cloud Native Storage
**Estimated time:** 60–75 minutes
**AWS services:** DynamoDB, Lambda, SQS, API Gateway

---

## Background

At the end of Lab 5, orders were flowing through the pipeline — API Gateway → Lambda → SQS → processor Lambda — but they were disappearing into CloudWatch logs. The `GET /orders/{id}` and `GET /orders` routes you wired up returned `501 Not Implemented`. Janet noticed.

> *"We had five orders come in Tuesday and when I asked engineering to pull the details, they said they had to search CloudWatch logs. That's not a system — that's a workaround."*
> — Janet, VP Engineering, NovaSpark Technologies

Lab 6 closes this gap. You will add a DynamoDB table to the Pulumi stack, wire it into both the processor Lambda (writes) and the orders Lambda (reads), and implement the first two real routes in the Order API.

By the end of this lab, a `POST /orders` followed by `GET /orders/{id}` will return the same order. The pipeline is complete.

---

## What You Are Building

```
API Gateway
  → POST /orders Lambda   ──→  SQS queue
                                   │
                                   ↓
                           Processor Lambda
                                   │
                           table.put_item()      ← TODO A (processor/handler.py)
                                   │
                                   ↓
                            DynamoDB Table        ← TODO 1 (__main__.py)
                           novaspark-orders
                                   │
                    ───────────────┴───────────────
                    │                             │
         GET /orders/{id}               GET /orders
         table.get_item()              table.scan()
         TODO B (orders/handler.py)   TODO C (orders/handler.py)
```

There are **4 TODOs in `__main__.py`** and **3 TODOs in the handler files** (TODO A, B, C).

---

## Part 1 — Add DynamoDB to the Pulumi Stack

Open `__main__.py`. Your work is in the Lab 6 section.

### TODO 1 — Create the DynamoDB table

Create a `aws.dynamodb.Table` resource named `novaspark-orders` with `order_id` as the partition key and on-demand billing.

**What to think about:**

- Why `order_id` as the partition key? Every `GET /orders/{id}` lookup is an exact match on `order_id`. That maps perfectly to a DynamoDB PK query — single-digit milliseconds at any scale.
- Why no sort key? Each order is a standalone item identified entirely by `order_id`. There is no second dimension to range over at the base table level.
- Why `PAY_PER_REQUEST`? NovaSpark's order volume is unpredictable and low. On-demand mode means you pay per request with no idle cost and no capacity planning. For predictable high-volume workloads, provisioned mode would be cheaper — W2 asks you to reason through this.
- DynamoDB's `attributes` list only declares attributes used as keys. Fields like `item`, `quantity`, `status`, and `created_at` are not listed — they are written and read freely because DynamoDB is schemaless for non-key attributes.

### TODO 2 — Orders Lambda with TABLE_NAME

Create the `novaSpark-orders-fn` Lambda. It is identical to Lab 5 except it now needs `TABLE_NAME` in its environment variables alongside `QUEUE_URL`. The orders Lambda uses `TABLE_NAME` to read orders for `GET` requests.

### TODO 3 — Processor Lambda with TABLE_NAME

Create the `novaSpark-processor-fn` Lambda. It needs `TABLE_NAME` so it can write orders to DynamoDB. It does **not** need `QUEUE_URL` — SQS delivers messages to it; it never sends to the queue.

Keep `timeout=25`. This must stay strictly less than the queue's `visibility_timeout_seconds=30`.

### TODO 4 — Export table_name

Add `pulumi.export("table_name", orders_table.name)` after the existing exports. This lets you confirm the table name from the terminal and navigate directly to it in the console.

### Deploy

```bash
pulumi up
```

Look for approximately 19 resources and three outputs: `status_url`, `orders_url`, and `table_name`. The DynamoDB table should appear in the resource list.

---

## Part 2 — Persist Orders (processor/handler.py)

Open `app/processor/handler.py`. Find **TODO A**.

### TODO A — Write each order to DynamoDB

Replace the `pass` statement with a `table.put_item()` call that writes all order fields: `order_id`, `item`, `quantity`, `status`, and `created_at`.

After a successful write, log `[ORDER PERSISTED] order_id=...`. This is the log line D3 will ask you to screenshot.

Wrap the call in `try/except`. If the write fails, log the error and re-raise the exception. Re-raising is important — it tells SQS the message was not processed successfully, so SQS will re-deliver it after the visibility timeout rather than silently dropping the order.

**Redeploy after making this change:**

```bash
pulumi up
```

**Test the write path:**

```bash
curl -X POST $(pulumi stack output orders_url) \
  -H "Content-Type: application/json" \
  -d '{"item": "widget", "quantity": 3}'
```

Note the `order_id` in the 202 response. Wait a few seconds for the processor Lambda to run (SQS polling can take up to 20 seconds), then check the DynamoDB console:

**Console → DynamoDB → Tables → novaspark-orders → Explore table items**

You should see your order. Send two or three more orders and verify they all appear.

---

## Part 3 — Implement the GET Routes (orders/handler.py)

Open `app/orders/handler.py`. Find **TODO B** and **TODO C**.

### TODO B — GET /orders/{id}

Implement `handle_get_order_by_id()`. The order ID comes from `event["pathParameters"]["id"]`. Call `table.get_item()` with that ID as the partition key.

The key detail: DynamoDB does not raise an exception when a key is not found. It returns a response dict with no `"Item"` key. Check `response.get("Item")` and return a `404` if it is falsy.

### TODO C — GET /orders

Implement `handle_list_orders()`. Check for an optional `?status=` query parameter in `event.get("queryStringParameters")`. If provided, pass a `FilterExpression=Attr("status").eq(status_filter)` to `table.scan()`. If not provided, do a plain `table.scan()`.

Return the items list under a `"orders"` key along with a `"count"`.

**Redeploy:**

```bash
pulumi up
```

**Test the full round trip:**

```bash
# Post an order and capture the order_id
curl -s -X POST $(pulumi stack output orders_url) \
  -H "Content-Type: application/json" \
  -d '{"item": "gadget", "quantity": 2}'

# Wait a few seconds, then retrieve it by ID
curl $(pulumi stack output orders_url)/YOUR_ORDER_ID_HERE

# List all orders
curl $(pulumi stack output orders_url)

# List only received orders
curl "$(pulumi stack output orders_url)?status=received"
```

---

## Deliverables

Submit a PDF containing the five screenshots below followed by answers to the three written questions.

### Screenshots

**D1 — `pulumi up` output (10 pts)**

Terminal output showing the completed `pulumi up`. All resources created, no errors. Three stack outputs visible at the bottom: `status_url`, `orders_url`, and `table_name`.

**D2 — POST then GET round trip (20 pts)**

Two curl commands in the same screenshot (or two clearly sequenced screenshots):
1. `POST /orders` returning `202` with an `order_id`
2. `GET /orders/{id}` using that same `order_id`, returning `200` with the full order object

This is the proof the pipeline is end-to-end.

**D3 — CloudWatch processor logs showing [ORDER PERSISTED] (15 pts)**

Navigate to: Lambda → `novaSpark-processor-fn` → Monitor → View CloudWatch Logs

Show a log stream with at least two orders. Each order should have an `[ORDER RECEIVED]` line and an `[ORDER PERSISTED]` line. The `[ORDER PERSISTED]` line is the new line from your TODO A implementation.

**D4 — GET /orders/{id} returning 404 (10 pts)**

```bash
curl -v $(pulumi stack output orders_url)/00000000-0000-0000-0000-000000000000
```

Show the `404` response with an error message. This confirms your not-found handling works correctly.

**D5 — DynamoDB console showing items (5 pts)**

Screenshot of the DynamoDB console showing the `novaspark-orders` table with items. Navigate to: DynamoDB → Tables → novaspark-orders → Explore table items.

---

### Written Deliverables

**W1 — Partition key design (15 pts)**

Explain why `order_id` is the right partition key for this table. Address two specific points: (1) how the partition key choice relates to the `GET /orders/{id}` access pattern, and (2) why a sort key is not needed for the base table. Your answer should demonstrate that you understand the relationship between access patterns and key design — not just that you copied the lab instructions.

**W2 — Billing mode decision (15 pts)**

Compare on-demand (`PAY_PER_REQUEST`) and provisioned billing for DynamoDB. Explain which one fits NovaSpark's order workload and why. Your answer should address: traffic predictability, idle cost, and what would make you reconsider the choice in the future. 3–5 sentences.

**W3 — The status filter architecture question (10 pts)**

`GET /orders?status=received` works in your implementation because `scan()` with a `FilterExpression` reads every item and filters in memory. Explain why this is acceptable for NovaSpark today but would break down at scale. What would you add to DynamoDB to make the status filter efficient at large scale? Name the specific DynamoDB feature and sketch what it would look like (key schema only — no code required).

---

## Cleanup

When you have submitted your deliverables:

```bash
pulumi destroy
```

Confirm the destroy completes cleanly. The DynamoDB table, Lambda functions, SQS queue, and API Gateway will all be removed.
