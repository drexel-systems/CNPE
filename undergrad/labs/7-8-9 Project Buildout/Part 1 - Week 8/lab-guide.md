# Week 8 Lab Guide — Well-Architected Audit

**Course:** CS 463 — Cloud Native Platform Engineering
**Week 8**
**Session 1 (80 min):** 7u-WAF lecture
**Session 2 (80 min):** Lab 7 — WAF Audit (in class)
**Homework:** Written reflections W1, W2, W3 (~60 min)
**AWS infrastructure required:** None — analytical lab. Your Lab 6 stack does not need to be deployed.
**Prerequisite:** Lab 6 complete and submitted.

---

## The Scenario

It is Monday morning at NovaSpark. The order API is running. Linda pings the team.

> **Linda:** "Before anyone talks about a launch date, I want an honest read on what we built. Six pillars, real findings, no marketing language. I don't need it to be perfect — I need to know where the gaps are and whether we knew about them or not."

> **You:** "You want a full WAF audit?"

> **Linda:** "Yes. The same shape AWS Solutions Architects use in a real production review. I want the next conversation about going to production to be a conversation about *known* risks, not surprises."

This lab is that audit. The architecture you built across Labs 2–6 — the VPC, the bastion, the Lambda functions, the SQS queue, the DynamoDB table. Six pillars. Real findings.

---

## Session 1 — Lecture (80 min)

**7u-WAF — The AWS Well-Architected Framework**

The six pillars, the audit model, and how to classify what you find. Pay attention to the gap classification framework — it is the backbone of every entry in today's lab:

- **Unknown Gap** — the risk exists but you didn't think about it. Undocumented.
- **Conscious Tradeoff** — you knew the risk and made a deliberate choice. Documented.
- **Best Practice Met** — the pillar's recommendation is in place for your scale and context.

A finding classified as *Conscious Tradeoff* is not worse than *Best Practice Met* — it is different engineering. The audit's job is to make these explicit. An architecture with five *Conscious Tradeoffs* and honest documentation is more production-ready than one with five *Unknown Gaps*.

---

## Session 2 — Lab 7: WAF Audit (80 min in class)

### The Architecture Under Review

The NovaSpark Order API as you built it across the term:

```
         Internet
             │
             ▼
      API Gateway (public HTTPS endpoint)
             │
             ▼
      Orders Lambda ──────────────────────────► SQS Queue
      [POST: enqueue  GET: read DynamoDB]            │
             │                                       ▼
             │                              Processor Lambda
             │                                       │
             └───────────────────────────────────────▼
                                                 DynamoDB
                                            novaspark-orders

      ┌─── VPC (Labs 2–3) ──────────────────────────────────────────┐
      │  EC2 Bastion  [admin access only — not in the order path]   │
      └─────────────────────────────────────────────────────────────┘
```

**What the diagram is showing.** API Gateway, Lambda, SQS, and DynamoDB are AWS-managed services that run *outside* the VPC — they are publicly addressable. The VPC you built in Labs 2–3 contains the EC2 bastion for admin access, but it is not part of the order submission flow. Any client with the API Gateway URL — a browser, a mobile app, a curl command — can reach the API directly over HTTPS.

This is the **external/public API pattern**: the right choice when customers or external systems need to interact with your service. The alternative — an *internal API* scoped to a private network — would require a VPN or an internal load balancer and is more appropriate for services that should never be reachable from the public internet.

In a production system, a public API like this would use JWT tokens to verify caller identity, typically validated by an Application Load Balancer or API Gateway authorizer before the request reaches your Lambda. That pattern is outside the scope of this course, but it is worth exploring — and it is exactly what your Security pillar audit should surface as the gap between what you built and what production-ready looks like.

Audit *this* — the architecture you personally built. If your implementation diverged from the lab guides (e.g., your processor swallows errors instead of re-raising them, or you skipped the bastion in Lab 3), audit what you actually have and note the divergence honestly. Auditing a better version of your stack than you actually built earns no credit and produces no useful findings.

### The Audit Model

Every entry in your audit follows this five-step structure:

```
1. The Decision          2. The WAF Question       3. Current State
What you chose to do  →  What the pillar asks  →  What's actually there
                                                          │
                                                          ▼
                                                  4. Gap Classification
                                                  Unknown / Tradeoff / Met
                                                          │
                                                          ▼
                                                  5. The Improvement
                                                  One concrete change
```

### Worked Example — Security Pillar (10 min, instructor-led)

**Decision:** Lab 3 deployed an EC2 bastion with a security group allowing inbound SSH from `0.0.0.0/0`. Intentional — simplified setup across student networks with different IP ranges.

**WAF Question:** *How do you protect your workloads from external threats?* Is exposure minimized? Are controls audited? Is there a less risky alternative?

**Current State:** The SG limits inbound traffic to port 22 — that's good. But any IP on the public internet can attempt to connect. No MFA on SSH. No audit log of who connected or when.

**Gap Classification:** **Conscious Tradeoff.** We knew the SG was open. The reason (lab access across student networks) is documented in the lab guide. We know what would change at production scale.

**Improvement:** Option A — restrict the SG to a known CIDR (e.g., the university VPN range). Option B — replace the bastion with AWS Systems Manager Session Manager: no port 22, no inbound rule, full audit log, no SSH key management. Option B is the production answer.

This is the shape every pillar entry takes. Now write the remaining five yourself.

---

### Pillar 1 — Operational Excellence (~12 min)

**WAF question:** *How do you operate, observe, and evolve this workload over time?*

Where to look in your architecture:

- **Pulumi stack** — does `pulumi up` run cleanly from a fresh state every time, or do you have to manually fix something first? Repeatability is the Op Ex foundation.
- **Lambda logging** — your handlers use `print()` statements to CloudWatch. Are the log lines structured (JSON with named fields that a log aggregator could parse) or free-form strings? Try this: Linda calls you at 3am. "Show me every order for customer X in the last hour." How do you do that against your current logs?
- **CloudWatch alarms** — do you have any? A dashboard? Or are you only seeing problems reactively when something breaks?
- **Postman collection** — is it in the repo, or living only on your laptop?

Common findings: `pulumi up` repeatability is usually a Best Practice Met (that's what Pulumi is for); structured logging is usually an Unknown Gap; CloudWatch alarms are usually an Unknown Gap or Conscious Tradeoff depending on whether you ever thought about them.

---

### Pillar 2 — Security (~12 min)

**WAF question:** *How do you protect identities, data, networks, and workloads?*

Where to look:

- **IAM roles** — what permissions do your Lambda execution roles have? Look at the actual policy in `__main__.py`. The orders Lambda needs `sqs:SendMessage` and DynamoDB read permissions. The processor needs DynamoDB write. If either has `dynamodb:*` on `*`, that is broader than necessary.
- **API Gateway** — any authentication on your routes? Any rate limiting? Right now, anyone with your API URL can submit orders or read your entire order table. There is no concept of *whose* order is being submitted or retrieved.
- **Customer identity and data scoping** — `POST /orders` does not record which customer placed the order. `GET /orders` returns every order in the table to any caller. Think about the two contexts this API might operate in: if it is an *internal* tool used by customer service agents, returning all orders to any authenticated employee is probably acceptable — access is controlled at the network layer. If it is a *public-facing* API used by customers directly, returning every customer's orders to any caller is a serious data exposure gap. Which context does your architecture support, and is that a documented decision or an unknown gap? The improvement for external deployment is to add a `customer_id` field to orders and require callers to scope their queries — the data model foundation for multi-tenant access control.
- **Secrets** — is anything sensitive hardcoded in your repo (API keys, credentials, anything that shouldn't be public)?

Pick a **different** decision from the bastion (already worked above) for your Security entry. The customer identity / data scoping question is one strong candidate — it connects directly to the public API pattern you deployed.

---

### Pillar 3 — Reliability (~12 min)

**WAF question:** *How do you handle component failures and meet availability targets?*

Where to look:

- **Dead Letter Queue** — is there a DLQ on your SQS queue? If the processor Lambda fails five times on the same message, what happens to that message? Does it disappear, or does it land somewhere you can inspect and reprocess?
- **Error handling in the processor** — does your processor re-raise exceptions on DynamoDB write failure (so SQS retries), or does it swallow errors and return success (so the message is acknowledged and the order is silently lost)? Look at your `processor/handler.py`.
- **Single-region** — everything is deployed in one AWS region. If `us-east-1` has an outage, what happens? This is almost always a Conscious Tradeoff for a pre-launch startup.
- **DynamoDB backup** — is point-in-time recovery enabled on the table?

The DLQ finding is the most important reliability gap in this architecture. Most students deployed without one, and most students did not think about it. That makes it an Unknown Gap — which is exactly the right classification, and exactly the kind of finding the WAF is designed to surface.

---

### Pillar 4 — Performance Efficiency (~12 min)

**WAF question:** *How do you select, configure, and monitor resources to meet performance needs efficiently?*

Where to look:

- **Lambda memory** — what size are your functions? Was that a deliberate choice or whatever the default was in the starter code?
- **DynamoDB read patterns** — `GET /orders/{id}` uses `get_item()` (single-digit milliseconds at any scale — Best Practice Met). `GET /orders` uses `scan()` (reads the entire table — fine with 50 test orders, broken at 50 million). Name this explicitly: it is a Conscious Tradeoff for the current scale, and you should document when you'd fix it.
- **Cold starts** — you measured one in Lab 4. The processor Lambda is also subject to cold starts, which means occasional orders sit in SQS longer than expected. Did you account for this in your design?

---

### Pillar 5 — Cost Optimization (~12 min)

**WAF question:** *How do you avoid unnecessary cost and confirm you're getting value from what you spend?*

Where to look:

- **NAT Gateway** — you destroyed it between labs (good). Is the rest of your stack costing anything right now?
- **DynamoDB billing mode** — you chose `PAY_PER_REQUEST` in Lab 6. Why? Would provisioned capacity ever be cheaper for NovaSpark?
- **Resource tagging** — do your Pulumi resources have tags like `project=novaspark`? Without tags, AWS cost reports cannot distinguish your resources from other resources in the same account.
- **Billing alarms** — is there a CloudWatch billing alarm on your account? If credits run out while your stack is deployed, how would you find out?

---

### Pillar 6 — Sustainability (~12 min)

**WAF question:** *How do you minimize the environmental impact of running this workload?*

Where to look:

- **Lambda** — scales to zero when idle. No energy spent on standby. This is genuine Best Practice behavior — note it with the evidence (Lambda's execution model, not just "Lambda is serverless").
- **DynamoDB on-demand** — same pattern. No provisioned capacity consuming resources when no orders are flowing.
- **EC2 instance type** — what did you use for the bastion in Lab 3? `t4g.micro` (ARM Graviton) is meaningfully more power-efficient than an equivalent x86 instance like `t3.micro`. Did you choose deliberately?
- **Region selection** — different AWS regions have different percentages of renewable energy in their power mix. Did you consider this when choosing `us-east-1`? Probably not — which makes it an Unknown Gap rather than a Conscious Tradeoff.

Do not skip this pillar because it feels like "vendor marketing." Take it seriously and classify findings honestly. A pillar with no findings should be stated explicitly as such — not left blank.

---

### Pair Compare (10 min — end of Session 2)

Find another student. Compare your audits pillar by pillar. Two things to look for:

1. **Classification disagreements.** If you marked something *Conscious Tradeoff* and they marked the same thing *Unknown Gap*, that is interesting — one of you thought about it at build time and one didn't.
2. **Findings you missed.** Your partner probably surfaced something you didn't. If it genuinely belongs in your audit, add it.

This is not graded. It is the highest-leverage 10 minutes in the lab.

---

## Homework — Written Reflections (~60 min)

Three short prompts. Each is 3–5 sentences. Add them at the end of your audit report.

### W1 — Most Critical Gap (15 pts)

Of all the findings you classified as **Unknown Gap**, which one would most improve NovaSpark's production readiness if fixed? Justify your choice. Why this gap over the others? Name the specific failure mode it creates and why that failure mode is worse than the alternatives.

### W2 — Conscious Tradeoff Defense (15 pts)

Pick one finding you classified as **Conscious Tradeoff** and defend it as a reasonable choice for NovaSpark at its current stage. Then name the specific condition that would make this tradeoff unacceptable — what would have to change about NovaSpark (scale, regulatory environment, team size, revenue, a specific incident) for you to reclassify this as an Unknown Gap?

### W3 — The Extension Bridge (20 pts)

Look at the extension menu in the [project roadmap](../project-roadmap.md). Pick the extension that most directly addresses one of the gaps you found in your audit. Name the extension, name the gap, and explain the connection in one or two sentences.

> **Why this question matters.** Your Week 9 lab (Lab 8) asks you to produce an extension design doc. The extension you name here is the recommended starting point for that design. You are not locked in — you can change your mind in Week 9 — but if you do, your Week 9 lab must explain why you moved away from the audit-motivated choice.

The strongest W3 answers show a real connection: "My audit identified the absence of a DLQ as an Unknown Gap in the Reliability pillar — orders that fail processing can be silently lost. I'm choosing the SNS notifications extension... wait, actually the DLQ itself isn't on the extension menu." That's a valid observation — not every gap is closable by an extension. The extension should be the one that most directly connects to *something real* in your audit, even if it doesn't close the single most critical gap.

---

## Deliverables

Submit a single PDF (or markdown rendered to PDF) containing:

- [ ] **D1 — Six-pillar audit** — one structured entry per pillar: Decision → WAF Question → Current State → Gap Classification → Improvement (60 pts, 10 pts per pillar)
- [ ] **W1 — Most critical gap** (15 pts)
- [ ] **W2 — Conscious tradeoff defense** (15 pts)
- [ ] **W3 — Extension bridge** (20 pts) ← this feeds your Week 9 lab directly

**Total: 110 pts** (curved to 100)

Also: *(Optional, ungraded)* — Try the AWS Well-Architected Tool in the console. Answer one pillar's questions based on your audit. Screenshot the risk summary and write 2–3 sentences comparing what the tool flagged to what you found manually. No points, but "I have used the AWS Well-Architected Tool" is a real thing to put on a résumé.

---

## What Good Looks Like

**Specific evidence.** "Security: we used IAM" earns no credit. "Security: the orders Lambda execution role has `sqs:SendMessage` on the queue ARN and `dynamodb:GetItem` / `dynamodb:Scan` on the table ARN — scoped correctly. The processor role has `dynamodb:PutItem` only. Both roles are narrower than `dynamodb:*`, which is a Best Practice Met finding relative to the common pattern of over-permissioning Lambda roles during development" earns full credit.

**Honest classification.** A submission that classifies everything as Best Practice Met earns less than one that honestly surfaces gaps. The audit's purpose is to find gaps. Students who built good systems still have Unknown Gaps — they just tend to have more Conscious Tradeoffs.

**Actionable improvements.** "Improve reliability" is not an improvement. "Add a Dead Letter Queue to the SQS queue: `aws.sqs.Queue('novaspark-orders-dlq')` and set `redrivePolicy` with `maxReceiveCount=3` on the main queue. Add a CloudWatch alarm on `ApproximateNumberOfMessagesVisible` for the DLQ — any non-zero count should alert" is an improvement.

---

## What This Sets Up

Your W3 answer becomes the starting point for the extension you design in Week 9. Your six-pillar audit and W1/W2 paragraphs become the raw material for the project's WAF reflection — you are not writing that reflection from scratch in finals week.

The final project's WAF reflection is 1–2 pages: two pillars addressed well, one gap with a concrete fix, one surprise. Everything you write this week feeds directly into that. The finals week version should be editing and tightening, not starting over.
