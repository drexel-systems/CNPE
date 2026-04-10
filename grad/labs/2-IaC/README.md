# Lab 2: Infrastructure as Code — EC2, S3, and Automated Deployments

**Course:** CS545 — Cloud Native Platform Engineering (Graduate)
**Points:** 100 (+ up to 10 extra credit)
**Estimated Time:** 2–3 hours (Parts 1 and 2 required); Part 3 is optional extra credit

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

| Part | Directory | What You'll Do | Est. Time | Required? |
|------|-----------|----------------|-----------|-----------|
| **Part 1** | `lab-p1/` | Deploy EC2 with Pulumi; SSH in; observe the fragility | 30–40 min | ✅ Required |
| **Part 2** | `lab-p2/` | Deploy EC2 + S3 + IAM; explore credentials in depth | 50–70 min | ✅ Required |
| **Part 3** | `lab-p3/` | Deploy fully automated stack; trace every layer | 40–50 min | ⭐ Extra credit (+10 pts) |
| **Analysis** | Written | Context paragraph + analytical deliverables | 45–60 min | ✅ Required |

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

### Required — Screenshots (40 pts)

| # | Deliverable | Where | Points |
|---|-------------|-------|--------|
| D1 | `pulumi up` terminal — Part 1 (all 4 outputs visible) | Part 1, Step 3 | 5 |
| D2 | Browser screenshot of website at `http://<dns>:8080` — Part 1 | Part 1, Step 7 | 5 |
| D3 | `aws configure list` showing `iam-role` in the Type column | Part 2, Step 3 | 5 |
| D4 | IMDSv2 curl output — `AccessKeyId` starting with `ASIA`, a `Token` field, and an `Expiration` timestamp | Part 2, Step 5 | 10 |
| D5 | `aws s3 ls s3://<bucket>/` listing both HTML files | Part 2, Step 6 | 5 |
| D6 | `curl -v` terminal output showing `X-Served-From: S3` response header | Part 2, Step 8 | 5 |
| D7 | `pulumi destroy` — Parts 1 and 2 (2 terminal screenshots, 0 errors) | Cleanup | 5 |
| | **Screenshots subtotal** | | **40** |

### Required — Analytical Deliverables (60 pts)

| # | Deliverable | Length | Points |
|---|-------------|--------|--------|
| D8 | IAM credential chain analysis: trace the full path from EC2 → instance profile → IMDS → IAM → S3. What does each link in the chain do? Why does the `X-Served-From: S3` response header confirm the right pattern is in place? | 4–6 sentences | 15 |
| D9 | Default-deny defense: explain *why* EC2 cannot access S3 by default and model the threat at scale — what would happen to your org's data if any EC2 instance could access any S3 bucket without an explicit role? | 4–6 sentences | 10 |
| D10 | Credential risk analysis: for each of the following patterns, describe the specific failure mode and risk severity: (a) environment variables, (b) `~/.aws/credentials` on disk, (c) hardcoded in application code, (d) IAM role via IMDS. | Table | 10 |
| D11 | Automation analysis: compare Part 1 (local disk) vs Part 2 (S3 + manual setup) across 5 dimensions. Then predict: what would Part 3's `user_data` eliminate, and why does eliminating manual SSH steps matter for a production environment running 50+ instances? | 5–7 sentences + table | 5 |
| CP | **Context Paragraph:** see [`context-paragraph-prompt.md`](context-paragraph-prompt.md) | 150–250 words | 20 |
| | **Analytical subtotal** | | **60** |
| | **Grand Total** | | **100** |

### Extra Credit — Part 3 (+10 pts)

Deploy the fully automated stack and submit all four deliverables below. All four must be present for any extra credit to be awarded.

| # | Deliverable | Points |
|---|-------------|--------|
| EC1 | `pulumi up` terminal — Part 3 (9+ resources, all outputs visible) | 3 |
| EC2 | Browser screenshot — website live after automated deploy, no SSH used | 2 |
| EC3 | `pulumi stack output` showing all outputs including `checkBootstrap` | 2 |
| EC4 | Trace the bootstrap execution: what did `journalctl` show? Were there any failures or delays in the startup sequence? Name one specific thing you would change about this bootstrap design for a production environment and justify it. (4–6 sentences) | 3 |
| | **Extra Credit Total** | | **+10** |

---

## Grading Rubric

| Deliverable Type | Full Credit | Partial Credit | No Credit |
|-----------------|-------------|----------------|-----------|
| **Screenshots (D1–D7)** | All required elements visible; your own deployment | Missing a minor element (e.g., output partially cut off) | Missing, not your deployment, or recreated after the fact |
| **Analytical (D8–D11)** | Names specific AWS components; explains *why*, not just *what*; grounded in what you observed in the running system | Correct at a general level but not grounded in lab specifics | Vague generalities, copied, or AI-generated without disclosure |
| **Context Paragraph (CP)** | Connects a specific concept from the readings to a specific observation in the lab; original synthesis; meets word count | Mentions readings and lab but doesn't synthesize them | Summary of readings OR lab but not both; or under 100 words |
| **Extra credit (EC1–EC4)** | All four submitted and correct | Partial — awarded only if all four are present | Missing any one EC deliverable = 0 EC awarded |

**Point deductions:**
- D4 missing a key element (no ASIA prefix, no Token, or no Expiration): −10 pts
- Screenshot missing a minor element (D1–D3, D5–D7): −3 pts each
- Written response uses AI without disclosure: −5 pts per response

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
        └── __main__.py      ← optional: include if you completed Part 3 for extra credit
```

You do not need to push config files, `.pulumi/` state, or the `website/` directory — just the `__main__.py` files.

### 2 — Submit to Canvas

Submit **both** of the following in the Canvas Lab 2 assignment:

- **Upload:** `LastName_FirstName_Lab2.pdf` — screenshots (D1–D7), analytical responses (D8–D11), and context paragraph (CP), in order with a title page; include EC1–EC4 at the end if submitting for extra credit
- **Text entry:** Paste the URL to your `lab2/` directory in your GitHub repo
  *(Example: `https://github.com/your-org/your-repo/tree/main/lab2`)*

> **Due:** See course syllabus. Both the PDF upload and the GitHub link must be present in Canvas for the submission to be considered complete.
