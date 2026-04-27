# Lab 4: Serverless API — Lambda and API Gateway

**Estimated Time:** 2–2.5 hours total across Parts 1–3
**Due:** See course syllabus

---

## The Scenario

It's been a long Tuesday at NovaSpark. You've just gotten back to your desk when Ben flags you down in Slack.

> **Ben:** "Quick thing — Janet wants a status endpoint for the frontend team by end of week. Something simple: hit a URL, get back JSON saying the system is up. No new EC2. Linda will lose her mind if we spin up another server for this."

> **You:** "How much traffic?"

> **Ben:** "No idea. Could be ten requests a day, could be ten thousand. We don't know yet."

> **Janet [joining the thread]:** "It needs to be in version control and deployable by the engineering team. Not clicking around in consoles."

You know exactly what to do. Lambda is a function that runs when you call it — no server to provision, no SSH, no always-on compute. It costs essentially nothing at low volume and scales automatically if demand picks up. You'll wire it to API Gateway for the HTTPS front door.

This endpoint is the beginning of something bigger. By the end of the course, this serverless stack will be NovaSpark's Status Event Service — a production-quality API with persistent storage, multiple routes, and a clean IaC deployment. For now: get the first endpoint live.

---

## Before You Begin

Confirm your setup is ready: [`SETUP.md`](SETUP.md)

Have the `app/` directory and `__main__.py` in your `4-Serverless/` working directory before starting Part 3.

---

## Part 1: Your First Lambda Function

**What you're doing:** Create a Lambda function in the AWS Console, write a handler that returns JSON, invoke it, and find the logs.

**Why the console first?** You'll deploy everything with Pulumi in Part 3. Starting in the console lets you see exactly what a Lambda function is before you define it in code. When you write the Pulumi TODOs later, you'll recognize every property because you configured it by hand first.

---

### Step 1.1 — Open Lambda

1. Sign into the AWS Console and navigate to **Lambda**
2. Make sure your region is **us-east-1** (top-right corner)
3. Click **Create function**

---

### Step 1.2 — Configure the Function

On the Create function page:

- **Author from scratch** (default)
- **Function name:** `novaSpark-status-console` (you'll delete this before Part 3)
- **Runtime:** Python 3.12
- **Architecture:** x86_64
- **Permissions:** Expand "Change default execution role"
  - Select **Create a new role with basic Lambda permissions**
  - This creates an IAM role that lets your function write to CloudWatch Logs. You'll see this role explicitly in Pulumi's `__main__.py`.

Click **Create function**.

---

### Step 1.3 — Write the Handler

AWS puts you in the inline code editor. Replace the default code with this:

```python
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")
    logger.info(f"Function: {context.function_name}")
    logger.info(f"Memory: {context.memory_limit_in_mb} MB")
    logger.info(f"Time remaining: {context.get_remaining_time_in_millis()} ms")

    environment = os.environ.get("ENVIRONMENT", "not-set")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "service": "NovaSpark Status API",
            "status": "operational",
            "environment": environment,
            "message": "All systems go."
        })
    }
```

Click **Deploy** to save the code.

> **Note the handler signature:** `def lambda_handler(event, context)`. Lambda always calls this exact function when invoked. The `event` parameter contains whatever triggered the function (a test event, an API Gateway request, an S3 notification). The `context` parameter contains runtime metadata — function name, memory limit, how much time is left in the execution window.

> **Cold start setup:** The first time you invoke a Lambda function, AWS has to prepare an execution environment from scratch — download your code, initialize the runtime, run any module-level setup. This initialization overhead is called a **cold start**, and it only shows up in CloudWatch logs as `Init Duration`. Since you haven't invoked this function yet, your very first test in Step 1.5 will be a cold start. Don't invoke the function from the console before clicking Test in Step 1.5, or you'll miss it.

---

### Step 1.4 — Add an Environment Variable

In the **Configuration** tab → **Environment variables** → **Edit**:

- Add a variable: Key = `ENVIRONMENT`, Value = `dev`

Save. Your function now reads this value via `os.environ.get("ENVIRONMENT")`. This is the 12-factor app pattern for configuration: config lives in the environment, not in the code.

---

### Step 1.5 — Invoke from the Console

Back on the **Code** tab:

1. Click **Test** (top right) → **Create new test event**
2. Event name: `test-invoke`
3. Leave the default JSON body as-is (it will show up in your logs)
4. Save, then click **Test** again to invoke

You should see a green **"Execution result: succeeded"** panel showing:

```json
{
  "statusCode": 200,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"service\": \"NovaSpark Status API\", ...}"
}
```

**Take screenshot D1 now** — the full response panel visible.

> **This was a cold start.** Lambda had to prepare a fresh execution environment before running your code. The total time includes both your code's execution time and that setup overhead. Run the test a second time immediately — it should return noticeably faster because Lambda reuses the existing environment. The difference between those two invocations is what you'll quantify in W1 using the CloudWatch logs in Step 1.6.

---

### Step 1.6 — Find the Logs

1. Click the **Monitor** tab → **View CloudWatch Logs**
2. Click into the most recent log stream
3. You should see your log lines: the Event JSON, the function name, memory, and remaining time

**Take screenshot D2 now** — the log stream showing your invocations. You need **both** REPORT lines visible: the first invocation (with `Init Duration`) and the second invocation (without it). If you only ran the test once, go back and run it a second time, then refresh the log stream.

> **Reading the REPORT lines.** Your first invocation's REPORT will look like this:
> ```
> REPORT RequestId: abc123  Duration: 847.23 ms  Billed Duration: 848 ms
>        Memory Size: 128 MB  Max Memory Used: 35 MB  Init Duration: 312.45 ms
> ```
> Your second invocation's REPORT will look like this (no Init Duration):
> ```
> REPORT RequestId: def456  Duration: 4.11 ms  Billed Duration: 5 ms
>        Memory Size: 128 MB  Max Memory Used: 35 MB
> ```
> Write down both Duration values and the Init Duration — you'll need the actual numbers for W1. A response that says "cold starts are slow" gets partial credit. A response that says "my Init Duration was 312ms and my warm Duration was 4ms" demonstrates you actually read your logs.

---

## Part 2: Connect to API Gateway

**What you're doing:** Put API Gateway in front of your Lambda so it's accessible via a real HTTPS URL. Test it with `curl`.

---

### Step 2.1 — Create an HTTP API

1. Navigate to **API Gateway** in the console
2. Click **Create API**
3. Choose **HTTP API** → **Build**
   - Not "REST API" — HTTP API (v2) is simpler and cheaper
4. **API name:** `novaSpark-status-console`
5. Click **Next** through the remaining screens without configuring routes yet
6. Click **Create**

---

### Step 2.2 — Add a Route and Integration

Once the API is created:

1. In the left panel, click **Routes** → **Create**
2. **Method:** GET, **Path:** `/status` → **Create**
3. Click on the new `GET /status` route
4. Click **Attach integration** → **Create and attach an integration**
5. **Integration type:** Lambda function
6. **Lambda function:** select `novaSpark-status-console`
7. Create the integration

API Gateway will prompt you to add a resource-based policy (permission) to your Lambda. Click **OK** — this is the same `lambda:InvokeFunction` permission you'll see in Pulumi's `aws.lambda_.Permission` resource.

---

### Step 2.3 — Get the Endpoint and Test

1. In the left panel, click **API: novaSpark-status-console**
2. Find the **Invoke URL** — it looks like `https://abc123xyz.execute-api.us-east-1.amazonaws.com`
3. Open your terminal and run:

```bash
curl https://<your-api-id>.execute-api.us-east-1.amazonaws.com/status
```

You should get back your JSON response.

**Take screenshot D3 now** — the full `curl` command and response in your terminal.

> **Why HTTP API and not REST API?** HTTP APIs (v2) have lower latency, lower cost (~$1/million requests vs. ~$3.50), and a simpler routing model. REST APIs (v1) offer more features — request/response transformation, usage plans, API keys, and a more mature integration model. For NovaSpark's status endpoint, HTTP API is the right call. For a public API requiring API key management, you'd revisit.

---

### Step 2.4 — Clean Up Console Resources

Before moving to Part 3, delete both console resources:

1. **Lambda → Functions:** delete `novaSpark-status-console`
2. **API Gateway → APIs:** delete `novaSpark-status-console`

You're not deleting the IAM role — it will be cleaned up automatically when the function is deleted.

Why delete before Pulumi? If you leave these running, Pulumi will create duplicates with slightly different names. Clean slate first.

---

## Part 3: Tear Down and Redeploy with Pulumi

**What you're doing:** Redeploy the same Lambda + API Gateway using Pulumi. Everything you built by hand in Parts 1 and 2, you'll now define as code. Then make a change — and deploy the update with a single command.

**This is the important part.** The stack you create here is your capstone foundation. Do not destroy it at the end of this lab.

---

### Step 3.1 — Review `__main__.py`

Open `__main__.py` in your `4-Serverless/` directory. Read through the full file before changing anything. The IAM role and policy attachment at the top are complete. You have 8 TODOs to fill in.

Each TODO has a comment block explaining:
- What AWS resource you're creating
- The exact Pulumi class to use
- The required arguments with types and values

> **Strategy:** Don't start with TODO 1 and try to write all 8 in one pass. Deploy after each TODO to validate your progress. If you complete TODOs 1 and 2 and run `pulumi up`, Pulumi will create the IAM resources and the Lambda — you can verify the function exists in the console before wiring up API Gateway.

---

### Step 3.2 — Complete TODO 1 and 2 (Lambda)

Fill in TODOs 1 and 2 to create the `lambda_archive` and the Lambda function.

Run `pulumi up` to verify:

```bash
export PULUMI_CONFIG_PASSPHRASE=""
pulumi up
```

You should see the IAM role, policy attachment, and Lambda function created. Check the Lambda in the console — it should exist with your `handler.lambda_handler` handler and the `ENVIRONMENT=dev` variable.

---

### Step 3.3 — Complete TODOs 3–7 (API Gateway)

Fill in TODOs 3 through 7 to create the HTTP API, integration, route, stage, and Lambda permission.

Run `pulumi up` again. You should now have 9 resources total.

---

### Step 3.4 — Complete TODO 8 (Output)

Uncomment and complete the `pulumi.export("api_url", ...)` line.

Run `pulumi up` one more time to register the output. After it completes:

```bash
pulumi stack output api_url
```

Copy that URL and test it:

```bash
curl $(pulumi stack output api_url)
```

**Take screenshot D4** — `pulumi up` output showing all resources created, no errors.

**Take screenshot D5** — `curl` output confirming the Pulumi-deployed endpoint is live.

**Take screenshot D7** — `pulumi stack output api_url` output.

---

### Step 3.5 — Make a Code Change and Redeploy

Open `app/handler.py`. Change the `"message"` field in the response:

```python
"message": "All systems go. [v2]"
```

Save the file and run `pulumi up` again. Pulumi will detect that the Lambda function's code changed and update it in place.

**Take screenshot D6** — `pulumi up` output after the change, showing the Lambda function resource as "updated."

Verify the change is live:

```bash
curl $(pulumi stack output api_url)
```

You should see the updated message in the response.

---

### Step 3.6 — Understand What You Built

Before moving on to the written deliverables, look at the AWS Console for each resource Pulumi created:

- **Lambda → novaSpark-status-fn:** Check the IAM execution role attached to it. What policies does it have?
- **API Gateway → novaSpark-status-api:** Click **Integrations** — you should see your Lambda integration with `payload_format_version: 2.0`
- **IAM → Roles → LabRole:** This is the role your Lambda is using. It has far more permissions than a status endpoint needs — that's an AWS Academy sandbox constraint. The `__main__.py` comments show what a tightly scoped role would look like in a real AWS account.

> **The least-privilege principle:** In production, a Lambda function's execution role should grant only the specific actions it actually calls. For a function that writes logs and returns JSON, that's three CloudWatch Logs actions (`CreateLogGroup`, `CreateLogStream`, `PutLogEvents`) and nothing else. When you add DynamoDB in the capstone, you'd add `dynamodb:PutItem` and `dynamodb:GetItem` scoped to the specific table ARN — not to `*`. LabRole skips this scoping because the Learner Lab sandbox restricts creating new roles. Keep this tradeoff in mind for W2.

---

## Written Deliverables

Complete W1 and W2 and include them in your PDF after D7.

---

### W1 — Cold Starts (10 pts)

Answer the following in 3–5 sentences, using the actual numbers from your D2 screenshot:

What is a Lambda cold start and when does it happen? Using the two REPORT lines from D2, what was the `Init Duration` on your first invocation and the `Duration` on your second (warm) invocation? What is the ratio between them, and what would that gap mean for a user hitting this endpoint as the first request of the day? Name two strategies that reduce cold start frequency or impact.

> **Your actual numbers are required.** Partial credit for a correct explanation without measured values. Full credit requires citing the specific `Init Duration` and warm `Duration` from your CloudWatch logs.

---

### W2 — Lambda vs. EC2 (15 pts)

Write one paragraph for each scenario:

**Scenario A:** NovaSpark's status endpoint currently gets roughly 10 requests per day on weekdays and none on weekends.

**Scenario B:** The data team wants to run a 25-minute ETL job every night at 2am, triggered when a new file lands in S3.

For each scenario: would you choose Lambda or EC2 (or App Runner), and why? Consider cost, execution model, and operational complexity. You don't need to recommend the same answer for both — they're different problems.

---

## Deliverables Checklist

Before submitting, confirm you have all of the following in your PDF:

- [ ] D1 — Console test invocation showing JSON response
- [ ] D2 — CloudWatch log stream with REPORT line
- [ ] D3 — `curl` against the API Gateway console endpoint
- [ ] D4 — `pulumi up` output (all resources, no errors)
- [ ] D5 — `curl` against the Pulumi-deployed endpoint
- [ ] D6 — `pulumi up` after code change (Lambda shows "updated")
- [ ] D7 — `pulumi stack output api_url`
- [ ] W1 — Cold start explanation with real numbers from your logs
- [ ] W2 — Lambda vs. EC2 for both scenarios

Commit your `__main__.py` and `app/handler.py` to your course repo. Do not run `pulumi destroy` — this stack is your capstone foundation.
