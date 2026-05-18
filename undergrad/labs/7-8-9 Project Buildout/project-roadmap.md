# CS 463 — Final Three Weeks: Project Roadmap

**CS 463 · Cloud Native Platform Engineering (Undergraduate)**
**Dr. Brian Mitchell · Drexel University**

---

## Where We Are

You have built the NovaSpark Order API. Here is what is running:

| Lab | What You Built |
|-----|---------------|
| Lab 1 | AWS CLI, EC2, SSH — you can operate in AWS from a terminal |
| Lab 2 | EC2 + S3 + IAM via Pulumi — infrastructure as repeatable code |
| Lab 3 | VPC with public/private subnets, IGW, NAT GW, bastion host, route tables |
| Lab 4 | Lambda + API Gateway — NovaSpark's first serverless endpoint |
| Lab 5 | Async order pipeline — `POST /orders → SQS → processor Lambda` |
| Lab 6 | Storage backend — DynamoDB wired in, `GET /orders/{id}` and `GET /orders` live |

The full async pipeline is running end-to-end: a customer can submit an order, it flows through SQS to the processor, persists to DynamoDB, and can be retrieved by ID or listed in full. That is the required baseline for the course project.

**The three remaining weeks are not about building the core system — it's already built.** They are about evaluating what you built, extending it in one direction that interests you, and demonstrating it clearly on camera.

### A Note on API Context

The NovaSpark Order API is deployed via API Gateway as a **publicly addressable HTTPS endpoint** — any client with the URL can reach it. This is the right pattern for a customer-facing system (a React storefront, a mobile app, a third-party integration). It is different from an *internal API*, which would be scoped to a private network and accessed through a VPN or internal load balancer.

This distinction matters for your WAF audit. A public API with no authentication means any caller can submit orders and read the full order list. In a real production system, user identity would be verified using JWT tokens issued by an authorization service, and an Application Load Balancer would route and scope requests based on the claims inside the token — but that is outside the scope of this course and a good area to explore further. For now, your WAF Security analysis is where you will name this design decision and its implications.

---

## What the Course Project Requires

The course project is **30% of your grade**. It has three parts, all due in finals week.

### 1 — A Working API (deployed via Pulumi)

Your Lab 6 stack is the foundation. The project requires:

- All three core routes working end-to-end: `POST /orders` (202), `GET /orders/{id}` (200/404), `GET /orders` (200)
- **At least one extension** from the menu below — this is required, not optional
- Everything deployed via Pulumi — no manually created resources
- Clean `pulumi up` and `pulumi destroy` from a fresh state

### 2 — A Five-Minute Demo Video

A screen recording showing:
1. `pulumi up` completing cleanly
2. Postman collection run against the live API — all three core routes plus your extension
3. Architecture walkthrough — name each component and why it's there
4. One architectural decision explained in plain language
5. `pulumi destroy` completing cleanly

### 3 — A Written WAF Reflection (1–2 pages)

Three required components:
- Two pillars you addressed well — with specific code or configuration examples
- One pillar you did not address — with a concrete proposed fix
- One thing that worked differently than you expected

---

## The Extension Menu

You must implement at least one extension. More earns more credit. Choose based on what you want to learn — but choose something. Students who pick an extension in Week 9 and implement it in Week 10 are in good shape. Students who arrive at Week 10 without a choice spend the first 30 minutes of the build session deciding instead of building.

| Extension | Difficulty | What You Build |
|-----------|------------|---------------|
| `PATCH /orders/{id}` | Light | Update order status through the API |
| `DELETE /orders/{id}` | Light | Soft-cancel orders (record stays in DB with `status: cancelled`) |
| `GET /orders?status=...` | Light | Filter orders by status |
| Customer scoping — `GET /orders?customer_id=X` | Light | Add `customer_id` to orders; filter `GET /orders` by customer. Directly addresses the Security pillar gap you identify in Week 8. |
| `GET /orders` with pagination | Medium | Cursor-based pagination using DynamoDB `LastEvaluatedKey` |
| Order notifications via SNS | Medium | SNS publishes when an order is placed |
| Lambda authorizer | Heavy | Token validation before any route executes |
| Custom extension | Varies | Instructor approval required — bring a written sketch |

**Light extensions** land in 60–90 minutes for most students. **Medium extensions** need the full 80-minute build session. **Heavy extensions** require careful scoping in the design doc — your Lab 8 design doc must define the minimum viable version.

---

## Three-Week Arc

### Week 8 — Two Sessions

**Session 1 — Lecture (80 min):** 7u-WAF — The AWS Well-Architected Framework: six pillars, the audit model, gap classification.

**Session 2 — Lab 7 (80 min):** WAF audit of your own NovaSpark Order API in class. Written reflections as homework — including W3, which asks you to name the extension most directly motivated by your audit findings.

**Homework:** Complete the audit table + three written reflections. Your W3 answer is the recommended starting point for your Week 9 extension choice.

---

### Week 9 — One Session (Holiday Week)

**Single session (80 min):** Compressed 8u-CloudNative lecture (35 min) + Lab 8 extension planning (45 min).

The lecture covers 12-factor methodology applied to NovaSpark and the CNCF landscape. The lab time has one goal: you leave with a committed extension design doc that tells Lab 9 exactly what to build.

**Homework:** 12-factor audit (four focused factors) + CNCF mapping exercise — both assigned as homework this week to protect the in-class extension planning time.

---

### Week 10 — Two Sessions

**Session 1 — Lab 9 (80 min):** Build the extension. You arrive with a design doc. The session is implementation.

**Session 2 — Project working session (80 min):** Demo prep, WAF reflection assembly, clean `pulumi destroy` test.

**Finals week — no class:** Record and submit. Project due by the announced deadline.

---

## Build Timeline

| Milestone | When |
|-----------|------|
| WAF audit complete + W3 extension choice named | End of Week 8 homework |
| Extension design doc written + committed | End of Week 9 in-class session |
| Extension implemented end-to-end, Postman verified | End of Week 10 Session 1 |
| Demo video dry-run recorded (60 sec) | End of Week 10 Session 2 |
| Final demo video recorded, reflection written | Finals week |
| **Course project submitted** | **Finals week deadline** |

---

## Project Rubric

| Area | Full Credit | Weight |
|------|-------------|--------|
| **Working demo** | All 3 core routes + ≥1 extension work; data persists; `pulumi up`/`destroy` clean | 35 pts |
| **IaC completeness** | All resources in Pulumi — no manually created resources | 20 pts |
| **Storage integration** | DynamoDB reads/writes correctly; table defined in Pulumi | 15 pts |
| **WAF reflection** | Two pillars with specific code/config examples; one gap with a concrete fix | 20 pts |
| **Video clarity** | System shown working; one architectural decision explained clearly | 10 pts |

**Deductions:** Manually created resources that should be in Pulumi (−10 pts) · Video over 5 minutes (−5 pts) · Undisclosed AI use in reflection (−10 pts)

---

## What Good Looks Like

By the time you demo, you should be able to:

- Run `pulumi up` from a clean state and have the full stack live in under two minutes
- Open Postman, run the collection, and show `POST /orders → 202 → GET /orders/{id} → 200` end-to-end
- Demonstrate your extension working — including at least one failure case (e.g., `PATCH` to a missing ID returns 404)
- Explain, in plain language, why the order submission is asynchronous — and what specifically would break if it were synchronous
- Point to one decision in your IAM configuration that you would change in a production account, and why

Simple and correct beats ambitious and half-working. A clean three-route API with a working extension and a thoughtful reflection beats a complex system that requires manual steps to run.

---

*Lab guides are in the Week1 (Week 8), Week2 (Week 9), and Week3 (Week 10) directories.*
