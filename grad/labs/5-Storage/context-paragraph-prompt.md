# Lab 5 — Context Paragraph Prompt

**Points:** 25
**Length:** 150–250 words
**Where to submit:** Include in your Lab 5 PDF after D6

---

## Background: The Required Reading

**Required:** DeCandia, G., Hastorun, D., Jampani, M., Kakulapati, G., Lakshman, A., Pilchin, A., Sivasubramanian, S., Vosshall, P., & Vogels, W. (2007). *Dynamo: Amazon's Highly Available Key-Value Store.* SOSP 2007. [ACM Digital Library](https://dl.acm.org/doi/10.1145/1294261.1294281)

DeCandia et al. describe the internal Dynamo system Amazon built to power services like the shopping cart — a system that had to remain writable even during network partitions, at the cost of eventual consistency. The key architectural choice: Dynamo chose **availability over consistency** (AP in CAP terms), accepting that different replicas might temporarily hold different values, and reconciling conflicts at read time using vector clocks and last-write-wins.

DynamoDB — the managed service you provisioned in this lab — descends from this design but is not identical to it. The Block 2 seminar explored where the tradeoffs are still visible and where Amazon has moved the dial since 2007.

---

## The Prompt

Write a context paragraph that connects **one specific design decision from DeCandia et al.** to **one concrete choice you made or observed in Lab 5**. Your paragraph should do three things:

1. **Name and characterize** the design decision from the paper — use the paper's framing, not a paraphrase (1–2 sentences)
2. **Connect it to a specific Lab 5 observation or choice** — which step, what you configured, what you observed in the response or CloudWatch logs (2–3 sentences)
3. **Evaluate and extend**: does DynamoDB's behavior match the 2007 design? Where has it diverged? What does the tradeoff mean concretely for NovaSpark's order data? (2–3 sentences)

The paragraph is not a summary of the paper. It is a focused connection between one idea from the reading and one thing you did in the lab.

---

## Candidate Connections

Any of the following would make a strong paragraph — these are starting points, not the only options:

- **Eventual consistency vs. strong consistency:** DeCandia et al. describe Dynamo's default as eventually consistent, with strongly consistent reads available at higher cost. `table.get_item()` uses strongly consistent reads by default in boto3 — does that match or contradict Dynamo's design philosophy? What does NovaSpark's order use case actually require?

- **AP tradeoff and the order lifecycle:** DeCandia et al. chose AP because shopping cart data being temporarily inconsistent across replicas was acceptable — a lost item could be added back. Is the same argument valid for NovaSpark's order status field? What would "temporarily inconsistent" mean for an order in `processing` state?

- **The vector clock decision:** Dynamo used vector clocks to track conflicting writes across replicas. DynamoDB replaced this with conditional writes and optimistic locking. How does `updated_at` in the NovaSpark data model connect to this shift? What conflict scenario does it not address?

- **Billing mode and Dynamo's replication model:** DeCandia et al. describe consistent hashing to distribute data across nodes. PAY_PER_REQUEST billing in DynamoDB abstracts this entirely — the partition assignment is invisible. What did you give up by choosing to hide that abstraction? What would you need to understand about partitioning if you chose PROVISIONED instead?

---

## What Strong Looks Like

**Weak:** *"The paper talks about eventual consistency, and DynamoDB also has consistency settings. I used strongly consistent reads in my handler."*

This is weak because it does not use the paper's terminology precisely, does not connect to a specific lab observation with concrete detail, and makes no evaluative claim about NovaSpark's situation.

**Strong:** *"DeCandia et al.'s central architectural choice was to prioritize availability over consistency, accepting that Dynamo replicas might temporarily diverge under partition, with client-side reconciliation via vector clocks. In Lab 5 Step 3.3, my GET /orders/test-order-001 call used boto3's default get_item(), which performs a strongly consistent read — meaning DynamoDB contacts the leader replica before returning, not a potentially stale secondary. This directly contradicts the 2007 design philosophy: Dynamo's default was eventual consistency specifically to avoid the latency penalty of leader-mandatory reads. The shift reflects a fundamental difference between Dynamo (designed for Amazon's internal shopping cart, where staleness was tolerable) and DynamoDB (a general-purpose database where application developers can't always reason about staleness). For NovaSpark, the latency cost of strong consistency is acceptable at this scale — but if order volume grows substantially and per-read cost becomes a concern, switching to eventually consistent reads for the list-all route (GET /orders) while keeping strong consistency for GET /orders/{id} would be a defensible optimization worth noting in the ADD."*

This is strong because it: names the specific design decision with the paper's terminology, cites a specific lab step and what it used, makes a concrete evaluative claim about the tradeoff and when it matters for NovaSpark, and connects the analysis to the ADD.

---

## Grading Scale

| Score | Criteria |
|-------|----------|
| **25** | Specific design decision named using paper's terminology; specific lab observation cited with step and implementation detail; original evaluation — either complicates the paper's framing, addresses what changed since 2007, or applies the tradeoff specifically to NovaSpark's order data |
| **20** | Design decision and lab observation connected clearly, but evaluation stays generic or only restates the paper |
| **15** | Design decision mentioned but lab observation is vague; or observation is specific but decision is not drawn from the paper |
| **5** | Only one element present (paper OR lab) but not both, or under 100 words |
| **0** | Not submitted, AI-generated without disclosure, or no attempt to connect reading and lab |
