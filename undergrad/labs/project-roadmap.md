# NovaSpark Order API — Course Project Roadmap

**CS 463 · Cloud Native Platform Engineering**
**Dr. Brian Mitchell · Drexel University**

---

## Where We Are

The first four weeks of this course were about building fluency with the tools and infrastructure patterns that underpin every modern cloud system. You deployed real AWS infrastructure — EC2 instances, VPC networks, a serverless API — and managed all of it through code using Pulumi. None of that was busywork.

Here is what you have built so far:

| Lab | What You Built | Why It Matters |
|-----|---------------|----------------|
| Lab 1 | AWS CLI, EC2, SSH access | You know how to operate in AWS from the terminal |
| Lab 2 | EC2 + S3 + IAM via Pulumi | You can define infrastructure as code and deploy it repeatably |
| Lab 3 | VPC: subnets, routing, security groups, bastion host | You understand how network boundaries are designed and enforced |
| Lab 4 | Lambda + API Gateway, cold start analysis | You understand serverless compute and deployed NovaSpark's first API endpoint |

Labs 1–4 gave you the foundation. Everything from this point on uses it.

---

## The Pivot

NovaSpark's status endpoint is live. Janet is happy with it. But the team has a bigger problem.

> **Ben:** "We're taking orders by email right now. Literally email. Janet wants a real order API by end of quarter — something customers can hit, something that persists data, something we can actually operate."

> **Linda:** "And I want to be able to audit it. If we're going to call this production-ready, I want to score it against the Well-Architected Framework before we ship."

For the rest of this course, you are building that API. Not a toy, not a demo — a properly designed, cloud-native order processing service for NovaSpark, deployed entirely through Infrastructure as Code, that you will evaluate against real industry standards before you're done.

---

## What You're Building

The **NovaSpark Order API** is a serverless REST API that accepts customer orders, processes them asynchronously, and persists them to a managed database. It is the kind of service that exists at the core of almost every e-commerce, logistics, and SaaS platform in production today.

By the time you finish, your system will:

- Accept order submissions and respond immediately with a confirmation (not a wait)
- Process orders asynchronously through a message queue
- Persist every order to a cloud database
- Allow orders to be retrieved by ID, listed by status, and updated as they move through fulfillment
- Be deployed entirely through Pulumi — no manually created resources
- Be testable end-to-end with a single Postman collection you can run against any environment

---

## The API Specification

This is the full API you are building. Some routes are implemented in Lab 5. Others are completed in Lab 6. The final routes are yours to choose in the last weeks of the course. The spec does not change — your implementation catches up to it incrementally.

### Resource: Orders

| Method | Path | Description | Status Code |
|--------|------|-------------|-------------|
| `POST` | `/orders` | Place a new order | `202 Accepted` |
| `GET` | `/orders` | List all orders (optional `?status=` filter) | `200 OK` |
| `GET` | `/orders/{id}` | Retrieve a specific order by ID | `200 OK` or `404` |
| `PATCH` | `/orders/{id}` | Update an order's status | `200 OK` |
| `DELETE` | `/orders/{id}` | Cancel an order (soft delete) | `204 No Content` |

### Order Data Model

Every order in the system has this shape:

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

**Status lifecycle:** `received → processing → shipped` (or `cancelled` at any point via soft delete — the record stays in the database with `status: cancelled` rather than being removed).

### Design Decisions Worth Understanding

**Why `POST /orders` returns 202 and not 200?**
A 200 response means "here is the result." A 202 means "I received your request and I am working on it." Order submission kicks off an asynchronous pipeline — the order is queued, not yet fulfilled. Returning 200 would be a lie. Correct HTTP semantics matter because clients use status codes to decide what to show users.

**Why soft delete on `DELETE /orders/{id}`?**
In a real order system, permanently deleting an order destroys the audit trail. Setting `status: cancelled` means the record survives, the history is preserved, and the API remains predictable. Idempotent cancellation — cancelling a cancelled order should return the same result, not an error.

**Why `?status=` as a query parameter and not a path segment?**
`/orders?status=received` is filtering a collection. `/orders/received` would imply `received` is a resource identifier. The lecture covers this — filters and sorting belong in query parameters; resource identity belongs in the path.

---

## Testing with Postman

Starting with Lab 5, you will use **Postman** alongside `curl` to test your API. Postman is the industry-standard tool for API development and testing — you will encounter it in any engineering team that builds APIs.

**Download Postman before Lab 5:** [https://www.postman.com/downloads/](https://www.postman.com/downloads/)

A pre-built **NovaSpark Orders collection** will be provided as a `.json` file you can import directly into Postman. It includes all five routes with sample request bodies, headers, and a single environment variable — `api_url` — that you set to your Pulumi stack output URL. Change the URL, run the collection, every route is ready to test.

This mirrors how real engineering teams work: a shared Postman collection lives alongside the codebase, anyone can import it, and the API is immediately testable against any environment.

> **Notice the pattern:** setting `api_url` as a Postman environment variable is the same principle as `os.environ["QUEUE_URL"]` in your Lambda handler — configuration injected at runtime, not hardcoded. This is 12-factor Factor III showing up again in a different tool.

---

## Lab Roadmap

Each lab builds a specific part of the NovaSpark Order API. The table below shows which routes are live after each lab. An API that has `POST /orders` and both `GET` routes working is already more capable than most student projects in this space.

| | `POST /orders` | `GET /orders/{id}` | `GET /orders` | `PATCH /orders/{id}` | `DELETE /orders/{id}` |
|-|:-:|:-:|:-:|:-:|:-:|
| After Lab 5 | ✅ Live | 🔲 Stubbed | 🔲 Stubbed | 🔲 Stubbed | 🔲 Stubbed |
| After Lab 6 | ✅ Persisted | ✅ Live | ✅ Live | 🔲 Stubbed | 🔲 Stubbed |
| After Lab 7 (WAF) | ✅ | ✅ | ✅ | 🔲 | 🔲 |
| Final project | ✅ | ✅ | ✅ | Your choice | Your choice |

---

### Lab 5 — API Scaffold

**The goal:** Build the async order submission pipeline and establish the full API surface.

You will implement `POST /orders` end-to-end: a Lambda function validates the request, places the order on an SQS queue, and returns `202 Accepted` immediately. A second Lambda processes messages from the queue asynchronously. The remaining routes (`GET`, `PATCH`, `DELETE`) are stubbed — they exist, they return a `501 Not Implemented` response, and they will be completed in Lab 6.

By the end of Lab 5 you have the shape of the entire API and the async backbone running. Orders go in. They move through a queue. The pattern is live.

**What you will not have yet:** persistence. Orders land in the processor Lambda and are logged to CloudWatch. They are not stored anywhere you can query. That gap is intentional — it is what Lab 6 fixes.

---

### Lab 6 — Storage Backend

**The goal:** Wire DynamoDB into the pipeline. Make the stub routes real.

You will add a DynamoDB table to your Pulumi stack, connect the processor Lambda to write every order to the database, and implement `GET /orders/{id}` and `GET /orders` using real DynamoDB reads. The stubs from Lab 5 become working endpoints.

By the end of Lab 6 you have a functioning order service: place an order, retrieve it by ID, list all orders. The full async pipeline — API Gateway → Lambda → SQS → Lambda → DynamoDB — is running end-to-end.

This is the core of the NovaSpark Order API. Everything else builds on this foundation.

---

### Lab 7 — Well-Architected Audit

**The goal:** Evaluate what you built against the AWS Well-Architected Framework.

You have a real system now. Lab 7 asks you to score it against the six WAF pillars using your own architecture as the subject. No new AWS infrastructure — this is an analytical lab. The questions are not abstract: they are about decisions you actually made, gaps that actually exist, and improvements you could actually implement.

Every pillar will surface something real. The security pillar will surface the IAM role. The reliability pillar will surface the absence of a Dead Letter Queue. The performance efficiency pillar will surface cold start decisions you made in Lab 4. This is what a production readiness review looks like before a real system ships.

---

### Final Weeks — Build Your Own Adventure

**The goal:** Extend the NovaSpark Order API in a direction that interests you.

The core API is complete after Lab 6. The final weeks give you structured time to add depth in an area you want to explore. You are required to implement at least one meaningful extension — more earns more credit.

**Choose from the extension menu (or propose your own):**

| Extension | What You Build | Skills It Develops |
|-----------|---------------|-------------------|
| `PATCH /orders/{id}` | Update order status through the API | DynamoDB update operations, HTTP PATCH semantics |
| `DELETE /orders/{id}` | Soft-cancel orders via the API | Conditional writes, idempotency |
| Status filtering | `GET /orders?status=received` returns only matching orders | DynamoDB query vs. scan, pagination patterns |
| Authentication | Lambda authorizer validates a token before any route executes | API security, OAuth concepts from lecture |
| Order notifications | SNS publishes a message when an order is placed | Fan-out pattern, event-driven architecture |
| Pagination | `GET /orders` returns pages of results with a cursor | DynamoDB pagination, API design for large datasets |
| Custom extension | Propose your own — instructor approval required by Week 9 | Your call |

The extension you choose shapes your final deliverable. Choose something that genuinely interests you — you will be demonstrating it in a five-minute video.

---

## The Final Deliverable

Your course project submission has three parts:

**1. A working API** — deployed through Pulumi, all core routes functional, at least one extension implemented. `pulumi up` and `pulumi destroy` both run cleanly.

**2. A five-minute demo video** — show `pulumi up` completing, run the Postman collection against your live API, explain one architectural decision you made (why async? why that DynamoDB key design? why that extension?), and show `pulumi destroy` cleaning up.

**3. A written WAF reflection** — two pillars you addressed well (with specific examples from your code), one pillar you did not address and what you would do to fix it, and one thing that worked differently than you expected.

Simple and correct beats ambitious and half-working. A clean three-route API with a thoughtful reflection is a better submission than a complex system that requires manual steps to run.

---

## What Good Looks Like

By the time you demo, you should be able to:

- Run `pulumi up` from a clean state and have the full stack live in under two minutes
- Open Postman, hit `POST /orders`, get a `202` back, then `GET /orders/{id}` with the returned ID and get your order back
- Explain, in plain language, why the order submission is asynchronous — and what would break if it were not
- Name one decision in your IAM configuration that you would change in a production account, and why

If you can do all four of those things, you have learned what this course set out to teach.

---

*This document will be updated as labs are finalized. Check the course repository for the latest version.*
