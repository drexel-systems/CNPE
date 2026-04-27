# Lab 4: Serverless Computing — Lambda, API Gateway, and Cold Start Analysis

**Block 3 (in class) + out of class work**
**Due:** See course syllabus

---

## The Scenario

You are a senior cloud engineer at **NovaSpark Technologies**. Janet has given you infrastructure code for the company's first serverless service — a status endpoint the frontend team needs live this week. The code is written. Your job is not to write it: it is to deploy it, understand every decision in it, and produce a written analysis that the team can use to make better architectural choices going forward.

Ben wants to know: *"Is there a latency surprise users are going to hit?"*

Linda wants to know: *"What exactly can this function do? Walk me through the IAM."*

Janet wants to know: *"What are we going to run into when we add DynamoDB next week?"*

Your deliverables answer all three questions.

---

## Before You Deploy: Read the Code First

This is not optional. Open `__main__.py` and `app/handler.py` and read them fully before running any commands.

For each resource in `__main__.py`, be able to answer:
- What does this resource create?
- Why is it necessary? (What breaks if it's missing?)
- What design decision is implicit in the parameter values chosen?

The comments in the template are intentional — they explain the choices. Read them as a practitioner explaining a decision, not as tutorial boilerplate.

**Specific things to annotate before you run `pulumi up`:**

1. The IAM role's `assume_role_policy` — what does it allow and who is the principal?
2. Why `payload_format_version: "2.0"` on the integration must match the handler's response format
3. What `source_arn=http_api.execution_arn.apply(lambda arn: f"{arn}/*/*")` scopes the Lambda permission to
4. Why `auto_deploy=True` on the stage is convenient but might not be appropriate in production

---

## Step 1: Deploy the Stack

Confirm your environment is ready: [`SETUP.md`](SETUP.md)

Copy `__main__.py` and the `app/` directory into your `4-Serverless/` project directory. Then:

```bash
export PULUMI_CONFIG_PASSPHRASE=""
pulumi up
```

Review the preview carefully before confirming. You should see 9 resources queued for creation:
- 1 IAM role
- 1 IAM role policy attachment
- 1 Lambda function
- 1 API Gateway HTTP API
- 1 API Gateway integration
- 1 API Gateway route
- 1 API Gateway stage
- 1 Lambda permission
- 1 stack output registration

Confirm and let the deployment complete.

**D1 deliverable:** Take a screenshot of the completed `pulumi up` output showing all resources created with no errors.

> **Stop here before running curl.** Your function has been deployed but never invoked — the next call you make will be a guaranteed cold start. Proceed directly to Step 2 to capture it now, before the execution environment has any chance to warm up.

---

## Step 2: Cold Start Analysis

The cold start is one of the most discussed limitations of serverless compute. Lambda keeps execution environments warm for some period after each invocation, but when a new environment is needed — after a long idle period, when concurrency scales up, or on first deployment — the function incurs an initialization penalty. The Hellerstein et al. paper classifies this as a fundamental limitation of the FaaS model, not just an AWS implementation detail.

You are going to measure it — and you don't need to wait for anything. The guaranteed cold start is right now.

---

### Step 2.1 — Capture the Cold Start

Your function has been deployed but never invoked. The first invocation after deployment always creates a fresh execution environment — there is nothing cached to reuse. No waiting required.

Invoke the function now, then immediately open CloudWatch — do not run curl a second time first:

```bash
curl $(pulumi stack output api_url)
```

**D2 deliverable:** Screenshot of the `curl` command and JSON response confirming the endpoint is live.

Navigate to: **Lambda → novaSpark-status-fn → Monitor → View CloudWatch Logs**

Open the most recent log stream. Look for the REPORT line:

```
REPORT RequestId: abc123  Duration: 4.21 ms  Billed Duration: 5 ms
       Memory Size: 128 MB  Max Memory Used: 38 MB  Init Duration: 284.31 ms
```

The `Init Duration` is the cold start overhead — the time Lambda spent initializing the execution environment before your code ran. It appears only when the environment was freshly created.

If you don't see `Init Duration`, something invoked the function before you got here — possibly a health check or a test event during setup. In that case, wait 20 minutes for the environment to expire, then invoke again.

---

### Step 2.2 — Capture a Warm Invocation

Immediately invoke the function a second time:

```bash
curl $(pulumi stack output api_url)
```

Open CloudWatch again. The new REPORT line should NOT have an `Init Duration` — just `Duration` and `Billed Duration`. The `Duration` should be significantly smaller.

**D3 deliverable:** Screenshots of both REPORT lines (cold and warm). Label which is which. The cold start report must include `Init Duration`.

---

### Step 2.3 — Write the Analysis (D4)

Using your actual measured values, write your cold start performance analysis. Your analysis should address:

1. **The measured gap:** What was your Init Duration? What was your warm Duration? What is the ratio? What does this mean for NovaSpark's users if they're the first to hit the endpoint after it's gone cold?

2. **Two mitigation approaches:** Pick two from the list below and explain the mechanism and the cost tradeoff for each:
   - Provisioned Concurrency (keeps N environments pre-initialized)
   - Scheduled "keep-warm" pings (invoke the function on a schedule)
   - Increasing memory allocation (larger runtime, faster init)
   - Moving initialization code outside the handler (module-level imports)

3. **NovaSpark's specific situation:** The current traffic is low and variable. Given that, which mitigation makes the most sense for now? What threshold of traffic would change your recommendation?

Maximum 1 page.

---

## Step 3: Execution Role Analysis

Run the following to get the LabRole ARN Pulumi used:

```bash
pulumi stack output lambda_role_arn
```

Open the IAM console → **Roles** → search for `LabRole`. Click into it and review the **Permissions** tab.

You'll notice immediately that LabRole has significantly more permissions than a Lambda function writing a status response actually needs. This is an AWS Academy constraint: the Learner Lab sandbox restricts `iam:CreateRole`, so all labs use the pre-existing `LabRole` rather than creating a tightly scoped execution role. The template's comments show what a properly scoped role would look like.

**D5 deliverable:** 3–5 sentences answering:

1. **What does LabRole permit that this function actually uses?** Identify which permissions are relevant to a Lambda function that writes logs and returns JSON. (Think: CloudWatch Logs actions.)
2. **What does LabRole permit that this function does NOT need right now?** Name at least two AWS service categories visible in the permissions list that are entirely irrelevant to the current function.
3. **What would a least-privilege role look like?** Name the specific IAM actions a properly scoped execution role would grant for this function — just enough for CloudWatch Logs access. Then extend: when you add a DynamoDB write in the next lab, what additional actions would you add, and would you scope them to `*` or to a specific table ARN?

> The gap between LabRole and a least-privilege role is not an abstract concern. Every excess permission is part of the blast radius if the function is ever compromised. Linda's question at the start of this lab — "Walk me through the IAM" — is exactly this analysis. A Lambda function that can read and write every DynamoDB table in the account is a much bigger problem than one scoped to a single table.

---

## Step 4: Prediction Exercise

The next lab adds DynamoDB integration to this same function. You will connect the Lambda to a DynamoDB table and implement a `POST /events` route that writes to it.

Before you get there, make a specific, testable prediction.

**D6 deliverable:** 3–5 sentences answering:

1. Hellerstein et al. identify several formal limitations of serverless — which specific limitation (named and defined from the paper) is most relevant to a Lambda function that makes synchronous DynamoDB writes?
2. Based on that limitation, what latency outcome do you predict? Give a number or range.
3. What would you observe in CloudWatch that would confirm or refute your prediction?

You will return to this prediction in the Lab 5 deliverables and evaluate whether it held.

> **Note:** This is not asking you to be right — it is asking you to think carefully before observing. A specific prediction you later discover was wrong is more valuable than a vague hedge. The evaluation of whether you were right (and why) is where the learning happens.

---

## Context Paragraph

See [`context-paragraph-prompt.md`](context-paragraph-prompt.md) for the full prompt, examples, and grading scale.

Include your context paragraph in your submission PDF after D6.

---

## Submission Checklist

Before submitting, confirm you have all of the following in your PDF in this order:

- [ ] D1 — `pulumi up` output (all resources, no errors)
- [ ] D2 — `curl` response from Pulumi-deployed endpoint
- [ ] D3 — Cold start REPORT and warm REPORT lines (labeled)
- [ ] D4 — Cold start performance analysis (1 page max, with measured values)
- [ ] D5 — Execution role analysis (3–5 sentences)
- [ ] D6 — Prediction exercise (3–5 sentences, specific claim)
- [ ] CP — Context paragraph (150–250 words)

Push `__main__.py` and `app/handler.py` to your course repo. Leave the stack running — you will extend it in Lab 5.
