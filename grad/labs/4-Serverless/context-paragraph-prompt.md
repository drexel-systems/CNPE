# Lab 4 — Context Paragraph Prompt

**Points:** 25
**Length:** 150–250 words
**Where to submit:** Include in your Lab 4 PDF after D6

---

## Background: The Required Reading

**Required:** Hellerstein, J. M., Faleiro, J., Gonzalez, J. E., Hellerstein, J., Kannan, S., Sreekanti, V., Tumanov, A., & Wu, C. (2019). *Serverless Computing: One Step Forward, Two Steps Back.* CIDR 2019. [arXiv:1902.03383](https://arxiv.org/abs/1902.03383)

Hellerstein et al. formally characterize five limitations of the serverless/FaaS model as it existed in 2019. The paper is deliberately provocative — it is a critique from systems researchers, not a vendor whitepaper. The limitations they identify are: limited lifetimes, I/O bottlenecks, communication limitations, lack of specialized hardware access, and opaque resource management.

---

## The Prompt

Write a context paragraph that connects **one specific limitation from Hellerstein et al.** to **one specific observation you made during Lab 4**. Your paragraph should do three things:

1. **Name and define** the limitation from the paper — use the paper's terminology, not a paraphrase (1–2 sentences)
2. **Describe a specific observation** from the lab that makes that limitation concrete — which step, what you observed, what it measured (2–3 sentences)
3. **Evaluate and extend**: does the paper's framing hold, or does your lab experience complicate it? Consider: what has changed since 2019? Where does the limitation apply most to NovaSpark's use case, and where does it matter less? (2–3 sentences)

The paragraph is not a summary of the paper. It is a focused connection between one idea and one thing you observed.

---

## What Strong Looks Like

**Weak:** *"The paper talks about limitations of serverless, and we saw cold starts in the lab. Cold starts are a known issue with Lambda."*

This is weak because it doesn't name a specific limitation from the paper, doesn't reference a specific lab observation with data, and makes no evaluative claim.

**Strong:** *"Hellerstein et al. define 'limited lifetimes' as the inability of FaaS functions to maintain long-running background threads or socket connections, which they argue makes serverless unsuitable for stateful or streaming workloads. In Lab 4 Step 2, I observed this indirectly: my cold start Init Duration was 287ms, compared to a warm Duration of 4ms — a 70x gap that exists precisely because Lambda's execution environment does not persist between invocations and must be reconstructed from scratch. What the paper describes as a structural limitation manifests here as an operational cost that a status endpoint at NovaSpark's current scale can absorb, but that becomes a hard problem once latency is user-facing and SLA-bound. The paper was written in 2019; Provisioned Concurrency (released late 2019) directly addresses the cold start surface of this limitation, though the connection timeout and statefulness constraints Hellerstein identifies remain unresolved by that feature."*

This is strong because it: names the specific limitation with the paper's term, cites a specific measured value from the lab, makes an evaluative claim that distinguishes when the limitation matters from when it doesn't, and engages with how the landscape has changed since the paper was written.

---

## Grading Scale

| Score | Criteria |
|-------|----------|
| **25** | Specific limitation named using paper's terminology; specific lab observation cited with step and measured value; original evaluation — either complicates the paper's framing, considers what has changed since 2019, or applies the limitation specifically to NovaSpark's situation |
| **20** | Limitation and lab observation connected clearly, but evaluation stays generic or only restates the paper |
| **15** | Limitation mentioned but lab observation is vague ("we saw cold starts") without citing specific data; or observation is specific but limitation is not drawn from the paper |
| **5** | Only one element present (paper OR lab) but not both, or under 100 words |
| **0** | Not submitted, AI-generated without disclosure, or no attempt to connect reading and lab |
