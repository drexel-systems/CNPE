# Week 8 Lab Guide — Async Order Pipeline + ADD Section 1

**Course:** CS 545 — Cloud Native Platform Engineering
**Paired lecture:** APIs and Event-Driven Architecture (6g-APIandEDA)
**Session structure:** Block 1 (70 min lecture) → Block 2 (40 min seminar) → Block 3 (40 min lab kickoff)
**Estimated total time:** 40 min in class (Block 3) + 90 min homework
**AWS infrastructure required:** Yes — extending your Lab 5 Pulumi stack
**Prerequisite:** Lab 5 complete. Your DynamoDB table (`novaspark-orders`) and Lambda execution role must be deployed.

---

## The Scenario

It is Monday morning at NovaSpark. Lab 5 left you with a DynamoDB table and a Lambda that can read from it. But the table is empty because there is no way to put orders into it yet.

> **Ben:** "Janet is presenting to investors Thursday. She wants to demo the order API — not a slide, not a diagram. A real HTTP call that returns 202, a queue that processes it, and a database read that shows the order. I need this working by Wednesday."
>
> **Linda:** "Before it goes in front of investors I want to understand every architectural decision. Why SQS? Why 202? Why this key design? I'm going to have opinions about each of those and I want them documented."

This lab delivers both. By the end of the in-class session you will have the async pipeline live and testable. The homework turns that working system into ADD Section 1 and the seed of ADD Section 3 — the written record Linda is asking for.

---

## What You Are Getting

You will receive a near-complete Pulumi stack for the NovaSpark async pipeline. It includes:

- An **SQS standard queue** (`novaspark-orders-queue`) already defined as a Pulumi resource
- An **orders Lambda** with a handler that routes `POST /orders`, `GET /orders/{id}`, `GET /orders`, and stubs `PATCH` and `DELETE` as 501 responses. `POST /orders` requires a `customer_id` field in the request body; `GET /orders` supports an optional `?customer_id=X` query parameter to filter results by customer.
- A **processor Lambda** with a handler that reads from SQS and writes each order — including `customer_id` — to DynamoDB
- An updated **API Gateway** with all five routes wired to the orders Lambda
- Updated **IAM role definitions** for both Lambdas

**What is deliberately left for you to configure** — three connection points that represent the most architecturally significant wiring decisions in the pipeline:

1. **The SQS event source mapping** — connecting the SQS queue as a trigger for the processor Lambda
2. **Environment variables** — injecting `QUEUE_URL` and `TABLE_NAME` into the right Lambdas at deploy time
3. **DynamoDB write permissions** — confirming the processor Lambda's execution role has `dynamodb:PutItem` on the orders table

These are not arbitrary exercises. Each one is a decision you will need to explain in ADD Section 3. If you don't understand why `QUEUE_URL` is an environment variable rather than a hardcoded string, you cannot write a credible Section 3.

**A note on API context.** The stack you are deploying uses API Gateway as a publicly addressable HTTPS endpoint — any client with the URL can reach it. The `customer_id` field on `POST /orders` and the `GET /orders?customer_id=X` filter are the data model foundation for multi-tenant access control. In an *internal* deployment (a customer service tool used by employees), any agent passes `customer_id` explicitly to look up any customer's orders. In an *external* deployment (a customer-facing app), `customer_id` would be extracted from a verified JWT token rather than trusted as caller input — ensuring customers can only see their own data. Your ADD Section 3 and Section 4 are where you document this design choice and classify the authentication gap.

---

## Part 1 — Configure and Deploy (Block 3, ~40 min in class)

### Before you start

Confirm your Lab 5 stack is currently deployed and healthy:

```bash
cd your-lab-5-directory
pulumi stack output
```

You should see your DynamoDB table name and your Lambda function name in the outputs. If the stack isn't deployed, run `pulumi up` now. Do not move to Part 1 until Lab 5 is running.

### Step 1 — Pull the starter stack

The Week 8 starter files are distributed via GitHub Classroom. Pull them into a new directory in your repo:

```
/6-API/
  __main__.py          ← near-complete Pulumi stack (3 TODOs marked)
  orders/
    handler.py         ← orders Lambda handler (complete)
  processor/
    handler.py         ← processor Lambda handler (complete)
  requirements.txt
```

Open `__main__.py`. You will see three `# TODO` blocks — one for each connection point. Everything else is complete and should not need modification.

### Step 2 — Configure the three connection points

Work through the three TODOs in order. Each one has a comment block explaining what it does and a link to the relevant Pulumi/AWS documentation.

**TODO 1 — SQS event source mapping**

Find the block labeled `# TODO 1: Wire SQS trigger to processor Lambda`. You need to add a `aws.lambda_.EventSourceMapping` resource that connects the SQS queue to the processor Lambda.

Key parameters to set:
- `event_source_arn` — the ARN of the SQS queue (use Pulumi's output reference, not a hardcoded string)
- `function_name` — the processor Lambda's name (again, use the Pulumi output)
- `batch_size` — set to `1` for now (one message processed per invocation; simpler to debug)

> *Why batch_size = 1?* At NovaSpark's current scale, processing one order at a time is fine and makes CloudWatch logs much easier to read during testing. A batch size of 10 would be appropriate at 10K orders/day. This is a decision worth noting in ADD Section 3.

**TODO 2 — Environment variables**

Find the block labeled `# TODO 2: Set environment variables on both Lambdas`.

The orders Lambda needs:
- `QUEUE_URL` — the SQS queue URL (Pulumi output reference)
- `TABLE_NAME` — the DynamoDB table name (Pulumi output reference from your Lab 5 stack, or re-declared here)

The processor Lambda needs:
- `TABLE_NAME` — the same DynamoDB table name

> *Why environment variables?* The handler code reads `os.environ["QUEUE_URL"]` rather than having a URL hardcoded. This is 12-factor Factor III — configuration that varies between environments lives in the environment, not in code. If you deployed a dev and a prod version of this stack, each would have a different `QUEUE_URL` injected automatically. This is worth one sentence in ADD Section 1's 12-factor compliance hooks paragraph.

**TODO 3 — DynamoDB write permissions**

Find the block labeled `# TODO 3: Add DynamoDB PutItem permission to processor role`.

The processor Lambda's execution role needs `dynamodb:PutItem` on the orders table. The orders Lambda already has `dynamodb:GetItem` and `dynamodb:Scan` from Lab 5. Add only what is missing — do not replace the existing policy.

> *Why not `dynamodb:*`?* Least privilege. The processor only writes. The orders Lambda only reads. A role with `dynamodb:*` would grant each Lambda permissions it never uses — exactly the kind of overly permissive IAM configuration that surfaces in a Security pillar audit. Expect to cite this in ADD Section 4.

### Step 3 — Deploy and verify

```bash
pulumi up
```

The deployment should add the event source mapping and update both Lambda configurations. When it completes, capture the `orders_url` stack output — this is your API Gateway endpoint.

Confirm the pipeline is alive with a quick `curl`:

```bash
curl -X POST <orders_url>/orders \
  -H "Content-Type: application/json" \
  -d '{"item": "widget", "quantity": 3, "customer_id": "cust-001"}'
```

Expected: `{"message": "Order received", "order_id": "..."}` with HTTP 202. If you omit `customer_id`, you should get a `400 Bad Request` — the handler validates it as a required field.

If you get 202, the orders Lambda and SQS are working. Move to Part 2.
If you get 500, check CloudWatch Logs for the orders Lambda — the most common issue is a missing environment variable.

---

## Part 2 — Test the Full Pipeline with Postman (~30 min, in class or early homework)

Import the NovaSpark Orders Postman collection (provided in the repo). Set the `api_url` environment variable to your `orders_url` output.

### Test sequence

Run requests in this order and observe what happens at each step.

**Test 1 — Submit an order**

`POST /orders` — include `customer_id` in the body (e.g., `"customer_id": "cust-001"`). Confirm `202 Accepted` and note the `order_id` in the response body. Copy it. Then submit the same request without `customer_id` — confirm you get `400 Bad Request`.

**Test 2 — Immediate retrieval (the consistency window)**

Immediately run `GET /orders/{id}` using the `order_id` from Test 1. You will likely get a `404`. This is not a bug. This is the eventual consistency window — the order has been accepted and is sitting in SQS, but the processor Lambda has not yet written it to DynamoDB. Record how long this 404 persists.

Run `GET /orders/{id}` again after 5–10 seconds. You should now get `200` with the order record — confirm `customer_id` is present in the stored record. Record the time elapsed. This window — from POST to GET visibility — is the **pipeline consistency window**, and it is a Reliability finding in your ADD Section 4.

**Test 3 — List all orders**

Run `GET /orders`. Confirm your order appears in the list.

**Test 4 — Submit orders for multiple customers, then filter**

Submit 2–3 orders with `customer_id: "cust-001"` and 1–2 orders with `customer_id: "cust-002"`. Then:
- Run `GET /orders?customer_id=cust-001` — confirm only cust-001's orders appear.
- Run `GET /orders?customer_id=cust-002` — confirm only cust-002's orders appear.
- Run `GET /orders` with no filter — confirm all orders appear (internal/admin behavior).

This test demonstrates both the data scoping behavior and the internal vs. external API distinction. In your ADD Section 3 seed, you will document why `customer_id` is accepted as a parameter here and what would change for a production external deployment.

### What to capture

Take screenshots of:
- The 202 response from `POST /orders` (showing `order_id` and `customer_id` in the body)
- The 400 response from `POST /orders` without `customer_id` (showing validation)
- The 404 immediately after POST (showing the consistency window exists)
- The 200 after waiting (showing the order persisted with `customer_id`)
- The `GET /orders?customer_id=X` response showing filtered results

These screenshots are part of your lab submission and will also appear in your demo video.

---

## Part 3 — Architectural Q&A → ADD Sections 1 and 3 (Homework, ~90 min)

This is the written component of the lab. Answer each question in the format specified. Your answers become the first drafts of ADD Section 1 and ADD Section 3.

The questions are not abstract — they are about decisions visible in the code you just deployed. Go back to `__main__.py` and the handler files as you write.

---

### Section 1: Requirements (target: ~1.5 pages)

Write four short subsections.

**1a — Functional Requirements**

List the system's functional requirements as discrete, testable statements. For each of the three core routes, state what request it accepts and what observable behavior it produces. Include the async pipeline behavior as a requirement — not just "orders are processed" but what the processing entails and what state it leaves in DynamoDB.

Example format (do not copy verbatim — write your own based on what you observed):
> FR-1: `POST /orders` accepts a JSON body with `item` (string), `quantity` (integer), and `customer_id` (string, required), places the order on the SQS queue, and returns `202 Accepted` with an `order_id` within 200ms. A missing `customer_id` returns `400 Bad Request`.
> FR-2: `GET /orders/{id}` returns the full order record for a valid `order_id` with `200 OK`, or `404 Not Found` if the order does not exist in DynamoDB.
> FR-3: `GET /orders` returns all orders. Supports an optional `?customer_id=X` query parameter to return only orders for that customer. An unrecognized `customer_id` returns `200` with an empty list.

Include a requirement that addresses the API context: this is a publicly addressable endpoint, and the current implementation accepts `customer_id` as caller-supplied input. State whether this is a documented constraint or a gap relative to external deployment requirements.

**1b — Non-Functional Requirements**

State at least four non-functional requirements with specific numbers. Cover latency, availability, throughput, and the eventual consistency window you observed in Test 2.

> Guidance: "The system should be fast" is not a non-functional requirement. "POST /orders returns 202 Accepted at p50 under 200ms" is. Your consistency window observation gives you a real number for the pipeline latency NFR.

**1c — Constraints**

Name the real constraints this architecture operates under. At minimum: the AWS Academy sandbox (LabRole IAM scope — what can you not do because of it?), single-region deployment, and the Pulumi/Python toolchain.

Include the authentication gap as an explicit constraint: this API is publicly addressable and accepts `customer_id` as caller-supplied input. For an internal tool (customer service agents querying on behalf of customers), this is a reasonable operational constraint. For an external deployment where customers interact with the API directly, this is a documented gap — in production, `customer_id` would be extracted from a verified JWT token issued by an authorization service, not accepted from the request body. That pattern (JWT validation via an Application Load Balancer or API Gateway authorizer) is outside the scope of this course but is a natural next step to explore.

**1d — 12-Factor Compliance Hooks**

One paragraph. Name three 12-factor principles your architecture satisfies with specific evidence, and one where a real gap exists.

> Suggested starting points: Factor III (Config) — the environment variables you set in TODO 2; Factor VI (Stateless Processes) — what state does your Lambda hold between invocations?; Factor XI (Logs as Streams) — `print()` to CloudWatch; Factor XII (Admin Processes) — how would you run a one-off data backfill?

---

### Section 3 Seed: Component Decisions (target: ~1 page, to be expanded in Week 10)

For each of the five major components below, answer the three questions. This is the seed for ADD Section 3 — you will expand and polish it during the Week 3 synthesis session. Write in draft form; complete sentences but no need for final polish.

**API Gateway (HTTP API)**
- What did you choose and why?
- What is one alternative you considered? (REST API product? Direct Lambda URL?)
- Why did you reject it?
- This API Gateway is deployed as a publicly addressable HTTPS endpoint — any client with the URL can reach it. Is that the right choice for NovaSpark's use case? What would change architecturally if this were an internal API reachable only from a private network?

**Orders Lambda**
- What runtime, memory, and timeout did you configure?
- Were these deliberate choices or defaults? What would change at higher throughput?
- What is the single most important thing this Lambda must not do (i.e., what would break the 202 semantics)?
- The handler accepts `customer_id` as a required field in `POST /orders` and as a query parameter in `GET /orders`. For what calling context is this design appropriate as-is? What would need to change for a production external deployment where customers should only see their own orders?

**SQS Queue (standard)**
- Why SQS between the orders Lambda and the processor, rather than a synchronous call?
- Why a standard queue rather than a FIFO queue?
- What is the failure mode if the processor Lambda crashes after receiving a message but before writing to DynamoDB?

**Processor Lambda**
- What is the batch size you configured and why?
- What happens if SQS delivers the same message twice? (Look at your `put_item` call — is the second write idempotent?)
- What should happen when the processor fails to write to DynamoDB? Does your current implementation handle this correctly?

**DynamoDB Table**
- What is your partition key and why?
- Why on-demand capacity rather than provisioned?
- You designed this table in Lab 5 — is the access pattern you designed then still correct for the full pipeline you have now?

---

## Deliverables

Submit a single PDF (or markdown rendered to PDF) containing:

- [ ] **D1 — Postman screenshots** — five screenshots per the test sequence above (15 pts)
- [ ] **D2 — ADD Section 1: Requirements** — four subsections as described (40 pts)
- [ ] **D3 — ADD Section 3 Seed: Component Decisions** — five components, three questions each (30 pts)
- [ ] **D4 — Context paragraph** — 150–250 words connecting the Vogels *Eventually Consistent* reading to the consistency window you observed in Test 2. What does eventual consistency mean specifically for a customer who submits an order and immediately queries for it? Is the pipeline consistency window you observed the same thing as DynamoDB eventual consistency? (15 pts)

**Total: 100 points.**

Also commit to your GitHub repo:
- `/6-API/__main__.py` — your completed Pulumi stack with the three TODOs resolved
- `/6-API/orders/handler.py` — unchanged (or note any modifications)
- `/6-API/processor/handler.py` — unchanged (or note any modifications)

---

## What Good Looks Like

**On the Section 1 requirements:** Numbers, not adjectives. "The system should handle reasonable load" earns no credit. "The system targets p50 latency of 200ms for POST /orders at NovaSpark's current throughput of ~100 orders/day" earns full credit. Use your Postman observations as evidence — you have real latency data from testing.

**On the Section 3 seed:** The SQS vs. synchronous-call question is the most important one in this section. A strong answer names the specific failure mode that a synchronous call creates (processor latency directly affects customer response time; processor failure causes 5xx to the customer) and explains why SQS eliminates it. A weak answer says "SQS is better for async processing" without naming the failure mode.

**On the context paragraph:** The Vogels reading argues eventual consistency is a design choice, not a bug. Your paragraph should name whether your pipeline's consistency window is a designed, documented choice or an unknown gap. There is no right answer — but there is a difference between saying "we accept eventual consistency because the pipeline is async by design and customers are informed via 202" and saying "we didn't think about what a customer does in the window between POST and GET."

---

## What This Sets Up

Your ADD Section 1 draft and Section 3 seed are the foundation the next two weeks build on. In Week 9, the WAF audit will reference specific decisions you documented here — the IAM scope you set in TODO 3, the batch size you chose in TODO 1, the consistency window you observed in Test 2. In Week 10, Section 3 gets expanded and integrated with Section 2 into a coherent architecture narrative.

If Section 1 is vague — full of adjectives instead of numbers, constraints instead of real constraints — the downstream sections will be weaker. This is the week to get it right.
