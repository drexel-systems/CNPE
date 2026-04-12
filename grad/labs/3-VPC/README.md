# Lab 3: Network Architecture — Building a Production VPC

**Course:** CS545 — Cloud Native Platform Engineering (Graduate)
**Points:** 100 total (45 pts Part 1 + 55 pts Part 2) + 10 pts Extra Credit
**Weeks:** 3 and 4

---

## Lab Objectives

By the end of this lab, you will be able to:

- Explain why the AWS default VPC is not appropriate for production workloads
- Describe the difference between public and private subnets and what determines which is which
- Explain how an Internet Gateway and a NAT Gateway differ in purpose and direction of traffic
- Deploy a multi-subnet VPC with bastion host and private instance using Pulumi
- Use SSH agent forwarding to authenticate through a bastion without copying private keys to a server
- Prove that a private instance has outbound internet access via NAT but is unreachable from the internet
- Justify every architectural decision in the deployed infrastructure — not just what it is, but why it was built this way

---

## What You're Doing

You are a new engineer at **NovaSpark Technologies**. The code is complete and the infrastructure runs. Your task is to **deploy it, observe the system in depth, and justify every architectural choice** — in writing, with specifics.

The procedural steps (deploy, SSH in, verify, destroy) are shared with the lab guide. The work is in your analysis.

| Part | Week | Guide | What You'll Do | Est. Time |
|------|------|-------|----------------|-----------|
| **Part 1** | 3 | [lab-p1/lab-guide.md](lab-p1/lab-guide.md) | Read and annotate the code; deploy VPC; explore console; destroy at end of class | 60–75 min |
| **Part 2** | 4 | [lab-p2/lab-guide.md](lab-p2/lab-guide.md) | Rebuild; SSH agent forwarding; bastion hop; NAT verification; final destroy | 60–75 min |

> **Start here if this is your first time:** [`SETUP.md`](SETUP.md) — install Pulumi, configure AWS credentials, set up SSH key.

> ⚠️ **Cost note:** The NAT Gateway costs ~$0.045/hour just to exist. Do **not** leave it running between weeks — run `pulumi destroy` at the end of Week 3 class as directed. You will rebuild at the start of Week 4 (takes 4–6 minutes).

---

## Deliverables Summary

Submit a **single PDF** named `LastName_FirstName_Lab3.pdf` combining deliverables from both parts.

### Part 1 Deliverables (due end of Week 3) — 45 points

| # | Deliverable | Points |
|---|-------------|--------|
| D1 | `pulumi up` terminal output — 16+ resources created, all 5 outputs visible | 10 |
| D2 | AWS Console: Private Route Table showing `0.0.0.0/0 → nat-xxxx` and `10.0.0.0/16 → local` | 10 |
| D3 | Analytical: Difference between Internet Gateway and NAT Gateway — explain the traffic direction and security model for each, with specific reference to what you observed in the deployed route tables | 3–5 sentences | 10 |
| D4 | Analytical: The bastion host pattern — why it exists, what problem it solves, and one specific improvement to reduce the risk it introduces. Name the AWS service or configuration change you'd make | 3–5 sentences | 10 |
| D5 | Terminal: `pulumi destroy` completing with 0 errors (end of Week 3) | 5 |

### Part 2 Deliverables (due end of Week 4) — 55 points

| # | Deliverable | Points |
|---|-------------|--------|
| D6 | Terminal: `ssh-add -l` confirming `labsuser.pem` is loaded in the agent | 5 |
| D7 | Terminal: `curl https://checkip.amazonaws.com` from **bastion** — IP matches `bastionPublicIp` | 10 |
| D8 | Terminal: `hostname -I` from **private instance** — shows `10.0.11.x` address | 10 |
| D9 | Terminal: metadata check returning `No public IP` from private instance | 5 |
| D10 | Terminal: `curl https://checkip.amazonaws.com` from **private instance** — IP matches `natEip` | 15 |
| D11 | Terminal: `pulumi destroy` completing with 0 errors (end of Week 4) | 10 |

### Extra Credit (due end of Week 4) — 10 points

| # | Deliverable | Points |
|---|-------------|--------|
| CP | Context paragraph — connects one concept from this week's reading to one specific lab observation. See [`context-paragraph-prompt.md`](context-paragraph-prompt.md) for the full prompt, examples, and grading scale. Include after D11 in your submission PDF | +10 |

---

## Grading Rubric

| Deliverable Type | Full Credit | Partial Credit | No Credit |
|-----------------|-------------|----------------|-----------|
| **Terminal screenshots (D1, D5–D11)** | All required elements visible; prompt shows which machine you're on | Missing a minor element | Not captured, recreated, or from wrong machine |
| **D10 (NAT proof — key deliverable)** | IP exactly matches `natEip` output; student notes which output it matches | IP shown but no comparison provided | Not captured or IPs don't match with no explanation |
| **D2 (Console RT)** | Private Route Table visible with both route entries | Only one route entry visible | Public RT submitted instead of Private RT |
| **Analytical (D3, D4)** | Names specific AWS components; explains *why*, not just *what*; references specific observations from the lab (route table entries, security group rules, etc.) | Correct at a general level but not grounded in lab specifics | Vague generalities, AI-generated without disclosure, or factually incorrect |
| **CP (Extra Credit)** | All three components present (concept defined, specific lab observation cited with part/step, original evaluation); adds nuance the reading didn't cover | Concept and lab connected but evaluation is thin or repeats the reading | Surface-level, AI-generated without disclosure, or does not attempt the connection |

**Point deductions:**
- Either `pulumi destroy` missing (D5 or D11): −5 pts each
- Analytical response uses AI without disclosure: −5 pts per response
- CP (if submitted) uses AI without disclosure: −5 pts
- D10 captured but IPs don't match with no explanation: −10 pts

---

## Submission

All deliverables for this lab go in the `lab3/` directory of your **private course GitHub repository**:

```
your-course-repo/
└── lab3/
    ├── lab-p1/
    │   └── __main__.py                  ← your Pulumi code
    └── LastName_FirstName_Lab3.pdf      ← all screenshots and analytical responses
                                            (D1–D11 in order, with a title page;
                                             include CP after D11 if attempting extra credit)
```

You do not need to push config files, `.pulumi/` state, or Pulumi stack files — just `__main__.py` and your PDF.

### Submit to Canvas

Submit the following as a text entry in the Canvas Lab 3 assignment:

- The URL to your `lab3/` directory in your GitHub repo
  *(Example: `https://github.com/your-org/your-repo/tree/main/lab3`)*

> **Due:** See course syllabus. Both `__main__.py` and `LastName_FirstName_Lab3.pdf` must be committed and visible in your repo before the deadline. There are no exceptions for files that were "on your machine" or "almost pushed."

---

## A Note on AI Use

You may use AI tools to help you understand concepts, look up documentation, or check your writing. The analytical deliverables in this course are specifically designed to require engagement with what you observed in the running system — the actual route table entries, the specific security group rules, the exact behavior you saw during the SSH hop. Generic responses that could have been written without doing the lab will not receive full credit regardless of their origin.
