# Lab 2: Infrastructure as Code — EC2, S3, and Automated Deployments

**Course:** CS463 — Cloud Native Platform Engineering (Undergraduate)
**Points:** 100
**Estimated Time:** 3–4 hours across three parts

---

## Lab Objectives

By the end of this lab, you will be able to:

- Write Pulumi code to deploy and manage AWS infrastructure
- Explain how IAM roles give EC2 instances temporary, scoped credentials — without storing any keys on disk
- Articulate why hardcoded credentials are dangerous and how to avoid them
- Use S3 to decouple content storage from compute, enabling resilient deployments
- Automate a full multi-resource AWS environment so it deploys with a single `pulumi up`

---

## What You're Building

You are a new engineer at **NovaSpark Technologies**. Over three parts, you'll progressively automate the deployment of the company's website — starting from a fragile manual setup and ending with a fully automated, production-pattern deployment.

| Part | Directory | What You'll Build | Est. Time |
|------|-----------|-------------------|-----------|
| **Part 1** | `lab-p1/` | Deploy EC2 with Pulumi; serve a website from local disk | 45–60 min |
| **Part 2** | `lab-p2/` | Add S3 + IAM role; move content off the instance | 60–90 min |
| **Part 3** | `lab-p3/` | Automate everything — no SSH required, single `pulumi up` | 45–60 min |

> **Start here if this is your first time:** [`SETUP.md`](SETUP.md) — install Pulumi, configure AWS credentials, set up SSH key.

---

## How This Lab Works

Each part contains a `__main__.py` with `TODO` sections. **You write the missing code.** The lab guide walks you through what to write, explains why each piece works the way it does, and has you verify the result before moving on.

The goal isn't just to get the code running — it's to understand why it's written this way. The written deliverables ask you to explain the *why*, not just describe the *what*.

---

## Using the Pulumi Registry

The TODOs in this lab ask you to write Pulumi resource definitions. You are not expected to memorize argument names — real engineers look them up every time they use an unfamiliar resource. The **Pulumi Registry** is where you do that, and learning to navigate it is part of the point of this lab.

**Base URL:** `https://www.pulumi.com/registry/packages/aws/api-docs/`

Every AWS resource has a dedicated page. To find one, append the service and resource name in lowercase:

| Resource you need | Registry path |
|---|---|
| `aws.ec2.SecurityGroup` | `ec2/securitygroup/` |
| `aws.ec2.Instance` | `ec2/instance/` |
| `aws.s3.BucketV2` | `s3/bucketv2/` |
| `aws.s3.BucketPublicAccessBlock` | `s3/bucketpublicaccessblock/` |
| `aws.iam.Role` | `iam/role/` |
| `aws.iam.RolePolicy` | `iam/rolepolicy/` |
| `aws.iam.InstanceProfile` | `iam/instanceprofile/` |

**How to read a registry page — four steps:**

1. Open the URL for the resource you need
2. Click the **Python** tab near the top of the page — the default view shows Terraform HCL syntax which will not work here
3. Scroll to the **Args** section — this lists every argument the resource accepts, whether it is required or optional, and what type it expects
4. Check the **Example Usage** section near the top for a working Python snippet you can adapt directly

**Worked example — finding how to write a SecurityGroup:**

Go to `https://www.pulumi.com/registry/packages/aws/api-docs/ec2/securitygroup/`, click Python, and read the Args section. You will find `ingress` listed as a sequence of `SecurityGroupIngressArgs`. Click that type and you will see its fields: `protocol`, `from_port`, `to_port`, `cidr_blocks` — exactly what TODO 1 in Part 1 asks you to fill in.

Each TODO comment in the code includes the direct registry link for that specific resource. Open it, read the Args, and write the code.

---

## Deliverables Summary

Submit a **single PDF** named `LastName_FirstName_Lab2.pdf`. Capture screenshots as you work — don't recreate them after the fact.

| # | Deliverable | Where | Points |
|---|-------------|-------|--------|
| D1 | `pulumi up` terminal output — Part 1 (all 4 outputs visible) | Part 1, Step 3 | 5 |
| D2 | Browser screenshot of website at `http://<dns>:8080` — Part 1 | Part 1, Step 7 | 5 |
| D3 | `aws configure list` showing `iam-role` credential type | Part 2, Step 5 | 5 |
| D4 | IMDSv2 curl showing `AccessKeyId` starting with `ASIA`, Token, and Expiration | Part 2, Step 5 | 10 |
| D5 | `aws s3 ls s3://<bucket>/` listing `index.html` and `about.html` | Part 2, Step 6 | 5 |
| D6 | `curl -v` output showing `X-Served-From: S3` response header | Part 2, Step 8 | 5 |
| D7 | Written: Why can't EC2 access S3 by default? (3–5 sentences) | Written | 10 |
| D8 | Written: 3 specific risks of hardcoded credentials on EC2 | Written | 10 |
| D9 | `pulumi up` terminal — Part 3 (9+ resources, all outputs visible) | Part 3, Step 4 | 5 |
| D10 | Browser screenshot of website after automated deploy — no SSH used | Part 3, Step 5 | 5 |
| D11 | `pulumi stack output` showing all outputs including `checkBootstrap` | Part 3, Step 6 | 5 |
| D12 | Written: What does `user_data` do + why it's better than SSH setup | Written | 10 |
| D13 | Pulumi vs Terraform: comparison table (8+ dimensions) + recommendation | Written/Research | 10 |
| D14 | `pulumi destroy` completion for all 3 parts (3 screenshots) | Cleanup | 10 |
| | **Total** | | **100** |

---

## Grading Rubric

| Deliverable Type | Full Credit | Partial Credit | No Credit |
|-----------------|-------------|----------------|-----------|
| **Screenshots** | All required elements visible; your own deployment | Missing a minor element | Missing, not your deployment, or recreated after the fact |
| **Written: conceptual (D7, D8, D12)** | Explains *why*, names specific AWS components, uses examples from the lab | Correct but vague — describes *what* without explaining *why* | Copied, AI-generated without disclosure, or factually incorrect |
| **Written: research (D13)** | 8+ dimensions, accurate, includes a concrete recommendation with reasoning | Fewer than 8 dimensions or no recommendation | Not present, or fewer than 4 dimensions |
| **Cleanup (D14)** | All 3 parts destroyed, screenshots show 0 errors | 2 of 3 destroyed | 0 or 1 destroyed |

**Point deductions:**
- Missing screenshot (D1–D6, D9–D11): −3 pts each
- Cleanup missing one part (D14): −3 pts per missing part
- Written response uses AI without disclosure: −5 pts per response

---

## Submission

This lab has two submission components. Both are required for full credit.

### 1 — Push your code to GitHub

Your course repository uses a single-repo convention — one repo for the entire course, organized by lab directory. Push your completed Pulumi code to the `lab2/` directory in your assignment repo:

```
your-course-repo/
└── lab2/
    ├── lab-p1/
    │   └── __main__.py      ← your completed Part 1 code
    ├── lab-p2/
    │   └── __main__.py      ← your completed Part 2 code
    └── lab-p3/
        └── __main__.py      ← your completed Part 3 code
```

You do not need to push config files, `.pulumi/` state, or the `website/` directory — just the `__main__.py` files you wrote.

### 2 — Submit to Canvas

Submit **both** of the following in the Canvas Lab 2 assignment:

- **Upload:** `LastName_FirstName_Lab2.pdf` — your screenshots and written responses, D1–D14 in order with a title page
- **Text entry:** Paste the URL to your `lab2/` directory in your GitHub repo
  *(Example: `https://github.com/your-org/your-repo/tree/main/lab2`)*

> **Due:** See course syllabus. Both the PDF upload and the GitHub link must be present in Canvas for the submission to be considered complete.
