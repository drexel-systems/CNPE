# Lab 5: Async Order API — SQS + Lambda

**Estimated Time:** 2–2.5 hours total across Parts 1–3
**Due:** See course syllabus
**Prerequisite:** Lab 4 must be completed and submitted

---

## The Scenario

It is Wednesday morning at NovaSpark. The status endpoint from Lab 4 is live and working. Ben flags you in Slack.

> **Ben:** "Good news — Janet loved the status API. Bad news — she has a follow-up ask. She wants customers to be able to submit orders through the platform. The team is debating whether to just do this synchronously, but the fulfillment service is sometimes slow."

> **You:** "How slow?"

> **Ben:** "Could be a few seconds, could be thirty. Depends on inventory checks, warehouse load, all kinds of things. We don't want customers staring at a spinner."

> **Linda [joining the thread]:** "And whatever we build, it needs to handle a spike. If we go on the news, I don't want the order service to be the thing that goes down."

You know the answer. Decoupling the submission from the processing with a queue gives you three things at once: a fast response to the customer (202 Accepted, immediately), resilience to downstream slowness, and natural load leveling if traffic spikes.

Two questions to answer before you write a line of code: does the caller need the result right now? No — the customer just needs confirmation the order was received. Can the operation take longer than expected? Yes — fulfillment is variable. Both answers point to async.

---

## Before You Begin

Confirm your setup is ready: [`SETUP.md`](SETUP.md)

You are not starting from scratch. The `__main__.py` provided for this lab includes the complete Lab 4 section (status Lambda + API Gateway) as provided, working code — you don't need your Lab 4 stack running. Your job is the Lab 5 additions: the SQS queue, the order submission Lambda, the five API routes, and the processor Lambda.

---

## Part 1: Design First (~20 min)

**What you're doing:** Apply the RESTful URL design principles from lecture before touching Pulumi. A few minutes of design here saves a lot of refactoring later — and the written deliverable W1 asks you to show your work.

---

### Step 1.1 — Design the URL Structure

NovaSpark needs an order service. You will implement one route today (`POST /orders`) and stub out the shape of the others.

Before writing any code, write out the full URL design for a basic order service. For each route, specify the HTTP method, the path, and one sentence on what it does.

A complete order service might include: submitting an order, retrieving a specific order by ID, listing all orders (with optional status filter), and canceling an order.

Apply what you learned from lecture: use nouns not verbs, use plural resource names, put the resource identifier in the path (not the query string), and use query parameters only for filtering/pagination.

**Deliverable W1 asks you to write this up** — do it now, on paper or in a scratch doc, before proceeding.

---

### Step 1.2 — The 202 Decision

Before writing any code, answer these two diagnostic questions from lecture:

1. Does the caller (the customer placing an order) need the result right now to continue?
2. Can the operation (fulfillment, inventory check, warehouse routing) realistically take longer than a few seconds?

Write down your answers. **Deliverable W2 asks you to explain this reasoning** — your answers here are the reasoning.

---

## Part 2: Extend the Pulumi Stack (~70 min)

**What you're doing:** Add an SQS queue, an order submission Lambda, a new API route, and a processor Lambda triggered from the queue.

**Start with:** The `__main__.py` provided for this lab. It includes the complete Lab 4 section (status Lambda + API Gateway) and 10 TODOs for the Lab 5 additions.

> **Strategy:** Don't try to complete all 10 TODOs and run `pulumi up` once. Deploy after each logical group. Complete TODOs 1–3 and deploy to confirm the queue and orders Lambda exist in the console before wiring up the route. Then complete TODOs 4–6 and deploy again for the full submission path. Then TODOs 7–9 for the processor.

---

### Step 2.1 — Create the SQS Queue (TODO 1)

Fill in TODO 1 to create the SQS queue.

Run `pulumi up`. In the AWS Console, navigate to **SQS** — you should see `novaSpark-orders` in the list. Click into it and note the **Queue URL** — this is what gets passed into your Lambda as the `QUEUE_URL` environment variable.

> **Visibility timeout:** When the processor Lambda picks up a message and starts working on it, SQS hides that message from other consumers for `visibility_timeout_seconds`. If the Lambda finishes and succeeds, it signals Lambda to delete the message. If the Lambda crashes or times out before finishing, the message reappears after 30 seconds and gets retried. Your processor Lambda's timeout (25 seconds) must be shorter than this window — which it is.

---

### Step 2.2 — Add the Orders Lambda and Routes (TODOs 2–6)

Fill in TODOs 2 through 6. Each TODO has comments explaining the required arguments.

Pay attention to TODO 3 — the `QUEUE_URL` environment variable. Your Lambda reads this via `os.environ["QUEUE_URL"]`. The value is `orders_queue.url`, which is a Pulumi `Output` — Pulumi resolves it to the real URL at deploy time and injects it as an environment variable. You never hardcode the URL.

TODO 5 asks you to create **five routes** — `POST /orders`, `GET /orders/{id}`, `GET /orders`, `PATCH /orders/{id}`, and `DELETE /orders/{id}` — all pointing to the same orders integration. The orders Lambda dispatches based on the `routeKey` field in the event. `POST /orders` is fully implemented; the others return `501 Not Implemented` as stubs.

> **Why stubs?** 501 Not Implemented is more informative than 404 Not Found — it tells the caller "this route exists in the API but hasn't been wired up yet." The full API surface is visible from day one so you can see the shape of what you're building toward. The stubs become real in Lab 6.

Run `pulumi up`. Confirm in the console:
- **Lambda → novaSpark-orders-fn:** exists, has `QUEUE_URL` environment variable set
- **API Gateway → novaSpark-api → Routes:** shows `GET /status` and all five `/orders` routes

Now test the submission endpoint:

```bash
curl -X POST $(pulumi stack output orders_url) \
  -H "Content-Type: application/json" \
  -d '{"item": "widget", "quantity": 3}'
```

You should get back a `202 Accepted` response with an `order_id`. Note the status code — it is not 200.

**Take screenshot D1 now** — the `pulumi up` output showing all resources created, no errors.

**Take screenshot D2 now** — the `curl POST` command and the 202 response with `order_id`.

> **202 vs. 200:** HTTP 200 means "here is the result." HTTP 202 means "I received your request and will process it — but it is not done yet." Returning 200 here would be a lie: the order has been queued, not fulfilled. Correct HTTP semantics matter — especially when clients use the status code to decide what to show the user.

---

### Step 2.3 — Add the Processor Lambda (TODOs 7–9)

Fill in TODOs 7 through 9 to create the processor Lambda and the SQS event source mapping.

The event source mapping is what connects the queue to the Lambda — you don't write any polling code. Lambda handles the poll loop: it continuously checks the queue, batches up to 5 messages, and invokes your processor.

Run `pulumi up`. Confirm in the console:
- **Lambda → novaSpark-processor-fn:** exists
- **Lambda → novaSpark-processor-fn → Configuration → Triggers:** shows SQS `novaSpark-orders` as a trigger

---

### Step 2.4 — Verify End-to-End

Submit a few more orders:

```bash
curl -X POST $(pulumi stack output orders_url) \
  -H "Content-Type: application/json" \
  -d '{"item": "sprocket", "quantity": 10}'

curl -X POST $(pulumi stack output orders_url) \
  -H "Content-Type: application/json" \
  -d '{"item": "flange", "quantity": 1}'
```

Then navigate to: **Lambda → novaSpark-processor-fn → Monitor → View CloudWatch Logs**

Open the most recent log stream. You should see your processor logs — one line per order showing the `order_id`, item, and quantity.

**Take screenshot D3 now** — the CloudWatch log stream showing your processor logs with at least two order entries. Each entry should show `[ORDER RECEIVED]` and `[ORDER LOGGED]` lines.

> **What you're seeing:** An order went from your terminal → API Gateway → orders Lambda → SQS queue → processor Lambda → CloudWatch. The customer got 202 Accepted in milliseconds. The processing happened asynchronously behind the scenes. The customer never waited for fulfillment.

---

### Step 2.5 — Test a Bad Request

Try submitting an invalid order:

```bash
curl -X POST $(pulumi stack output orders_url) \
  -H "Content-Type: application/json" \
  -d '{"item": "widget"}'
```

You should get a `400 Bad Request` with an error message explaining that `quantity` is required.

**Take screenshot D4 now** — the `curl` command and the 400 response.

> **Input validation at the entry point:** The orders Lambda validates before putting anything on the queue. A malformed order never reaches the processor. This is the right place for validation — not in the processor, where a bad message would retry repeatedly until it hit the DLQ.

---

### Step 2.6 — Find the SQS Queue in the Console

Navigate to **SQS → novaSpark-orders → Monitoring** tab. You should see metrics for messages sent and received.

**Take screenshot D5 now** — the SQS console showing the queue with message activity.

---

## Part 3: Written Deliverables (~20 min)

Complete W1, W2, and W3. Include them in your PDF after D5.

---

### W1 — RESTful URL Design (15 pts)

Write out the full URL design for NovaSpark's order service. You implemented `POST /orders` today — now complete the picture.

Include at least four routes covering: creating an order, retrieving a specific order by ID, listing orders (with a status filter), and canceling an order.

For each route, show: the HTTP method, the path, a one-sentence description, and which parameter type you used (path, query, body) and why.

Then show two anti-patterns from the lecture and their correct equivalents — for example, what you would have written before the lecture vs. what you write now.

---

### W2 — The 202 Decision (15 pts)

Answer the following in 3–5 sentences:

Apply the two diagnostic questions from lecture to the order submission scenario. Why is `POST /orders` asynchronous? What would a synchronous version look like — and what specifically breaks when the fulfillment service is slow? What does the customer experience differ between 200 and 202, and why does it matter?

---

### W3 — The Missing Piece (10 pts)

Answer the following in 3–5 sentences:

Open `app/processor/handler.py` and read the comment block starting with `# TODO (Lab 6 — Storage)`. Ben asks you: "Where are the orders? Can I look up order #abc123?" What is your answer right now? What happens to a log entry if the Lambda container is recycled? What would need to change to make this production-ready, and what AWS service would you reach for?

> This is not a trick question — the answer is intentionally incomplete at this stage. The point is to identify the gap and articulate what fills it.

---

## Deliverables Checklist

Before submitting, confirm you have all of the following in your PDF:

- [ ] D1 — `pulumi up` output showing all resources created, no errors
- [ ] D2 — `curl POST /orders` showing 202 response with `order_id`
- [ ] D3 — CloudWatch log stream from the processor with at least two order entries
- [ ] D4 — `curl POST /orders` with missing field showing 400 response
- [ ] D5 — SQS console showing the queue with message activity
- [ ] W1 — RESTful URL design (4+ routes, anti-patterns, parameter placement)
- [ ] W2 — The 202 decision (3–5 sentences with diagnostic reasoning)
- [ ] W3 — The missing piece (3–5 sentences identifying the persistence gap)

Commit your `__main__.py`, `app/orders/handler.py`, and `app/processor/handler.py` to your course repo. Then run `pulumi destroy` to clean up. The next lab starts from a fresh provided template.
