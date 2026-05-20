# Week 10 Lab Guide — ADD Synthesis + Final Project Close

**Course:** CS 545 — Cloud Native Platform Engineering
**Paired lecture:** None — final project session
**Session structure:** First 60 min (instructor-guided synthesis) → Remaining 110 min (open work session)
**AWS infrastructure required:** Yes — your Week 8 stack for demo recording
**Prerequisite:** Weeks 8 and 9 labs complete. ADD Sections 1, 4, 5 notes, and 6 drafted and submitted.

---

## The Goal for This Session

You arrive with four ADD sections drafted (1, 4, 5 notes, 6) and seeds for two more (3 from Week 8, diagrams from Labs 3–5). You leave with a complete ADD draft and a plan for the demo video.

This session is not a lecture. It is not a new lab. It is structured work time with instructor support — the kind of session where sitting still and waiting for inspiration is the worst strategy.

Here is what "done" looks like by the end of this session:

- ADD Sections 2 and 3 assembled from prior work
- ADD Section 5 expanded from notes to prose
- All six sections in one document, reading as a coherent argument
- `pulumi up` confirmed working on your Week 8 stack
- Postman collection confirmed running against the live stack
- Demo video either recorded or blocked on something specific you can fix tonight

---

## First 60 Minutes — Instructor-Guided Synthesis

### Section 2 — Architecture Overview (~25 min)

Section 2 is a system diagram plus a narrative paragraph. You are not drawing a new diagram from scratch — you are pulling diagrams you already produced.

**The diagram:** Assemble one coherent architecture diagram from:
- Your Lab 3 VPC diagram (the network boundary)
- Your Lab 4 Lambda + API Gateway diagram (the serverless compute layer)
- Your Lab 5 DynamoDB table diagram or model (the storage layer)
- Your Week 8 pipeline diagram or the one from the project roadmap (the async flow)

The target is a single diagram showing the complete request path: Client → API Gateway → Orders Lambda → SQS → Processor Lambda → DynamoDB, with the VPC boundary shown and the key IAM relationships noted.

Tools: draw.io, Lucidchart, even a clean hand-drawn diagram photographed clearly. The diagram does not need to be beautiful — it needs to be accurate and complete.

**The narrative:** Three short paragraphs:
1. What the system does in one sentence, and what each major component's role is
2. A request walkthrough — trace a single `POST /orders` call from the client HTTP request to the persisted DynamoDB record, naming each component in the path
3. One sentence on the AWS Academy constraints that differ from a production account (LabRole IAM scope, single-region, no custom domain)

Section 2 target length: ~2 pages including the diagram.

---

### Section 3 — Component Decisions (~35 min)

Section 3 is assembled from the Section 3 seed you wrote in Week 8, plus one addition: each component now needs at least one explicitly named rejected alternative.

**The scaffold (provided):**

Work through each component in this order. For each, you already have a draft answer from Week 8 — your job now is to sharpen it and confirm the rejected alternative is named.

**API Gateway (HTTP API)**

Your Week 8 seed covered why you chose HTTP API. For the ADD, also name:
- What you explicitly rejected: the REST API product (AWS's older, more feature-rich API Gateway product). One sentence on why — it is ~3.5× more expensive per request and has features (usage plans, API keys, request validation schemas) NovaSpark does not currently need.
- The deployment context choice: API Gateway here is a **publicly addressable HTTPS endpoint** — the external API pattern, appropriate for a customer-facing or partner-accessible service. The alternative is an internal API scoped to a private network (via VPN or internal Application Load Balancer), which would be appropriate if this were a backend service that should never be reachable from the public internet. NovaSpark's order submission use case is a customer-facing workflow, so the public endpoint is the correct choice. Your ADD entry should state this explicitly, because the public endpoint is the architectural premise for the `customer_id` data model and the Security pillar finding in Section 4.

**Orders Lambda**

From your Week 8 seed. Add the rejected alternative:
- Synchronous processing (no queue) — the orders Lambda calls the processor logic directly and waits. Name the failure mode this creates and why it violates the 202 semantics you documented in Section 1.

Also address the `customer_id` implementation in this entry. The handler accepts `customer_id` as a required field in `POST /orders` and as a query parameter in `GET /orders?customer_id=X`. Your ADD entry should state the calling context this is designed for: an *internal* deployment where a customer service agent passes `customer_id` explicitly is a fully reasonable pattern — the data scoping is correct and the missing piece is only authentication (who is the agent). For an *external* deployment where customers interact with the API directly, accepting caller-supplied identity is a documented gap: in production, `customer_id` would be extracted from a verified JWT token rather than trusted as a request parameter. JWT validation via an Application Load Balancer or API Gateway authorizer is outside the scope of this course, but it is the concrete improvement to name. This entry in Section 3 is what the Security pillar finding in Section 4 should reference — make the cross-reference explicit.

**SQS Queue (standard)**

From your Week 8 seed. Add the rejected alternative:
- SNS + Lambda fan-out — SNS pushes to subscribers rather than SQS queuing. Name why SQS was chosen over SNS for this use case: SQS provides durable queuing with retry and DLQ support; SNS does not guarantee delivery if the subscriber is unavailable. For a pipeline where every order must be processed, SQS is the right choice.

**Processor Lambda**

From your Week 8 seed. This one often needs the most expansion. The `put_item` idempotency question from Week 8 belongs here, not in Section 4. If your processor does `put_item` with `order_id` as the key, a duplicate SQS delivery results in an idempotent overwrite — this is a Conscious Tradeoff (not a bug, but also not the same as an explicit idempotency key strategy). Name it clearly.

**DynamoDB Table**

From your Lab 5 design and Week 8 seed. Add:
- Rejected alternative: Amazon RDS (relational database). One sentence on why DynamoDB fits better for this access pattern — key-value lookups by `order_id` and full scans for listing; no relational joins needed; managed scaling without a connection pool.

**Integrating Section 3 with Section 1:**

Section 3 should reference Section 1 at least once. The component decisions you document in Section 3 should trace back to requirements you stated in Section 1. Example: "The decision to use a standard SQS queue rather than synchronous processing directly satisfies NFR-3 (POST /orders returns 202 under 200ms) — decoupling the submission response from the processor execution time ensures the latency target is met regardless of processor performance."

---

## Remaining 110 Minutes — Open Work Session

The rest of the session is yours. Use it for the tasks below in priority order.

### Priority 1 — Deploy and Verify Your Stack (~15 min)

Before recording anything:

```bash
cd your-project-directory
pulumi up
```

Confirm the deployment completes cleanly with no errors. Then run your Postman collection against the deployed stack — all three core routes should return the expected status codes. If anything is broken, fix it now. You cannot record a demo of a broken system.

Common issues at this stage:
- Stack state is stale — run `pulumi refresh` if you get errors about resources that already exist
- Environment variable missing — check CloudWatch Logs for the Lambda that's failing
- DynamoDB table from Lab 5 not accessible — confirm the table name matches what Week 8's `__main__.py` expects

### Priority 2 — Finalize ADD Section 5 (~20 min)

Expand your Week 9 Section 5 notes from bullet points to prose. Three subsections:

**Monitoring Strategy**

Based on the two CloudWatch metrics you identified in Week 2, write 2–3 sentences per metric: what it measures, what threshold constitutes an alertable condition, and what the alert should trigger (page the on-call engineer, auto-scale, trigger a DLQ reprocessing job).

For the NovaSpark async pipeline, the two metrics most students identify are:
- SQS queue depth (ApproximateNumberOfMessagesNotVisible) — high queue depth means the processor is falling behind; at NovaSpark's scale a depth > 50 for 5 minutes is worth investigating
- Processor Lambda error rate — any sustained error rate above 1% in a 15-minute window means orders are potentially being lost to the DLQ

**Deployment Approach**

Three sentences: the `pulumi up` workflow, how you would handle a failed deployment (rollback strategy), and one sentence on secret management (are there any secrets in this stack? where should they live in a production account?).

**Failure Modes and Mitigations**

Two failure modes, each with a current state and a mitigation. Use the two you identified in Week 9. Example format:

> *Failure mode: Processor Lambda throws an unhandled exception during DynamoDB write.*
> *Current state: SQS retries the message up to the configured `maxReceiveCount`. With no DLQ configured, the message is deleted after max retries — the order is silently lost.*
> *Mitigation: Configure a Dead Letter Queue on the SQS queue. Set `maxReceiveCount` to 3. Monitor the DLQ size with a CloudWatch alarm that pages on any non-zero count.*

### Priority 3 — Polish the Full ADD (~30 min)

With all six sections drafted, do one pass for coherence:

1. Does Section 1 use the same component names as Sections 2 and 3? Inconsistent naming ("the worker Lambda" in one section, "processor Lambda" in another) makes the document harder to read.
2. Does Section 4 reference specific decisions documented in Section 3? The WAF audit should cite the architectural choices you justified in Section 3 — "the batch size of 1 discussed in Section 3 means cold start behavior on the processor Lambda directly affects queue throughput" is a connection that earns credit. In particular, the Security pillar finding about `customer_id` caller-supplied identity should reference the deployment context decision documented in Section 3's API Gateway and Orders Lambda entries. If Section 3 states that this is an internal deployment pattern with a documented external gap, Section 4 should classify the `customer_id` finding as a **Conscious Tradeoff** (not an Unknown Gap) and cite Section 3 as evidence that the choice was deliberate.
3. Does the cost estimate in Section 6 connect back to the architecture described in Sections 2 and 3? The cost table should reference specific components by the names used elsewhere in the document.

### Priority 4 — Record Your Demo Video (~30 min)

The demo is 5 minutes. Plan your segments before recording:

| Segment | Duration | What to show |
|---------|----------|-------------|
| `pulumi up` | 60 sec | Terminal — stack deploying cleanly, outputs appearing |
| Postman collection run | 90 sec | All three core routes: POST (202), GET by ID (200), GET all (200). Show the order_id from POST used in the GET by ID request. |
| Architecture walkthrough | 60 sec | Your Section 2 diagram on screen — name each component and its role |
| ADD design decisions | 45 sec | Name two decisions from your ADD (Section 3) and say whether implementation matched design |
| `pulumi destroy` | 45 sec | Terminal — clean teardown |

Record using Loom, QuickTime (Mac), or OBS. Confirm audio is working before the full recording. The demo does not require narration throughout — you can pause and explain during the architecture walkthrough — but the Postman run should be clean and uninterrupted.

If you cannot complete the recording in class, use this session to at minimum record the Postman run segment. That is the segment most likely to fail under time pressure at home, and it is the hardest to re-record cleanly.

### Priority 5 — Draft the Written Reflection (~30 min, may continue at home)

The reflection is 1–2 pages. Four required components:

**1. Where implementation matched your ADD and where it diverged.**
Be specific. "The implementation matched Section 3's SQS choice because X" and "The implementation diverged from Section 1's latency requirement because Y" are both good answers. The divergence is not a failure — it is the most interesting part of the reflection. Common divergences in this architecture: the consistency window was longer than the NFR stated in Section 1; the IAM permissions ended up broader than Section 3 intended; the `GET /orders` scan is already slow with even a small number of test records.

**2. One WAF pillar addressed well — with a specific code or configuration example.**
Point to a line in `__main__.py` or a handler file. "We addressed the Security pillar by scoping the processor Lambda's execution role to `dynamodb:PutItem` only — see `__main__.py` line X" is the right level of specificity.

**3. One WAF pillar not addressed — with a concrete proposed fix.**
"We did not configure a Dead Letter Queue on the SQS queue. The fix is a `aws.sqs.Queue` resource in `__main__.py` with `redrive_policy` pointing at a new DLQ queue ARN, plus a `maxReceiveCount` of 3 on the main queue." Concrete enough to implement.

**4. One thing you learned from building that the ADD didn't anticipate.**
Factor XI (Logs as Streams) and the eventual consistency window are common answers here — not because they're required, but because they tend to genuinely surprise students who thought about them analytically in Section 1 but observed them differently in practice.

---

## Final Submission Checklist

Submit all of the following by the end of Week 10.

### Architecture Design Document (Canvas — PDF)

- [ ] Section 1: Requirements — functional, non-functional, constraints, 12-factor hooks
- [ ] Section 2: Architecture Overview — diagram + narrative
- [ ] Section 3: Component Decisions — five components, each with rationale + ≥1 rejected alternative
- [ ] Section 4: WAF Analysis — six pillars with evidence + gap count summary
- [ ] Section 5: Operational Considerations — monitoring, deployment, failure modes
- [ ] Section 6: Cost Estimate — two traffic levels, per-service breakdown, crossover threshold
- [ ] Length: 10–14 pages total
- [ ] No leftover scaffolding or TODO placeholders

### Final Project Code (GitHub repo `/project/` directory)

- [ ] `__main__.py` — complete Pulumi stack, three core routes wired
- [ ] `orders/handler.py` — POST, GET by ID, GET all implemented
- [ ] `processor/handler.py` — SQS trigger → DynamoDB write
- [ ] `requirements.txt`
- [ ] `README.md` — how to deploy, where to find the Postman collection, what the extension does (if any)
- [ ] `pulumi up` runs cleanly from a fresh state
- [ ] `pulumi destroy` runs cleanly

### Demo Video (Canvas — YouTube or Loom link)

- [ ] Under 5 minutes
- [ ] `pulumi up` shown completing
- [ ] Postman run showing all three core routes
- [ ] Architecture diagram walkthrough with narration
- [ ] Two ADD decisions named with implementation comparison
- [ ] `pulumi destroy` shown completing

### Written Reflection (Canvas — PDF)

- [ ] 1–2 pages
- [ ] All four required components answered
- [ ] References the ADD explicitly (at least two section citations)

---

## A Note on the Week 10 Deadline

Both the ADD and the Final Project are due **end of Week 10**. There are no late submissions on either deliverable.

The grading timeline is tight — final grades are due shortly after the end of the term. Submissions received after the deadline cannot be graded in time. If you are concerned about completing on time, bring your specific blocker to the instructor during this session. The most common late-stage blockers are fixable in 30 minutes with the right help.

The students who struggle at this stage almost always have the same problem: their Week 8 stack isn't working, so they have no system to demo and no concrete evidence to cite in the WAF audit. If that is your situation, that is the one thing to fix today, before anything else.
