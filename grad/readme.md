# CS 545: Cloud Native Platform Engineering
## Course Syllabus

**Instructor:** Brian Mitchell, Ph.D.

**Email:** bmitchell@drexel.edu

**Department:** Computer Science, College of Engineering and Computing (also CCI)

---

## Course Description

An graduate-focused study of the principles, architectures, and tools used to design and operate modern cloud-native systems. Students examine the technical and organizational tradeoffs behind cloud infrastructure decisions — from networking and storage to serverless compute and distributed systems patterns — through weekly seminar discussions, hands-on configuration labs, and a substantial written architecture deliverable.

This course is the graduate counterpart to an undergraduate offering in cloud platform engineering. Where the undergraduate version emphasizes hands-on construction — writing infrastructure code, deploying services, and building functioning systems from scratch — CS 545 shifts the emphasis to **architectural investigation, critical evaluation, and written justification**. Students engage directly with primary literature from industry and academia, examine the broader impacts of cloud computing on how modern software systems are designed and operated, and develop the reasoning skills expected of engineers, architects, and technical leads.

This course serves a deliberately mixed cohort: students with strong technical CS backgrounds will deepen their analytical and architectural thinking, while students transitioning into technical roles will find that the scaffolded lab approach and emphasis on evaluation over construction provides an accessible and rigorous entry point. Both groups are expected to engage fully with the technical content and the written work. Labs provide starter infrastructure so you spend your time reasoning about decisions, not fighting syntax. Throughout the course, students will apply industry best practices including the use of modern Infrastructure as Code tooling — specifically **Pulumi**, a developer-first IaC platform that lets you define and provision cloud resources using standard Python rather than a proprietary configuration language.

**College/Department:** CCI, Department of Computer Science
**Repeat Status:** Not repeatable for credit
**Prerequisites:** Foundational experience with cloud platforms equivalent to an undergraduate cloud computing course, or instructor approval. Familiarity with at least one cloud provider and basic comfort in a Linux terminal are expected. No prior cloud certification is required, but students who have never used AWS, GCP, or Azure in a structured way should speak with the instructor before enrolling.
**Credits:** 3 credits
**Meeting Schedule:** Once weekly, 2 hours 50 minutes per session

---

## Course Format

CS 545 meets once per week for a single extended session divided into three blocks:

| Block | Duration | Activity |
|-------|----------|----------|
| **Block 1** | 70 min | Lecture — concepts, architectures, and technical depth |
| **Break** | 10 min | — |
| **Block 2** | 40–50 min | Seminar discussion — the week's primary reading in the context of the lecture |
| **Block 3** | 40–50 min | Lab or workshop — configuration, design exercise, or project time |

The rhythm is intentional. The lecture provides the technical foundation. The reading discussion asks you to engage with how practitioners and researchers have thought about the problem at industry scale. The lab asks you to configure, evaluate, or design something real. Block 2 and Block 3 are not independent — the best lab submissions show that you're connecting what you read to what you built.

This course requires a consistent weekly commitment outside of class to complete lab deliverables, engage with the week's reading, and make progress on the Architecture Design Document and final project. The time required will vary significantly based on your background across infrastructure, networking, software design, and software development — students who are newer to any of these areas should expect a heavier weekly investment, potentially 5–7 hours or more in some weeks. Plan accordingly from the start of the term rather than the week a major deliverable is due.

---

## Philosophy: Configure, Evaluate, and Justify

CS 545 does not ask you to write cloud infrastructure code from scratch. You will configure AWS services, modify provided Pulumi templates, and adapt working examples to your design decisions. The learning goal is not "can you write a Lambda handler" — it is "can you explain *why* this architectural choice is appropriate, what you considered and rejected, and what the broader implications are for how the system behaves under real conditions."

Every lab in this course has two components: a technical deliverable (something you configure, deploy, or design) and a written component (something you justify, analyze, or connect). The writing is not extra credit — it is half the work.

---

## Course Objectives

Students will:

- Evaluate cloud architectures against professional standards (AWS Well-Architected Framework, 12-factor app, distributed systems principles)
- Engage with primary literature from industry research and engineering practice to understand how cloud computing has changed what is possible and what is expected
- Apply distributed systems concepts — consistency models, failure modes, CAP theorem — to concrete infrastructure decisions
- Configure and reason about AWS managed services: EC2, VPC, Lambda, DynamoDB, S3, IAM, API Gateway, CloudWatch
- Produce a professional-grade Architecture Design Document from requirements through trade-off analysis
- Develop technical communication skills through a recorded project demo

---

## Learning Outcomes

Students completing this course will be able to:

- Configure cloud infrastructure using Pulumi templates and the AWS console with full understanding of what they're configuring and why
- Read and critically evaluate technical papers, whitepapers, and engineering blog posts from cloud practitioners
- Write a professional Architecture Design Document covering requirements, design decisions, trade-off analysis, and operational considerations
- Apply the AWS Well-Architected Framework to evaluate and critique a real system
- Explain distributed systems tradeoffs in both written and oral form
- Present a technical system architecture and defend design choices in a recorded demo

---

## Course Materials

### Required

- **AWS Academy Learner Lab Access** — provided by instructor; sandbox AWS environment with **$50 in credits** per student
- **Infrastructure as Code (IaC) Tooling** — this course uses **Pulumi**, a modern IaC tool that lets you define and provision cloud resources using standard programming languages like Python. This is a deliberate choice: unlike configuration-focused tools such as Terraform (which use a proprietary domain-specific language), Pulumi takes a developer-first approach — your infrastructure code looks and behaves like regular Python, which makes it easier to reason about, debug, and extend. No prior Pulumi experience is required; starter templates are provided for all labs. ([Pulumi docs](https://www.pulumi.com/docs/))
- **Python 3.8+** — required to run Pulumi programs; no Python programming from scratch required
- **AWS CLI** — free; installation covered in Week 1
- **Git + GitHub account** — free; used for lab submission

### Development Tools

- Text editor or IDE — VS Code recommended (free)
- Terminal — native on Mac/Linux; WSL2 recommended on Windows

### Course Materials

Provided via Canvas and the course GitHub repository:
- Lab guides, Pulumi starter templates, and configuration scaffolding
- Lecture slides and annotated architecture diagrams
- Weekly reading links (primary source + optional supplements)
- Architecture Design Document template and rubric

### Recommended References

- [AWS Documentation](https://docs.aws.amazon.com/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Google Site Reliability Engineering Book](https://sre.google/sre-book/table-of-contents/) (free online)
- [The 12-Factor App](https://12factor.net/)
- [Pulumi Examples](https://github.com/pulumi/examples)
- [CNCF Landscape](https://landscape.cncf.io/)
- [AWS Architecture Center](https://aws.amazon.com/architecture/)

---

## 10-Week Schedule

Each week follows the same three-block structure. The table below shows the lecture topic, what you should read before class (with direct links), the discussion angle for Block 2, and what is due. Lab guides and detailed rubrics are distributed on Canvas. Optional items in the reading column are recommended but not required for discussion.

| Week | Lecture (Block 1) | Read Before Class | Discussion Focus (Block 2) | Lab / Workshop (Block 3) | Due End of Week |
|------|-------------------|-------------------|---------------------------|--------------------------|-----------------|
| **1** | Cloud Fundamentals: the shift from owned hardware to managed services; AWS service categories; the economics of scale that make cloud different | **Recommended — read after class this week:** [Barroso, Hölzle & Ranganathan, *The Datacenter as a Computer*, 3rd ed.](https://link.springer.com/book/10.1007/978-3-031-01761-2) (free Open Access, Springer — Ch. 1–2) | Ad hoc discussion — no pre-read required for Week 1. Instructor introduces the paper's core argument in class: what changes when you treat a datacenter as a single computer? Does warehouse-scale thinking apply to a company NovaSpark's size? | AWS CLI setup, Learner Lab orientation, GitHub Classroom repo confirmation, launch and SSH into an EC2 instance using the Learner Lab key, terminate the instance | **Lab 1** — setup confirmation + context paragraph |
| **2** | Infrastructure as Code: why configuration drift breaks teams; declarative vs. imperative IaC; Pulumi architecture and state model | [Fowler, *Infrastructure as Code* (martinfowler.com)](https://martinfowler.com/bliki/InfrastructureAsCode.html) · optional: [Pulumi — How Pulumi Works (docs)](https://www.pulumi.com/docs/concepts/) | Where does IaC create discipline, and where does it create new failure modes? What does Fowler say that practitioners often skip? | Read and annotate provided Pulumi template; modify instance type + S3 bucket; write 1-page justification of what the template does and what would break without the IAM role | **Lab 2** — annotated template + justification + context paragraph |
| **3** | Cloud Networking: VPC architecture, subnet isolation, routing table logic, NAT Gateway cost model, security groups vs. NACLs | [AWS, *VPC Security Best Practices* (AWS Docs)](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html) · optional: [Advanced VPC Design (re:Invent, 60 min)](https://www.youtube.com/watch?v=fnxXNZdf6ew) | Why does Linda care so much about the network? What does the reading say about the blast radius of a misconfigured VPC? | Deploy provided VPC Pulumi template; trace route tables in console; draw network diagram with annotations; write 1-page routing justification. **Destroy at end of class (NAT Gateway cost)** | **Lab 3** — network diagram + routing justification + context paragraph |
| **4** | Serverless Computing: Lambda execution model, cold starts, API Gateway as an integration layer, event triggers, synchronous vs. async invocation, IAM execution roles (Thread 2 of 3), when serverless is the wrong answer | [Hellerstein et al., *Serverless Computing: One Step Forward, Two Steps Back* (arXiv 2019)](https://arxiv.org/abs/1902.03383) · optional: [Lambda Under the Hood (re:Invent, 30 min)](https://www.youtube.com/watch?v=xmacMfbrG28) · optional: [Eismann et al., *The State of Serverless Applications* (2021)](https://arxiv.org/abs/2010.14023) | Hellerstein identifies five formal limitations of serverless. Which still hold in 2025? For NovaSpark's workload (small team, variable load, API-driven), do they apply? **Prediction exercise:** DynamoDB integration is next week — predict which I/O bottleneck and slow-storage limitations you expect to encounter. You will evaluate your predictions empirically in Lab 5. | Deploy provided Lambda + API Gateway Pulumi template; function returns hardcoded JSON; hit endpoint with `curl`; measure cold start vs. warm latency; write 1-page performance analysis and evaluate execution role scope | **Lab 4** — deployed Lambda + API Gateway + cold start analysis + context paragraph |
| **5** | Storage: taxonomy of storage options; object vs. database storage; management spectrum (self-managed → RDS → DynamoDB); DB type dimension (relational, key-value, document, time-series); DynamoDB deep dive — access patterns, partition keys, sort keys; back-reference: how the execution role from Lab 4 grants DynamoDB access without hardcoded credentials | [DeCandia et al., *Dynamo: Amazon's Highly Available Key-value Store* (SOSP 2007)](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf) · optional: [DynamoDB Advanced Design Patterns (re:Invent, 60 min)](https://www.youtube.com/watch?v=yvBR71D0nAQ) | DeCandia's team chose availability over consistency. Where is that tradeoff visible in DynamoDB's design, and how should NovaSpark think about it for a status event log? Revisit the Hellerstein predictions you made in Week 4 — did your cold start and I/O observations match what the paper predicted? | Extend your Lab 4 Pulumi stack to add a DynamoDB table; design access patterns first (written); configure PITR; connect Lambda to DynamoDB using the execution role from Lab 4 — no new credentials needed | **Lab 5** — extended Pulumi stack + access pattern design + DynamoDB table + RTO/RPO analysis + context paragraph |
| **6** | Event-Driven Architecture: synchronous vs. async patterns; SQS, SNS, and EventBridge compared; fan-out design; idempotency; the hidden costs of tight coupling | [Vogels, *Eventually Consistent* (allthingsdistributed.com, 2008)](https://www.allthingsdistributed.com/2008/12/eventually_consistent.html) · optional: [ACM Queue version (full paper)](https://dl.acm.org/doi/10.1145/1466443.1466448) | Vogels argues eventual consistency is not a bug — it's a design choice. How does that reframe the conversation about event-driven systems vs. synchronous APIs? | Workshop (no AWS): design an event-driven extension for NovaSpark's status service; choose between SQS / SNS / EventBridge for fan-out to email + Slack + database write; annotate diagram with component justifications | **Workshop 6** — architecture diagram + component justifications + context paragraph |
| **7** | Observability and Monitoring: the three pillars (logs, metrics, traces); CloudWatch architecture; alert design; SLIs, SLOs, and error budgets; how observability changes incident response | [SRE Book, Ch. 6: *Monitoring Distributed Systems* (free online)](https://sre.google/sre-book/monitoring-distributed-systems/) · optional: [Google SRE Book — full text (free)](https://sre.google/sre-book/table-of-contents/) | What does Google's SRE team mean by "symptoms not causes" in alerting? How would you apply that to NovaSpark's alerting setup? | No Block 3 lab — time used for ADD peer review and Q&A. **ADD due end of week.** | **Architecture Design Document** (25%) — no late submissions |
| **8** | Security and IAM: identity vs. access; IAM roles, policies, and the principle of least privilege; the confused deputy problem; S3 bucket policies; what "production-ready" security actually means | [Felten & Schneider, *The Confused Deputy* (1988, 2 pages)](https://dl.acm.org/doi/10.1145/74851.74857) · [AWS IAM Best Practices (AWS Docs)](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html) · optional: [AWS re:Invent — IAM Best Practices (video)](https://www.youtube.com/watch?v=YQsK4MtsELU) | What makes the confused deputy problem subtle? Where in your own ADD could this class of vulnerability appear? | Project work session: initialize Pulumi stack, define DynamoDB table, stub at least one Lambda route. Submit a one-paragraph project scope statement — which service you're building, which project option you've chosen, and any divergence from your ADD plan. Instructor will confirm or flag concerns before Week 9. | Project scope statement (required, not separately graded — confirms you're on track before the final two weeks) |
| **9** | Cost Optimization and the Well-Architected Framework: the six WAF pillars; cost as an architectural decision; right-sizing; reserved capacity vs. on-demand; what the WAF misses | [AWS, *Cost Optimization Pillar* (Well-Architected Framework)](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html) · optional: [AWS Well-Architected Tool overview (docs)](https://docs.aws.amazon.com/wellarchitected/latest/userguide/intro.html) | The WAF is comprehensive but it's also a vendor document. Where does it help you think clearly, and where might it lead you toward AWS-specific solutions when something simpler would work? | Complete all 3 required API routes; cost analysis using AWS Pricing Calculator at 3 traffic levels (100 / 10K / 1M req/day) | **Lab 9 deliverable** — all routes working + cost analysis write-up (graded as part of Final Project) |
| **10** | Emerging Topics: containers and Kubernetes in context; where serverless and container-based architectures fit together; what has changed in cloud infrastructure in the last five years and what is likely to change next | Student-selected: one recent practitioner post or talk on a cloud topic you want to discuss (shared on Canvas by Wednesday) | Open format — you bring the reading this week. What is worth understanding about where cloud is heading, and what would you tell Janet about containers given everything NovaSpark has built? | Final project work session and overflow. **Final project due end of week.** | **Final Project** (25%) — no late submissions |

---

## The Context Paragraph

Every lab submission includes a short written component called the **Context Paragraph**. This is not a research essay — it is one focused paragraph (150–250 words) that connects the week's reading to something specific in your own lab work or the NovaSpark narrative.

Each lab guide includes the specific prompt. Prompts are designed to be answerable in one paragraph by anyone who did the reading and completed the lab. Examples of the type of question you can expect:

- *"Fowler argues that IaC creates consistency as a forcing function. Point to one specific decision in the template you modified and explain how it either supports or complicates that claim."*
- *"DeCandia's team chose availability over consistency. Where is that tradeoff visible in the DynamoDB table you designed for NovaSpark?"*
- *"Vogels describes eventual consistency as a design choice, not a bug. What does that mean for how NovaSpark should handle a fan-out failure in the event architecture you designed?"*

Context paragraphs are graded on a simple 3-point scale as part of each lab:

| Score | What it means |
|-------|---------------|
| **3/3** | Connects the reading to your specific lab work or the NovaSpark scenario with a concrete, accurate observation |
| **2/3** | Engages with the reading but stays generic — no direct connection to what you built or configured |
| **1/3** | Submitted but does not engage with the reading |
| **0/3** | Missing |

The paragraph is worth approximately 20–25% of each lab grade. If you did the reading and completed the lab, full marks should be straightforward.

---

## Major Deliverables

### Architecture Design Document (ADD) — Due Week 7 — 25% of grade

The signature graduate deliverable. You will design a cloud-native service for NovaSpark Technologies — the same fictional company from the labs — but *before* building the final version of it. The document is 10–14 pages and covers:

- **Section 1: Requirements** — functional requirements, non-functional requirements (latency, availability, cost), and constraints
- **Section 2: Architecture Overview** — diagrams and narrative description of all components
- **Section 3: Component Decisions** — for each major component, explain what you chose and why, including at least one rejected alternative
- **Section 4: Well-Architected Analysis** — evaluate your design against all six WAF pillars; identify gaps and explain tradeoffs
- **Section 5: Operational Considerations** — monitoring strategy, deployment approach, failure modes and mitigations
- **Section 6: Cost Estimate** — rough estimate of monthly AWS costs using the AWS Pricing Calculator

A strong ADD is specific and defensible. It demonstrates that you understand *why* every piece is there, what you considered and rejected, and what the realistic operational concerns are. The final project is the implementation of this document — or an honest accounting of where the implementation diverged from the design and why.

By the time the ADD is due in Week 7, you will have completed labs covering networking (Week 3), serverless compute (Week 4), and storage (Week 5). The network diagram from Lab 3, the cold start and performance analysis from Lab 4, and the access pattern and RTO/RPO analysis from Lab 5 are all inputs to the ADD — students who do the labs well will find the ADD largely assembles itself.

Full details: see `architecture-design-doc-guide.md` (to be published on Canvas before Week 4). The guide includes annotated examples of strong and weak submissions, section-by-section guidance on what each part of the document should accomplish, and the complete grading rubric.

### Final Project — Due Week 10 — 25% of grade

Build the service you designed in your ADD (or a clearly scoped subset of it). Technical requirements:

| Requirement | Details |
|-------------|---------|
| Serverless compute | At minimum 2 Lambda functions (or one handling multiple routes) |
| API endpoint | API Gateway HTTP API with at least 3 routes: `POST`, `GET` (list), `GET` (by ID) |
| Persistent storage | DynamoDB table — data survives between API calls |
| Infrastructure as Code | Entire stack deployed with Pulumi — no manually created resources |
| Clean teardown | `pulumi destroy` runs without errors |
| IAM least privilege | Lambda role scoped to only what it needs — no `AdministratorAccess` |

**Final Project Deliverables — all due end of Week 10:**

*Demo video (5–7 minutes):*
- `pulumi up` running and completing successfully
- At least three `curl` calls showing all required routes working end-to-end
- Walk through your architecture diagram on screen — explain what each component is and why it's there
- Explain two design decisions from your ADD: did the implementation match your plan, and if not, why not?
- `pulumi destroy` completing cleanly

*Written reflection (1–2 pages):*
- Where did your implementation match your ADD? Where did it diverge, and why?
- One WAF pillar you addressed well, with a specific code or configuration example
- One WAF pillar you did not address, and what you would do to fix it given more time

### Project Options

Choose one NovaSpark internal service to build:

- **Status Event Service** — log and retrieve system health events (the service the whole course narrative has been building toward)
- **Task Tracker** — create, update, and retrieve engineering tasks
- **Product Inventory** — manage NovaSpark product catalog items
- **Feedback Collector** — submit and retrieve internal feedback
- **Student-proposed idea** — submit a one-paragraph description for instructor approval by end of Week 7

---

## Grading

| Assignment | Overall Weight | Notes |
|------------|----------------|-------|
| Lab 1: AWS Setup | 5% | Technical + context paragraph |
| Lab 2: IaC | 10% | Technical + context paragraph |
| Lab 3: VPC | 10% | Technical + context paragraph |
| Lab 4: Serverless | 10% | Technical + context paragraph |
| Lab 5: Databases | 10% | Technical + context paragraph |
| Workshop 6: Event Architecture | 5% | Design diagram + context paragraph |
| Architecture Design Document | 25% | Canvas PDF — no late submissions |
| Final Project | 25% | Video + reflection + code — no late submissions |
| **Total** | **100%** | |

Labs and the workshop together account for 50% of the course grade. The ADD and Final Project together account for the other 50%. This split reflects the course philosophy: you are expected to both do the technical work and explain it.

### Within Each Lab: Technical vs. Paragraph

Each lab is scored on a 10-point rubric. The context paragraph represents approximately 2–3 points of each lab grade. The technical deliverable (configured infrastructure, diagram, analysis, or combination) represents the remaining 7–8 points. Specific rubric breakdowns are in each lab guide.

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

Graduate students are expected to perform at the B level or above. Sustained C-range work is a signal to schedule office hours.

### Late Work Policy

Each student receives **5 late days** at the start of the term. Late days apply to lab deliverables only (Labs 1–6 and Workshop 6). The Architecture Design Document and Final Project do not accept late submissions — the ADD is a gate for project feedback, and the final project deadline is fixed to align with end-of-term grading.

---

## Cost Management

**AWS Academy credits: $50 per student.** This is a real constraint — manage it carefully.

| Resource | Expected cost |
|----------|--------------|
| EC2 + NAT Gateway (Labs 2–3) | ~$5–10 |
| Lambda + API Gateway | ~$0 (free tier) |
| DynamoDB | ~$0 (free tier) |
| S3 | ~$1 |
| CloudWatch metrics/alarms | ~$1–2 |
| **Total expected** | **~$7–13** |

Rules of thumb: always run `pulumi destroy` when done with any lab that uses EC2 or NAT Gateway. Lambda, API Gateway, and DynamoDB are free tier — no destroy urgency, but practice the habit. Monitor your balance in the AWS Academy Learner Lab panel. If you see an unexpected spike, email the instructor immediately.

---

## NovaSpark Technologies

All labs and the final project are set in the context of **NovaSpark Technologies**, a fictional early-stage cloud startup. You play the role of a senior cloud engineer or architect. The cast:

- **Janet** — CTO. Cares about architecture and business outcomes. Introduces requirements and challenges the team's design choices.
- **Ben** — Engineering Manager. Focused on shipping velocity, cost, and operational reliability. He's the one explaining the AWS bill.
- **Linda** — SRE lead. Worried about reliability, security, and what happens at 3am. Pushes back on anything that isn't production-grade.

A one-page NovaSpark briefing is on Canvas. Read it before Week 1.

---

## Submissions and Course Administration

This course uses a hybrid submission model: code and infrastructure artifacts live in GitHub, written deliverables go to Canvas.

### GitHub Classroom

At the start of the term you will receive a GitHub Classroom invitation that creates a private repository. Organize your work with one directory per lab:

```
/1-AWS-Setup/
/2-IaC/
/3-VPC/
/4-Serverless/
/5-Databases/
/6-EventArchitecture/
/project/
```

Each directory should contain your Pulumi code, screenshots, and the written analysis markdown (including context paragraph) for that lab.

### Canvas Assignments

Canvas has **one assignment per week**. At the end of the week, submit the link to your GitHub repo directory for that week's lab. The context paragraph is part of your lab's written analysis in GitHub — not a separate Canvas submission.

**Three deliverables go directly to Canvas rather than GitHub:**

| Deliverable | Why Canvas |
|-------------|------------|
| Architecture Design Document (PDF) | Inline SpeedGrader comments are the primary feedback channel |
| Final project reflection (1–2 pages, PDF) | Written feedback via SpeedGrader |
| Final project video link | YouTube/Loom link — not a repo artifact |

### Submission Summary

| What | Where |
|------|-------|
| Lab code + screenshots + written analysis + context paragraph | GitHub repo directory |
| Lab completion confirmation | Canvas (GitHub link) |
| Architecture Design Document | Canvas (PDF, direct) |
| Final project reflection | Canvas (PDF, direct) |
| Final project video link | Canvas (direct) |
| Final project code | GitHub repo `/project/` directory |

---

## Policies

### AI Tools

You are encouraged to use AI tools (ChatGPT, Claude, GitHub Copilot, etc.) to help with learning, debugging, and understanding concepts. All submitted work — especially written work — must reflect your own thinking. Using AI to generate a context paragraph you haven't thought through defeats the purpose of the exercise and the discussion that depends on it.

When AI assistance is used in written deliverables, disclose it. Undisclosed AI use in the Architecture Design Document carries a 10-point penalty. Disclosed use does not — what matters is that the reasoning is yours.

### Collaboration

You may discuss concepts and help each other debug. All submitted code, written work, and architecture documents must be individual unless explicitly stated otherwise. Peer review of ADD drafts is encouraged — peer writing of another student's ADD is not.

### Discussion Norms

Block 2 research discussions are seminars, not lectures. There is no single right answer. Arrive having done the reading. Build on what others say. Disagree constructively. Connect the reading to your lab work. The best discussions are ones where the practitioner perspective in the reading changes how you would approach a technical decision in the labs.

Participation is not graded — but the discussion is where the learning compounds. Students who engage seriously with Block 2 consistently write better context paragraphs and stronger ADDs.

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
Write a detailed post (minimum 1,500 words) about your final project — architecture, decisions, lessons learned. Published on Medium, dev.to, or a personal blog. Submit link by end of Week 10.

**Advanced Infrastructure (+5 points, choose one)**
- Implement S3 backend for Pulumi state management with documentation
- Add a CI/CD pipeline using GitHub Actions for automated deployment
- Add authentication to your project API (AWS Cognito or Lambda authorizer)
- Add a CloudWatch dashboard and at least two alarms to your project with written justification for the metrics chosen

---

## What This Course Will Ask of You

CS 545 is a course about architectural thinking. The technical skills matter — you will configure real AWS infrastructure, read real systems papers, and build a working service — but the primary question this course asks is not *can you build it?* It is *do you understand why it's built that way, what the alternatives were, and what the broader implications are for how modern software systems work?*

In practice, that means:

**Labs are about reasoning, not output.** Starter templates and scaffolded infrastructure are provided so you spend your time understanding and evaluating decisions, not fighting syntax. A working deployment with no justification of the tradeoffs is an incomplete submission. The written component of every lab is where the graduate-level work happens.

**Readings situate technology in a bigger picture.** Every week's primary reading connects the technical topic to how practitioners and researchers have actually grappled with these problems at scale. Cloud computing has fundamentally changed what is possible in software — the readings help you develop a vocabulary and perspective for that shift that you won't get from documentation alone.

**The ADD is the course's center of gravity.** Professional cloud engineers and architects rarely build first and think later. The Architecture Design Document asks you to design the full NovaSpark system on paper before building it — requirements, component choices, rejected alternatives, operational concerns, and cost model. By the time it's due in Week 7, you will have done the analysis across networking, storage, and compute in the earlier labs. The ADD assembles that thinking into a coherent whole.

**The written work is probably the hardest part.** Students with strong technical backgrounds sometimes find that explaining *why* is harder than doing. Students newer to the technical side find the scaffolded approach accessible, and the analytical emphasis rewards clear thinking over prior experience. Both groups tend to find the written deliverables — the context paragraphs, the ADD, the final reflection — where they grow the most.

---

*Syllabus subject to adjustment. Any changes will be announced in class and on Canvas.*
