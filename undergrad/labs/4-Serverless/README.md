# Lab 4: Serverless API — Lambda and API Gateway

**Course:** CS463 — Cloud Native Platform Engineering (Undergraduate)
**Points:** 100 total
**Due:** See course syllabus

---

## Lab Objectives

By the end of this lab, you will be able to:

- Write and deploy a Lambda function in Python and invoke it manually from the AWS Console
- Wire a Lambda function to an API Gateway HTTP endpoint and call it with `curl`
- Explain the Lambda execution model: cold starts, execution environment lifecycle, memory and timeout settings
- Read Lambda logs from CloudWatch and use them to understand what happened during an invocation
- Deploy a complete serverless stack — Lambda + API Gateway + IAM — using Pulumi
- Articulate the tradeoffs between Lambda and EC2 for a given workload

---

## What You're Building

You are a cloud engineer at **NovaSpark Technologies**. The team needs a lightweight API endpoint up and running this week — no new servers, no SSH, no always-on compute. This is NovaSpark's first serverless service.

The Pulumi stack you build in Part 3 of this lab is **your capstone foundation**. Do not run `pulumi destroy` at the end of this lab. You will extend this same stack in later labs to add persistence and additional routes.

| Part | Guide | What You'll Do | Est. Time |
|------|-------|----------------|-----------|
| **Part 1** | [lab-guide.md — Part 1](lab-guide.md#part-1-your-first-lambda-function) | Create a Lambda in the Console; write the handler; test and observe logs | 30–45 min |
| **Part 2** | [lab-guide.md — Part 2](lab-guide.md#part-2-connect-to-api-gateway) | Add API Gateway; test your live HTTPS endpoint with `curl` | 30 min |
| **Part 3** | [lab-guide.md — Part 3](lab-guide.md#part-3-tear-down-and-redeploy-with-pulumi) | Delete console resources; complete the Pulumi TODOs; redeploy as code | 45–60 min |

> **Start here if this is your first time:** [`SETUP.md`](SETUP.md) — confirm your environment before writing any code.

> 💰 **Cost note:** Lambda and API Gateway are both free tier — there is no per-hour cost to leave this running. You do not need to destroy at the end of this lab. Practice `pulumi destroy` only as the final step of the written exercise W4.

---

## Deliverables Summary

Submit a **single PDF** named `LastName_FirstName_Lab4.pdf` with all screenshots and written responses in deliverable order.

### Technical Deliverables — 75 points

| # | Deliverable | Part | Points |
|---|-------------|------|--------|
| D1 | AWS Console: Lambda test invocation showing a successful JSON response in the "Response" panel | 1 | 10 |
| D2 | AWS CloudWatch: Log stream showing at least one complete invocation — timestamp, START, END, and REPORT lines visible | 1 | 10 |
| D3 | Terminal: `curl https://<api-id>.execute-api.us-east-1.amazonaws.com/status` returning your JSON response | 2 | 10 |
| D4 | Terminal: `pulumi up` output showing Lambda + API Gateway + IAM resources created (all 8+ resources, no errors) | 3 | 15 |
| D5 | Terminal: `curl` on the Pulumi-deployed endpoint confirming the stack is live | 3 | 10 |
| D6 | Terminal: `pulumi up` output after a code change — at minimum the Lambda function resource shows as "updated" | 3 | 10 |
| D7 | Terminal: `pulumi stack output` showing the `api_url` output value | 3 | 10 |

### Written Deliverables — 25 points

| # | Deliverable | Points |
|---|-------------|--------|
| W1 | **Cold starts:** What is a Lambda cold start? Based on the REPORT line in your CloudWatch logs (D2), how long did the first invocation take versus a subsequent one? Name two strategies that reduce cold start frequency or impact. (3–5 sentences) | 10 |
| W2 | **Lambda vs. EC2:** NovaSpark has two new requirements: (a) a status endpoint that gets ~10 requests per day, and (b) a nightly data processing job that takes 25 minutes and is triggered by an S3 upload. For each, would you choose Lambda or EC2, and why? (one paragraph per scenario) | 15 |

---

## Grading Rubric

| Deliverable Type | Full Credit | Partial Credit | No Credit |
|-----------------|-------------|----------------|-----------|
| **Console screenshots (D1, D2)** | All required elements visible in a single screenshot; response or log output is clearly readable | Partial output visible; required lines truncated | Not captured, or clearly from a different run than the rest of the submission |
| **`curl` outputs (D3, D5)** | Full JSON response visible; URL clearly includes the AWS endpoint domain | Response shown but URL cropped or unclear | Not captured |
| **`pulumi up` (D4, D6)** | All resources listed; no errors; update vs. create distinction clear in D6 | Resources shown but errors visible or resource count too low | Stack did not deploy or output not captured |
| **`pulumi stack output` (D7)** | `api_url` value visible and is a valid AWS API Gateway URL | Output visible but URL malformed | Not captured |
| **Written (W1, W2)** | Names specific AWS components; references actual numbers from CloudWatch logs in W1; scenario reasoning is specific in W2 | Correct in general but vague — no reference to observed data or specific tradeoffs | Copied, AI-generated without disclosure, or factually incorrect |

**Point deductions:**
- Written response uses AI without disclosure: −5 pts per response
- D4 shows resources but `pulumi stack output` (D7) URL doesn't match API endpoint: −5 pts

---

## Submission

All deliverables for this lab go in the `4-Serverless/` directory of your **private course GitHub repository**:

```
your-course-repo/
└── 4-Serverless/
    ├── app/
    │   └── handler.py            ← your Lambda handler (from app/)
    ├── __main__.py               ← your completed Pulumi code
    └── LastName_FirstName_Lab4.pdf
```

Push before the deadline. You do not need to include config files, `.pulumi/` state directories, or virtual environment files.

### Submit to Canvas

Submit the URL to your `4-Serverless/` directory as a text entry in the Canvas Lab 4 assignment:

*(Example: `https://github.com/your-org/your-repo/tree/main/4-Serverless`)*

> **Due:** See the course syllabus for the exact deadline. Late day policy applies to this lab — see the syllabus for details.

---

## A Note on the Capstone

This lab is the foundation your capstone project builds on. The `pulumi up` stack you deploy in Part 3 — Lambda + API Gateway — is what you will extend with DynamoDB, additional routes, and IAM permissions in later labs and the final project. Keep it. Treat it like production infrastructure: commit your code, don't manually modify resources through the console after Part 2, and understand every resource in the stack before you add to it.

---

## A Note on AI Use

You may use AI tools to help you understand concepts, look up Pulumi documentation, or debug errors. The written deliverables ask you to reference specific things you observed — your CloudWatch REPORT line numbers, your scenario reasoning, your actual endpoint URL. Generic responses that could have been written without doing the lab will not receive full credit regardless of their origin. Disclose AI use if you use it for written responses; undisclosed use carries a 5-point deduction per response.
