# CS 545 — Final Three Weeks: Project Roadmap

**CS 545 · Cloud Native Platform Engineering (Graduate)**
**Dr. Brian Mitchell · Drexel University**

---

## Where We Are

You have completed the foundational labs for this course. Here is what you have built and analyzed:

| Lab | What You Built | What You Analyzed |
|-----|---------------|-------------------|
| Lab 1 | AWS CLI, EC2, SSH access | The economics and model of managed cloud services |
| Lab 2 | EC2 + S3 + IAM via Pulumi | Why IaC creates discipline — and where it creates new failure modes |
| Lab 3 | VPC: subnets, routing, security groups, bastion host | Network boundary design and blast radius of misconfiguration |
| Lab 4 | Lambda + API Gateway, cold start measurement | Serverless limitations, IAM execution roles, event object abstraction |
| Lab 5 | DynamoDB table connected to Lambda | Access pattern design, consistency tradeoffs, RTO/RPO |

You have a working stack: a VPC with bastion, an API Gateway HTTP API, a Lambda function with an execution role, and a DynamoDB table named `novaspark-orders`. The remaining three weeks assemble these pieces into a complete system and produce the written architectural justification alongside it.

---

## What You Are Building

The **NovaSpark Order API** — a serverless REST API that accepts customer orders asynchronously via SQS, processes them through a worker Lambda, and persists every order to the DynamoDB table you provisioned in Lab 5.

> **Ben:** "We're still taking orders by email. Janet wants a real order API by end of quarter — something customers can hit, something that persists data, something we can actually operate."
>
> **Linda:** "And before it ships, I want a Well-Architected review. Every pillar. Real findings."
>
> **Janet:** "Once it's working, I want a design document that explains why we built it the way we did. If we get acquired, I want someone to be able to read it and understand what we were thinking."

Janet's ask is the Architecture Design Document. Linda's ask is the WAF audit. Ben's ask is the working API. The next three weeks deliver all three — each week produces both an implementation step and a written section of the ADD.

### The Core API

| Route | Status Code | Description |
|-------|-------------|-------------|
| `POST /orders` | 202 Accepted | Submit an order — body requires `customer_id` (async via SQS) |
| `GET /orders/{id}` | 200 / 404 | Retrieve a specific order from DynamoDB |
| `GET /orders` | 200 | List all orders; supports optional `?customer_id=X` filter |

These three routes are what you will demo. Two additional routes (`PATCH` and `DELETE`) are stubbed and available as optional extensions — they are not required for the final project.

### The Full Pipeline

```
         Internet
             │
             ▼
      API Gateway (HTTP API)
      [public HTTPS endpoint]
             │
             ▼
      Orders Lambda ──────────────────────────────► SQS Queue
      [POST: enqueue   GET: read DynamoDB]               │
             │                                           ▼
             │                                  Processor Lambda
             │                                           │
             └───────────────────────────────────────────▼
                                                     DynamoDB
                                                novaspark-orders

      ┌─── VPC (Labs 2–3) ──────────────────────────────────────────┐
      │  EC2 Bastion  [admin access only — not in the order path]   │
      └─────────────────────────────────────────────────────────────┘
```

### A Note on API Context

API Gateway, Lambda, SQS, and DynamoDB are AWS-managed services that run *outside* the VPC — they are publicly addressable over HTTPS. The VPC you built in Labs 2–3 contains the EC2 bastion for admin access, but it is not part of the order submission flow.

This is the **external/public API pattern**: the right choice when customers or external systems need to interact with a service directly. It is architecturally distinct from an *internal API* scoped to a private network, which would require a VPN or an internal load balancer and is more appropriate for services that should never be reachable from the public internet.

The `customer_id` field in `POST /orders` and the `GET /orders?customer_id=X` filter are the data model foundation for multi-tenant access control. In an internal deployment, a customer service agent passes `customer_id` explicitly to look up any customer's orders. In an external deployment, `customer_id` would be extracted from a verified JWT token rather than accepted as caller-supplied input — ensuring customers can only see their own data. In a production system, JWT validation is typically handled by an Application Load Balancer or an API Gateway authorizer. That pattern is outside the scope of this course and a good area to explore further. Your ADD Section 3 and Section 4 are where you document this design choice and its implications.

---

## The Architecture Design Document (ADD)

The ADD is the signature deliverable of CS 545. It is a 10–14 page structured architectural justification of the NovaSpark Order API — what you built, why you built it that way, and what the realistic operational and cost concerns are.

**You are not writing the ADD from scratch at the end.** Each of the next three weeks produces one or more sections as a direct output of the lab work. By the end of Week 9, four of six sections are drafted. Week 10 is assembly and polish.

### ADD Sections

| # | Section | Target Length | Where It Comes From |
|---|---------|--------------|---------------------|
| 1 | Requirements | ~1.5 pp | Week 8 written deliverable |
| 2 | Architecture Overview | ~2 pp | Week 10 synthesis |
| 3 | Component Decisions | ~2–3 pp | Seeded Week 8 → finalized Week 10 |
| 4 | Well-Architected Analysis | ~3 pp | Week 9 WAF audit |
| 5 | Operational Considerations | ~1.5 pp | Week 9 notes → Week 10 polish |
| 6 | Cost Estimate | ~2 pp | Week 9 homework |

### What Each Section Must Cover

**Section 1 — Requirements**
What the system has to do, how well it has to do it, and what it operates within. Four subsections: functional requirements (the routes and pipeline behavior, including `customer_id` filtering), non-functional requirements (latency targets, availability, throughput, eventual consistency window), constraints (AWS Academy sandbox, LabRole IAM scope, and the authentication gap for external deployment), and a 12-factor compliance hooks paragraph.

Numbers, not adjectives. "Fast" is not a requirement. "POST returns 202 under 200ms at p50" is.

**Section 2 — Architecture Overview**
A coherent system diagram and narrative walking the reader through a single request — from client HTTP call to persisted DynamoDB record. Assembled from diagrams you produced in Labs 3–5 and the pipeline diagram from Week 8.

**Section 3 — Component Decisions**
For each major component (API Gateway, orders Lambda, SQS queue, processor Lambda, DynamoDB table): what you chose, why, and at least one alternative you considered and rejected. Why SQS over a direct synchronous call? Why DynamoDB over RDS? Why this partition key? The API Gateway entry should address the public vs. internal API choice and why a public endpoint was appropriate for NovaSpark's use case. The orders Lambda entry should address the `customer_id` implementation and the documented gap for external deployment.

**Section 4 — Well-Architected Analysis**
A six-pillar audit of the implemented architecture. For each pillar (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability), a structured argument:

> *Decision → WAF Question → Current State → Gap Classification → Improvement*

Each finding classified as **Unknown Gap**, **Conscious Tradeoff**, or **Best Practice Met**. Honest classification earns more credit than the "everything is fine" version. The Security pillar should include a finding on the `customer_id` parameter — accepting caller-supplied identity is a Conscious Tradeoff appropriate for internal use and a documented gap for external deployment.

**Section 5 — Operational Considerations**
Three subsections: monitoring strategy (which CloudWatch metrics matter for an async pipeline), deployment approach (`pulumi up` workflow, rollback strategy), and failure modes with mitigations (what happens when the processor Lambda fails, when DynamoDB throttles, when SQS receives malformed messages).

**Section 6 — Cost Estimate**
Monthly AWS cost at two traffic levels using the AWS Pricing Calculator (free public tool, no account changes):
- **100 req/day** — NovaSpark today
- **10K req/day** — modest growth

Per-service cost breakdown, what drives cost at each scale, and a specific crossover threshold where the architecture's economics change.

---

## Three-Week Arc

### Week 8 — Build the Pipeline + Start the ADD

**Lecture:** APIs and Event-Driven Architecture — REST contract, async patterns, SQS vs. SNS vs. EventBridge, eventual consistency, 202 semantics.

**Lab:** Deploy the guided NovaSpark async pipeline. You receive a near-complete Pulumi stack and configure the key connection points yourself — wiring the SQS trigger to the processor Lambda, setting environment variables, and confirming the DynamoDB permissions. Test end-to-end with Postman and observe the eventual consistency window.

**Written output:** ADD Section 1 (Requirements) + ADD Section 3 seed (Component Decisions — the architectural Q&A from the lab guide).

**Homework due before Week 9:** Complete lab, submit ADD Section 1 draft + Section 3 seed.

---

### Week 9 — WAF Audit + Cost Analysis

**Lecture:** Well-Architected Framework (full depth) + Cloud Native and CNCF (compressed — framing for cost-as-architecture-decision).

**Lab (in class):** Six-pillar WAF audit of your deployed NovaSpark Order API → ADD Section 4. Op Ex and Reliability findings draft ADD Section 5 notes.

**Homework:** Simplified cost analysis using the AWS Pricing Calculator at two traffic levels (100/day and 10K/day) → ADD Section 6.

**Written output:** ADD Sections 4 + 5 (draft) in class. ADD Section 6 as homework.

**Homework due before Week 10:** Complete Lab 7 + ADD Sections 4, 5 notes, 6.

---

### Week 10 — ADD Synthesis + Final Project Close

**No new lecture.**

**In class (first 60 min):** Instructor-guided ADD synthesis — assemble Section 2 (Architecture Overview) from prior lab diagrams and Section 3 (Component Decisions) from prior justifications. A scaffold is provided for Section 3.

**In class (remaining time):** Open work session — ADD polish, demo video recording, reflection writing.

**Due end of Week 10:** Architecture Design Document (PDF, Canvas) + Final Project (video link + reflection PDF + GitHub repo).

---

## ADD Progress Tracker

Use this to track where each section stands before each session.

| Section | After Week 8 | After Week 9 | After Week 10 |
|---------|-------------|-------------|-------------|
| 1. Requirements | ✅ Drafted | — | ✅ Polished |
| 2. Architecture Overview | — | — | ✅ Assembled |
| 3. Component Decisions | 🔲 Seeded | — | ✅ Finalized |
| 4. WAF Analysis | — | ✅ Drafted | ✅ Polished |
| 5. Operational Considerations | — | 🔲 Notes | ✅ Drafted |
| 6. Cost Estimate | — | ✅ Drafted | ✅ Polished |

---

## Final Deliverables

All due **end of Week 10**. No late submissions accepted on either deliverable.

### Architecture Design Document (20% of course grade)

A 10–14 page PDF submitted to Canvas. Six sections as described above. A strong ADD takes a position — it argues for why you made each choice, acknowledges tradeoffs honestly, and demonstrates you thought about what happens when things go wrong.

### Final Project (18% of course grade)

Three components submitted together:

**1. Working implementation** — the async order pipeline deployed via Pulumi with three core routes live (`POST /orders`, `GET /orders/{id}`, `GET /orders`). Both `pulumi up` and `pulumi destroy` must run cleanly. Code in GitHub repo `/project/` directory.

**2. Five-minute demo video** — screen capture showing:
- `pulumi up` running and completing
- Postman collection run against the live API (all three core routes end-to-end)
- Architecture walkthrough — each component named with its purpose
- Two design decisions from your ADD named, and whether the implementation matched
- `pulumi destroy` completing cleanly

Submitted as a Canvas link (YouTube or Loom).

**3. Written reflection (1–2 pages, PDF)** — four required components:
1. Where did the implementation **match** your ADD? Where did it **diverge**, and why?
2. One WAF pillar **addressed well** — specific code or configuration example
3. One WAF pillar **not addressed** — concrete proposed fix
4. One thing you learned from building that the ADD didn't anticipate

The reflection must explicitly reference the ADD. The point is not that implementation matched design — it almost never does. The point is that you can account for the gap with engineering reasoning.

### Final Project Rubric

| Area | Full Credit | Weight |
|------|-------------|--------|
| ADD — Requirements + Overview (Sec 1+2) | Specific requirements with numbers; coherent diagram + narrative | 20 pts |
| ADD — Component Decisions (Sec 3) | Each component has rationale + ≥1 rejected alternative | 20 pts |
| ADD — WAF Analysis (Sec 4+5) | Six pillars with evidence; honest gap classification; operational failure modes named | 30 pts |
| ADD — Cost Estimate (Sec 6) | Two traffic levels, per-service breakdown, crossover threshold named | 10 pts |
| Working implementation | Three core routes live, `pulumi up`/`destroy` clean | 30 pts |
| Demo video | System shown working; two ADD decisions referenced; architecture explained | 20 pts |
| Reflection | Divergences named honestly; WAF pillar with code example; genuine surprise | 20 pts |
| **Total** | | **150 pts** |

---

## What Good Looks Like

By the time you demo, you should be able to:

- Run `pulumi up` from a clean state and have the full stack live in under two minutes
- Run the Postman collection and show orders flowing through the full pipeline — submission, queue, processor, DynamoDB, retrieval
- Open your ADD to Section 3 and explain, for one component, what you considered and why you chose what you chose
- Name the specific eventual consistency window you observed during testing and explain what it means for a customer who submits an order and immediately queries for it
- Point to one place where your implementation diverged from your ADD and give the engineering reason why

If you can do all five of those things, you have learned what this course set out to teach.

---

*Lab guides are in the Week1 (Week 8), Week2 (Week 9), and Week3 (Week 10) directories.*
