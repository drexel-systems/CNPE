# Week 9 Lab Guide — Cloud Native Lens + Extension Design

**Course:** CS 463 — Cloud Native Platform Engineering
**Week 9 — one session only (holiday week)**
**Single session (80 min):** 8u-CloudNative lecture (35 min) + Lab 8 extension planning (45 min)
**Homework:** 12-factor audit + CNCF mapping (~60 min)
**AWS infrastructure required:** None — analytical + design lab
**Prerequisite:** Week 8 lab complete. W3 answer (your audit-motivated extension choice) submitted.

---

## Important: One Session This Week

This week has a single 80-minute session due to the holiday. That changes the structure of Lab 8. The in-class time is used entirely for the extension design doc — the piece Lab 9 depends on. The 12-factor audit and CNCF mapping move to homework.

**If you leave this session without a committed extension design doc, Lab 9 starts without a plan.** Lab 9 is a build session, not a design session. The design happens today.

---

## The Scenario

It is Wednesday at NovaSpark. Janet stops by.

> **Janet:** "I had a question from our new engineering director: 'is the platform cloud native?' I told her I wasn't sure how to answer that in practice. What would she find if she walked through our architecture?"

> **You:** "I can run it through the 12-factor methodology — that's about as concrete as it gets."

> **Janet:** "Good. And we said after the WAF audit we'd build an extension. I want to see the design before you start coding. One page. Enough that if you got hit by a bus, Linda could pick it up."

The lecture gives you the framework. The lab produces the design doc Janet is asking for.

---

## First 35 Minutes — Compressed Lecture: 8u-CloudNative

### What Cloud Native Actually Means

Cloud native is not a vendor certification or a buzzword. It is a set of architectural properties: loosely coupled, observable, automatable, elastic, designed for failure, declarative. The NovaSpark Order API you built has several of these properties — and several gaps.

### 12-Factor Applied to NovaSpark

The 12-factor app methodology ([12factor.net](https://12factor.net)) describes twelve practices for building software-as-a-service applications that run well in cloud environments. Four of them surface real tension in the NovaSpark architecture — you will audit these in your homework.

| Factor | What it says | NovaSpark status |
|--------|-------------|-----------------|
| **III — Config** | Configuration that changes between environments lives in the environment, not in code | Mostly clean — `QUEUE_URL` and `TABLE_NAME` are env vars. Some values in `__main__.py` may still be hardcoded. |
| **VIII — Concurrency** | Scale out via the process model | Lambda scales horizontally by default. But: if SQS delivers the same message twice, does your processor handle it correctly? |
| **XI — Logs as Streams** | Write to stdout; let the environment route and store | `print()` → CloudWatch satisfies the strict definition. But are the logs structured enough to be queryable? |
| **XII — Admin Processes** | Run one-off tasks in the same environment as the app | No admin process mechanism exists. How would you backfill orders if the schema changes? |

### CNCF Landscape — Brief Orientation

The Cloud Native Computing Foundation maintains an open-source ecosystem of tools that do what the AWS managed services in your stack do — minus the vendor lock-in, plus the operational complexity of running them yourself. You will map five of your AWS services to their CNCF equivalents in your homework.

The key question is not "which is better" but "what specifically is different?" The difference is usually one of operational responsibility, durability semantics, or scaling model. Understanding the difference is what lets you answer "did you consider non-AWS alternatives?" in your demo.

### Cost as an Architectural Decision

At NovaSpark's current scale (low double-digit orders per day), Lambda + DynamoDB is essentially free. At 10,000 orders per day, specific services exit free tier. At 1 million orders per day, the unit economics look completely different. Cost is not an afterthought — it is a design constraint. You do not need to do a full cost analysis for this course, but your demo should include one sentence on why the current architecture is cost-appropriate for NovaSpark's stage.

---

## Next 45 Minutes — Lab 8: Extension Design Doc

This is the only in-class deliverable today. By the end of this session you will have a one-page extension design doc committed to your repo. Everything else is homework.

### Step 1 — Confirm Your Extension Choice (5 min)

Start from your W3 answer in the Week 8 lab. You named an extension motivated by your WAF audit. You have three options now:

**Option A — Build the audit-motivated extension.** Your W3 answer stands. Move to Step 2.

**Option B — Switch to a different menu extension.** You can switch, but your design doc must explain why you moved away from the audit-motivated choice. "I picked PATCH because it looked easiest" earns no credit for the justification. "The DLQ gap I named in W3 is a configuration change, not an extension — PATCH closes the status lifecycle gap which is equally critical and more interesting to demo" is a legitimate reason.

**Option C — Propose a custom extension.** Submit a private Canvas comment to the instructor right now (beginning of this session) with a one-sentence description. The instructor will reply with approval or a redirect before the session ends. If you do not have approval before the session ends, fall back to your W3 answer.

The extension menu for reference:

| Extension | Difficulty |
|-----------|------------|
| `PATCH /orders/{id}` — update order status | Light |
| `DELETE /orders/{id}` — soft cancel | Light |
| `GET /orders?status=...` — status filtering | Light |
| Customer scoping — `GET /orders?customer_id=X` | Light |
| `GET /orders` with cursor pagination | Medium |
| Order notifications via SNS | Medium |
| Lambda authorizer | Heavy |

### Step 2 — Write the Design Doc (40 min)

One page. Six sections. No code — just enough specification that Lab 9 is implementation, not design.

**Section 1 — Extension chosen**
Name it and describe it in one sentence. If custom: note approval status.

**Section 2 — The contract**
What does this extension accept and what does it return?

For route-based extensions:
- HTTP method + path
- Request body shape (if any) — field names and types
- Success response: status code + body shape
- Failure cases: status codes and when each applies (404 if the order doesn't exist, 400 if the status value is invalid, etc.)

For non-route extensions (SNS, authorizer):
- Trigger condition (what causes the extension to fire)
- Observable effect (what changes, what gets logged, what the caller sees)

**Section 3 — Code changes**
Which files change? List them specifically. No code in this section — just the diff list.

Example for `PATCH /orders/{id}`:
- `app/orders/handler.py` — add `handle_patch_order()` function; add `PATCH` routing in the dispatch block
- `__main__.py` — add `dynamodb:UpdateItem` permission to the orders Lambda execution role; add PATCH route to API Gateway

**Section 4 — Pulumi / infrastructure changes**
New resources, modified resources, new permissions. For extensions that need new AWS infrastructure (SNS topic, DLQ, authorizer Lambda), name the resource and its key configuration. For extensions that only change handler logic, state that explicitly: "No new Pulumi resources — only IAM permission updates and Lambda code changes."

**Section 5 — Test plan**
3–5 specific test cases you will run in Postman to confirm the extension works. Must include at least one success case and one failure case.

Example for `PATCH /orders/{id}`:
- PATCH with valid `order_id` and valid status (`processing`) → 200, updated record returned
- PATCH with valid `order_id` and invalid status (`launched`) → 400
- PATCH with `order_id` that doesn't exist → 404
- GET after PATCH confirms status updated in DynamoDB → 200 with new status

**Section 6 — Effort estimate**
How long do you think implementation will take? Be honest. Light extensions should be ≤90 minutes. Medium extensions should be the full 80-minute Lab 9 session. If your custom extension estimate is over 80 minutes, narrow the scope now — not during Lab 9.

---

**Guidance for the customer scoping extension** (if you chose this one):

This extension directly addresses the Security pillar finding from Week 8 — the API currently has no concept of *whose* order it is. You are building the data model foundation for multi-tenant access control.

*The contract:*
- `POST /orders` — body now requires a `customer_id` field (string). The handler stores it in DynamoDB alongside the other order fields.
- `GET /orders?customer_id=X` — returns only orders where `customer_id` matches X. Returns an empty list if no orders exist for that customer (not a 404).
- `GET /orders` with no filter — continues to return all orders (this is the internal/admin behavior, appropriate for customer service tools).

*Code changes:* `orders/handler.py` — add `customer_id` validation in the POST handler; add it to the `put_item` call; add a filter expression to the GET all handler when `customer_id` is present in the query string.

*Infrastructure:* No new Pulumi resources. The DynamoDB table already exists; `customer_id` becomes a simple additional attribute on each record. State this explicitly in Section 4 of your design doc.

*Test plan:* POST two orders with `customer_id=alice`, one with `customer_id=bob`. GET?customer_id=alice returns two records. GET?customer_id=bob returns one. GET with no filter returns all three (admin behavior). GET?customer_id=unknown returns empty list with 200.

*WAF connection:* In your W1 paragraph on submission, note that this extension closes the data scoping gap but does not implement authentication — in production, `customer_id` would be extracted from a JWT token rather than accepted as a caller-supplied parameter. That distinction is the remaining gap to name.

### Step 3 — Commit the Design Doc (5 min)

Save as `/8-CloudNative/extension-design.md` in your repo and push before you leave. This is the contract for Lab 9. If it is not in your repo before Lab 9 starts, you are building without a plan.

---

## Homework — 12-Factor Audit + CNCF Mapping (~60 min)

### Part 1 — 12-Factor Audit (~35 min)

Audit the four factors that surface real design tension in the NovaSpark Order API. For each, use the three-part structure: **What we have → What 12-factor wants → The gap or the case it's already satisfied.**

**Factor III — Config**

12-factor says: configuration that varies between environments lives in the environment, never in code.

- The `QUEUE_URL` and `TABLE_NAME` environment variables on your Lambdas are good 12-factor behavior.
- Look at `__main__.py`: are there values that would change between a dev and a prod deployment? Region? Lambda memory size? The DynamoDB table name (`novaspark-orders` hardcoded as a string)?
- Look at your handler code: anything hardcoded that should be configurable?

**Factor VIII — Concurrency**

12-factor says: scale out via the process model.

- Lambda handles this automatically. But: if SQS delivers the same message twice (standard queues can do this), your processor runs twice for the same order. Look at your `processor/handler.py` — if it runs twice for the same `order_id`, what happens? Does `put_item` overwrite cleanly (accidentally idempotent) or create a data problem?

**Factor XI — Logs as Streams**

12-factor says: write to stdout; the environment routes and stores.

- Your Lambdas use `print()` → CloudWatch. Satisfied in the strict sense.
- But: are your log lines structured? Can CloudWatch Insights parse them? Run this thought experiment: Linda asks you to find all orders for `item=widget` placed in the last 30 minutes. How do you do that with your current logs?

**Factor XII — Admin Processes**

12-factor says: run one-off administrative tasks in the same environment as long-running processes.

- There is no admin process mechanism in your stack. If Janet asks you to update all orders from last Tuesday to `status: processing`, what do you do? (Option 1: edit DynamoDB manually in the console. Option 2: write a script on your laptop. Option 3: write a one-off Lambda. Only Option 3 is close to 12-factor — and you have not set up a pattern for it.)

For the other eight factors (I, II, IV, V, VI, VII, IX, X), write one sentence per factor — assertion + evidence:

> *Factor VI — Stateless Processes: Satisfied. Neither Lambda holds state between invocations; all persistent state lives in SQS and DynamoDB.*

### Part 2 — CNCF Mapping (~25 min)

For five services in your NovaSpark stack, name the closest CNCF or open-source equivalent and write one sentence on a **meaningful difference** — not "X is more flexible" but a specific operational, architectural, or cost property.

| Your AWS service | CNCF / open-source equivalent | One key difference |
|---|---|---|
| API Gateway | *(e.g., Kong, Envoy, Traefik)* | *(one sentence — specific operational property)* |
| Lambda | *(e.g., Knative, OpenFaaS)* | *(one sentence)* |
| SQS | *(e.g., NATS, Kafka, RabbitMQ)* | *(one sentence)* |
| DynamoDB | *(e.g., Cassandra, ScyllaDB)* | *(one sentence)* |
| CloudWatch | *(e.g., Prometheus + Grafana)* | *(one sentence)* |

Strong difference sentences name specific properties. Weak: "Kafka is more powerful." Strong: "Kafka persists messages to disk until a configurable retention window and supports consumer replay; SQS deletes a message once acknowledged, so there is no replay capability — if you need to reprocess historical events, SQS cannot support it."

---

## Deliverables

**In class (due before you leave):**
- [ ] Extension design doc committed to repo at `/8-CloudNative/extension-design.md`

**Homework (submit as a single PDF to Canvas):**
- [ ] **D1 — 12-Factor Audit** — focused entries for Factors III, VIII, XI, XII + one-line statements for the other eight (40 pts)
- [ ] **D2 — CNCF Mapping** — five rows with equivalent + one-sentence difference (20 pts)
- [ ] **D3 — Extension Design Doc** — all six sections (submit the same doc you committed to the repo) (30 pts)
- [ ] **W1 — Extension justification** — 3–5 sentences: which gap from your Week 8 audit does this extension address? If it doesn't address one directly, why is it the right call anyway? (10 pts)

**Total: 100 points.**

---

## What Good Looks Like

**On the design doc:** A reader who has not seen your code should be able to read the design doc and predict roughly which functions and Pulumi resources will change in Lab 9. If the doc says "update the handler" without naming the function or file, it is not specific enough. If it says "add IAM permissions" without naming which permissions and to which role, Lab 9 will get stuck on decisions that should have been made today.

**On the 12-factor audit:** Factor III findings that name actual variable names and file lines beat findings that gesture at "some things might be hardcoded." Factor VIII answers that engage with the idempotency question beat answers that say "Lambda scales automatically."

**On the CNCF mapping:** The "one key difference" column is the entire point of the exercise. The mapping itself takes 5 minutes to look up. The difference requires you to understand what the service actually does operationally.

---

## What This Sets Up

Lab 9 opens with your design doc as the contract. The Lab 9 guide says explicitly: "you arrive with a design doc in hand." If that doc is vague or missing, you spend the first third of Lab 9 deciding what to build instead of building it.

Your 12-factor homework also seeds the "one thing that worked differently than expected" paragraph in your final WAF reflection. Factor XII (admin processes) and Factor XI (structured logging) tend to surface things students didn't notice while building — the kind of genuine surprise the reflection is asking for.
