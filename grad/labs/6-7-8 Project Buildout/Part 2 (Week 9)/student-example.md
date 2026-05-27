# WAF Audit — Worked Example
## CS 545 Week 9: SSH Bastion Access and the Audit Format

Use this document as a reference when writing your own six-pillar audit. Part 1 and Part 2 cover the technical background from the in-class discussion. Part 3 shows exactly how that material maps to the five-step audit format — including how to write Step 5 as an Architecture Decision Record.

---

## Part 1 — The Security Problem with SSH Bastion Access

### What we built in Lab 3

An EC2 bastion host in a public subnet with a security group allowing inbound SSH from `0.0.0.0/0` on port 22. The bastion is the entry point for any admin access to resources inside the VPC.

The `0.0.0.0/0` rule was intentional — students connect from home networks, campus Wi-Fi, and mobile hotspots, so IP ranges are unknown in advance. That documented reason is what makes this a **Conscious Tradeoff** rather than an Unknown Gap.

### Current state assessment

A good audit entry covers both what is working and what isn't. When you write your own pillar entries, start by identifying the strengths of the current state before naming the gaps. This is not about being generous — it's about being accurate. If you can only see problems, your gap classifications won't hold up and your ADR reasoning will be shallow.

---

**Strengths**

**SSH key-based authentication is meaningfully stronger than password-based access.** To compromise key-based SSH, an attacker needs physical possession of the private key file — not a guessed password, not a phished credential, not a brute-forced username/password combination. Credential theft, which is the most common attack vector against remotely accessible systems, does not work against a well-managed private key. This is a real, substantive security control and it is worth naming as such.

**The bastion pattern itself is a security best practice.** Rather than exposing every EC2 instance in the VPC directly, all admin access flows through a single, controlled entry point. This limits the attack surface to one known host and reduces the blast radius of a misconfigured or compromised instance elsewhere in the network.

**The security group limits exposure to port 22 only.** The rule is not "allow all inbound traffic" — it is scoped to the SSH port. Other services and ports on the instance are not exposed to the public internet.

---

**Gaps**

The open security group is the most visible issue but not the deepest one. There are two distinct gaps worth separating in your audit:

**Gap 1 — Key lifecycle: SSH authenticates a key, not a person**

When you hand someone a private key, you lose visibility over it. You cannot answer:

- Who currently has a copy of this key?
- Has it been shared, copied to another machine, or checked into a repo?
- When was it last rotated?
- If someone's laptop is stolen, is the key on it?

You cannot revoke one person's access without rotating the key for *everyone* who has it. IAM lets you remove a single user's permission in seconds. Key-based SSH has no equivalent.

`auth.log` records that *a key* connected. It does not record which *person* was holding it at the time.

**Gap 2 — Session audit: no record of what happened during a session**

Even if you know exactly who connected, SSH gives you no log of commands run, files accessed, or changes made during the session. For any compliance framework — SOC 2, PCI-DSS, HIPAA — "who connected" is not enough. "What did they do" is the actual requirement.

These are two separate problems. A team could solve Gap 1 with strict key management and still have Gap 2 completely open.

---

## Part 2 — SSH vs. AWS Systems Manager Session Manager

### SSH: the inbound connection model

```
Your laptop ──── TCP port 22 ────► EC2 Bastion
                  (inbound)          (public IP)
                  Security Group allows 0.0.0.0/0
```

- Your machine reaches out to the instance on port 22
- The security group either allows or blocks the connection
- Authentication: private key file on your machine
- Audit: connection timestamps in `/var/log/auth.log` only — no commands

### Session Manager: the outbound connection model

```
Your laptop ──── HTTPS ────► AWS Systems Manager ──── outbound ────► EC2 Instance
                 (IAM auth)    (service endpoint)       (SSM agent
                                                         phones home)
```

- The SSM agent *inside* the instance opens an outbound connection to the AWS SSM service endpoint
- You connect to the AWS service, not directly to the instance — AWS brokers the session
- The instance never accepts inbound traffic from anyone
- Authentication: IAM identity (user, role, or assumed role)
- Audit: full session log — start/end time, identity, every command — streamed to CloudWatch Logs or S3

### Side-by-side comparison

| | SSH + Bastion | Session Manager |
|---|---|---|
| **Inbound port required** | Port 22 open | None — port 22 can be removed entirely |
| **Public IP required** | Yes | No |
| **Authentication** | Private key file | IAM identity |
| **Revoke one person's access** | Rotate key for everyone | Remove that user's IAM permission |
| **Audit trail** | Connection timestamps only | Full session log including every command |
| **Key management overhead** | Manual rotation, no tracking | None — IAM handles it |
| **Attack surface** | SSH port exposed to internet | No exposed port |
| **Compliance logging** | Requires additional tooling | Built-in via CloudWatch/S3 |

### The key insight

Session Manager does not change *what* you are doing — controlled admin access to a private resource. It changes the *mechanism*: from a network-layer control (firewall rules + key files) to an identity-layer control (IAM + full audit log). This is the direction AWS recommends for any production workload requiring EC2 admin access.

---

## Part 3 — The WAF Audit Format: Worked Example

Every pillar entry in your audit follows five steps. The Security pillar entry below — using the bastion host as the decision — is the complete worked example. Use it as the template for every entry you write.

### The five steps

| Step | What it asks |
|------|-------------|
| **1. Decision** | What did you choose to do? Name the specific resource, configuration value, or architectural choice. |
| **2. WAF Question** | What does this pillar ask you to evaluate? |
| **3. Current State** | What is actually in place right now? Be specific — resource names, permissions, config values. No adjectives. |
| **4. Gap Classification** | **Unknown Gap**, **Conscious Tradeoff**, or **Best Practice Met**? One sentence of justification. |
| **5. Improvement (ADR)** | Options → Decision → Reasoning. See below. |

---

### Worked entry — Security pillar

**1. Decision**
Lab 3 deployed an EC2 bastion with a security group allowing inbound SSH from `0.0.0.0/0` on port 22. The open rule was intentional — simplified access across student networks with unknown IP ranges.

**2. WAF Question**
*How do you protect your workloads from external threats? Are identities and credentials managed? Is there an audit trail for privileged access?*

**3. Current State**
Port 22 open to all IPs. Key-based SSH auth prevents password brute-force, but there is no key lifecycle management — no record of who holds the private key, no per-user revocation, no rotation enforcement. `auth.log` records connection timestamps but no commands executed during sessions.

**4. Gap Classification**
**Conscious Tradeoff.** The risk is known, the reason is documented (lab access across student networks with varying IP ranges), and the production fix is identified. A risk you can name, explain, and remediate is a Conscious Tradeoff. A risk you discover during the audit that you hadn't thought about is an Unknown Gap.

**5. Improvement — Architecture Decision Record**

> **Option 1 — Do nothing.**
> The current state is not without merit. SSH key-based authentication is a meaningful control — it requires physical possession of a private key, which is a stronger barrier than password-based access. The bastion pattern centralizes admin access to a single known entry point. These are real strengths worth acknowledging. The key lifecycle and session audit gaps are real, but with informal controls over access and rotation, and given that other findings in this audit may pose more immediate operational risk, deferring this work is defensible. This option accepts the current state and documents the known gaps explicitly.
>
> **Option 2 — Restrict the security group to a known IP range.**
> Change `0.0.0.0/0` to a CIDR range owned by NovaSpark (e.g., the corporate VPN range). This reduces the attack surface materially — only IPs on the NovaSpark network can attempt connections — while preserving the SSH key strengths already in place. The key lifecycle and session audit gaps remain open, but the exposure window is meaningfully narrower. A reasonable interim step if SSM adoption is on the roadmap but not yet resourced.
>
> **Option 3 — Eliminate SSH key-based access and implement AWS Systems Manager Session Manager.**
> Remove the inbound port 22 rule from the security group entirely. Install the SSM agent on the bastion instance, grant `ssm:StartSession` to authorized IAM identities, and enable session logging to CloudWatch Logs. This replaces a good control (SSH keys) with a better one (IAM identity), and closes the two gaps the current state leaves open: per-user revocation and a full session audit trail. Compromised access to EC2 instances — whether via a stolen key or an exploited SSH vulnerability — can provide a pivot point into the VPC and all resources inside it. At any stage of growth, that risk is worth eliminating when the remediation is low-friction.
>
> **Decision: Option 3.**
>
> **Reasoning:** The decision is not a rejection of the current state — SSH key-based auth is a real security control, and the bastion pattern is sound. The decision is that SSM Session Manager is strictly better across every dimension that matters: it retains the "requires deliberate action to gain access" property of SSH keys while adding per-user revocation, eliminating the exposed port, and providing the session audit trail the current state cannot. Moving from a good control to a better one is low-risk when the infrastructure is small. The key lifecycle problem only gets harder to remediate as the team grows and more people accumulate key copies — there is no benefit to deferring it.

---

## What Makes This Format Effective: Architecture Decision Records

Step 5 is written as an **Architecture Decision Record (ADR)**. This is a pattern used by engineering teams to document significant decisions in a structured, durable way. Understanding why it is the right format for a WAF audit will help you write stronger entries for your own five pillars.

### What an ADR is

An ADR captures four things:

1. **The context** — what situation prompted a decision
2. **The options considered** — the realistic alternatives, including doing nothing
3. **The decision** — which option was chosen
4. **The reasoning** — why that option over the others

The format exists because decisions made without documented reasoning are effectively invisible to anyone who joins the team later — or to the person who made them six months later. "We use SQS because it's better" tells you nothing. "We use SQS because a synchronous call would expose our customers to processor latency and make 202 semantics impossible to guarantee" tells you everything you need to know about whether that decision still applies.

### Why it matters for the WAF audit specifically

The WAF gap classifications — Unknown Gap, Conscious Tradeoff, Best Practice Met — only mean something if there is documentation behind them. Classifying the open security group as a Conscious Tradeoff is only credible if you can show:

- You knew the risk existed
- You evaluated the alternatives
- You made a deliberate choice and can state the reason

An ADR is exactly that evidence. A finding with a well-reasoned ADR is not just a better audit entry — it is what separates an architecture that has been thought about from one that just happened.

### Why "do nothing" is always an option

Including "do nothing" as Option 1 is not pessimism — it is honesty. Every engineering team has finite time and competing priorities. Acknowledging that "do nothing" is a legitimate choice (sometimes the right one) and then explaining why you chose differently demonstrates that your decision was deliberate rather than reflexive. A team that implements SSM because they thought about it is in a better position than one that implements it because it was the first thing in the tutorial.

### The standard ADR format for your audit entries

```
Option 1 — [Do nothing / accept current state]
[One paragraph: what this option accepts, why it might be defensible, what risk remains]

Option 2 — [Targeted improvement]
[One paragraph: what specifically changes, what gap it closes, what remains open]

Option 3 — [More complete solution, if applicable]
[One paragraph: what this fully addresses, why it might be deferred]

Decision: Option [N]

Reasoning: [One paragraph explaining why this option over the others, 
what would change the decision, and any preconditions or dependencies]
```

Not every finding requires three options — some have two realistic choices. What every finding requires is at least one alternative considered and a reason the chosen option won.
