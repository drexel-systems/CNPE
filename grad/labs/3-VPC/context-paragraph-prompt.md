# Lab 3 — Context Paragraph Prompt

**Points:** 25
**Length:** 150–250 words
**Where to submit:** Include in your Lab 3 PDF after D11

---

## The Prompt

This week's readings addressed network architecture, security boundaries, and defense-in-depth principles in cloud infrastructure.

Write a context paragraph that connects **one specific concept from this week's reading** to **one specific observation you made during Lab 3**. Your paragraph should do three things:

1. **Name and briefly define** the concept from the reading (1–2 sentences)
2. **Describe a specific moment or observation** from the lab where you saw that concept in action — cite the part and step (2–3 sentences)
3. **Extend or evaluate**: did the lab confirm, complicate, or add nuance to how the reading presented the concept? Where does the real implementation differ from the textbook explanation? (2–3 sentences)

---

## What Strong Looks Like

A strong context paragraph doesn't just mention both the reading and the lab in passing. It makes a specific connection — naming the concept, pointing to the exact step or observation where it appeared, and then saying something original about what that revealed.

**Weak example:** *"The reading talked about defense in depth and we used a bastion host and security groups in the lab."*

**Strong example:** *"The reading defines defense in depth as layering independent security controls so that no single failure exposes a system. In Lab 3 Part 2, Step 6, I tested this by running `nc -zvw 3 10.0.11.x 80` from the bastion — a host already inside the VPC — and the connection timed out silently. The private instance wasn't reachable on port 80 not because of subnet routing, but because the security group drops the packet before it reaches the instance's network stack. What the reading doesn't address is the operational consequence of silent drops versus explicit rejects: `nc` hangs until its timeout rather than returning an immediate error, which makes security group debugging significantly slower than firewall rule debugging in traditional on-prem environments. The stateless, fire-and-forget nature of the drop is a feature from a security standpoint but a liability from a debugging standpoint — and the reading presents these as simply 'layers' without discussing the asymmetry."*

---

## Grading Scale

| Score | Criteria |
|-------|----------|
| **25** | Specific concept named and defined; specific lab observation cited with part/step; original evaluation that adds nuance beyond the reading |
| **20** | Concept and lab connected clearly, but evaluation is thin or repeats the reading without adding nuance |
| **15** | Mentions both reading and lab but the connection is surface-level or generic |
| **5** | One is present (reading OR lab) but not both, or under 100 words |
| **0** | Not submitted, AI-generated without disclosure, or does not attempt the connection |
