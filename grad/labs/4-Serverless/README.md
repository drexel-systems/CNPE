# Lab 4: Serverless Computing — Lambda, API Gateway, and Cold Start Analysis

**Course:** CS545 — Cloud Native Platform Engineering (Graduate)
**Points:** 100 total (75 technical + 25 context paragraph)
**Due:** See course syllabus

---

## Lab Objectives

By the end of this lab, you will be able to:

- Deploy a complete Lambda + API Gateway stack from a provided Pulumi template
- Read and explain every resource in the Pulumi code, including the IAM execution role scoping
- Measure cold start latency versus warm invocation latency and analyze the performance difference
- Evaluate the execution role's permissions against the principle of least privilege
- Explain where the template's design decisions are conservative and where you would change them for production
- Connect the Hellerstein et al. paper's critique of serverless to what you observe in the running system

---

## What You're Doing

You are a senior cloud engineer at **NovaSpark Technologies**. The infrastructure code for the Status API is already written. Your job is to deploy it, understand every decision in it, and produce a written performance and design analysis.

The analytical work is the point of this lab. The deployment is the prerequisite.

> **Start here:** [`SETUP.md`](SETUP.md) — confirm Pulumi and AWS credentials are working before reading the code.

> 💰 **Cost note:** Lambda and API Gateway are free tier. Leave the stack running — you will extend it in the next lab (DynamoDB integration). Do not run `pulumi destroy` at the end of this lab.

---

## Deliverables Summary

Submit a **single PDF** named `LastName_FirstName_Lab4.pdf`.

### Technical and Analytical Deliverables — 75 points

| # | Deliverable | Points |
|---|-------------|--------|
| D1 | Terminal: `pulumi up` output — all resources created, 0 errors | 10 |
| D2 | Terminal: `curl $(pulumi stack output api_url)` returning the JSON response | 5 |
| D3 | AWS CloudWatch: Cold start log showing the REPORT line with `Init Duration`. Capture the **first invocation** of the deployed function (invoke once, wait 15+ minutes, invoke again to confirm warm). Include both REPORT lines side by side or as adjacent screenshots | 15 |
| D4 | Written: **Cold start performance analysis** — using actual numbers from D3: what was the Init Duration, what was the warm Duration, what is the ratio? What does this mean for NovaSpark's user-facing latency? What are two architectural approaches to mitigate this, and what is the cost tradeoff of each? (1 page max) | 20 |
| D5 | Written: **Execution role analysis** — review the IAM role in the template. What does it permit? What does it explicitly not permit? Is this scope appropriate for the current function, and what would need to change if NovaSpark added a DynamoDB write to this function? Name the specific policy ARN or inline policy you would add. (3–5 sentences) | 15 |
| D6 | Written: **Prediction exercise** — DynamoDB integration is next week. Based on the Hellerstein et al. paper's discussion of I/O bottlenecks and the "slow storage" limitation of serverless, predict: (a) which specific limitation you expect to observe when Lambda writes to DynamoDB, and (b) what latency outcome you expect. You will revisit this prediction in Lab 5. (3–5 sentences) | 10 |

### Context Paragraph — 25 points

| # | Deliverable | Points |
|---|-------------|--------|
| CP | Context paragraph — see [`context-paragraph-prompt.md`](context-paragraph-prompt.md) for the full prompt and grading scale. Include after D6 in your PDF. | 25 |

---

## Grading Rubric

| Deliverable Type | Full Credit | Partial Credit | No Credit |
|-----------------|-------------|----------------|-----------|
| **`pulumi up` (D1)** | All resources created; output visible; no errors | Resources shown but minor errors present | Stack did not deploy |
| **`curl` (D2)** | Full response visible; API Gateway URL in the command | Response shown but URL unclear | Not captured |
| **CloudWatch (D3)** | Both cold and warm REPORT lines present; `Init Duration` clearly visible on cold start; student indicates which is which | One REPORT line captured | Not captured or Init Duration not present |
| **Cold start analysis (D4)** | Uses actual measured values; distinguishes Init Duration from execution Duration; both mitigation strategies named with cost tradeoff explained | Values referenced but analysis stays general; mitigations named without tradeoff | No numbers; generic serverless description |
| **Execution role (D5)** | Specific policy ARN named; clear statement of what current role cannot do; specific policy or inline policy for DynamoDB named correctly | Role permissions described in general terms; DynamoDB policy unnamed | Generic IAM description unconnected to this template |
| **Prediction exercise (D6)** | Specific Hellerstein limitation cited with section reference; specific latency prediction stated as a testable claim | Limitation mentioned but not connected to DynamoDB specifically | Vague prediction; no connection to the paper |
| **Context paragraph (CP)** | See grading scale in `context-paragraph-prompt.md` | — | — |

**Point deductions:**
- Analytical response uses AI without disclosure: −5 pts per response
- D3 missing `Init Duration` line (not a cold start): −10 pts on D3 score

---

## Submission

All deliverables go in the `4-Serverless/` directory of your **private course GitHub repository**:

```
your-course-repo/
└── 4-Serverless/
    ├── app/
    │   └── handler.py            ← Lambda handler (unmodified from template)
    ├── __main__.py               ← Pulumi template (unmodified, or document changes)
    └── LastName_FirstName_Lab4.pdf
```

### Submit to Canvas

Submit the URL to your `4-Serverless/` directory as a text entry in the Canvas Lab 4 assignment.

> **Due:** See the course syllabus for the exact deadline. Late day policy applies.

---

## Connection to the Architecture Design Document

The work in this lab is direct input to your ADD:

- **Section 2 (Architecture Overview):** The Lambda + API Gateway pattern you deploy here is the compute tier of your NovaSpark service design
- **Section 3 (Component Decisions):** Your execution role analysis (D5) is the IAM component decision. Document what you chose and at least one rejected alternative (e.g., `AdministratorAccess` for convenience)
- **Section 4 (Well-Architected Analysis):** Your cold start analysis (D4) maps to the Performance Efficiency pillar
- **Section 5 (Operational Considerations):** The CloudWatch logs you observe in D3 are your monitoring baseline

Students who do this lab carefully will find that several ADD sections write themselves from their lab deliverables.
