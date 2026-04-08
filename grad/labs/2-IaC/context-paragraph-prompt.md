# Lab 2 — Context Paragraph Prompt

**Points:** 20
**Length:** 150–250 words
**Where to submit:** Include in your Lab 2 PDF after D12

---

## The Prompt

This week's readings addressed principles of infrastructure design, configuration management, and the role of automation in modern cloud systems.

Write a context paragraph that connects **one specific concept from this week's reading** to **one specific observation you made during Lab 2**. Your paragraph should do three things:

1. **Name and briefly define** the concept from the reading (1–2 sentences)
2. **Describe a specific moment or observation** from the lab where you saw that concept in action — cite the part and step (2–3 sentences)
3. **Extend or evaluate**: did the lab confirm, complicate, or add nuance to how the reading presented the concept? Where does the real implementation differ from the textbook explanation? (2–3 sentences)

---

## What Strong Looks Like

A strong context paragraph doesn't just mention both the reading and the lab in passing. It makes a specific connection — naming the concept, pointing to the exact line of code or step where it appeared, and then saying something original about what that observation revealed.

**Weak example:** *"The reading talked about least privilege and we saw IAM roles in the lab."*

**Strong example:** *"The reading defines least privilege as granting only the permissions required for a specific task. In Lab 2 Part 2, Step 5, I saw this implemented in the IAM role policy: `s3:GetObject` and `s3:ListBucket` were granted only on `arn:aws:s3:::novaspark-website-*`, not on all S3 resources. What the reading doesn't address is the operational tension this creates — in Part 2, I had to manually specify the bucket ARN in the policy, which required knowing the bucket name before the policy could be written. Pulumi's `.apply()` pattern solves this by deferring policy evaluation until the bucket exists, but this dependency ordering isn't visible in the policy document itself. A team reading the Pulumi code without knowing `.apply()` semantics might not realize the policy is bucket-scoped until they inspect the deployed IAM console."*

---

## Grading Scale

| Score | Criteria |
|-------|----------|
| **20** | Specific concept named and defined; specific lab observation cited with part/step; original evaluation that adds nuance beyond the reading |
| **15** | Concept and lab connected clearly, but evaluation is thin or repeats the reading without adding nuance |
| **10** | Mentions both reading and lab but the connection is surface-level or generic |
| **5** | One is present (reading OR lab) but not both, or under 100 words |
| **0** | Not submitted, AI-generated without disclosure, or does not attempt the connection |
