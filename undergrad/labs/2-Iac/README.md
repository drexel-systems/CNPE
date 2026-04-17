# Lab 2: Infrastructure as Code — EC2, S3, and Automated Deployments

**Course:** CS463 — Cloud Native Platform Engineering (Undergraduate)
**Points:** 100 (+ up to 10 extra credit)
**Estimated Time:** 2–3 hours (Parts 1 and 2 required); Part 3 is optional extra credit

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

| Part | Directory | What You'll Build | Est. Time | Required? |
|------|-----------|-------------------|-----------|-----------|
| **Part 1** | `lab-p1/` | Deploy EC2 with Pulumi; serve a website from local disk | 45–60 min | ✅ Required |
| **Part 2** | `lab-p2/` | Add S3 + IAM role; move content off the instance | 60–90 min | ✅ Required |
| **Part 3** | `lab-p3/` | Automate everything — no SSH required, single `pulumi up` | 45–60 min | ⭐ Extra credit (+10 pts) |

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

### Required (100 pts)

| # | Deliverable | Where | Points |
|---|-------------|-------|--------|
| D1 | `pulumi up` terminal output — Part 1 (all 4 outputs visible) | Part 1, Step 3 | 10 |
| D2 | Browser screenshot of website at `http://<dns>:8080` — Part 1 | Part 1, Step 7 | 10 |
| D3 | `aws configure list` showing `iam-role` in the Type column | Part 2, Step 3 | 10 |
| D4 | IMDSv2 curl output — `AccessKeyId` starting with `ASIA`, a `Token` field, and an `Expiration` timestamp | Part 2, Step 5 | 20 |
| D5 | `aws s3 ls s3://<bucket>/` listing `index.html` and `about.html` | Part 2, Step 6 | 10 |
| D6 | `curl -v` output showing `X-Served-From: S3` response header | Part 2, Step 8 | 10 |
| D7 | Written: Why can't an EC2 instance access S3 by default, and why is that a good thing? (2–3 sentences) | Written | 10 |
| D8 | Written: Name one specific risk of storing long-lived AWS credentials on an EC2 instance, and explain how the IAM role + IMDS approach eliminates that risk. (2–3 sentences) | Written | 10 |
| D9 | `pulumi destroy` — Parts 1 and 2 (2 terminal screenshots showing 0 errors) | Cleanup | 10 |
| | **Total** | | **100** |

### Extra Credit — Part 3 (+10 pts)

Complete Part 3 to automate the full deployment with `user_data` — no SSH required. All four deliverables below must be submitted for extra credit to be awarded.

| # | Deliverable | Where | Points |
|---|-------------|-------|--------|
| EC1 | `pulumi up` terminal — Part 3 (9+ resources, all outputs visible) | Part 3, Step 4 | 3 |
| EC2 | Browser screenshot of website after automated deploy — no SSH used | Part 3, Step 5 | 2 |
| EC3 | `pulumi stack output` showing all outputs including `checkBootstrap` | Part 3, Step 6 | 2 |
| EC4 | Written: What does `user_data` do, and why is it better than SSHing in to configure a server? (2–3 sentences) | Written | 3 |
| | **Extra Credit Total** | | **+10** |

---

## Grading Rubric

| Deliverable Type | Full Credit | Partial Credit | No Credit |
|-----------------|-------------|----------------|-----------|
| **Screenshots (D1–D6)** | All required elements visible; your own deployment | Missing a minor element (e.g., output partially cut off) | Missing, not your deployment, or clearly recreated after the fact |
| **Written (D7, D8)** | Names the specific AWS mechanism, explains *why* in your own words | Correct but vague — says *what* without explaining *why* | AI-generated without disclosure, copied, or factually wrong |
| **Cleanup (D9)** | Both parts destroyed, terminal shows 0 errors | One of two parts destroyed | Neither destroyed |
| **Extra credit (EC1–EC4)** | All four submitted and correct | Partial — awarded only if all four are present | Missing any one EC deliverable = 0 EC awarded |

**Point deductions:**
- Screenshot missing a key element (D4 — no ASIA prefix, no Token, or no Expiration): −10 pts
- Screenshot missing a minor element (D1–D3, D5–D6): −5 pts each
- Written response uses AI without disclosure: −5 pts per response

---

## Submission

This lab has two submission components. Both are required for full credit.

Push all deliverables to the `lab2/` directory of your **private course GitHub repository**:

```
your-course-repo/
└── lab2/
    ├── lab-p1/
    │   └── __main__.py      ← your completed Part 1 code
    ├── lab-p2/
    │   └── __main__.py      ← your completed Part 2 code
    ├── lab-p3/
    │   └── __main__.py      ← optional: include if you completed Part 3 for extra credit
    └── LastName_FirstName_Lab2.pdf   ← your screenshots and written responses, D1–D9
                                         in order with a title page; include EC1–EC4
                                         at the end if submitting for extra credit
```

You do not need to push config files, `.pulumi/` state, or the `website/` directory.

### Confirm on Canvas

Submit the URL to your `lab2/` directory as a text entry in the Canvas Lab 2 assignment:

*(Example: `https://github.com/your-org/your-repo/tree/main/lab2`)*

> **Due:** See course syllabus. Your `__main__.py` files and PDF must be committed and visible in your repo before the deadline. There are no exceptions for files that were "on your machine" or "almost pushed."
