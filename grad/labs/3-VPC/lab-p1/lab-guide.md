# Lab 3, Part 1: Deploy and Understand Your Production VPC

**Week:** 3
**Estimated Time:** 60–75 minutes
**Pulumi Directory:** `lab-p1/`

---

## The Scenario

It's been a productive few weeks at NovaSpark. The investor demo went great, the website is running on S3, and Janet just gave you a longer to-do list. You grab coffee and find Ben waiting at your desk.

> "We need to talk about the network. Everything we've built so far is running in the **default VPC** that AWS automatically creates for new accounts. It works, but it's not production-grade — everything is in a flat public network with no isolation. If one service gets compromised, there's nothing stopping lateral movement to everything else."

He pulls up a diagram.

> "In a real production system, you have public subnets and private subnets. Load balancers and bastion hosts go in the public subnets — they're designed to face the internet. Application servers, databases, anything that processes data — they go in private subnets. They can call out to the internet for package updates, but nothing from the internet can reach them directly."

Linda appears over his shoulder.

> "And we need this in Pulumi. I'm not having someone click this together in the console."

Today you're deploying NovaSpark's real network — and justifying every decision in it.

---

## Learning Objectives (Week 3)

By the end of Part 1, you will be able to:

- Explain what a VPC is and why the AWS default VPC is not suitable for production
- Describe the difference between public and private subnets and what determines which is which
- Read a route table in the AWS Console and explain what each entry means
- Explain how an Internet Gateway and a NAT Gateway differ in purpose
- Compare the default VPC to a custom VPC and articulate the security difference
- Explain what NACLs are, how they differ from security groups, and when you'd use each
- Understand the bastion host pattern and why it exists
- Deploy a multi-subnet VPC with Pulumi and verify the architecture from the AWS Console

---

## Concepts First: The Network Architecture

Before touching any code, spend five minutes understanding what you're building. It will make the analysis much more grounded.

```
                        INTERNET
                            │
                            │ inbound & outbound
                            ▼
               ┌────────────────────────┐
               │   Internet Gateway     │
               │   (VPC's front door)   │
               └────────────┬───────────┘
                            │
               ╔════════════╧══════════════════════════╗
               ║          VPC  10.0.0.0/16             ║
               ║                                        ║
               ║  ┌─────────────────────────────────┐  ║
               ║  │  PUBLIC SUBNETS                  │  ║
               ║  │  10.0.1.0/24  (AZ-A)            │  ║
               ║  │  10.0.2.0/24  (AZ-B)            │  ║
               ║  │                                  │  ║
               ║  │  [Bastion EC2]  [NAT Gateway]   │  ║
               ║  └──────────┬──────────────┬────────┘  ║
               ║             │ SSH hop      │ outbound   ║
               ║             │              │ only       ║
               ║  ┌──────────▼──────────────┴────────┐  ║
               ║  │  PRIVATE SUBNETS                 │  ║
               ║  │  10.0.11.0/24 (AZ-A)            │  ║
               ║  │  10.0.12.0/24 (AZ-B)            │  ║
               ║  │                                  │  ║
               ║  │  [Private EC2]  [Future: DB]    │  ║
               ║  └──────────────────────────────────┘  ║
               ╚════════════════════════════════════════╝
```

**Internet Gateway (IGW):** The VPC's connection to the internet. Resources in public subnets with public IPs can both send and receive traffic through it.

**NAT Gateway (Network Address Translation):** A one-way door for private subnets. Private instances can send outbound requests *through* the NAT Gateway to reach the internet (for OS updates, AWS APIs, etc.), but the internet cannot initiate connections *to* them.

**Bastion Host:** A "jump server" in a public subnet whose only job is to be an SSH entry point. You SSH into the bastion first, then SSH from it to private instances.

**Route Tables:** Every subnet is associated with a route table that tells network packets where to go. The entire public/private distinction is a routing decision:

| Route Table | Destination | Target | Meaning |
|---|---|---|---|
| Public RT | `10.0.0.0/16` | local | VPC-internal traffic stays internal |
| Public RT | `0.0.0.0/0` | Internet Gateway | Everything else → internet (both directions) |
| Private RT | `10.0.0.0/16` | local | VPC-internal traffic stays internal |
| Private RT | `0.0.0.0/0` | NAT Gateway | Everything else → NAT (outbound only) |

---

## Step 1: Read and Annotate the Code Before You Deploy

Open `lab-p1/__main__.py`. The infrastructure is complete — your task before deploying is to read it carefully, understand every decision, and be prepared to justify each one. As you read, ask yourself:

- Why is this resource structured this way?
- What would break if this line were removed?
- What security assumption is embedded in this choice?

Work through each section with these questions in mind:

**Section 2 (VPC):** `enable_dns_hostnames=True` is set. What does this enable? What would a deployment look like without it?

**Section 3 (Subnets):** Private subnets use `.11.x` and `.12.x` rather than `.3.x` and `.4.x`. Why the gap? And what is the significance of `map_public_ip_on_launch=False` on private subnets — is this a security control, a configuration default, or both?

**Section 4 (Internet Gateway):** One line: `vpc_id=vpc.id`. The IGW is attached, but attaching it doesn't route any traffic. What else must exist for the IGW to actually be used?

**Section 5 (NAT Gateway):** `opts=pulumi.ResourceOptions(depends_on=[igw])` is set explicitly. Pulumi can often infer resource dependencies from code — why can't it infer this one? What does this tell you about implicit vs explicit dependencies in IaC?

**Section 6 (Route Tables):** The public and private route tables look almost identical in structure, but the `gateway_id` vs `nat_gateway_id` argument changes the entire traffic path. What is the operational consequence of accidentally swapping these?

**Section 7 (Security Groups):** Compare `bastion_sg` and `private_sg`. The private SG allows SSH from `10.0.0.0/16` — not from a specific bastion IP. Why is the rule written this broadly? What does this mean if another instance in the VPC is compromised?

**Section 8 (EC2 Instances):** Both instances use `key_name="vockey"`. There's no `associate_public_ip_address` on the private instance. Where does the public IP (or absence of it) actually get controlled?

> **Note:** The goal of this lab is to configure, deploy, and justify — not to write infrastructure from scratch. The code gives you the complete, working picture. Your analytical deliverables require you to explain the design decisions, not just describe what the resources are.

---

## Step 2: Deploy the VPC

```bash
cd lab-p1/
pulumi stack init dev
pulumi config set aws:region us-east-1
pulumi preview
```

Look at the preview carefully. You should see roughly 16 resources being created: VPC, 4 subnets, IGW, EIP, NAT Gateway, 2 route tables, 4 route table associations, 2 routes, 2 security groups, 2 EC2 instances.

```bash
pulumi up
```

Confirm with `yes`.

> ⏱️ **Expected time: 4–6 minutes.** The NAT Gateway is the slow resource — AWS takes a couple of minutes to provision it. **Use this time productively:** while the deployment runs, move on to Step 3 and start exploring the AWS Console.

When complete, note your outputs:
```
bastionPublicDns  : "ec2-XX-XX-XX-XX.compute-1.amazonaws.com"
natEip            : "54.XX.XX.XX"
privateInstanceIp : "10.0.11.XXX"
sshCommand        : "ssh -A -i ~/.ssh/labsuser.pem ec2-user@..."
sshHopCommand     : "ssh ec2-user@10.0.11.XXX  # run from bastion"
```

Notice what's **not** in the outputs: there's no `privateInstancePublicIp` or `privateInstanceDns`. That's not an oversight — the private instance simply doesn't have these. This is private subnet isolation working exactly as designed.

**Take your D1 screenshot here** (the full `pulumi up` terminal output with all outputs visible).

---

## Step 3: Explore Route Tables in the AWS Console

Open the AWS Console → VPC → Route Tables (left sidebar).

Filter by the VPC you just created (look for `NovaSpark-Public-RT` and `NovaSpark-Private-RT`, or filter by your VPC ID from Pulumi output).

**Click on NovaSpark-Public-RT:**
- Under the **Routes** tab: `10.0.0.0/16 → local` and `0.0.0.0/0 → igw-xxxx`
- Under **Subnet Associations**: `public-subnet-a` and `public-subnet-b`

**Click on NovaSpark-Private-RT:**
- Routes tab: `10.0.0.0/16 → local` and `0.0.0.0/0 → nat-xxxx`
- Subnet Associations: `private-subnet-a` and `private-subnet-b`

Now look at the `nat-xxxx` identifier in the Private RT. Navigate to VPC → NAT Gateways and find your NAT Gateway. Its ID should match the `nat-xxxx` in the route. Also note the Elastic IP column — it should match your `natEip` output. You're looking at the same resource from two different views.

**Take your D2 screenshot here** — the Private Route Table with both route entries visible.

---

## Step 4: Explore Security Groups in the AWS Console

Go to VPC → Security Groups and find `NovaSpark-Bastion-SG` and `NovaSpark-Private-SG`. Click on each and look at the **Inbound Rules** tab.

- Bastion SG: Source is `0.0.0.0/0` — SSH allowed from anywhere on the internet
- Private SG: Source is `10.0.0.0/16` — SSH only from within the VPC

Think about what the `10.0.0.0/16` source really means in practice. It's not "only the bastion" — it's "any resource inside the VPC." This is a deliberate tradeoff: overly specific rules (like allowing only the bastion's IP) break every time the bastion is replaced. The VPC CIDR is stable; the bastion's IP is not.

---

## Step 5: Compare to the Default VPC

Navigate to **VPC → Your VPCs**. Find the VPC named `default` (every AWS account has one). Click on it, then go to Subnets and filter by the default VPC.

Click on any default subnet and look at the **Route Table** tab — you'll see `0.0.0.0/0 → igw-xxxx`. Every default VPC subnet is public. Any EC2 instance launched into the default VPC gets a public IP by default and is reachable from the internet unless a security group blocks it. That's one layer of defense — security groups only — for all workloads with no network-level isolation between them.

Your custom VPC adds a second layer: subnet placement. A misconfigured security group on a private instance doesn't suddenly expose it to the internet, because the route table has no path there.

> **The default VPC is a great sandbox tool. It is never appropriate for production workloads.**

---

## Step 6: Explore NACLs — The Subnet-Level Firewall

Security groups operate at the **instance level** — they filter traffic to and from individual EC2 instances. Network Access Control Lists (NACLs) operate at the **subnet level** — they filter all traffic crossing the subnet boundary.

Navigate to **VPC → Network ACLs** and find the NACL associated with your custom VPC.

Click on it and look at the **Inbound Rules** and **Outbound Rules** tabs. You'll see the default NACL allows all traffic in both directions — rule 100 allows everything.

Key differences between NACLs and security groups:

| | Security Groups | NACLs |
|---|---|---|
| **Level** | Instance | Subnet |
| **State** | Stateful — return traffic is auto-allowed | Stateless — return traffic needs its own rule |
| **Rules** | Allow only | Allow or Deny |
| **Order** | All rules evaluated | Lowest number first, first match wins |
| **Default** | Deny all inbound | Allow all (default NACL) |

The **stateless** nature of NACLs is the most important thing to internalize. If you add an inbound rule allowing port 443, you must also add an outbound rule allowing the response back — typically on ephemeral ports 1024–65535. Security groups handle this automatically; NACLs do not.

In most architectures, NACLs are left at their default (allow all) and security groups do the real work. In highly regulated environments, NACLs add a second independent layer — a NACL `DENY` rule can catch traffic that a misconfigured security group might accidentally allow.

---

## Step 7: Architecture Reflection

Before cleaning up, work through these questions — they're the foundation of your written deliverables.

**Why does the NAT Gateway live in a public subnet?** The NAT Gateway needs to receive traffic from private instances AND forward it to the internet. Only public subnets have a route to the Internet Gateway — so the NAT Gateway must live there. A NAT Gateway in a private subnet has no path to the internet and is nonfunctional.

**What if someone adds a new EC2 instance to a private subnet?** It automatically gets the private subnet's route table — NAT access only, not reachable from the internet. Subnet placement is itself a form of access control, independent of any security group configuration.

**What is the security risk the bastion introduces?** The bastion has port 22 open to `0.0.0.0/0`. Any vulnerability in the SSH daemon, the OS, or the configuration becomes a potential entry point into the VPC. The bastion is a necessary compromise — it's the trade-off for being able to SSH into private instances at all. Mitigation options include: restricting the bastion SG to specific office/VPN CIDR ranges, or replacing SSH entirely with AWS Systems Manager Session Manager (which needs no inbound port 22 at all).

---

## Step 8: Cleanup — Destroy Before You Leave

```bash
pulumi destroy
```

Confirm with `yes`. Watch the destruction order: instances first, then security groups, then route tables, then NAT Gateway (~2 minutes to delete), then IGW, then subnets, then VPC.

> **Why we destroy now, not next week:** The NAT Gateway costs approximately **$0.045/hour** just to exist. Leaving it running for a week costs ~$7 on a $50 credit budget. You'll rebuild at the start of Part 2 — `pulumi up` takes 4-6 minutes.

**Take your D5 screenshot** — the `pulumi destroy` completion showing all resources destroyed with 0 errors.

**Verify the NAT Gateway is gone** in the AWS Console (VPC → NAT Gateways) before you leave.

---

## Troubleshooting

**`pulumi up` is stuck on NAT Gateway for more than 8 minutes**
This occasionally happens in AWS Academy. Press Ctrl+C, run `pulumi destroy`, wait for it to complete fully, then run `pulumi up` again.

**`pulumi preview` shows 0 resources**
Make sure you ran `pulumi stack init dev` first, and that `PULUMI_CONFIG_PASSPHRASE=""` is set in your environment.

**"No valid credential sources found"**
Your AWS Academy session expired. Refresh credentials from the AWS Academy portal and update `~/.aws/credentials`.

---

## 📋 Part 1 Deliverables

**45 points total.** Capture these during the lab — they cannot be recreated after `pulumi destroy`.

| # | What to capture | Step | Points |
|---|-----------------|------|--------|
| **D1** | Terminal: `pulumi up` completing — 16+ resources created, all 5 outputs visible | Step 2 | 10 |
| **D2** | AWS Console: Private Route Table showing both routes (`10.0.0.0/16 → local` and `0.0.0.0/0 → nat-xxxx`) | Step 3 | 10 |
| **D5** | Terminal: `pulumi destroy` completing with 0 errors | Step 8 | 5 |

**Analytical deliverables — include in your submission PDF. Full prompts are in the README.**

| # | Question | Length | Points |
|---|----------|--------|--------|
| **D3** | What is the difference between an Internet Gateway and a NAT Gateway? Why can't private instances just use the Internet Gateway directly? | 3–5 sentences | 10 |
| **D4** | Why does the bastion host pattern exist? What problem does it solve, and what is one concrete improvement you could make to reduce the security risk the bastion itself introduces? | 3–5 sentences | 10 |

---

## What's Next

In **Part 2** (Week 4), you'll rebuild this infrastructure at the start of class and then do the hands-on proof: SSH agent forwarding, the bastion → private instance hop, and the key experiment — verifying that the private instance's outbound traffic exits through the NAT EIP. The abstract networking concepts from today become concrete and observable.
