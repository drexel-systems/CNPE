# Lab 2: Infrastructure as Code — EC2, S3, and Automated Deployments

**Course:** CS545 — Cloud Native Platform Engineering (Graduate)
**Points:** 100
**Estimated Time:** 3–4 hours across three parts + 1 hour written analysis

---

## Lab Objectives

By the end of this lab, you will be able to:

- Deploy a multi-resource AWS environment using Pulumi and explain every design decision in it
- Evaluate the IAM role pattern for EC2 credential management and justify its advantages over alternatives
- Analyze the tradeoffs between manual configuration, semi-automated, and fully automated infrastructure
- Connect the IaC concepts from this lab to the week's readings on infrastructure design principles
- Articulate the business value of each architectural choice — not just that it works, but *why* it was built this way

---

## What You're Doing

You are a new engineer at **NovaSpark Technologies**. The code is complete and the infrastructure runs. Your task is to **deploy it, observe the system in depth, and justify every architectural choice** — in writing, with specifics.

| Part | Directory | What You'll Do | Est. Time |
|------|-----------|----------------|-----------|
| **Part 1** | `lab-p1/` | Deploy EC2 with Pulumi; SSH in; observe the fragility | 30–40 min |
| **Part 2** | `lab-p2/` | Deploy EC2 + S3 + IAM; explore credentials in depth | 50–70 min |
| **Part 3** | `lab-p3/` | Deploy fully automated stack; trace every layer | 40–50 min |
| **Analysis** | Written | Context paragraph + analytical deliverables | 45–60 min |

> **Start here if this is your first time:** [`SETUP.md`](SETUP.md) — install Pulumi, configure AWS credentials, set up SSH key.

---

## How to Approach This Lab: Configure, Evaluate, Justify

This lab asks: *Can you explain why it was built this way — and identify where it could be improved?*

Before running any `pulumi up`, read the code. Not to understand what to type, but to understand the design. Ask yourself:
- Why is this resource structured this way?
- What would break if this line were removed?
- What security assumption is embedded in this choice?
- What would you do differently in a real production environment?

Your written deliverables require *specific* answers to questions like these, grounded in what you observe in the running system.

---

## Deliverables Summary

Submit a **single PDF** named `LastName_FirstName_Lab2.pdf`.

### Screenshots (prove your deployment ran)

| # | Deliverable | Where | Points |
|---|-------------|-------|--------|
| D1 | `pulumi up` terminal — Part 1 (all 4 outputs visible) | Part 1, Step 3 | 5 |
| D2 | Browser screenshot of website at `http://<dns>:8080` | Part 1, Step 7 | 5 |
| D3 | `aws configure list` showing `iam-role` credential type | Part 2, Step 5 | 5 |
| D4 | IMDSv2 curl showing `AccessKeyId` starting with `ASIA`, Token, and Expiration | Part 2, Step 5 | 10 |
| D5 | `aws s3 ls s3://<bucket>/` listing both HTML files | Part 2, Step 6 | 5 |
| D9 | `pulumi up` terminal — Part 3 (9+ resources, all outputs) | Part 3, Step 4 | 5 |
| D14 | `pulumi destroy` completion for all 3 parts (3 screenshots) | Cleanup | 5 |
| | **Screenshots subtotal** | | **40** |

### Analytical Deliverables

| # | Deliverable | Length | Points |
|---|-------------|--------|--------|
| D6 | IAM role architecture analysis: explain the full credential chain from EC2 → IMDS → S3. Why does `X-Served-From: S3` prove the right pattern is in place? Include `curl -v` output as evidence. | 4–6 sentences | 10 |
| D7 | Default-deny defense: explain *why* EC2 cannot access S3 by default and why this is the correct default at scale. Model the threat: what would happen to your org's data if any EC2 instance could access any S3 bucket without a role? | 4–6 sentences | 10 |
| D8 | Credential risk analysis: for each of the following storage patterns, describe the specific failure mode and risk severity: (a) environment variables, (b) `~/.aws/credentials` on disk, (c) hardcoded in application code, (d) IAM role via IMDS. | Table or structured list | 10 |
| D12 | Automation analysis: compare the three deployment approaches (Parts 1, 2, 3) across at least 5 dimensions. Then evaluate: what does `user_data_replace_on_change=True` guarantee about the instance, and why does that matter for a production system? | 5–7 sentences + table | 10 |
| CP | **Context Paragraph:** see [`context-paragraph-prompt.md`](context-paragraph-prompt.md) | 150–250 words | 20 |
| | **Analytical subtotal** | | **60** |
| | **Grand Total** | | **100** |

---

## Grading Rubric

| Deliverable Type | Full Credit | Partial Credit | No Credit |
|-----------------|-------------|----------------|-----------|
| **Screenshots** | Required elements visible; your own deployment | Missing a minor element | Missing, not your deployment, or recreated |
| **Analytical (D6–D8, D12)** | Names specific AWS components; explains *why*, not just *what*; draws on what you observed in the running system | Correct at a general level but not grounded in lab specifics | Vague generalities, copied, or AI-generated without disclosure |
| **Context Paragraph** | Connects a specific concept from the readings to a specific observation in the lab; original synthesis; meets word count | Mentions readings and lab but doesn't synthesize them | Summary of readings OR lab but not both; or under 100 words |

---

## A Note on AI Use

You may use AI tools to help you understand concepts, look up documentation, or check your writing. You may not use AI to generate your analytical responses. If AI-generated text appears in your submission without disclosure, the deliverable receives zero credit. The point is that *you* can explain this — not that you can prompt something that can.

---

## Submission

This lab has two submission components. Both are required for full credit.

### 1 — Push your code to GitHub

Your course repository uses a single-repo convention — one repo for the entire course, organized by lab directory. Push the code you deployed to the `lab2/` directory in your assignment repo:

```
your-course-repo/
└── lab2/
    ├── lab-p1/
    │   └── __main__.py
    ├── lab-p2/
    │   └── __main__.py
    └── lab-p3/
        └── __main__.py
```

You do not need to push config files, `.pulumi/` state, or the `website/` directory — just the `__main__.py` files.

### 2 — Submit to Canvas

Submit **both** of the following in the Canvas Lab 2 assignment:

- **Upload:** `LastName_FirstName_Lab2.pdf` — your screenshots, analytical responses, and context paragraph (D1–D14 + CP), in order with a title page
- **Text entry:** Paste the URL to your `lab2/` directory in your GitHub repo
  *(Example: `https://github.com/your-org/your-repo/tree/main/lab2`)*

> **Due:** See course syllabus. Both the PDF upload and the GitHub link must be present in Canvas for the submission to be considered complete.
