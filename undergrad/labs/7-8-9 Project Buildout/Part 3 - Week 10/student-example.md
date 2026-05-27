# Final Project — Worked Examples
## CS 463 Week 10: The WAF Reflection and the Demo Decision Explanation

Use this document before Session 2 and before you record your final video. Part 1 explains what the WAF reflection is — and what it is not. Part 2 shows a complete worked reflection with commentary. Part 3 shows a worked architectural decision explanation at demo quality. Part 4 shows the weak versions of both so you can see the difference.

---

## Part 1 — What the WAF Reflection Is (and What It Is Not)

The WAF reflection is not a summary of the six pillars. The grader has read the AWS Well-Architected documentation. What they have not read is your honest assessment of your specific system.

The Week 8 audit table you filled in is the raw material. The reflection is what you decide to say about the three most interesting findings in that table. You are not writing about the WAF — you are writing about the NovaSpark Order API you actually built, evaluated against the WAF.

**The three required components:**

| Component | What it requires |
|-----------|-----------------|
| Two pillars addressed well | A specific resource or configuration, the behavior it enables, and the risk it mitigates — in 2–3 sentences each |
| One pillar not addressed | The gap named specifically, a concrete proposed fix with enough detail that it could be implemented, and (if relevant) what your extension changed or didn't change |
| One genuine surprise | Something that worked differently than you expected during the build — not a lesson-learned platitude, a specific incident |

**The difference between a reflection and a summary:**

A summary describes the pillars in general. A reflection names a resource, a behavior, and a consequence — and does so for your system, not for a generic serverless API.

| Summary (not what this is) | Reflection (what this is) |
|---------------------------|--------------------------|
| "We addressed Reliability by thinking about what happens when components fail." | "The processor Lambda re-raises exceptions on DynamoDB write failures rather than swallowing them. This means SQS retries the message automatically — visible in `processor/handler.py` at the `put_item` call — so a transient DynamoDB failure does not permanently lose an order." |
| "We did not address Security fully." | "The API accepts `customer_id` as a caller-supplied parameter in `POST /orders`. In production, `customer_id` should be extracted from a verified JWT token issued by an identity provider — the caller should not be trusted to identify themselves. The fix is an API Gateway Lambda authorizer that validates the token before the request reaches the orders handler." |
| "I was surprised how hard IAM was." | "The processor Lambda had `GetItem` but not `PutItem` in its execution role. The error appeared in CloudWatch as `AccessDeniedException` with no indication of which permission was missing — identifying it required comparing the policy document in the console against the DynamoDB SDK call in the handler." |

The specificity is not style. It is what demonstrates that you built and evaluated your own system rather than writing generically about cloud architecture.

---

## Part 2 — Worked WAF Reflection

The following is a complete 1–2 page WAF reflection at full-credit quality. Commentary in *italics* after each component explains what makes it effective.

---

### NovaSpark Order API — WAF Reflection

---

**Two pillars I addressed well**

**Reliability — SQS decoupling and automatic retry**

The most significant reliability decision in the system is the SQS queue between the submission Lambda and the processor Lambda. When the processor fails — because of a DynamoDB write error, a cold start, or any other transient condition — SQS retains the message and retries delivery automatically. The customer has already received their 202 Accepted response, so processor failure is invisible to them. This is visible in the async flow: `POST /orders → submission Lambda → SQS → processor Lambda → DynamoDB`. The processor re-raises exceptions rather than catching them silently, which ensures SQS treats a failed execution as a failed delivery and retries it — this is the specific behavior in `processor/handler.py` at the `put_item` call. Without the re-raise, a failed write would be silently acknowledged and the order would be lost permanently.

*This paragraph names the specific resource (SQS queue), the specific behavior it enables (automatic retry), the specific condition it handles (processor failure), and the specific code location where the behavior is enforced (`processor/handler.py` at `put_item`). It also names what would break without it — silent loss. Every sentence adds something the reader could not have known without reading this system's code.*

**Operational Excellence — Infrastructure as code with Pulumi**

Every resource in the system — the VPC, the Lambda functions, the API Gateway, the SQS queue, the DynamoDB table, the IAM execution roles — is defined in `__main__.py`. There are no manually created resources. This means the full stack can be destroyed and recreated from a blank AWS account in under two minutes with `pulumi up`. It also means every infrastructure change is reviewed as code before it applies: a security group rule that was accidentally opened too broadly, a Lambda memory limit that was set too high, or a DynamoDB billing mode that should have been on-demand — all of these are visible in the code and in the git history. In production, this eliminates the "configuration drift" problem where what is deployed diverges from what is documented.

*The second paragraph does the same thing for a different pillar: names specific resources, names specific behaviors, and names the specific risk that is mitigated. The mention of `__main__.py` anchors it in the actual codebase. The sentence about configuration drift names a real operational problem — which demonstrates that the student understands why the practice matters, not just that the practice was required.*

---

**One pillar I did not address**

**Security — No authentication on any route**

The API is a publicly addressable HTTPS endpoint. Any caller with the URL can submit an order, read any order by ID, or list all orders in the database. There is no mechanism to verify who is making a request or whether they are authorized to make it.

The customer scoping extension I implemented in Lab 9 partially addresses this by storing `customer_id` in DynamoDB and filtering `GET /orders` by customer when a `customer_id` query parameter is provided. However, `customer_id` is still a caller-supplied parameter — there is no verification that the caller is who they claim to be. In production, `customer_id` should be extracted from a signed JWT token issued by an identity provider, not accepted as a plain string from the request body.

The concrete fix: add an API Gateway Lambda authorizer. The authorizer Lambda would validate the JWT token in the `Authorization` header before the request reaches the orders handler — returning an IAM `Allow` policy document on success or an IAM `Deny` on failure. This would require one new Lambda function (the authorizer), one Pulumi resource (`aws.apigateway.Authorizer`), and an update to the `__main__.py` API Gateway route configuration to attach the authorizer. The `customer_id` value would then be extracted from the validated token claims inside the handler, not accepted from the caller.

*This component does three things that a weak entry does not: it names the gap specifically (any caller can submit orders, read any order, list all orders), it names what the extension did and did not close (customer scoping without authentication), and it proposes a fix concrete enough to implement (one new Lambda, one Pulumi resource, the specific resource type to use). The last sentence explains where `customer_id` would come from in the corrected version — which shows the student understands the architecture, not just the API surface.*

---

**One thing that worked differently than I expected**

I expected the SQS → Lambda trigger to behave synchronously in testing — meaning I thought a message sent to the queue would be processed within a second or two and show up in DynamoDB immediately. In practice, the first few messages I sent during Lab 5 were not processed for 20–30 seconds. I spent time debugging the processor Lambda before realizing the polling interval was the cause: Lambda polls SQS at intervals, and there is a delay between when a message arrives and when the Lambda receives it, especially on the first invocation after an idle period. Understanding that the 202 response and the final DynamoDB write are not just conceptually decoupled — they are separated by real, observable time — changed how I thought about the asynchronous model.

*This paragraph names a specific incident (first messages not appearing in DynamoDB for 20–30 seconds during Lab 5), the incorrect assumption (synchronous timing), the root cause (SQS polling interval), and the shift in understanding it produced. It is not a lesson-learned platitude like "I learned a lot about how AWS works." It is a specific thing that happened during the build, written honestly.*

---

*End of WAF reflection.*

---

## Part 3 — Worked Architectural Decision Explanation (Demo Quality)

The demo requires you to explain one architectural decision in plain language. You have approximately 45 seconds. This is not a description of a component — it is an explanation of a choice and why you made it.

The two strongest decisions to explain are the ones with the clearest trade-off: why async, and why this partition key. Below are both at demo quality.

---

### Decision 1 — Why is order submission asynchronous?

**Weak version (description, not explanation):**
> "We used SQS because it decouples the submission Lambda from the processor Lambda."

**Strong version (explanation with trade-off):**
> "When a customer submits an order, the submission Lambda writes the message to SQS and immediately returns a 202 Accepted. The processor Lambda picks it up asynchronously. The reason we designed it this way is that a synchronous call would make the customer wait for the processor to finish — and if the processor is slow, has a cold start, or hits a DynamoDB timeout, that failure becomes visible to the customer as a slow or broken checkout experience. By putting SQS in between, processor failures are invisible to the customer. The order is safe in the queue, it will be retried automatically, and the customer got their confirmation in milliseconds."

*What makes it strong: names the specific behavior (SQS receives the message, Lambda returns 202 immediately), names the specific failure mode a synchronous design would expose (processor latency → customer-visible failure), and names the specific remedy the async design provides (retry without customer impact). It answers the unstated follow-up question — "why does that matter?" — without being asked.*

---

### Decision 2 — Why `order_id` as the DynamoDB partition key?

**Weak version:**
> "We used `order_id` as the partition key because each order is unique."

**Strong version:**
> "DynamoDB requires a partition key, and the most important access pattern in this system is 'look up a specific order by ID' — which is what GET /orders/{id} does. Using `order_id` as the partition key makes that lookup O(1) regardless of how many orders are in the table. The trade-off is that scanning by customer or by status — which `GET /orders` currently does as a full table scan — gets expensive at high volume. In a production system with millions of orders, you would add a Global Secondary Index on `customer_id` to make customer-scoped queries efficient. We documented this as a known trade-off in the WAF audit."

*What makes it strong: names the access pattern the key was chosen to serve (GET /orders/{id}), names the performance implication (O(1) lookup), names the trade-off (table scans for non-key attributes), and names the production fix (GSI on customer_id). It shows the student made a deliberate choice and knows what it costs — which is exactly what "explaining an architectural decision" means.*

---

## Part 4 — What Weak Versions Look Like

### Weak WAF reflection

> "I addressed the Reliability pillar by using SQS to make the system more resilient. SQS provides message durability and retry functionality which is important for production systems. I also addressed Operational Excellence through infrastructure as code with Pulumi which is a best practice.
>
> I did not fully address Security. In a production system you would want to add authentication and authorization to the API endpoints.
>
> One thing that surprised me was how well everything worked together once it was deployed."

**What is wrong with this:**

The Reliability paragraph says "SQS provides retry functionality" — which is true of SQS in general, but says nothing about *this* system. It does not name the specific Lambda behavior (re-raise exceptions) that makes retry actually work. A system where the processor swallows exceptions would technically also "use SQS" — but would lose orders silently. The difference is in the handler code, which this paragraph never mentions.

The Security paragraph names the gap but the proposed fix is "add authentication and authorization" — which tells the reader nothing actionable. There is no resource name, no Pulumi change, no description of what would change in the handler.

The surprise is a generic positive statement that could appear in any course reflection ever written. It names nothing specific.

### Weak demo decision explanation

> "We made a lot of good architectural decisions. One of them was using SQS for async processing, which makes the system more scalable and reliable. Lambda also auto-scales so we don't have to worry about server capacity."

**What is wrong with this:**

"A lot of good architectural decisions" followed by a vague general claim is not an explanation — it is promotional language. "More scalable and reliable" without naming what specific failure it prevents or what specific behavior it enables is meaningless. Lambda auto-scaling is a feature description, not a decision explanation — the decision would be "why Lambda instead of EC2" or "why async instead of synchronous."

The grader cannot tell from this explanation whether the student understands why the system was built the way it was, or just read the lab guide.

---

## Before You Record — One Test

Before you hit record on the final demo video, answer this question out loud without looking at any notes:

> "Why is the order submission asynchronous — and what specifically would happen to a customer's experience if it were synchronous?"

If you can answer it clearly in under 60 seconds, you have your decision explanation. If you cannot, that is the gap to close before recording. Practicing the Postman run and the architecture walkthrough matters too — but this is the question where students most often get through the demo without actually answering it.
