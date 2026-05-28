# Architecture Design Document — Table of Contents
## CS 545 · Cloud Native Platform Engineering

The ADD is your course's signature deliverable: a 10–14 page structured argument for why the NovaSpark Order API is designed the way it is. It is not written in Week 3 from scratch — each section is seeded by a specific lab and refined over the final three weeks. By the time you sit down to polish it, most of the content already exists in your prior lab work.

---

## The Six Sections

| # | Section | What It Covers | Week 1 | Week 2 | Week 3 |
|---|---------|----------------|--------|--------|--------|
| **§ 1** | **Requirements** | The functional routes, the async pipeline semantics (202 Accepted), non-functional targets (latency, availability, cost), and the real constraints of the AWS Academy sandbox and LabRole IAM scope. Numbers, not adjectives — "p50 under 200ms" not "fast." | **Draft written.** This is the written deliverable for the Week 1 lab. Functional requirements, non-functional requirements, constraints, and the 12-factor compliance hooks paragraph. | **Light revision.** After the WAF lecture, you may tighten the non-functional targets or add a constraint the audit surfaced. | **Polish pass.** Confirm component names match Sections 2 and 3. Verify non-functional targets are the same numbers cited in the cost analysis. |
| **§ 2** | **Architecture Overview** | One coherent system diagram showing the complete request path — Client → API Gateway → Orders Lambda → SQS → Processor Lambda → DynamoDB — assembled from existing lab diagrams. Plus a three-paragraph narrative: what the system does, a single request traced end-to-end, and one sentence on what changes in a production account. | **Not started.** The raw materials exist (Lab 3 VPC diagram, Lab 4 Lambda+API Gateway, Lab 5 DynamoDB, Week 1 pipeline), but assembly happens in Week 3. | **Not started.** Focus is on Sections 4, 5, and 6 this week. | **Assembled.** Pull diagrams from Labs 3–6 into one coherent architecture diagram. Write the three-paragraph narrative. This is assembly work, not authoring — the components already exist. |
| **§ 3** | **Component Decisions** | For each major component (API Gateway, Orders Lambda, SQS Queue, Processor Lambda, DynamoDB Table): what you chose, why, and at least one alternative you explicitly rejected with one sentence on why. | **Seed written.** The Week 1 lab produces a Section 3 seed covering the first design decision you defend (why SQS, why 202). This is a starting skeleton, not the finished section. | **Not yet expanded.** The WAF audit will likely surface additional component-level decisions worth documenting here — note them as you go. | **Assembled and completed.** Expand the Week 1 seed using justifications from prior labs. Add one rejected alternative per component. Cross-reference Section 1 (requirements should justify the decisions here) and Section 4 (WAF findings should reference specific decisions here). |
| **§ 4** | **Well-Architected Analysis** | A six-pillar audit of the implemented system using the structured format: *Decision → WAF Question → Current State → Gap Classification → Improvement.* Each finding classified as Unknown Gap, Conscious Tradeoff, or Best Practice Met. Honest classification earns more credit than the "everything is fine" version. Closes with a count: X Unknown Gaps, Y Conscious Tradeoffs, Z Best Practice Met. | **Not started.** The WAF lecture happens in Week 2. | **Drafted.** This is the primary deliverable for the Week 2 lab. Six pillar entries, specific evidence (file paths, resource names, configuration values), gap classifications, and proposed improvements. | **Polish pass.** Confirm Section 4 references specific decisions named in Section 3. Verify the `customer_id` Security finding explicitly cross-references your Section 3 API Gateway and Orders Lambda entries. |
| **§ 5** | **Operational Considerations** | How the system is monitored, deployed, and recovered. Three subsections: (1) monitoring strategy — which CloudWatch metrics matter for an async pipeline, with thresholds; (2) deployment approach — `pulumi up` workflow, rollback, secret handling; (3) failure modes — what happens when the processor Lambda fails, when DynamoDB throttles, when SQS receives malformed messages. | **Not started.** | **Draft notes written.** The Week 2 lab produces Section 5 as working bullet notes: two CloudWatch metrics with thresholds, two failure modes with mitigations, one gap to address before production. Bullet form is fine at this stage. | **Expanded to prose.** Convert the Week 2 bullet notes into three short paragraphs. Each failure mode should read as: *mode → current state → mitigation.* Seeded by the Op Ex and Reliability pillar findings from Section 4. |
| **§ 6** | **Cost Estimate** | Monthly AWS cost at three traffic levels using the AWS Pricing Calculator. Per-service breakdown table, what drives cost at each scale (one sentence per service), three public Pricing Calculator URLs, a specific crossover threshold where the current architecture stops being cost-effective, and one architectural change that would defer it. | **Not started.** | **Drafted.** The Week 2 homework produces Section 6: two completed Pricing Calculator estimates (100 req/day, 10K req/day), a per-service table, two explanatory paragraphs, the crossover analysis, and one deferral strategy. | **Polish pass.** Confirm the component names in the cost table match the names used in Sections 2 and 3. Verify the crossover threshold is cited with a specific number. |

---

## Progress Snapshot by Week

**End of Week 1**
Section 1 fully drafted. Section 3 seed written. Sections 2, 4, 5, 6 not yet started. Implementation deployed and testable end-to-end.

**End of Week 2**
Sections 1, 4, 5 (notes), and 6 drafted. Section 3 seed exists. Section 2 materials assembled from prior labs but not yet written. ADD is approximately 70% complete by content.

**End of Week 3**
All six sections drafted and polished. Sections 2 and 3 assembled from prior work and cross-referenced with Sections 1 and 4. Section 5 expanded from notes to prose. ADD submitted as a PDF to Canvas.

---

## What "Draft" vs. "Polish" Means

A **draft** means the content is present and graded — this section would earn partial credit in its current state. A **polish pass** means the section is complete but should be read for internal consistency (component names, number references, cross-section citations) before submission. Assembly means the section does not exist yet but all of its source materials are in prior lab work — you are organizing and connecting, not writing from scratch.

The students who struggle in Week 3 almost always have the same problem: they treated a section as "done" in the week it was drafted and did not revisit it. Section 4 written without specific evidence earns partial credit. Section 4 revised after building Section 2 — so the component names are consistent and the WAF findings cite real decisions from Section 3 — earns full credit.

---

## The One Cross-Reference That Matters Most

The `customer_id` design decision touches three sections and must be consistent across all three:

- **Section 1 (Constraints):** The API is designed for an internal deployment — a customer service agent calls it on behalf of a customer. This is a stated constraint, not an oversight.
- **Section 3 (Orders Lambda):** The decision to accept `customer_id` as a caller-supplied parameter is correct for an internal tool. The production gap — extracting identity from a verified JWT rather than trusting the request body — is named as a documented alternative.
- **Section 4 (Security Pillar):** Because Section 1 and Section 3 document the internal deployment context and name the gap, this finding is classified as **Conscious Tradeoff**, not Unknown Gap. The cross-reference is the evidence.

If these three sections tell three different stories, the ADD has a coherence problem. If they tell one consistent story — "we made a deliberate choice, documented the context, and named the production fix" — that is graduate-level architectural reasoning.
