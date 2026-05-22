# Project Getting Started
## CS 463 — Cloud Native Platform Engineering | Final Three Weeks

Read this before you open the Week 8 lab guide. It will give you the context you need to understand why you are doing this work, what the three weeks are building toward, and how to approach each deliverable.

---

## The NovaSpark Context — How We Got Here

NovaSpark is a mid-size retail platform that has been processing customer orders for several years. Until recently, their order processing system was built around a traditional synchronous model: a customer submits an order, the web server calls the order processor directly, waits for it to complete, and returns a confirmation. That model worked when order volume was low and the system ran on a handful of long-running servers. It has not scaled well.

**What broke as the business grew:**

When the processor was slow — because of database latency, a cold start, or a spike in orders — customers waiting for confirmations experienced that slowness directly. When the processor failed, customers got errors, even when their order data was perfectly valid. The submission surface and the processing logic were tightly coupled: changing one required touching the other, and deploying a fix meant coordinating downtime.

The infrastructure itself added operational drag. Servers needed to be kept running and patched. Capacity had to be sized for peak load, which meant paying for resources that sat idle most of the time. Scaling required manual intervention.

**What the stakeholders asked for:**

- **Janet (VP Engineering):** A system that can handle growth without a new infrastructure decision every quarter. She wants to show investors that NovaSpark operates with the rigor and efficiency of the companies they compete against.

- **Ben (Engineering Lead):** Wants order submission separated from order processing. A slow or failing processor should not block a customer from getting a confirmation. He wants each piece of the system to deploy and scale independently.

- **Linda (Principal Architect):** Has seen systems rebuilt without any record of why decisions were made, leaving the next team guessing. Before NovaSpark launches anything publicly, she wants an honest evaluation of what was built: where it holds up, where the gaps are, and whether those gaps are known or unknown.

**What was built:**

Across Labs 1 through 6, you built the modernized version of NovaSpark's order processing system from the ground up. An API Gateway that accepts order submissions. Lambda functions that handle routing and processing. An SQS queue that decouples submission from processing. A DynamoDB table that persists every order. A VPC with controlled network access. Infrastructure defined as code with Pulumi so it can be recreated and torn down reliably.

The core platform is complete. These final three weeks are not about building the foundation. They are about something harder: honestly evaluating what you built, extending it in a direction that matters, and demonstrating it clearly.

**Your role:**

You are being asked to step into the role of a practicing cloud engineer at NovaSpark. You built this system. Now you need to evaluate it against a professional standard, identify what is production-ready and what isn't, make one concrete improvement, and show your work on camera. That is exactly the cycle engineers go through before any system goes live.

The three deliverables you will produce across these weeks are the evidence that you can do that.

---

## The Three Deliverables — What Each One Is

### 1. A Working API with at Least One Extension

Your Lab 6 stack is the foundation. The project asks you to extend it in at least one direction from the extension menu. The extension is not optional and it is not a bonus. It is required because adding something new to a working system — and keeping it working — is a different skill than building from a lab guide.

The extension you choose should be motivated by something real: a gap you found in your WAF audit, a capability NovaSpark would actually need, or a technical problem you want to solve. A working `PATCH /orders/{id}` endpoint is a better project outcome than an ambitious Lambda authorizer that half-works.

**What "working" means:** `pulumi up` from a clean state produces a live stack. Your Postman collection runs against it and every route returns the expected response. `pulumi destroy` tears it down cleanly with no orphaned resources. If any of those three fail, the demo doesn't work.

> **Getting started:** Before Week 9, read the full extension menu in the project roadmap and pick one. The students who use Week 9 to choose an extension spend the first half of the Week 10 build session deciding instead of building. Make the choice early, even if you revise it after the WAF audit.

---

### 2. A Five-Minute Demo Video

A screen recording showing the system working and you explaining why it is built the way it is. This is not a tutorial and it is not a walkthrough of your code. It is a demonstration of a running system with an explanation of at least one architectural decision.

The five required elements are: `pulumi up` completing cleanly, a Postman collection run against the live API, an architecture walkthrough naming each component, one decision explained in plain language, and `pulumi destroy` completing cleanly.

**What "explaining a decision" means:** Naming a component is not explaining a decision. "We used SQS" is a description. "We used SQS because a direct Lambda call would make the customer wait on processor execution time and turn a slow processor into a customer-facing failure" is an explanation. Pick one decision you actually understand and explain it that clearly.

> **Getting started:** Before you record, answer this question out loud, without notes: why is the order submission asynchronous? If you can answer it clearly in one minute, you have your decision explanation. If you can't, that's the gap to close before you hit record. Practice the Postman run at least twice before recording — a fumbled demo eats your five minutes.

---

### 3. A Written WAF Reflection (1 to 2 pages)

Three required components: two pillars you addressed well with specific evidence, one pillar you did not address with a concrete proposed fix, and one thing that worked differently than you expected.

This is not a summary of what the WAF pillars are. It is a specific, honest evaluation of your specific system. The grader has read the AWS Well-Architected documentation. What they haven't read is your assessment of your own work.

**What "specific evidence" means:** "We addressed the Reliability pillar" is not evidence. "The SQS queue provides reliability because unprocessed messages are retried automatically when the processor Lambda fails, preventing order loss without any additional code on our part" is evidence. Name the resource, name the behavior, name the risk it mitigates.

**What "concrete proposed fix" means:** Naming a gap without proposing a fix is half a finding. "We did not implement authentication" is a gap. "We did not implement authentication; in production we would add an API Gateway Lambda authorizer that validates JWT tokens issued by an identity provider, ensuring only verified callers can submit or read orders" is a finding with a proposed fix.

> **Getting started:** Before you write a word, complete the WAF audit table in the Week 8 lab. Fill in all six pillars. The audit table is not the reflection — it is the raw material. The reflection is what you decide to say about the three most interesting findings in that table. If you try to write the reflection without completing the audit first, you will write generic sentences about pillars instead of specific sentences about your system.

---

## The Three-Week Arc — How It Fits Together

Understanding the sequence makes each week's work easier to scope.

```
Week 8 — Evaluate
  └── In class:  WAF audit table — all six pillars, gap classifications
  └── Homework:  Written reflections W1, W2, W3
                 W3 = your audit-motivated extension choice (bridges to Week 9)

Week 9 — Plan
  └── In class:  Extension design doc — one page, committed before you leave
  └── Homework:  12-factor audit (four factors) + CNCF mapping exercise

Week 10 — Build and Demonstrate
  └── Session 1: Build the extension (you arrive with a design doc)
  └── Session 2: Demo prep — dry run, pulumi destroy test, reflection assembly
  └── Finals:    Record demo video + submit WAF reflection + push final stack
```

Nothing in this sequence is throwaway. The audit findings from Week 8 motivate the extension you design in Week 9. The extension you design in Week 9 is what you build in Week 10. The demo video shows the system working and explains a decision. The WAF reflection draws directly from the audit table you filled in Week 8.

**Week 8 — Evaluate**

The WAF audit is the foundation everything else builds on. You are asking one question about the system you built: where does it hold up and where does it fall short? The audit table you fill in during the in-class session and the written reflections you complete as homework are the outputs. Your W3 answer — the extension most directly motivated by your audit findings — is the bridge to Week 9.

The most important thing Week 8 produces, beyond the written reflections, is a clear answer to: what would I fix first if this were going to production next month? That answer should drive your extension choice.

**Week 9 — Plan**

One session, compressed. The lecture gives you the cloud-native context. The lab time has one goal: you leave with a written extension design doc. Not a vague intention — a one-page description of exactly what you are building in Week 10, what Pulumi resources it requires, and what Postman test will confirm it works.

Students who leave Week 9 without a committed design doc spend the first part of the Week 10 build session deciding instead of building. The design session is Week 9. The build session is Week 10.

**Week 10 — Build and Demonstrate**

Session 1 is the build session. You arrive with a design doc and spend the time implementing. Session 2 is demo prep: a dry run, a clean `pulumi destroy` test, and getting the WAF reflection assembled from the audit work you did in Week 8.

Finals week: record and submit. The recording is low-stakes if the system is working and you have practiced the explanation. It is high-stakes if you are still debugging.

---

## How to Think About the Work

The shift in these three weeks is not about difficulty. It is about ownership. The labs gave you step-by-step instructions and a defined correct answer. The project asks you to evaluate, decide, and justify.

A few things that will help:

**Evaluate your actual system, not an idealized version of it.** The WAF audit is most useful when it is honest. If your processor Lambda swallows errors silently, that is a Reliability gap. Write it down. If your security group is open to all IPs, that is a Security finding. Write it down. Auditing a better version of the system than you actually built produces findings that aren't yours and a reflection that isn't honest.

**Choose an extension you can finish, not one that sounds impressive.** A working filter on `GET /orders` that you fully understand and can explain is a better project outcome than a Lambda authorizer that almost works. Simple and correct beats ambitious and broken.

**The demo is your strongest argument.** A system that runs cleanly and an explanation that is clear and specific will carry the demo even if the reflection is thin. A system that requires manual steps or errors during the Postman run will undermine everything else.

**The reflection is where the thinking shows.** Two paragraphs with specific evidence and a concrete proposed fix are worth more than two pages of general statements about cloud architecture. Write less, mean more.
