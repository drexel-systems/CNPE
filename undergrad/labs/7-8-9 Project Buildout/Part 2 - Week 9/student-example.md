# Extension Design Doc — Worked Example
## CS 463 Week 9: What a Good Design Doc Looks Like

Use this document before you write your own extension design doc in Lab 8. Part 1 explains what the design doc is actually for and what each section needs to do. Part 2 shows a complete worked example — `PATCH /orders/{id}` — with commentary on what makes each section effective. Part 3 shows a weak version of the same doc so you can see the difference.

---

## Part 1 — What the Design Doc Is For

The design doc has one job: make Lab 9 a build session, not a design session.

Lab 9 is 80 minutes. If you arrive knowing exactly what you are building — what the route accepts, what it returns, which files change, what Postman test confirms it works — you will finish. If you arrive deciding those things in Lab 9, you will spend the first 30 minutes figuring out what to build and the last 50 minutes rushing.

The six sections are not bureaucracy. Each one closes a specific type of uncertainty that would otherwise surface mid-build:

| Section | What uncertainty it closes |
|---------|---------------------------|
| Extension chosen | Are we aligned on what I'm building? |
| The contract | What does success look like from the caller's perspective? |
| Code changes | Which files am I touching, and what am I adding to each one? |
| Pulumi / infrastructure | Do I need new AWS resources, or is this just handler code? |
| Test plan | How will I know it works before the demo? |
| Effort estimate | Will this actually fit in 80 minutes? |

A design doc that leaves any of these questions unanswered is not a design doc — it is a wish. Write it so that someone else could pick it up and build the same extension without asking you a single question.

---

## Part 2 — Complete Worked Example: `PATCH /orders/{id}`

The following is a complete, well-written extension design doc. After each section, commentary in *italics* explains what makes it effective. Use the same level of specificity in your own doc.

---

### Section 1 — Extension Chosen

`PATCH /orders/{id}` — Update the status of an existing order by ID.

*One sentence. Names the HTTP method, the path, and what it does. No ambiguity about which extension this is.*

---

### Section 2 — The Contract

**HTTP method + path:** `PATCH /orders/{id}`

**Request body:**
```json
{
  "status": "string"
}
```
The only accepted field is `status`. No other fields are read or stored by this route.

**Valid status values:** `pending`, `processing`, `fulfilled`, `cancelled`

**Success response:**
- Status code: `200`
- Body: the full updated order record as stored in DynamoDB
```json
{
  "order_id": "abc-123",
  "item": "widget",
  "quantity": 2,
  "status": "processing",
  "customer_id": "alice"
}
```

**Failure cases:**

| Condition | Status code | Body |
|-----------|-------------|------|
| `order_id` does not exist in DynamoDB | `404` | `{"error": "Order not found"}` |
| `status` field is missing from the request body | `400` | `{"error": "Missing required field: status"}` |
| `status` value is not in the valid list | `400` | `{"error": "Invalid status value"}` |
| Request body is not valid JSON | `400` | `{"error": "Invalid request body"}` |

*This section is the most important one in the doc. It defines the behavior completely — not just the happy path. A caller reading this knows exactly what to send and exactly what they will get back in every case. Notice that valid status values are enumerated explicitly: "pending, processing, fulfilled, cancelled." Without that list, the builder has to decide what is valid during implementation — that is a design decision, not an implementation decision, and it belongs here.*

---

### Section 3 — Code Changes

**`app/orders/handler.py`**
- Add a `handle_patch_order(order_id, body)` function
- Parse `status` from the request body; validate against the allowed list
- Call `dynamodb.update_item()` with a `ConditionExpression` to ensure the item exists; catch `ConditionalCheckFailedException` and return 404
- Return the updated item on success
- Add `PATCH` method routing in the main `lambda_handler` dispatch block alongside existing `GET` and `POST` routing

**`__main__.py`**
- Add `dynamodb:UpdateItem` to the Lambda execution role's IAM policy (currently only has `PutItem`, `GetItem`, `Scan`)
- Add a `PATCH` method to the existing `/orders/{id}` API Gateway resource

*Every changed file is named, and the specific change to each file is described. Not "update the handler" — but "add `dynamodb:UpdateItem` to the IAM policy." This matters because the IAM change is the one most likely to be forgotten during a build session. Writing it here means it won't be.*

---

### Section 4 — Pulumi / Infrastructure Changes

No new AWS resources required.

Two existing resources require changes:
- **Lambda execution role IAM policy** (`orders_lambda_role_policy` in `__main__.py`) — add `dynamodb:UpdateItem` to the existing `Action` list
- **API Gateway method** — add a `PATCH` method to the existing `/orders/{id}` resource, alongside the current `GET` method

No new DynamoDB tables, Lambda functions, SQS queues, or other resources are needed. The status field is an attribute update on an existing DynamoDB item — no schema or table configuration changes required.

*Two things make this section effective: it explicitly says "no new resources," and it names the specific existing resources that change. Students often forget the IAM permission update because it's in `__main__.py` and feels disconnected from the handler code. Writing it here means it shows up on your checklist during the build.*

---

### Section 5 — Test Plan

All tests run in Postman against the live stack after `pulumi up`.

**Test 1 — Happy path: valid status update**
- First submit an order via `POST /orders` and retrieve the `order_id`
- `PATCH /orders/{order_id}` with body `{"status": "processing"}`
- Expected: `200`, response body includes `"status": "processing"`

**Test 2 — Confirm persistence**
- Immediately after Test 1, run `GET /orders/{order_id}`
- Expected: `200`, response body shows `"status": "processing"` — confirms DynamoDB was actually updated, not just returned from handler memory

**Test 3 — Invalid status value**
- `PATCH /orders/{order_id}` with body `{"status": "launched"}`
- Expected: `400`, response includes error message about invalid status

**Test 4 — Missing status field**
- `PATCH /orders/{order_id}` with body `{}`
- Expected: `400`, response indicates missing required field

**Test 5 — Order not found**
- `PATCH /orders/nonexistent-id` with body `{"status": "processing"}`
- Expected: `404`, response includes error message about order not found

*Five tests. Two success cases (update + persistence check), three failure cases. Test 2 is the one most students skip — and it is the most important one. Returning a 200 with the updated body is easy to fake accidentally. `GET` after `PATCH` confirms the data actually persisted in DynamoDB. Including at least one "confirm persistence" test in your plan is what separates a tested extension from a demo that works by coincidence.*

---

### Section 6 — Effort Estimate

**Estimated time: 60–75 minutes**

| Task | Estimated time |
|------|---------------|
| Add `handle_patch_order()` to handler, including validation and DynamoDB call | 25 min |
| Update dispatch block in `lambda_handler` | 5 min |
| Update IAM policy and API Gateway in `__main__.py` | 10 min |
| `pulumi up` and initial smoke test | 10 min |
| Run full Postman test plan, debug failures | 15 min |

Primary risk: the `ConditionExpression` on `update_item` to handle "order not found" cleanly. If that takes longer than expected, the fallback is to catch the error less specifically and return 404 on any DynamoDB exception — that is acceptable for the demo.

*The estimate is broken into tasks, not given as a single number. This matters because it tells you where you might get stuck. The "primary risk" note is the part most students skip — and it's the most useful part of an effort estimate. If you know where the complexity is before you start, you can decide in advance what the fallback is. That decision takes 10 seconds here and 15 minutes mid-build.*

---

## Part 3 — What a Weak Design Doc Looks Like

The following is a design doc for the same extension that would not pass. Read it and identify what is missing before continuing.

---

**Extension:** PATCH endpoint to update orders

**Contract:** Send a PATCH request with the new status. Returns the updated order or an error.

**Code changes:** Update the handler file to support PATCH. Update Pulumi to add permissions.

**Infrastructure:** Update IAM and API Gateway.

**Test plan:** Test that the PATCH works and returns the right response.

**Effort estimate:** About an hour.

---

**What is missing:**

The contract does not say what field names to use, what the valid status values are, what status codes are returned, or what the error responses look like. The builder will make all of those decisions during implementation — which means Lab 9 is partly a design session.

The code changes section names files but not what changes inside them. "Update the handler" does not tell you whether you need `dynamodb:UpdateItem` or not.

The infrastructure section restates "update IAM and API Gateway" without saying which resource, which permission, or what specifically to add. The IAM change will get forgotten.

The test plan has one test that is not actually described. There are no failure cases. There is no persistence check.

The effort estimate is a guess with no task breakdown and no identified risk. If the `ConditionExpression` takes longer than expected, there is no fallback plan.

---

**The difference is not length. The difference is specificity.**

The worked example and the weak version are both complete in structure. The weak version skips the specific details that make each section useful. By the time you commit your design doc, every cell in the contract table should be filled in, every file change should be named, and your test plan should include at least one failure case and one persistence check.

---

## Quick Checklist Before You Commit

Before you push your design doc, verify:

- [ ] Section 2 names the HTTP method, path, request body fields, success status code and body shape, and at least two failure cases with status codes
- [ ] Section 3 names each specific file that changes and what is being added to it (not just "update the handler")
- [ ] Section 4 explicitly says whether new Pulumi resources are required — if not, says so directly
- [ ] Section 5 has at least one success case, one failure case, and one test that confirms persistence (a GET after a write)
- [ ] Section 6 has a task breakdown and names the most likely place to get stuck

If any of these are missing, the design doc is not done.
