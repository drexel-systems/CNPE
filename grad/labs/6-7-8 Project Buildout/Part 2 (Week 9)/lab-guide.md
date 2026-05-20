# Week 9 Lab Guide — WAF Audit + Cost Analysis

**Course:** CS 545 — Cloud Native Platform Engineering
**Paired lecture:** Well-Architected Framework (7g-WAF, full depth) + Cloud Native and CNCF (8g-CloudNative, compressed)
**Session structure:** Block 1 (70 min combined lecture) → Block 2 (40 min Lab 7 checkpoint + Q&A) → Block 3 (40 min WAF audit start)
**Estimated total time:** 80 min in class + 90 min homework
**AWS infrastructure required:** None — analytical lab. Your Week 8 stack does not need to be deployed.
**Prerequisite:** Week 8 lab complete. ADD Section 1 draft and Section 3 seed submitted.

---

## The Scenario

It is Monday morning. The pipeline is running. Linda calls the team.

> **Linda:** "Before we talk about launch, I want the WAF review. Six pillars, real findings, no marketing language. I don't care if we look bad — I care that we know what we're trading off and that we made those trades consciously. Unknown gaps get fixed before launch. Conscious tradeoffs get documented. Either way, we need to know what we have."

> **Janet:** "And Ben needs numbers for the investor deck. Not 'it's cost-effective on Lambda' — actual dollars at three traffic levels. What does this cost today? What does it cost if we grow 100x?"

This week delivers both. The in-class work produces ADD Sections 4 and 5. The homework produces ADD Section 6.

---

## Block 1 — Combined Lecture (70 min)

### Well-Architected Framework (45 min)

The six pillars, the audit model, and the gap classification framework. This is the depth portion — you will apply this directly in Block 3 and in your homework.

Key concepts from this lecture that you will use today:
- The five-step audit model: *Decision → WAF Question → Current State → Gap Classification → Improvement*
- The three gap classifications: **Unknown Gap** (didn't think about it), **Conscious Tradeoff** (knew and chose deliberately), **Best Practice Met** (handled correctly)
- Why honest classification matters more than optimistic classification

### Cloud Native and CNCF (25 min)

Cloud-native as architectural properties, not a vendor certification. The 12-factor methodology applied to the NovaSpark Order API. How cost is an architectural decision — the bridge into today's homework.

Key framing for the cost analysis homework:
- At low traffic (100 req/day), Lambda's free tier makes cost nearly invisible
- At moderate traffic (10K req/day), specific services exit free tier and the unit economics become real
- The question is not "is it cheap?" but "what drives cost, and at what scale does the current architecture stop making sense?"

---

## Block 2 — Lab 7 Checkpoint (40 min)

This block is not a seminar — it is a structured work checkpoint.

### Part A — Week 8 Lab Status (15 min)

Quick show of hands / open check: who has a working pipeline? If your Week 8 `POST /orders → 202 → SQS → processor → DynamoDB → GET /orders/{id}` pipeline is not working end-to-end, raise it now. You cannot write a credible WAF audit of a system you haven't built. If your stack is broken, the instructor and peers can help you identify the issue in this block.

If your Week 8 stack is working, use this time to re-read your ADD Section 3 seed from last week. You will cite it in the WAF audit.

### Part B — Audit Prep (25 min)

Before starting the six-pillar audit in Block 3, do two things:

**1. Pull up your Week 8 `__main__.py` and handler files.** The audit requires specific evidence — actual file paths, actual resource names, actual IAM permissions. You cannot write "the Lambda has appropriate permissions" and earn credit. You need "the processor Lambda's execution role has `dynamodb:PutItem` on `arn:aws:dynamodb:us-east-1:*:table/novaspark-orders` as configured in `__main__.py` lines X–Y."

**2. Record your observations from Week 8 Postman testing.** The eventual consistency window you measured — the time between `POST 202` and `GET 200` — is your primary evidence for the Reliability pillar finding. If you did not record it during Week 8 testing, deploy your stack now (`pulumi up`), run the test sequence again, and record the window.

---

## Block 3 — WAF Audit Start (40 min)

### The Worked Example (10 min, instructor-led)

Open **`student-example.md`** in this directory. The instructor will walk through the Security pillar entry using the Lab 3 bastion host as the decision — Parts 1, 2, and 3 cover the technical context, the SSH vs. Session Manager architecture, and the complete five-step audit entry including an Architecture Decision Record.

Read the worked entry carefully before starting your own audit. Three things to notice:

**The current state assessment names strengths before gaps.** The bastion entry doesn't open with problems — it opens with what the current state does well (SSH keys require physical possession; the bastion pattern is itself a best practice). Your entries should do the same. If you can only see gaps, your classification won't hold up and your ADR reasoning will be shallow.

**The ADR format changes shape depending on the finding.** The bastion entry is a Conscious Tradeoff — the risk was known, documented, and a production fix is identified. Your six pillars will likely include findings across all three classifications. A Best Practice Met entry has no ADR (you document the strength and move on). An Unknown Gap entry has a shorter Option 1 ("do nothing" carries more weight when you hadn't considered the risk at all). A Conscious Tradeoff — like the bastion — has a full ADR with real options and a reasoned decision. Match the depth of Step 5 to the classification.

**The "do nothing" option is always honest, not pessimistic.** Every finding where Option 1 is "accept current state" should explain what that option acknowledges and what risk it carries. This is what separates an architecture that has been thought about from one that just happened.

### Start Your Audit (30 min)

Begin two pillars in class. The full audit is homework; the goal here is to get the format right before you work independently.

**Start with Operational Excellence.** Focus on:
- Pulumi stack repeatability — does `pulumi up` from a clean state always produce the same result?
- Lambda logging — your handlers use `print()` statements. Are the log lines structured (JSON with named fields) or free-form strings? Could CloudWatch Insights parse them automatically?
- Observability — do you have any CloudWatch alarms? A dashboard? Or are you operating purely reactively from logs?

**Then Security.** Pick a different decision from the bastion (already worked above). Strong candidates:
- The IAM permission scope you configured in Week 8 TODO 3 — `dynamodb:PutItem` only, or did you end up with something broader?
- API Gateway authentication — the API is currently open to anyone with the URL. Any rate limiting?
- **The `customer_id` design** — the orders Lambda accepts `customer_id` as a caller-supplied parameter in the `POST` body and as a query parameter in `GET /orders`. For an *internal* tool where a customer service agent queries on behalf of a customer, this is a reasonable operational model — access is controlled at the human layer, not the API layer. For an *external* deployment where customers interact with the API directly, accepting caller-supplied identity is a Conscious Tradeoff (it is documented as a gap) rather than an Unknown Gap. Classify it honestly based on what you documented in your ADD Section 1 Constraints. A production external deployment would verify identity via a JWT token (issued by an authorization service) before the Lambda ever runs — often handled by an Application Load Balancer or API Gateway authorizer. That pattern is outside the scope of this course, but it is the specific improvement to name here.
- Anything hardcoded in the handler files that should not be?

---

## Homework — Complete the WAF Audit + Cost Analysis (~90 min)

### Part 1 — Complete the Remaining Four Pillars (~50 min)

Budget roughly 10 minutes per pillar. The prompts below tell you where to look — they are not the answers.

#### Pillar 3 — Reliability

**WAF question:** *How do you handle component failures and meet availability targets?*

Where to look:
- **The SQS queue** — is there a Dead Letter Queue? If the processor Lambda fails five times on the same message, what happens to it? Does it disappear, or is it preserved somewhere you can inspect?
- **The processor Lambda** — does it re-raise on DynamoDB write failure, or swallow the exception? Look at your handler code.
- **The pipeline consistency window** — this is the Reliability finding from your Week 8 testing. The gap between `POST 202` and `GET 200` visibility is not DynamoDB eventual consistency (DynamoDB's `GetItem` is strongly consistent by default); it is the pipeline's asynchrony. How long is the window you observed? Is it documented for customers? Is there a mitigation (polling pattern, webhook, status endpoint)?
- **Single-region deployment** — conscious tradeoff for most pre-launch startups. Name it explicitly.

#### Pillar 4 — Performance Efficiency

**WAF question:** *How do you select, configure, and monitor resources to meet performance needs efficiently?*

Where to look:
- **Lambda memory** — what size did the provided starter use for the orders and processor Lambdas? Was this an informed choice or the default? What would change at 10K orders/day?
- **DynamoDB read patterns** — `GET /orders/{id}` uses `get_item()` (consistent, single-digit ms at any scale — this is a Best Practice Met). `GET /orders` uses `scan()` (reads every item — acceptable at NovaSpark's current scale, but broken at millions of orders). Name this explicitly as a Conscious Tradeoff.
- **Cold starts** — you measured one in Lab 4. Did you think about cold starts again when the async pipeline was introduced? A cold start on the processor Lambda means orders sit in SQS longer than expected. Is that acceptable?

#### Pillar 5 — Cost Optimization

**WAF question:** *How do you avoid unnecessary cost and confirm you're getting value from what you spend?*

Where to look:
- **DynamoDB billing mode** — `PAY_PER_REQUEST` (on-demand) was your Lab 5 choice. Why? Would provisioned capacity ever be cheaper for NovaSpark?
- **Resource tagging** — do your Pulumi resources have tags like `project=novaspark`? Without tags, AWS cost reports cannot distinguish your resources from anyone else's in the same account.
- **Billing alarms** — any CloudWatch billing alarm configured? If not, how would you discover a runaway cost before it consumes your entire Academy credit balance?

#### Pillar 6 — Sustainability

**WAF question:** *How do you minimize the environmental impact of running this workload?*

Where to look:
- **Lambda** — scales to zero when idle. No energy consumed when no orders are being processed. This is a genuine Best Practice Met.
- **DynamoDB on-demand** — same pattern; no provisioned capacity sitting idle.
- **EC2 instance type** — what did you use in Lab 2? ARM-based Graviton instances (`t4g` family) are meaningfully more power-efficient than equivalent x86 instances.
- **Region selection** — different AWS regions have different energy mixes (renewable percentage varies). You probably did not consider this when choosing `us-east-1`. Is that an Unknown Gap or a Conscious Tradeoff?

Take this pillar seriously. "Lambda is green because it scales to zero" earns partial credit. A finding that names a specific conscious tradeoff (e.g., "we chose us-east-1 for cost and latency reasons without considering its energy mix, which is lower renewable percentage than us-west-2") earns full credit.

### Part 2 — Write ADD Sections 4 and 5 (~30 min)

**Section 4 — Well-Architected Analysis**

Convert your six pillar entries into ADD Section 4. The format is a structured argument — not a checklist — that flows from one pillar to the next. Two pages is the target. Each pillar gets:

- A short framing sentence (the decision and WAF question)
- Current state with specific evidence (file paths, resource names, configuration values)
- Gap classification with one sentence of justification
- Proposed improvement, specific enough to file as a ticket

At the end of Section 4, add a one-line summary: *X findings classified as Unknown Gap, Y as Conscious Tradeoff, Z as Best Practice Met.* Honest counts earn full credit.

**Section 5 — Operational Considerations (draft notes)**

ADD Section 5 is finalized in Week 3, but your Op Ex and Reliability findings are the primary inputs. Capture as working notes:

- **Two CloudWatch metrics** that matter most for this async pipeline, with a threshold that would warrant an alert (e.g., SQS queue depth > 100 messages for 5 minutes; processor Lambda error rate > 1% over 15 minutes)
- **Two failure modes** from your audit — what happens when each occurs, and what the mitigation is or should be
- **One gap** from your WAF audit that should be addressed before production

Bullet form is fine for the notes. These become prose in Week 3.

### Part 3 — Cost Analysis → ADD Section 6 (~40 min)

Use the **AWS Pricing Calculator** at [calculator.aws](https://calculator.aws). No AWS account changes. Two estimates, both saved as public URLs.

#### Workload Assumptions

Use these standardized inputs so estimates are comparable:

| Parameter | Value |
|---|---|
| Average order request body | 500 bytes |
| Average response body | 250 bytes |
| Average DynamoDB record size | 1 KB |
| Orders Lambda memory | 128 MB |
| Orders Lambda avg duration | 150 ms |
| Processor Lambda memory | 128 MB |
| Processor Lambda avg duration | 200 ms |
| GET route ratio | 50% of total requests |
| Region | us-east-1 |
| Log volume per invocation | 1 KB |

At each traffic level: 50% of requests are `POST /orders` (which trigger a processor Lambda invocation), 50% are `GET` requests.

#### Estimate 1 — 100 req/day (~3K/month)

This is NovaSpark today. At this scale, almost everything is inside free tier. Monthly bill should be under $5.

Per-service inputs:
- API Gateway (HTTP API): 3,000 requests/month
- Orders Lambda: 3,000 invocations × 150ms × 128MB
- Processor Lambda: 1,500 invocations × 200ms × 128MB
- SQS: ~5,000 API calls (3 per processed message: send, receive, delete)
- DynamoDB on-demand: 1,500 reads + 1,500 writes, ~0.01 GB storage
- CloudWatch Logs: ~0.003 GB ingested

Save as `NovaSpark-100-per-day`. Copy the public URL.

#### Estimate 2 — 10K req/day (~300K/month)

Modest growth — some services exit free tier. This is where the unit economics start to become real.

Scale the inputs up 100× from the first estimate.

Notable at this scale:
- Lambda invocations may approach or exceed the free tier (1M invocations/month free — check if you cross it)
- CloudWatch log ingestion approaches the free tier ceiling (5 GB free)
- DynamoDB remains very cheap at on-demand for this volume

Save as `NovaSpark-10K-per-day`. Copy the public URL.

#### Write ADD Section 6

Two pages. Structure:

**1. The two estimates (table).** One row per traffic level. Columns: API Gateway, Lambda (combined orders + processor), SQS, DynamoDB, CloudWatch, Total.

**2. What drives cost at each scale (two paragraphs).** At 100/day: what is the dominant cost and why? At 10K/day: what changed, and which service is now the cost driver?

**3. When does the architecture stop being cost-effective? (1 paragraph)** Identify a specific threshold — either extrapolated from your two estimates or a calculation — where on-demand Lambda + DynamoDB becomes more expensive than a comparable Fargate or provisioned alternative. Name the specific crossover with a number.

**4. One architectural change that would defer the crossover (1 paragraph).** Be specific — switching DynamoDB from on-demand to provisioned at X writes/month, or migrating the processor to Fargate at Y orders/day. The change should come with a number.

---

## Deliverables

Submit a single PDF (or markdown rendered to PDF) containing:

- [ ] **D1 — ADD Section 4: Well-Architected Analysis** — six structured pillar entries + gap count summary (50 pts)
- [ ] **D2 — ADD Section 5 notes** — two CloudWatch metrics with thresholds, two failure modes with mitigations (20 pts)
- [ ] **D3 — ADD Section 6: Cost Estimate** — two Pricing Calculator URLs + summary table + four-part written analysis (25 pts)
- [ ] **D4 — Context paragraph** — 150–250 words connecting the SRE Book Ch. 6 "symptoms not causes" framing to one finding from your Op Ex pillar audit. What symptom should NovaSpark monitor that the current architecture doesn't expose, and what cause would that symptom typically indicate? (5 pts — light weight this week given overall load)

**Total: 100 points.**

---

## What Good Looks Like

**Specific evidence in Section 4.** "Security: we used IAM" earns no credit. "The processor Lambda's execution role has `dynamodb:PutItem` on `arn:aws:dynamodb:us-east-1:*:table/novaspark-orders`, scoped to write-only as configured in `__main__.py` Week 8 TODO 3 — the orders Lambda has separate read-only permissions" earns full credit.

**Honest gap classification.** A submission that classifies everything as Best Practice Met earns less than one that classifies most findings as Unknown Gap or Conscious Tradeoff. The purpose of the WAF is to find gaps, not to pass an exam. Most student architectures at this stage have 3–4 Unknown Gaps, 3–4 Conscious Tradeoffs, and 2–3 Best Practice Met findings across six pillars.

**Internally consistent cost numbers.** The 10K/day estimate should be roughly 100× the 100/day estimate, except where free tier breaks the linearity (most visibly at the 100/day level, where most costs are $0). If your 10K/day total is lower than your 100/day total, something is wrong.

**A real crossover threshold in Section 6.** "At some point Lambda gets expensive" earns no credit. "At approximately 20M DynamoDB writes per month, on-demand capacity costs $X; provisioned capacity for equivalent throughput costs $Y — the crossover is around 15M writes/month for this workload" earns full credit.

---

## What This Sets Up

By end of this week:
- ADD Sections 1, 4, 5 (draft), and 6 are complete
- Two of the remaining sections (2 and 3) are partially drafted from Week 8 work
- One section (3) needs finalization

Week 10 is assembly, not authoring. If Section 4 is vague this week, Week 10 cannot fix it in time. Do the WAF audit at depth now.
