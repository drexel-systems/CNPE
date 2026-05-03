# CS 463: Cloud Native Platform Engineering
## Course Syllabus

**Instructor:** Brian Mitchell, Ph.D.

**Email:** bmitchell@drexel.edu

**Department:** Computer Science, College of Engineering and Computing (formally CCI)


---

## Course Description

An introduction to the principles, tools, and architectures used to design, build, and deploy modern cloud-native software systems. Students apply software engineering concepts across the full stack of cloud infrastructure — from networking and compute to APIs and persistent storage — entirely through hands-on lab work and a course project. There are no exams. Every grade in this course comes from something you build and deploy.

The course follows a build-from-scratch philosophy: you will write the infrastructure code, configure the network, deploy the services, and wire everything together yourself. By the end of the term, you will have a working, cloud-deployed serverless API — built entirely through code, from a blank AWS account. Along the way, you will apply industry best practices including the use of modern Infrastructure as Code tooling — specifically **Pulumi**, a developer-first IaC platform that lets you define and provision cloud resources using standard Python rather than a proprietary configuration language.

All lab work is grounded in a single running scenario: **NovaSpark Technologies**, a fictional startup where you play the role of a cloud engineer helping the team move from manual servers to a properly architected AWS environment.  Read more about  [NovaSpark Technologies Here](../novaspark/readme.md)

**College/Department:** CCI, Department of Computer Science
**Repeat Status:** Not repeatable for credit
**Prerequisites:** CS 283 – Systems Programming (Min Grade: C)
**Credits:** 3 credits
**Meeting Schedule:** Twice weekly, 80-minute sessions

The ideal student has background in application design and development along with systems programming concepts, including some familiarity with operating systems and basic networking.

---

## Course Format

CS 463 meets twice per week. Most weeks follow this pattern:

- **Session 1 (Lecture):** New concepts, architecture principles, and live demonstrations
- **Session 2 (Lab):** You apply what you learned — deploying, configuring, and building

Some weeks are structured differently when content demands it. A lecture-heavy week may use both sessions for instruction with no lab. A lab may require more time than the 80-minute session provides — in those cases, the lab continues outside of class and is due later in the week. These variations are noted clearly in the schedule below.

---

## Commitment and Pacing

This is not a course you can catch up on at the end of the term. **Every lab builds on the previous one.** Your course project — worth 30% of your grade — is a direct extension of the API and storage work in Labs 5 and 6. If those labs are incomplete when you reach Week 9, you have no foundation to build on.

The time required outside of class will vary depending on your background across infrastructure, networking, software design, and software development. Students who are newer to any of these areas should budget more time, not less. Some labs will be straightforward; others will require real troubleshooting. Falling a week behind in this course is recoverable. Falling two weeks behind is difficult. Falling three weeks behind almost always is not.

Use your 5 late days strategically — they exist for genuine disruptions, not procrastination. The students who do well in this course show up to every session, start labs the same day they're assigned, and ask questions early when something isn't working.

---

## Philosophy: Build from Scratch

CS 463 is a doing course. You will not watch cloud infrastructure get built — you will build it. Starting from a blank AWS account, you will write Python code that provisions EC2 instances, defines VPC networks, deploys Lambda functions, and wires together a functioning API. Each lab leaves you with something real: a deployed system, a running service, or a written analysis that proves you understand what you built and why.

The industry has moved toward treating infrastructure as software. Engineers who can read a Pulumi stack, reason about a VPC routing table, or explain a Lambda cold start are more valuable than those who can only click through a cloud console. This course teaches that fluency by putting you in the position of doing it yourself, from scratch, every week.

---

## Course Objectives

Students will:

- Understand how cloud infrastructure enables software products to be deployed with resilience and run at scale
- Build and deploy real AWS infrastructure using Infrastructure as Code from scratch
- Design and implement VPC network architecture including subnets, routing, and security controls
- Build and deploy REST APIs using both server-based and serverless approaches
- Apply the AWS Well-Architected Framework to evaluate a real system you built
- Apply the 12-factor app methodology to cloud-native application design
- Use DynamoDB for cloud-native persistent storage
- Complete a working course project: a serverless order API deployed entirely through code

---

## Learning Outcomes

Students completing this course will be able to:

- Write and deploy cloud infrastructure using Pulumi (Python) from a blank environment
- Design a VPC with public and private subnets, route tables, and security controls
- Build and deploy a REST API using AWS Lambda and API Gateway
- Integrate DynamoDB as persistent storage for a serverless application
- Evaluate a cloud architecture against the AWS Well-Architected Framework
- Apply cloud-native design principles to identify and address weaknesses in a real system
- Present a working cloud system in a recorded demo with clear architectural explanation

---

## Course Materials

### Required

- **AWS Academy Learner Lab Access** — provided by instructor; sandbox AWS environment with **$50 in credits** per student
- **Infrastructure as Code (IaC) Tooling** — this course uses **Pulumi**, a modern IaC tool that lets you define and provision cloud resources using standard Python. This is a deliberate choice: unlike configuration-focused tools such as Terraform (which use a proprietary domain-specific language), Pulumi takes a developer-first approach — your infrastructure code looks and behaves like regular Python, which means you debug it, version it, and reason about it the same way you would any other code. No prior Pulumi experience is required; installation is covered in Week 1. ([Pulumi docs](https://www.pulumi.com/docs/))
- **Python 3.8+** — primary language for all labs and the course project
- **AWS CLI** — free; installation covered in Lab 1
- **Git + GitHub account** — free; used for all lab submissions
- **Postman** — free API testing tool; introduced in Lab 5. [Download here](https://www.postman.com/downloads/)

### Development Tools

- Text editor or IDE — VS Code recommended (free)
- Terminal — native on Mac/Linux; WSL2 recommended on Windows

### Course Materials

Provided via Canvas and the course GitHub repository:
- Lab guides and starter code
- Lecture slides and live demo walkthroughs
- Instructor-provided code examples
- NovaSpark Orders Postman collection (provided with Lab 5)

### Recommended References

- [AWS Documentation](https://docs.aws.amazon.com/)
- [Pulumi Examples](https://github.com/pulumi/examples)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [The 12-Factor App](https://12factor.net/)
- [CNCF Landscape](https://landscape.cncf.io/)

---

## 11-Week Schedule

Most weeks: Session 1 is lecture, Session 2 is lab. Exceptions are noted. The "Want to Learn More" column is entirely optional — these are industry readings and resources for students who want to go deeper. They will never appear on a rubric, but students who engage with them tend to write better reflections and ask better questions.

| Week | Session 1 — Lecture | Session 2 — Lab | Want to Learn More | Due End of Week |
|------|--------------------|-----------------|--------------------|-----------------|
| **1** | Cloud Platform Engineering: what it is and why it matters; the shift from owned hardware to managed services; AWS service categories and the economics of scale; NovaSpark Technologies introduced — company context, cast, and course arc | **Lab 1: AWS Setup** — Install and configure the AWS CLI; connect to AWS Academy Learner Lab; verify identity with `aws sts get-caller-identity`; confirm GitHub Classroom repo access; launch an EC2 instance in the default VPC and SSH in using the Learner Lab key; terminate the instance | [Steve Yegge's "Platforms Rant"](https://gist.github.com/chitchcock/1281611) — the accidentally-published Google+ post that describes Amazon's internal API mandate; gives you the organizational backstory for why AWS was built the way it was | **Lab 1** — four screenshots: CLI output, GitHub repo, SSH connection, terminated instance |
| **2** | Infrastructure as Code: why manual configuration breaks teams; declarative vs. imperative IaC; Pulumi architecture and state model; deploying EC2, S3, and IAM from Python; the `user_data` pattern for zero-SSH automation | **Lab 2: IaC — EC2, S3, and Automation** — Three-part lab completed outside class time: (1) deploy EC2 + S3, (2) add IAM role + bucket policy, (3) full automation with `user_data` — no SSH required | [Martin Fowler, *Infrastructure as Code*](https://martinfowler.com/bliki/InfrastructureAsCode.html) — the definitive short version; Kief Morris wrote the O'Reilly book on this topic if you want the long version | **Lab 2** — all 3 parts: working Pulumi stack + screenshots *(late submissions accepted with 50% penalty through end of Week 5 only — see Late Work Policy)* |
| **3** | Network Architecture — full lecture: the traditional datacenter and why cloud changes everything; AWS regions and availability zones; VPC as a software-defined datacenter; public vs. private subnets; CIDR blocks; Internet Gateway, NAT Gateway, and route table logic; security groups vs. NACLs; the bastion host pattern | **Lab 3 Part 1: VPC Architecture** — Deploy a custom VPC with Pulumi; public + private subnets; IGW + NAT Gateway + route tables; explore routing in the console; written reflection on every routing decision. **Destroy at end of class (NAT Gateway cost)** | [AWS, *How Amazon VPC Works*](https://docs.aws.amazon.com/vpc/latest/userguide/how-it-works.html) — short, accurate, and what Linda actually reads when something breaks | No submission — complete Lab 3 Part 1 during class. Part 2 builds on it; unresolved issues from Part 1 should be addressed before Week 4 |
| **4** | VPC continued: SSH patterns and network security in practice — bastion host mechanics, agent forwarding, and why private instances should never have a public IP *(first 15 min: students rebuild VPC from Week 3 at class start)*. Serverless preview: Lambda execution model overview, API Gateway as a front door — enough context to start Lab 4. *Full serverless depth is covered in Week 5.* | **Lab 3 Part 2: SSH Patterns and Network Verification** — Rebuild VPC from scratch; load SSH key with agent forwarding; hop from bastion to private instance; prove no direct public IP; test security group port enforcement. **Destroy at end of class.** Use any remaining time to start Lab 4 — it continues in Week 5 and is due end of Week 5. | [Martin Fowler, *Serverless Architectures*](https://martinfowler.com/articles/serverless.html) — a thorough practitioner perspective on when serverless makes sense and when it doesn't | **Lab 3** (Parts 1 & 2 combined, single submission) — all deliverables due *(late submissions accepted with 25% penalty through end of Week 5 only — see Late Work Policy).* **Lab 4 assigned this week — due end of Week 5** |
| **5** | **Serverless Computing — Lambda, API Gateway, and Cold Start Analysis.** Lambda execution model in depth; cold start mechanics and how to measure them; the module-level vs. handler-level execution model; API Gateway as a Lambda trigger; IAM execution roles and least privilege; the event object abstraction. *This session provides the depth behind the Lab 4 hands-on work.* | **Lab 4: Serverless API** — Deploy a Lambda function with API Gateway using Pulumi; capture and analyze a cold start in CloudWatch; examine the API Gateway event object; analyze the IAM execution role. Start in class, finish as homework. **Labs 2 and 3 final submission deadline — no submissions accepted after this point** | [Hellerstein et al., *Serverless Computing: One Step Forward, Two Steps Back*](https://arxiv.org/abs/1812.03651) — the academic critique of the FaaS model; the specific limitations named here are exactly what you will observe in the lab | **Lab 4 due** (end of Week 5) + **Labs 2 & 3 final deadline** |
| **6** | **APIs — Design, Patterns, and Async Architecture.** What is an API and why every service boundary is one; REST fundamentals and RESTful design principles (nouns not verbs, parameter placement, status codes); gRPC and GraphQL compared; the synchronous chain failure problem; async patterns — SQS, SNS, EventBridge; streaming APIs; API security layers — OAuth, API Gateway auth, WAF preview. *Directly sets up Lab 5: you will implement the async order pipeline you design in this lecture.* | **Lab 5: Async Order API** — Extend the Pulumi stack with SQS; implement the order submission pipeline (API Gateway → Lambda → SQS → processor Lambda); apply RESTful URL design principles to the full NovaSpark Order API; explain the 202 Accepted decision. Start in class, finish as homework. Postman introduced as API testing tool. | [Roy Fielding's REST dissertation, Chapter 5](https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm) — longer read, but if you want to understand why REST is designed the way it is, this is the primary source | **Lab 5 due** |
| **7** | **Storage and Databases — DynamoDB Deep Dive.** Cloud storage taxonomy (object vs. block vs. database); management spectrum from self-managed to fully managed; database types (relational, key-value, document); DynamoDB access patterns, partition keys, and sort keys; the `boto3` DynamoDB API; Scan vs. Query tradeoffs. | **Lab 6: Storage Backend** — Wire DynamoDB into the NovaSpark Order API; connect the processor Lambda to write every order to the database; implement `GET /orders/{id}` and `GET /orders` using real DynamoDB reads. The full async pipeline — API Gateway → Lambda → SQS → Lambda → DynamoDB — is running end-to-end by the end of this lab. | [DeCandia et al., *Dynamo: Amazon's Highly Available Key-value Store*](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf) — the original paper behind DynamoDB; more accessible than it looks | **Lab 6 due** |
| **8** | **The AWS Well-Architected Framework.** The six pillars; how each pillar maps to decisions already made in Labs 2–6; common gaps in student architectures; what "production-ready" actually means | **Lab 7: WAF Audit** — Written evaluation of your own NovaSpark Order API architecture against the six WAF pillars; identify real gaps; propose one concrete improvement per unsatisfied pillar. No new AWS infrastructure this week. | [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) — the full whitepaper; more useful after you've built something than before | **Lab 7** — written WAF audit |
| **9** | **Cloud Native and the CNCF Ecosystem.** What "cloud native" actually means; the 12-factor app methodology applied to the NovaSpark Order API; CNCF landscape tour; containers and EKS survey; where your current architecture stands against modern cloud-native patterns. | **Project working session** — Class time dedicated to course project extension work. Goal: at least one extension route working end-to-end (`pulumi up` clean, data persisting). See the [Project Roadmap](../../Project-Roadmap/undergrad/project-roadmap.md) for extension options and the full final deliverable description. | [The 12-Factor App](https://12factor.net/) — read the full manifesto; every factor maps to something you've already built | No formal deliverable — working prototype with at least one extension expected by end of session |
| **10** | **No new lecture — project week.** Instructor and TAs available the full session. | **Project working session** — Full class time dedicated to course project work. Goal by end of week: all 3 required API routes working, at least one extension complete, `pulumi up` runs clean | [CNCF Case Studies](https://www.cncf.io/case-studies/) — real companies describing how they use the same tools you've been learning; good fuel for the project reflection | No formal deliverable — working prototype expected by end of session |
| **11** | **Finals week — no class sessions.** | — | — | **Course project due** (exact date announced in Week 9): video demo + written reflection + GitHub repo |

---

## Course Project

### Overview

The **NovaSpark Order API** is the course project — a serverless REST API that accepts customer orders, processes them asynchronously through a message queue, and persists them to a managed database. The core API is defined; you are not choosing what to build. What you control is which extensions you implement and how far you go.

The project is not a separate deliverable — it grows directly out of the lab work. Lab 5 builds the async submission pipeline. Lab 6 adds the storage backend. The final weeks give you time to extend, harden, and demonstrate what you built.

See the [Project Roadmap](../../Project-Roadmap/undergrad/project-roadmap.md) for a full description of the API spec, the extension menu, and what good looks like at demo time.

Simple and correct beats ambitious and half-working. A clean three-route API with a thoughtful reflection is a better submission than a complex system that requires manual steps to run.

### Core API (Required)

After Lab 6, your stack must have the following working end-to-end:

| Route | Status Code | Description |
|-------|-------------|-------------|
| `POST /orders` | 202 Accepted | Submit an order (async, via SQS queue) |
| `GET /orders/{id}` | 200 / 404 | Retrieve a specific order by ID from DynamoDB |
| `GET /orders` | 200 | List all orders |

These three routes are implemented through Labs 5 and 6. They are the baseline. Without them working, you have no project to extend.

### Extensions (Choose at Least One)

The final weeks are for extensions. You are required to implement at least one; more earns more credit.

| Extension | What You Build |
|-----------|---------------|
| `PATCH /orders/{id}` | Update order status through the API |
| `DELETE /orders/{id}` | Soft-cancel orders (set `status: cancelled`, record stays in DB) |
| Status filtering | `GET /orders?status=received` returns only matching orders |
| Authentication | Lambda authorizer validates a token before any route executes |
| Order notifications | SNS publishes a message when an order is placed |
| Pagination | `GET /orders` returns pages of results with a cursor |
| Custom extension | Propose your own — instructor approval required by Week 9 |

### Technical Requirements

| Requirement | Details |
|-------------|---------|
| Async order submission | `POST /orders` Lambda → SQS queue → processor Lambda pipeline |
| Persistent storage | DynamoDB table — data survives between API calls |
| Full stack via IaC | Entire stack deployed with Pulumi — no manually created resources |
| Clean teardown | `pulumi destroy` runs without errors |
| At least one extension | One meaningful route or feature beyond the Lab 6 baseline |

### Build Timeline

| Milestone | When |
|-----------|------|
| `POST /orders` + SQS async pipeline working | End of Lab 5 (Week 6) |
| `GET /orders/{id}` + `GET /orders` + DynamoDB working | End of Lab 6 (Week 7) |
| Extension chosen and implementation started | End of Week 9 session |
| All core routes + at least one extension working | End of Week 10 session |
| Video demo recorded; reflection written | Early Week 11 |

### Final Deliverables

**1. A working API** — deployed through Pulumi, all core routes functional, at least one extension implemented. `pulumi up` and `pulumi destroy` both run cleanly.

**2. A five-minute demo video** — show `pulumi up` completing, run the Postman collection (or curl) against your live API demonstrating all core routes and your extension, explain one architectural decision you made, and show `pulumi destroy` cleaning up.

**3. A written WAF reflection (1–2 pages)** — two pillars you addressed well (with specific examples from your code or configuration), one pillar you did not address and what you would do to fix it, and one thing that worked differently than you expected.

### Project Rubric

| Area | Full Credit | Partial Credit | No Credit |
|------|-------------|----------------|-----------|
| **Working demo (35 pts)** | All 3 core routes work + at least one extension, data persists, `pulumi up/destroy` clean | Core routes work, no extension; or minor issues | Nothing works or stack won't deploy |
| **IaC completeness (20 pts)** | All resources in Pulumi | Most in code, 1–2 manual resources | Console-only, no Pulumi |
| **Storage integration (15 pts)** | DynamoDB reads/writes correctly, table defined in Pulumi | Table exists but read or write broken | No DynamoDB or hardcoded data only |
| **WAF reflection (20 pts)** | Two pillars with specific code/config examples; one gap with a concrete fix | Pillars named but vague | Generic WAF description, not connected to your project |
| **Video clarity (10 pts)** | System shown working; one architectural decision explained clearly | System shown, no explanation | No video or system not demonstrated |

**Deductions:** Manually created resources that should be in Pulumi (−10 pts) · Video over 5 minutes (−5 pts) · Undisclosed AI use in reflection (−10 pts)

---

## Grading

This course has no exams. All grades come from lab work and the course project.

| Assignment | Weight |
|------------|--------|
| Lab 1: AWS Setup | 5% |
| Lab 2: Infrastructure as Code | 15% |
| Lab 3: VPC Architecture (Parts 1 & 2) | 15% |
| Lab 4: Serverless API | 10% |
| Lab 5: Async Order API | 10% |
| Lab 6: Storage Backend | 10% |
| Lab 7: Well-Architected Audit | 5% |
| Course Project (video demo + reflection) | 30% |
| **Total** | **100%** |

### Grading Scale

| Grade | Range |
|-------|-------|
| A | 93–100% |
| A− | 90–92% |
| B+ | 87–89% |
| B | 83–86% |
| B− | 80–82% |
| C+ | 77–79% |
| C | 73–76% |
| C− | 70–72% |
| D | 60–69% |
| F | Below 60% |

### Late Work Policy

Each student receives **5 late days** at the start of the term. The late day bank applies to Labs 1, 4, 5, 6, and 7. Draw from it freely for those labs — once exhausted, late submissions receive a 50% penalty on day 1 and are not accepted after that.

**Labs 2 and 3 follow a different policy — the late day bank does not apply to them.** These two labs span the first half of the course and are direct prerequisites for everything that follows. To give students who fall behind a structured path to partial credit, Labs 2 and 3 have a hard checkpoint at the end of Week 5:

| Lab | Submitted on time | Submitted late, by end of Week 5 | Submitted after Week 5 |
|-----|-------------------|----------------------------------|------------------------|
| Lab 2: IaC | Full credit | **50% penalty** | Zero — not accepted |
| Lab 3: VPC | Full credit | **25% penalty** | Zero — not accepted |

The lower penalty for Lab 3 reflects that it runs across two class sessions (Weeks 3–4), is the most technically complex lab in the first half of the course, and is submitted as a single combined deliverable at the end of Week 4. The Week 5 checkpoint is not an expected submission window — it is a last-chance grace window. Students who plan to submit Labs 2 or 3 late are accepting a meaningful grade penalty; this policy exists to give you a path forward, not an excuse to deprioritize those labs.

**One-off extensions are not available for any lab.** The late day bank and the Week 5 checkpoint provide all the flexibility built into this course. The course project does not accept late submissions under any circumstances.

---

## Cost Management

**AWS Academy credits: $50 per student.** This is a real constraint — manage it carefully.

| Resource | Expected cost |
|----------|--------------|
| EC2 + NAT Gateway (Labs 2–3) | ~$5–10 |
| Lambda + API Gateway | ~$0 (free tier) |
| DynamoDB | ~$0 (free tier) |
| SQS | ~$0 (free tier) |
| S3 | ~$1 |
| **Total expected** | **~$6–11** |

Labs 3 Part 1 and Part 2 require destroying the VPC at the end of class. The NAT Gateway costs approximately $0.045/hour — leaving it running overnight wastes ~$1/day and eats into your project budget. The `pulumi destroy` screenshot in those labs is how you prove cleanup happened.

Running rules: always run `pulumi destroy` when done with any lab. Lambda, API Gateway, DynamoDB, and SQS are free tier — no cost urgency, but practice the habit every lab. Monitor your balance in the AWS Academy Learner Lab panel. If you see an unexpected spike, email the instructor immediately.

---

## Submissions and Course Administration

This course uses a hybrid submission model: code and infrastructure artifacts live in GitHub, written deliverables go to Canvas.

### GitHub Classroom

At the start of the term you will receive a GitHub Classroom invitation that creates a private repository for you. This is your single repo for the entire course. Organize your work using one directory per lab:

```
/1-AWS-Setup/
/2-IaC/
/3-VPC/
/4-Serverless/
/5-API/
/6-Storage/
/7-WAF/
/project/
```

Each directory should contain your Pulumi code, screenshots, and any written deliverable markdown files for that lab. Commit and push before the deadline.

### Canvas Assignments

Canvas has one assignment per lab. Submit the link to your GitHub repo directory (e.g., `github.com/yourname/cs463-yourname/tree/main/2-IaC`) to confirm completion. Canvas records the submission timestamp — this is how late days are tracked.

**Two deliverables go directly to Canvas rather than GitHub:**

| Deliverable | Why Canvas |
|-------------|------------|
| Course project reflection (1–2 pages, PDF) | Inline SpeedGrader feedback |
| Course project video demo link | YouTube/Loom link — not a repo artifact |

### Submission Summary

| What | Where |
|------|-------|
| Pulumi code + screenshots + written lab analysis | GitHub repo directory |
| Lab completion confirmation | Canvas (GitHub link) |
| Course project reflection PDF | Canvas (direct) |
| Course project video link | Canvas (direct) |

---

## Policies

### AI Tools

You are encouraged to use AI tools (ChatGPT, Claude, GitHub Copilot, etc.) to help with learning, debugging, and understanding concepts. All submitted work must be your own, and you must be able to explain any code you submit. Using AI to generate solutions you don't understand is academic dishonesty — and it will show immediately in a 5-minute video where you have to explain what you built.

When AI assistance is used for written deliverables, disclose it. Undisclosed AI use carries a point penalty specified in each lab's rubric. Disclosed use does not — what matters is that the thinking is yours.

### Collaboration

You may discuss concepts and help each other debug. All submitted code and written work must be individual unless explicitly stated otherwise. When in doubt, ask.

### Academic Integrity

This course follows all university, college, and department policies:
- [Academic Integrity Policy](https://drexel.edu/provost/policies-calendars/policies/academic-integrity/)
- [Students with Disabilities](https://drexel.edu/disability-resources/support-accommodations/student-family-resources/)
- [Course Add-Drop Policy](https://drexel.edu/provost/policies-calendars/policies/course-add-drop/)
- [Course Withdrawal Policy](https://drexel.edu/provost/policies-calendars/policies/course-withdrawal/)
- [CCI Academic Affairs](https://drexel.edu/cci/current-students/policies/)

---

## Extra Credit

Up to 10 extra credit points are available:

**Technical Blog Post (+5 points)**
Write a detailed post (minimum 1,500 words) about your course project — architecture, decisions, lessons learned, code examples. Published on Medium, dev.to, or a personal blog. Submit link by end of Week 11.

**Advanced Infrastructure (+5 points, choose one)**
- Implement S3 backend for Pulumi state management with documentation
- Add a CI/CD pipeline using GitHub Actions for automated deployment
- Add authentication to your project API (AWS Cognito or Lambda authorizer)

---

## What This Course Will Ask of You

Every week in this course, you will build something. Not read about it, not watch someone else do it — build it yourself, from code, deployed to real AWS infrastructure. The labs are not exercises in following instructions; they are exercises in engineering judgment. You will run into errors, things will not work the first time, and the solution will rarely be obvious from the error message alone. That is not a flaw in the course design — it is the point.

What success looks like here is not a perfect grade on every lab. It is showing up consistently, debugging systematically, and understanding what you built well enough to explain it in a 5-minute video. Students who do well in CS 463 are not always the ones who knew the most coming in. They are the ones who stayed current week to week, asked questions before they were buried, and treated each lab as the foundation for the next one — because it is.

The students who struggle are almost always the ones who let a week slip, told themselves they'd catch up, and then found themselves two labs behind with the project on the horizon. There is no version of this course where that ends well.

If a lab is taking longer than expected, reach out. If a concept isn't clicking, come to office hours. If you're falling behind, say something early — there is much more that can be done at week two than at week nine.

---

*Syllabus subject to adjustment. Any changes will be announced in class and on Canvas.*
