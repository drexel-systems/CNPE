# NovaSpark Order API — Course Project Roadmap

**CS 545 · Cloud Native Platform Engineering (Graduate)**
**Dr. Brian Mitchell · Drexel University**

---

## Where We Are

The first four weeks of this course were about building the analytical and technical foundation behind every modern cloud system. You deployed real AWS infrastructure — EC2 instances, VPC networks, a serverless Lambda function — configured it through Infrastructure as Code, and produced written justifications for every major decision. That written justification is what distinguishes this course from a hands-on tutorial.

Here is what you have built and analyzed so far:

| Lab | What You Built | What You Analyzed |
|-----|---------------|-------------------|
| Lab 1 | AWS CLI, EC2, SSH access | The economics and model of managed cloud services |
| Lab 2 | EC2 + S3 + IAM via Pulumi | Why IaC creates discipline — and where it creates new failure modes |
| Lab 3 | VPC: subnets, routing, security groups, bastion host | Network boundary design and blast radius of misconfiguration |
| Lab 4 | Lambda + API Gateway, cold start measurement | Serverless limitations, IAM execution roles, event object abstraction |
| Lab 5 | DynamoDB table connected to Lambda | Access pattern design, consistency tradeoffs, RTO/RPO |

Labs 1–5 gave you the building blocks. Everything from this point on assembles them into a coherent system.

---

## The Pivot

NovaSpark's status endpoint is live and the DynamoDB table is provisioned. But the business problem is larger than a status check.

> **Ben:** "We're still taking orders by email. Literally email. Janet wants a real order API by end of quarter — something customers can hit, something that persists data, something we can actually operate."

> **Linda:** "And if we're going to call this production-ready, I want to score it against the Well-Architected Framework before it ships. Every pillar."

> **Janet:** "Before we build it, I want a design document. I want to know what we're building, why we're building it that way, and what we're trading off. We've been burned before by building first and thinking second."

Janet's ask is the Architecture Design Document. Linda's ask is the WAF audit. Ben's ask is the working API. The remaining weeks deliver all three — in that order, because designing before building is what distinguishes an architect from a developer.

---

## What You're Building

The **NovaSpark Order API** is a serverless REST API that accepts customer orders, processes them asynchronously through a message queue, and persists them to the DynamoDB table you provisioned in Lab 5. It is the kind of service that sits at the core of almost every e-commerce, logistics, and SaaS platform in production today.

By the time you finish, your system will:

- Accept order submissions and respond immediately with a confirmation (not a wait)
- Process orders asynchronously through an SQS queue
- Persist every order to DynamoDB, readable by ID or listed in full
- Be deployed entirely through Pulumi — no manually created resources
- Be testable end-to-end with a Postman collection you can run against any environment
- Be defensible — you can explain every architectural decision in writing and on camera

---

## The Architecture Design Document

The ADD is due Week 7 — before the final implementation sprint. This is intentional. The labs give you the raw material; the ADD is where you synthesize it into an architectural argument.

### How the Labs Feed the ADD

Every lab produces a direct input to a section of the ADD. Students who complete the labs with care will find the ADD largely writes itself from prior work.

| Lab | ADD Section |
|-----|-------------|
| Lab 3 — VPC diagram and routing justification | Section 2: Architecture Overview (network layer) |
| Lab 4 — Cold start analysis, IAM role evaluation | Section 3: Component Decisions (compute), Section 4: WAF (Security pillar) |
| Lab 5 — Access pattern design, RTO/RPO analysis | Section 3: Component Decisions (storage), Section 4: WAF (Reliability pillar) |
| Lab 6 — Async pipeline, 202 vs 200 justification | Section 1: Requirements, Section 3: Component Decisions (messaging), Section 5: Operational Considerations |
| Lab 7 — WAF audit of your own system | Section 4: Well-Architected Analysis (direct input) |

### What the ADD Must Cover

- **Section 1: Requirements** — functional requirements (the five API routes, the async pipeline), non-functional requirements (latency, availability, cost), and real constraints (AWS Academy IAM sandbox, LabRole limitations)
- **Section 2: Architecture Overview** — system diagram and narrative covering every component: API Gateway, order Lambda, SQS queue, processor Lambda, DynamoDB table
- **Section 3: Component Decisions** — for each major component: what you chose, why, and at least one alternative you considered and rejected
- **Section 4: Well-Architected Analysis** — honest evaluation against all six pillars; name the gaps explicitly
- **Section 5: Operational Considerations** — which CloudWatch metrics matter for an async pipeline, failure modes and mitigations, what happens when the processor Lambda fails
- **Section 6: Cost Estimate** — AWS Pricing Calculator estimate at 100 / 10K / 1M requests per day

A strong ADD takes a position. It does not describe what each AWS service does — it argues for why you made the choices you made, acknowledges the tradeoffs honestly, and demonstrates that you thought about what happens when things go wrong.

---

## The API Specification

This is the full API you are building. Lab 6 implements POST /orders and stubs the rest. The remaining routes are completed as part of the final project. The spec does not change — your implementation catches up to it.

### Resource: Orders

| Method | Path | Description | Status Code |
|--------|------|-------------|-------------|
| `POST` | `/orders` | Place a new order | `202 Accepted` |
| `GET` | `/orders` | List all orders (optional `?status=` filter) | `200 OK` |
| `GET` | `/orders/{id}` | Retrieve a specific order by ID | `200 OK` or `404` |
| `PATCH` | `/orders/{id}` | Update an order's status | `200 OK` |
| `DELETE` | `/orders/{id}` | Cancel an order (soft delete) | `204 No Content` |

### Order Data Model

```json
{
  "order_id": "a3f1c2d4-...",
  "item": "widget",
  "quantity": 3,
  "status": "received",
  "created_at": "2026-05-06T14:32:00",
  "updated_at": "2026-05-06T14:32:00"
}
```

**Status lifecycle:** `received → processing → shipped` (or `cancelled` at any point via soft delete — the record stays in DynamoDB with `status: cancelled`).

### Design Decisions Worth Defending in Your ADD

**Why `POST /orders` returns 202 and not 200?**
A 202 means "I received your request and I am working on it." The order is queued, not fulfilled. Returning 200 would be a semantic lie that clients would act on incorrectly. Your ADD Section 3 should defend this choice explicitly.

**Why soft delete on `DELETE /orders/{id}`?**
Permanently deleting an order destroys the audit trail. Setting `status: cancelled` means the record survives, history is preserved, and the API remains idempotent. Your ADD should address this in the Operational Considerations section — what does the data lifecycle look like over time?

**Why SQS between the order Lambda and the processor?**
The fulfillment pipeline can be slow and variable. A synchronous call couples the customer's response time to the processor's performance. SQS decouples them — the customer gets 202 immediately, and the processor works at its own pace. Your ADD Section 3 should include at least one rejected alternative (synchronous call, SNS direct invocation) and explain why you chose SQS.

**Why `?status=` as a query parameter and not a path segment?**
`/orders?status=received` is filtering a collection. `/orders/received` would imply `received` is a resource identifier. Filters belong in query parameters; resource identity belongs in the path. Your ADD should note the DynamoDB implications — filtering by status requires a Scan or a GSI, not a simple key lookup.

---

## Testing with Postman

Starting with Lab 6, you will use **Postman** alongside `curl` to test your API. A pre-built **NovaSpark Orders collection** is provided as a `.json` file you can import directly into Postman. It includes all five routes with sample request bodies and a single environment variable — `api_url` — that you set to your Pulumi stack output URL.

Setting `api_url` as a Postman environment variable is the same principle as `os.environ["QUEUE_URL"]` in your Lambda handler — configuration injected at runtime, not hardcoded. Your ADD Section 5 (Operational Considerations) should note how this pattern makes the system testable across environments without code changes. This is 12-factor Factor III in practice.

---

## Lab and Milestone Roadmap

| | `POST /orders` | `GET /orders/{id}` | `GET /orders` | `PATCH` | `DELETE` | ADD | WAF Audit |
|-|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| After Lab 5 | — | — | — | — | — | Drafting | — |
| After Lab 6 | ✅ Live | 🔲 Stubbed | 🔲 Stubbed | 🔲 Stubbed | 🔲 Stubbed | In progress | — |
| After Lab 7 (WAF) | ✅ | 🔲 | 🔲 | 🔲 | 🔲 | ✅ Submitted | ✅ |
| Week 9 (Extensions) | ✅ | ✅ | ✅ | Your choice | Your choice | ✅ | ✅ |
| Final project | ✅ | ✅ | ✅ | Per extension | Per extension | ✅ | ✅ |

---

## Extension Options

The core API is complete after Week 9's implementation session. Extensions are what differentiate final projects. Every extension has a technical component and an analytical requirement — the code alone is not sufficient.

| Extension | What You Build | Analytical Requirement in Reflection |
|-----------|---------------|-------------------------------------|
| `PATCH /orders/{id}` | Update order status via API | Explain idempotency and conditional write design in DynamoDB |
| `DELETE /orders/{id}` | Soft-cancel orders | Explain why soft delete preserves the audit trail; address idempotency |
| Status filtering | `GET /orders?status=received` | Explain DynamoDB Scan vs. GSI query tradeoff at scale |
| Authentication | Lambda authorizer validates a token | Explain the OAuth flow and how the authorizer mitigates the confused deputy problem |
| Order notifications | SNS fan-out on order placement | Explain at-least-once delivery implications and fan-out failure handling |
| Observability | CloudWatch dashboard + alarms | Justify each metric and threshold against a defined SLO for the order pipeline |
| Custom extension | Propose your own | Instructor approval required by Week 9 session; written proposal required |

---

## The Final Deliverables

Your final project submission has four parts:

**1. A working API** — deployed through Pulumi, all three core routes functional, at least one extension implemented. `pulumi up` and `pulumi destroy` both run cleanly.

**2. A demo video (5–7 minutes)** — run `pulumi up`, execute the Postman collection against your live API (all core routes + extension), walk through the architecture diagram and explain each component, explain two decisions from your ADD (did the implementation match your design? if not, why not?), then run `pulumi destroy`.

**3. A written reflection (1–2 pages)** — where did your implementation match your ADD? Where did it diverge and why? One WAF pillar addressed well with a specific code or configuration example. One pillar not addressed with a concrete proposed fix. Cost analysis at three traffic levels — does the architecture remain cost-effective at scale?

**4. ADD alignment** — your reflection must explicitly reference your ADD. The point is not that your implementation matched the design perfectly — it almost never does. The point is that you can account for the gap with engineering reasoning.

Simple and correct beats ambitious and half-working. A clean three-route API with a thoughtful ADD and honest reflection is a stronger submission than a complex system with vague justification.

---

## What Good Looks Like

By the time you demo, you should be able to do all of the following:

- Run `pulumi up` from a clean state and have the full stack live in under two minutes
- Run the Postman collection and show orders flowing through the full pipeline — submission, queue, processor, DynamoDB, retrieval
- Point to your ADD and explain one place where your implementation diverged from your design — and give the engineering reason why
- Name the specific IAM permission that LabRole grants that a least-privilege role would not, and explain why that matters in production
- Explain, in plain language, why order submission is asynchronous — what concretely breaks if the processor Lambda is slow and the submission is synchronous

If you can do all five of those things, you have learned what this course set out to teach.

---

*This document will be updated as labs are finalized. Check the course repository for the latest version.*
