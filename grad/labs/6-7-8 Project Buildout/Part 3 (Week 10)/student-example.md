# ADD Synthesis — Worked Examples
## CS 545 Week 10: Architecture Overview, Component Decisions, and the Reflection

Use this document before and during the Week 10 synthesis session. Part 1 explains what Sections 2 and 3 are actually doing and why they are assembled rather than written from scratch. Part 2 shows a complete worked Section 2 narrative. Part 3 shows a complete worked Section 3 component entry — the Orders Lambda with the `customer_id` design. Part 4 shows a worked reflection divergence component. Part 5 shows the weak versions of each.

---

## Part 1 — What Sections 2 and 3 Are Doing

### Section 2 is a guided tour, not a new design

Section 2 has two parts: a diagram and a narrative. Neither is written from scratch. The diagram combines drawings you produced across Labs 3–5 and the pipeline diagram from the project roadmap. The narrative is three paragraphs that make the diagram legible to someone who hasn't read the rest of the ADD.

The goal is not to describe the architecture in exhaustive detail — Section 3 does that. The goal is to give the reader a clear mental model of the system before they read the detailed justifications. A reader who finishes Section 2 should be able to close their laptop and sketch the request path from memory.

The three paragraphs each have a single job:
- Paragraph 1: orient the reader — what does the system do and what is each component's role?
- Paragraph 2: trace the request — walk a single `POST /orders` call from client HTTP request to persisted DynamoDB record
- Paragraph 3: ground the context — one sentence on what differs from a production account (LabRole scope, single region, no custom domain)

### Section 3 is justification, not description

A weak Section 3 describes each component. A strong Section 3 argues for it — names what you chose, names what you did not choose, and explains why the choice made for NovaSpark's specific situation.

The minimum content for each component entry:
- What you chose, stated in one sentence
- Why: the specific property that makes it the right fit for this use case
- The rejected alternative, named explicitly
- Why you rejected it, in one sentence

For the API Gateway and Orders Lambda entries specifically, the `customer_id` deployment context must also be stated. That statement is what determines whether the Security pillar finding in Section 4 is a Conscious Tradeoff or an Unknown Gap.

---

## Part 2 — Worked Section 2: Architecture Overview

### The Diagram

The diagram shows the complete request path: Client → API Gateway → Orders Lambda → SQS → Processor Lambda → DynamoDB. The VPC sits underneath with a dotted boundary. The bastion is inside the VPC, labeled "admin access only." API Gateway, Lambda, SQS, and DynamoDB are outside the VPC.

Two IAM execution roles are annotated:
- Orders Lambda execution role: `sqs:SendMessage` + `dynamodb:GetItem` + `dynamodb:Scan`
- Processor Lambda execution role: `dynamodb:PutItem`

---

### The Narrative

**What the system does and what each component's role is:**

The NovaSpark Order API is a serverless REST API that accepts customer orders asynchronously and persists them to DynamoDB. API Gateway is the publicly addressable HTTPS endpoint — any client with the URL can reach it, and it routes incoming requests to the appropriate Lambda handler based on HTTP method and path. The Orders Lambda handles both order submission and retrieval: on `POST /orders`, it enqueues the order to SQS and immediately returns 202 Accepted; on `GET /orders/{id}` and `GET /orders`, it reads directly from DynamoDB. SQS is the decoupling layer between submission and processing — it receives the order message from the Orders Lambda and delivers it asynchronously to the Processor Lambda. The Processor Lambda reads from the SQS trigger, validates the message, and writes the order record to DynamoDB. The VPC contains an EC2 bastion used for admin access only — it is not part of the order submission or retrieval path.

**A single POST /orders request, end-to-end:**

A client sends an HTTP POST to the API Gateway endpoint with a JSON body containing `customer_id`, `item`, and `quantity`. API Gateway routes the request to the Orders Lambda based on the `POST /orders` route configured in `__main__.py`. The Orders Lambda generates a UUID as the `order_id`, sets the initial status to `received`, adds a timestamp, and calls `sqs.send_message()` with the order payload. It immediately returns an HTTP 202 Accepted response with the `order_id` — at this point, the order has not yet been written to DynamoDB. Seconds later (the eventual consistency window observed in testing was approximately 8–15 seconds), the SQS trigger fires the Processor Lambda. The Processor reads the message from the event object, calls `dynamodb.put_item()` with the order fields, and — if the write succeeds — returns without raising an exception, allowing SQS to delete the message from the queue. The order is now retrievable via `GET /orders/{id}`.

**AWS Academy constraints that differ from a production account:**

This stack runs under the LabRole IAM policy, which scopes all resource operations to the Academy account and does not permit custom IAM role creation or VPC endpoint configuration — a production account would use purpose-built execution roles with tighter resource ARN scoping and VPC endpoints to keep Lambda-to-DynamoDB traffic off the public internet.

---

*Commentary:* The narrative above never says "API Gateway is a managed AWS service" — that is a description of what it is, not its role. Every sentence names either a role ("is the publicly addressable HTTPS endpoint") or a behavior ("routes incoming requests"). The request walkthrough is sequential and specific: it names the exact SDK call (`sqs.send_message()`), the exact timing observation (8–15 seconds), and the SQS delete-on-success behavior. The Academy constraints paragraph is one sentence and does not apologize for the environment — it states what is different and what the production fix would be.

---

## Part 3 — Worked Section 3 Entry: Orders Lambda

**What was chosen:**
The submission handler is implemented as an AWS Lambda function (the Orders Lambda) triggered by API Gateway. It handles `POST /orders` by enqueueing the order to SQS and returning 202 immediately, and `GET /orders/{id}` / `GET /orders` by reading from DynamoDB directly.

**Why SQS enqueue rather than synchronous processing:**
A synchronous implementation — where the Orders Lambda calls the processor logic directly and waits for the DynamoDB write to complete — would expose the processor's execution time to the customer. If the processor is slow, cold-starting, or hitting a DynamoDB throttle, the customer's `POST /orders` request blocks until the write succeeds. A 200ms DynamoDB cold path becomes a 2–3 second customer-facing delay. By returning 202 immediately after enqueuing, the submission response time is decoupled from processor execution time, and processor failures are invisible to the customer — the order remains in SQS and will be retried automatically. This directly satisfies NFR-3 from Section 1: *POST /orders returns 202 Accepted under 200ms at p50.*

**Rejected alternative — direct synchronous Lambda-to-Lambda invocation:**
An alternative design would have the Orders Lambda invoke the Processor Lambda synchronously using the Lambda SDK rather than routing through SQS. This eliminates the queue infrastructure but reintroduces the coupling problem: the submission response time includes the processor invocation time, and a Processor Lambda failure surfaces as a 500 error on the submission route. Synchronous invocation also removes the retry behavior SQS provides — a transient failure requires client-side retry logic rather than automatic requeuing.

**The `customer_id` design:**
The Orders Lambda accepts `customer_id` as a required field in the `POST /orders` request body and as an optional query parameter in `GET /orders?customer_id=X`. This design is appropriate for an **internal deployment** — a customer service agent querying on behalf of a customer. In that context, the caller is a trusted internal user, `customer_id` is passed explicitly as an operational parameter, and the absence of per-user authentication at the API layer is an acceptable constraint given the calling context.

For an **external deployment** where customers interact with the API directly, accepting caller-supplied `customer_id` is a documented gap: a customer could supply any `customer_id` and read another customer's orders. The production fix is a Lambda authorizer or Application Load Balancer that validates a JWT token and extracts `customer_id` from the token claims — the customer cannot supply an identity the token doesn't assert. This pattern is outside the scope of this course but is the specific improvement documented in ADD Section 4, Security pillar. The choice to implement `customer_id` as a caller-supplied parameter in the current deployment is a **Conscious Tradeoff** given the internal deployment context — it is not an Unknown Gap, because the external deployment risk was considered and documented rather than overlooked.

**Cross-reference:**
The SQS enqueue decision satisfies NFR-3 (Section 1, Non-Functional Requirements). The `customer_id` design is the subject of the Security pillar finding in Section 4 — see that entry for the ADR.

---

*Commentary:* This entry does five things the weak version doesn't. First, it names the rejected alternative with specificity (Lambda-to-Lambda synchronous invocation, not just "we could have done it differently"). Second, it traces the decision back to a specific NFR from Section 1. Third, it states the `customer_id` deployment context explicitly before naming the gap — which is what makes Section 4's Conscious Tradeoff classification credible. Fourth, it writes the external deployment gap as a specific proposed fix ("Lambda authorizer or ALB that validates a JWT token") rather than "add authentication." Fifth, it ends with cross-references so the reader knows where the decision threads lead in the rest of the document.*

---

## Part 4 — Worked Reflection: Implementation vs. ADD Divergence

The reflection requires you to name at least one place where the implementation diverged from the ADD and give the engineering reason.

**Weak version:**
> "The implementation mostly matched my ADD. There were some small differences but overall the architecture I built matched what I documented."

This earns no credit. It doesn't name a divergence, doesn't cite the ADD, and doesn't give an engineering reason for anything.

**Strong version:**
> "Section 1 of my ADD states NFR-2: `GET /orders/{id}` returns 200 in under 100ms at p95. During Week 10 testing, I observed that the first `GET` request after a cold start on the Orders Lambda took 400–600ms — well outside the NFR. Subsequent requests in the same warm period returned in under 30ms. My ADD did not account for cold-start behavior in the NFR specification — I stated the target as a steady-state figure without acknowledging that cold starts exist or what their frequency would be at NovaSpark's order volume (approximately one cold start per request at 100 orders/day with no provisioned concurrency). The ADD should have specified the NFR as 'under 100ms for warm invocations, with cold starts expected at low-volume traffic patterns,' and Section 5 should have addressed cold start exposure as an operational consideration. The implementation exposed a gap in the requirements specification, not a gap in the build."

*Commentary:* This paragraph names a specific NFR (Section 1 NFR-2), names the observed value (400–600ms), names the cause (cold start), explains why the ADD didn't anticipate it (NFR written as steady-state, not accounting for invocation frequency), and proposes the correction both to the NFR text and to Section 5. It ends with a sharp diagnosis: the implementation was correct, the spec was incomplete. That is genuine engineering reasoning.*

---

## Part 5 — Weak Versions Side by Side

### Weak Section 3 entry

> "API Gateway was used because it is a managed service that handles HTTP routing. It was the right choice for our API. We considered other options but API Gateway was the best fit for NovaSpark."

**What is wrong:** No specific property stated (why HTTP API vs. REST API?). No rejected alternative named. "Best fit" is an assertion, not a reason. No deployment context. No cross-reference to Section 1 or Section 4.

### Weak Section 3 entry (customer_id version)

> "The orders Lambda accepts customer_id from the request. This is a security gap because the caller can supply any customer_id."

**What is wrong:** No deployment context stated — who is the caller? Is this an internal tool or an external deployment? Without that context, "security gap" is either the wrong classification (if it's an internal tool with a documented tradeoff) or incomplete (if it's external and the gap is real but no fix is proposed). The classification must follow from the context.

### Weak Section 2 narrative

> "The architecture consists of API Gateway, Lambda, SQS, and DynamoDB. API Gateway is a managed service that handles HTTPS requests. Lambda is serverless compute. SQS is a queue. DynamoDB is a NoSQL database. Together these services form the NovaSpark Order API."

**What is wrong:** Every sentence describes what a service *is*, not what its *role* is in this system. There is no request walkthrough. A reader who finishes this paragraph cannot sketch the order submission path.

---

## Quick Checklist Before the ADD Is Submitted

**Section 2:**
- [ ] Diagram shows complete path including VPC boundary with Lambda/API GW/SQS/DynamoDB *outside* the VPC
- [ ] Narrative Paragraph 1 names each component's role, not its technology
- [ ] Narrative Paragraph 2 traces one `POST /orders` call component by component to the DynamoDB write
- [ ] Narrative Paragraph 3 states the Academy constraints in one sentence

**Section 3:**
- [ ] Each of the five components has a named rejected alternative
- [ ] At least one Section 3 entry references a specific requirement from Section 1
- [ ] The Orders Lambda entry (or API Gateway entry) states the internal vs. external deployment context explicitly
- [ ] The `customer_id` design is in Section 3 — not only in Section 4

**Cross-references:**
- [ ] Section 4 Security pillar finding cites the deployment context documented in Section 3
- [ ] Section 4 Reliability finding (duplicate delivery / idempotency) cites the Processor Lambda note in Section 3
- [ ] Section 3 SQS or Orders Lambda entry cites the relevant NFR from Section 1

**No scaffolding:**
- [ ] No Q&A format remaining from the Week 8 seed
- [ ] No TODO, PLACEHOLDER, or unanswered prompts
- [ ] Component names are consistent throughout all six sections
