# The ADD: Big Picture
## CS 545 — Week 8 | Project Week 1 of 3

Before you open the lab guide, read this. It takes ten minutes and will save you from the most common mistake students make in the project: writing ADD entries that are technically correct but architecturally shallow.

---

## The NovaSpark Context — How We Got Here

NovaSpark is a mid-size retail platform that has been processing customer orders for several years. Until recently, their order processing system was built around a traditional synchronous model: a customer submits an order, the web server calls the order processor directly, waits for it to complete, and returns a confirmation. That model worked when order volume was low and the system lived on a handful of long-running servers. It has not scaled gracefully.

**The problems that surfaced as the business grew:**

The order processor does real work — it validates inventory, applies pricing rules, and persists the record. Under load, customers submitting orders were waiting on all of that before getting a response. During peak periods, slow processor performance cascaded directly into slow response times for customers. Worse, a processor failure meant a 500 back to the customer, even when the failure had nothing to do with whether the order was valid. The ordering surface and the processing logic were tightly coupled in ways that made both harder to change independently.

Beyond performance, the infrastructure itself became a liability. Servers needed to be kept running, patched, and sized for peak load — which meant paying for capacity that sat idle most of the time. Deploying a change to the order processor meant coordinating a deployment window. Adding a new route meant touching the same server configuration that ran everything else.

**What the primary stakeholders have been asking for:**

- **Janet (VP Engineering):** Wants to show investors a system that can handle growth without expensive infrastructure decisions every quarter. The ask is a modern, cloud-native order pipeline that demonstrates the organization can operate with the same rigor as the companies they compete with.

- **Ben (Engineering Lead):** Has been managing the operational pain of the current system. His concern is reliability and deployment independence — he wants order submission to be separated from order processing so that a slow processor doesn't block customers, and so his team can deploy and scale each piece independently.

- **Linda (Principal Architect):** Has seen too many systems get rebuilt without a clear record of why decisions were made, leaving the next team to guess. Her requirement is documentation. Not a description of what was built — a record of what was decided, what was considered and rejected, and why. That record is what makes a system maintainable and defensible in an engineering review.

**What is being proposed:**

A rebuild of the order processing components using a cloud-native, event-driven architecture. The core of the proposal is to decouple order submission from order processing using an asynchronous queue: when a customer submits an order, the system immediately acknowledges receipt and hands the order off to a queue for processing. The customer gets a fast, reliable response. The processor works at its own pace, independently scalable, without affecting the submission surface.

The full stack — API Gateway, Lambda, SQS, DynamoDB — replaces the synchronous monolith with components that scale independently, deploy independently, and fail independently. Infrastructure is defined as code so it can be recreated consistently across environments and torn down cleanly when not needed.

**Your role:**

You are a primary architect on this project. You are not just implementing the system — you are responsible for defining the architecture, documenting the decisions, and producing the written record that Linda requires and that the organization can stand behind. The Architecture Design Document you are building across these three weeks is that record. It is not a lab report. It is the artifact that explains, to anyone who reads it in the future, why NovaSpark's order pipeline is the way it is and what was consciously considered and rejected along the way.

The system you are deploying in today's lab is the first complete implementation of this proposal. What you write in the ADD is the engineering foundation that justifies it.

---

---

## What the ADD Is — and What It Isn't

The Architecture Design Document is a **record of decisions and reasoning** — not a description of what you built. This distinction matters more than any formatting requirement.

A description of what you built might say:

> The system uses SQS between the orders Lambda and the processor Lambda.

A record of a decision says:

> The orders Lambda enqueues to SQS rather than invoking the processor Lambda directly, because a synchronous invocation would couple the customer's response time to the processor's execution time and make a 202 response semantically dishonest. The alternative — a direct Lambda-to-Lambda call — was rejected because a processor failure or cold start would propagate as a 5xx to the customer. SQS eliminates that coupling.

Both sentences describe the same architecture. Only the second one documents a decision. The grader cannot tell, from the first sentence, whether you understood why SQS was the right choice or whether you just used what was in the starter stack.

**Every major ADD entry answers three questions:**
1. What did you choose?
2. What did you not choose, and why?
3. What does the chosen option cost you that the alternative would not have?

---

## The Six Sections — What Each One Is Doing

The ADD has six sections. You will build them across three weeks. Here is what each section is actually trying to answer:

---

### Section 1 — Requirements
**The question:** What does this system need to do, and what are the constraints it operates under?

This section has nothing to do with implementation. It is the specification that all your later decisions are measured against. If you cannot state a concrete requirement, you cannot evaluate whether your architecture satisfies it.

The four subsections each serve a different purpose:

**1a — Functional Requirements** answer: *What observable behaviors does the system produce?* For each route, what does a caller send and what does the system guarantee in return? "The system processes orders" is not a functional requirement. "POST /orders returns 202 Accepted with an order_id within 200ms and places the order on SQS" is.

> **Getting started:** Open `orders/handler.py`. Read each route handler top to bottom. For every route, ask: what HTTP method and path does it handle? What fields does it require in the body or query string, and what happens when they're missing? What HTTP status code does it return on success — and why that code and not another? What side effects does it produce (writes to SQS, reads from DynamoDB)? Write one FR statement per route, in the form: *[METHOD /path] accepts [inputs], does [action], and returns [status code + response body]. If [bad input], returns [error code].* The async pipeline behavior — that the processor Lambda eventually writes to DynamoDB — is itself a functional requirement. Don't omit it just because it happens out of band.

**1b — Non-Functional Requirements** answer: *How well does the system need to perform, and how do you measure it?* These are numbers, not adjectives. Your Postman test session gives you real latency data — use it. The consistency window you observed in Test 2 is a measured NFR, not an abstract concept.

> **Getting started:** Pull up your Postman test results. You have real response times — use them as your baseline. For each NFR, ask: what unit does this get measured in? Latency is milliseconds. Availability is percentage uptime. Throughput is requests per second or orders per day. Consistency is a time window. Write each NFR with a number and a source: *"POST /orders returns 202 at p50 under 200ms (observed: [X]ms in Postman testing)."* Then think about what you haven't measured yet. You observed the consistency window — how long did the 404 persist before the GET returned 200? That time is your pipeline latency NFR. What throughput is NovaSpark realistically targeting today? What would be unacceptable from a user experience standpoint? Work backwards from the user to get to the number.

**1c — Constraints** answer: *What is the system not allowed to do, or not able to do, regardless of what might be architecturally ideal?* The AWS Academy LabRole restriction is a real constraint — it means you cannot implement least-privilege IAM, and your ADD should say so explicitly rather than pretending the architecture is something it isn't. The authentication gap (this API accepts customer_id as caller input rather than extracting it from a verified token) is also a constraint worth naming here before it becomes a Security finding in Section 4.

> **Getting started:** Think about what you wanted to do but couldn't — or what you know you should do in production but can't here. Start with IAM: did you try to create a custom Lambda execution role? You couldn't — the Academy sandbox blocks it. Write that down as a constraint, name what it costs you (both Lambdas share LabRole instead of having least-privilege roles), and state what you would do in a real account. Then think about deployment scope: everything is in one AWS region. Is that a constraint? Yes — a regional outage takes down NovaSpark entirely. Then ask: who can call this API right now? Anyone with the URL. Is `customer_id` verified anywhere, or is it just trusted as caller input? That authentication gap is a constraint with a name. Constraints are not failures — they are things you are choosing to accept or are forced to accept, documented honestly.

**1d — 12-Factor Compliance** answers: *How well does this system align to cloud-native operational principles?* Not every factor is relevant — three or four that directly apply to this architecture are more useful than a superficial pass through all twelve.

> **Getting started:** Trace three things through your system. First, trace your configuration: where does `QUEUE_URL` live? Is it hardcoded in `handler.py` or injected at runtime? Open `handler.py` and search for any hardcoded ARNs or URLs — if you find one, that's a Factor III gap. If everything reads from `os.environ`, that's Factor III satisfied. Second, trace your state: does your Lambda store anything in memory between invocations? If the Lambda restarts, does it lose anything important? If no, that's Factor VI (stateless processes) satisfied. Third, trace your logs: where does a `print()` call go? How would you find a processor error that happened at 2am? That's Factor XI. After those three, ask what's missing: how would you run a one-off data backfill against your DynamoDB table? Is there a mechanism for that? If not, that's a Factor XII gap worth naming.

---

### Section 2 — Architecture Overview
**The question:** If someone who has never seen this system needs to understand it in five minutes, what do they need to know?

This section is written last (Week 3) because you cannot write a good overview until you have completed the audit and the component decisions. Section 2 is a synthesis — it references the decisions you documented in Section 3 and the findings you identified in Section 4.

You are not writing Section 2 this week. But keep it in mind: the decisions you document now will become the narrative of Section 2 later.

> **What to notice this week:** As you work through the lab, pay attention to the data flow — a customer submits a POST, the orders Lambda enqueues to SQS, the processor Lambda reads from the queue and writes to DynamoDB, and the GET routes read back from DynamoDB. Sketch that sequence on paper or in a doc. That sketch is the starting point for Section 2. If you can narrate the path of a single order from POST to GET in plain language, you have Section 2's core. You'll formalize it in Week 3.

---

### Section 3 — Component Decisions
**The question:** For each major architectural component, why this and not something else?

This section is the heart of the ADD. It is also the section most students underwrite in Week 1. The lab guide asks you to write a *seed* — draft-quality entries that establish the structure and key reasoning. You will expand and polish them in Week 3.

For each component you are documenting, the driving question is: **what was the decision, what alternatives existed, and what specifically made those alternatives worse?**

The five components you're writing about this week:

| Component | The Decision Being Documented |
|-----------|-------------------------------|
| API Gateway (HTTP API) | HTTP API vs. REST API vs. Lambda Function URL |
| Orders Lambda | Runtime, memory, timeout — and what the Lambda must not do |
| SQS Queue | Why async / why standard vs. FIFO / what the failure mode is |
| Processor Lambda | Batch size, idempotency, error handling |
| DynamoDB Table | Partition key choice, capacity mode, access pattern fit |

The SQS entry is the most important one this week. If you can explain exactly what breaks when you replace SQS with a synchronous call, you understand why the architecture is the way it is. If you cannot, you are documenting structure without understanding.

> **Getting started — the universal move for every component:** Open `__main__.py` and find the Pulumi resource definition for the component you are writing about. Look at every parameter that is explicitly set. Ask yourself: was this a deliberate choice or a default I left in place? If you left a default in, do you know what that default is and why it's appropriate? If you changed a value from the default, why? Those are your decision points.
>
> Then ask the removal question: *what would break if this component weren't here?* For SQS, remove it and replace it with a direct Lambda call — trace what happens to the orders Lambda when the processor is slow or fails. For DynamoDB, replace it with a different key design — trace what happens to your GET /orders/{id} lookup. The removal question forces you to articulate the value the component is providing, which is exactly what the Section 3 entry needs to capture.

**API Gateway:** Look at your resource type in `__main__.py` — it's `apigateway.HttpApi`, not `apigateway.RestApi`. Do you know the difference? HTTP API is cheaper and lower-latency for simple Lambda integrations; REST API adds features (usage plans, API keys, request transformation) that NovaSpark doesn't need yet. A Lambda Function URL is a third option — a direct HTTPS endpoint on the Lambda with no gateway layer. What would you lose with a Function URL? Routing. A single Function URL can only call one Lambda — you couldn't route `POST /orders` and `GET /orders/{id}` to the same handler via a gateway-style path pattern.

**Orders Lambda:** Find the memory and timeout values. Were those deliberate? The critical constraint on this Lambda is what it must *not* do — it must not wait for the processor. If it calls the processor synchronously and waits, then the 202 becomes a lie (you're not returning until processing is done) and the customer is waiting on processor latency. The decision to enqueue to SQS and return immediately is the core design decision for this component.

**SQS Queue:** This is the most important entry. Do the thought experiment: remove SQS and replace it with a direct `lambda.invoke()` call inside the orders Lambda. Now trace the order flow. The orders Lambda calls the processor Lambda and waits. What is the customer waiting for? Processor execution time plus DynamoDB write latency. What happens if the processor Lambda has a cold start? The customer waits longer. What happens if the processor throws an exception? The orders Lambda has to return a 5xx. None of that is what 202 promises. SQS breaks that coupling — the orders Lambda enqueues and returns 202 in milliseconds, and the processor runs on its own timeline. That reasoning is your Section 3 SQS entry.

**Processor Lambda:** Find the `batch_size` in your EventSourceMapping. It's 1 — one message per invocation. That was a choice. Why not 10? At NovaSpark's current scale, batching adds complexity (you have to handle partial batch failures) without meaningful throughput benefit. Now look at your `put_item` call in `processor/handler.py`. Is there a `ConditionExpression`? What happens if SQS delivers the same message twice — does your second write overwrite the first silently, reject it, or crash? That's your idempotency question, and it's the most technically interesting part of this entry.

**DynamoDB Table:** Find the `hash_key` in your Table resource. It's `order_id`. Now ask: could it have been `customer_id`? Trace both GET routes. `GET /orders/{id}` looks up a single order by ID — that's a direct key lookup, which is fast and cheap with `order_id` as the partition key. If `customer_id` were the partition key, that same lookup would require a scan. `GET /orders?customer_id=X` currently does a scan with a filter — that works at small scale. At large scale, a GSI on `customer_id` would make it a Query instead. That trade-off (current scan vs. future GSI) is what your DynamoDB entry should document.

---

### Section 4 — WAF Findings
**The question:** Does this architecture hold up against each of the six Well-Architected pillars — and where it doesn't, is that a known tradeoff or an unknown gap?

This section is Week 2's primary deliverable. You are not writing it this week. But several of your Week 1 decisions will feed directly into Week 2 findings:

- The LabRole constraint you document in Section 1c becomes the Security pillar finding in Section 4
- The consistency window you measure in Test 2 becomes the Reliability pillar finding
- The batch_size decision you document in Section 3 (Processor Lambda) connects to Reliability and Performance Efficiency

Write your Section 1 and Section 3 entries with enough specificity that Week 2-you can pick them up and use them as inputs.

> **What to notice this week:** Each WAF pillar asks a different question about the same system. As you test and deploy, notice the things that feel fragile or incomplete. What would happen if the processor Lambda failed mid-write? What would happen if a user submitted 10,000 orders at once? What does it cost to run this system for a month? What would you look at to know something was wrong? Those observations aren't WAF findings yet — but writing them down now means Week 2 is synthesis, not starting from scratch.

---

### Section 5 — Operational Considerations
**The question:** If this system were running in production, how would you monitor it, respond to failures, and keep it healthy?

Also Week 2. The WAF Operational Excellence pillar drives most of this. What you need to know now: the CloudWatch Logs behavior you observe during testing (processor Lambda logs, orders Lambda logs) is directly relevant to what you'll write here.

> **What to notice this week:** When something goes wrong during testing — a 500, a missing environment variable, a message that doesn't get processed — where did you look to diagnose it? That debugging path is your operational story. Open CloudWatch Logs during the lab and look at what a successful order invocation actually logs vs. what a failure logs. Is there enough information to diagnose a problem at 2am without access to the code? If not, that's an Operational Excellence finding.

---

### Section 6 — Cost Estimate
**The question:** What does this architecture cost to run, and where are the dominant cost drivers?

Week 3. Lambda, SQS, DynamoDB, and API Gateway each have distinct pricing models. You will not write this section now, but keeping rough numbers in mind as you work through the lab — Lambda invocation count, DynamoDB read/write units consumed — is useful background.

> **What to notice this week:** Every time you run a Postman test, you are consuming billable resources: an API Gateway request, a Lambda invocation (or two), an SQS message, a DynamoDB write and read. The numbers are tiny at test scale, but the pattern matters. Think about what 1,000 orders per day would look like — how many Lambda invocations, how many SQS messages, how many DynamoDB writes? Those estimates are the foundation of Section 6.

---

## The Living Document Model

The ADD is not a document you write once. Each week adds sections. Nothing is thrown away. Here is the build sequence:

```
Week 8 (this week)
  └── Section 1: Requirements ← write this now
  └── Section 3: Component Decisions (seed) ← write this now

Week 9
  └── Section 4: WAF Findings ← driven by the six pillars
  └── Section 5: Operational Considerations ← driven by Operational Excellence

Week 10
  └── Section 2: Architecture Overview ← synthesis of 3, 4, 5
  └── Section 3: Full expansion ← polish the seed, add GSI discussion, add IAM detail
  └── Section 6: Cost Estimate ← Lambda + SQS + DynamoDB + API GW pricing
```

The consequence of this: vague Section 1 writing creates problems in Week 2 and Week 3. If your NFRs are adjectives instead of numbers, you have nothing to measure your WAF findings against. If your Section 3 seed doesn't name rejected alternatives, Week 3-you has no foundation to build the full entry from.

---

## How to Approach the Writing

The most common weak ADD entries share a pattern: they describe the current state without revealing the reasoning. They sound like architecture documentation. They do not read like engineering decisions.

**Ask yourself these questions before writing each entry:**

- *What did this decision cost me?* Every architectural choice has a downside. SQS adds latency. On-demand DynamoDB costs more at high throughput than provisioned. If you can't name the cost, you haven't finished thinking about the decision.

- *What would have broken if I'd chosen differently?* This is the rejected-alternative test. If you can describe the specific failure mode that the alternative would have created, your reasoning is real. If you can only say "it wouldn't have been as good," keep thinking.

- *Is this a Conscious Tradeoff or an Unknown Gap?* A Conscious Tradeoff is a risk you know about, can explain, and have a remediation path for. An Unknown Gap is a risk you found during the audit that you hadn't thought about. Both are acceptable — but pretending a gap is a tradeoff when you didn't actually evaluate it is the thing the ADD is designed to prevent.

- *Would a new engineer reading this understand why the system is the way it is?* If the only way to understand the decision is to already understand the architecture, the entry isn't complete.

---

## What Week 1 Success Actually Looks Like

By the time you submit the Week 8 deliverable, the ADD foundation should be solid enough that Week 2 adds a new chapter rather than fixing a broken one.

Concretely:

- Section 1 has **numbers** — specific latency targets, a measured consistency window, a named constraint for the LabRole, an explicit statement about the authentication gap
- Section 3 seed has **named alternatives** — for SQS you named the synchronous call and explained the failure mode it creates; for DynamoDB you named why `order_id` is the partition key and not `customer_id`
- The consistency window observation from Test 2 is recorded with an actual time — not "about 10 seconds" but the number you measured
- The LabRole constraint is written as a constraint (not glossed over), with the production alternative stated

If the pipeline is deployed and the ADD entries are thin, you have completed the easier half of the work.
