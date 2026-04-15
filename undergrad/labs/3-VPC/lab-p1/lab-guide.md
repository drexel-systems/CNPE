# Lab 3, Part 1: Build and Understand Your Production VPC

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

Today you're building NovaSpark's real network — and understanding every piece of it.

---

## Learning Objectives (Week 3)

By the end of Part 1, you will be able to:

- Explain what a VPC is and why the AWS default VPC is not suitable for production
- Describe the difference between public and private subnets and what determines which is which
- Read a route table in the AWS Console and explain what each entry means
- Explain how an Internet Gateway and a NAT Gateway differ in purpose
- Compare the default VPC to a custom VPC and articulate the security difference
- Understand the bastion host pattern and why it exists
- Deploy a multi-subnet VPC with Pulumi and verify the architecture from the AWS Console

---

## Concepts First: The Network Architecture

Before writing any code, spend five minutes understanding what you're building. It will make the TODOs much clearer.

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

**NAT Gateway (Network Address Translation):** A one-way door for private subnets. Private instances can send outbound requests *through* the NAT Gateway to reach the internet (for OS updates, AWS APIs, etc.), but the internet cannot initiate connections *to* them. This is how a database server stays current without being directly reachable from the internet.

**Bastion Host:** A "jump server" in a public subnet whose only job is to be an SSH entry point. You SSH into the bastion first, then SSH from it to private instances. Private instances only need to allow SSH from within the VPC — not from the entire internet.

**Route Tables:** Every subnet is associated with a route table that tells network packets where to go. The key difference between public and private subnets is simply which route table they're associated with:

| Route Table | Destination | Target | Meaning |
|---|---|---|---|
| Public RT | `10.0.0.0/16` | local | VPC-internal traffic stays internal |
| Public RT | `0.0.0.0/0` | Internet Gateway | Everything else → internet (both directions) |
| Private RT | `10.0.0.0/16` | local | VPC-internal traffic stays internal |
| Private RT | `0.0.0.0/0` | NAT Gateway | Everything else → NAT (outbound only) |

> **Why four subnets if only two instances are deployed?**
> The Pulumi code creates subnets in two Availability Zones (AZ-A and AZ-B) — but the bastion, NAT Gateway, and private instance all land in AZ-A. The AZ-B subnets are empty for now. This is intentional. Production-grade VPC design always provisions subnets across at least two AZs up front, even before workloads need them. When you add a managed service later in the course — RDS, EKS, or a load balancer — those services require multi-AZ subnet groups and will consume both sets of subnets automatically. Building the scaffold now means you won't need to restructure the network later.
>
> **Why only one NAT Gateway?** In a real production environment you'd deploy one NAT Gateway per AZ. If AZ-A goes down, private instances in AZ-B would lose outbound internet access because their route points to a NAT Gateway that's unreachable. For this lab, one NAT Gateway is the right call — a second one doubles the cost to ~$0.09/hr on a $50 budget. It's a deliberate cost/availability tradeoff, and one worth knowing about.

---

## Step 1: Write the Code — Complete the TODOs in `__main__.py`

Open `lab-p1/__main__.py`. The public side of the infrastructure is fully provided as a working pattern. Your job is to complete the five TODOs that build the private side.

Read through the entire file before writing anything. The provided code is heavily commented — use it to understand what each resource does and why it's structured the way it is. The TODOs ask you to mirror the public side, so the pattern is right there to reference.

---

### TODO 1: Private Route Table

This is a `RouteTable` resource that belongs to the VPC. Look at how `public_rt` is defined a few lines above — the private version is identical except for the resource name and tags.

```python
private_rt = aws.ec2.RouteTable(
    "private-rt",
    vpc_id=vpc.id,
    tags={"Name": "NovaSpark-Private-RT", "Lab": "3"},
)
```

---

### TODO 2: Private Default Route

A route table without routes does nothing. You need to add the default route that sends all outbound traffic to the NAT Gateway.

The public version uses `gateway_id=igw.id`. For the private version, use `nat_gateway_id=nat_gateway.id` instead — that's the correct argument name when routing to a NAT Gateway.

```python
private_route = aws.ec2.Route(
    "private-default-route",
    route_table_id=private_rt.id,
    destination_cidr_block="0.0.0.0/0",
    nat_gateway_id=nat_gateway.id,   # <-- note: nat_gateway_id, not gateway_id
)
```

Why the different argument name? The Pulumi AWS provider distinguishes between the types of targets a route can point to: `gateway_id` is for Internet Gateways, `nat_gateway_id` is for NAT Gateways. Same concept, different properties.

---

### TODO 3: Private Route Table Associations

Associate the private route table with both private subnets. This is what makes a subnet "private" — not anything special about the subnet itself, but which route table tells its packets where to go.

Follow the exact pattern of `public-rt-assoc-a` and `public-rt-assoc-b`, swapping in the private subnet and route table variables:

```python
aws.ec2.RouteTableAssociation("private-rt-assoc-a",
    subnet_id=private_subnet_a.id,
    route_table_id=private_rt.id,
)

aws.ec2.RouteTableAssociation("private-rt-assoc-b",
    subnet_id=private_subnet_b.id,
    route_table_id=private_rt.id,
)
```

---

### TODO 4: Private Security Group

The private security group needs to allow SSH only from inside the VPC — not from the open internet. The key change from `bastion_sg` is in the `ingress` rule's `cidr_blocks`.

- `bastion_sg` uses `"0.0.0.0/0"` (anywhere) — the bastion is the internet-facing entry point
- `private_sg` uses `"10.0.0.0/16"` (VPC CIDR only) — nothing from outside the VPC can SSH in

The egress rule is the same for both: allow all outbound traffic (the private instance sends requests through the NAT Gateway).

```python
private_sg = aws.ec2.SecurityGroup(
    "private-sg",
    vpc_id=vpc.id,
    description="Private instance - SSH from within VPC only, no internet inbound",
    ingress=[{
        "protocol": "tcp",
        "from_port": 22,
        "to_port": 22,
        "cidr_blocks": ["10.0.0.0/16"],   # VPC CIDR only — not 0.0.0.0/0
        "description": "SSH from VPC CIDR only",
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
        "description": "All outbound - traffic goes through NAT Gateway",
    }],
    tags={"Name": "NovaSpark-Private-SG", "Lab": "3"},
)
```

---

### TODO 5: Private EC2 Instance

Create the private instance. It looks almost identical to the bastion — same AMI, same instance type, same key — but placed in the private subnet with the private security group.

```python
private_instance = aws.ec2.Instance(
    "private-instance",
    ami=ami.id,
    instance_type="t4g.micro",
    subnet_id=private_subnet_a.id,       # private subnet, not public
    vpc_security_group_ids=[private_sg.id],
    key_name="vockey",
    tags={"Name": "NovaSpark-Private", "Lab": "3", "Role": "Private"},
)
```

Note what's missing: there's no `associate_public_ip_address` argument. You don't need it — the private subnet already has `map_public_ip_on_launch=False`, so no public IP is ever assigned.

After completing TODO 5, **uncomment the two private instance output lines** at the bottom of the file:

```python
pulumi.export("privateInstanceIp", private_instance.private_ip)
pulumi.export("sshHopCommand", private_instance.private_ip.apply(
    lambda ip: f"ssh ec2-user@{ip}   # run this FROM the bastion, after SSH-ing in with -A"
))
```

---

## Step 2: Preview Your Infrastructure

Before deploying, ask Pulumi to show you exactly what it will create:

```bash
cd lab-p1/
pulumi stack init dev
pulumi config set aws:region us-east-1
pulumi preview
```

You should see approximately 20-21 resources listed:
- 1 VPC
- 4 subnets
- 1 IGW
- 1 EIP
- 1 NAT Gateway
- 2 route tables
- 4 route table associations
- 2 routes
- 2 security groups
- 2 EC2 instances

If you see fewer than 16, check that all five TODOs are complete and that the private instance outputs are uncommented.

If `pulumi preview` shows an error, read the error message carefully — it usually points directly to the resource and property with the problem.

---

## Step 3: Deploy the VPC

```bash
pulumi up
```

Confirm with `yes`.

> ⏱️ **Expected time: 4–6 minutes.** The NAT Gateway is the slow resource — AWS takes a couple of minutes to provision it. **Use this time productively:** while the deployment runs, move on to Step 4 and start exploring the AWS Console. You can switch back to your terminal to check on it.

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

## Step 4: Explore Route Tables in the AWS Console

Open the AWS Console → VPC → Route Tables (left sidebar).

Filter by the VPC you just created (look for names `NovaSpark-Public-RT` and `NovaSpark-Private-RT`, or filter by your VPC ID from the Pulumi output).

**Click on NovaSpark-Public-RT:**
- Under the **Routes** tab, you'll see two entries:
  - `10.0.0.0/16 → local` — VPC-internal traffic stays inside the VPC
  - `0.0.0.0/0 → igw-xxxx` — everything else goes to the Internet Gateway
- Under **Subnet Associations**, you'll see `public-subnet-a` and `public-subnet-b` listed

**Click on NovaSpark-Private-RT:**
- Routes tab: `10.0.0.0/16 → local` and `0.0.0.0/0 → nat-xxxx`
- Subnet Associations: `private-subnet-a` and `private-subnet-b`

This is the entire "public vs private subnet" distinction made concrete: same VPC, same instances, different route tables. The only thing that makes a subnet "private" is having its default route point to a NAT Gateway instead of an Internet Gateway.

**Take your D2 screenshot here** — the Private Route Table with both route entries visible.

---

## Step 5: Explore Security Groups in the AWS Console

Go to VPC → Security Groups (or EC2 → Security Groups) and find `NovaSpark-Bastion-SG` and `NovaSpark-Private-SG`.

Click on each and look at the **Inbound Rules** tab.

- Bastion SG: Source is `0.0.0.0/0` — SSH allowed from anywhere on the internet
- Private SG: Source is `10.0.0.0/16` — SSH only from within the VPC

These rules reflect the security intent you coded. The private instance's security group allows SSH from anywhere inside the VPC — the bastion is simply how you *get* inside the VPC.

---

## Step 6: Compare to the Default VPC

Ben said the default VPC is "not production-grade." Let's see exactly why.

In the AWS Console, navigate to **VPC → Your VPCs**. You'll see at least two VPCs: the one you just created (`NovaSpark-VPC`) and one simply named `default`. Click on the default VPC, then go to **Subnets** in the left sidebar and filter by the default VPC.

Notice what you see: every subnet listed is in a different AZ, but click on any one of them and look at the **Route Table** tab — you'll see `0.0.0.0/0 → igw-xxxx`.

**Every single subnet in the default VPC is public.** Any EC2 instance launched into the default VPC gets a public IP by default and is directly reachable from the internet — unless a security group blocks it. That's a single layer of defense for all your workloads with no network-level isolation between them.

Now look at your custom VPC's subnets:
- `public-subnet-a/b` → Route Table shows `0.0.0.0/0 → igw-xxxx`
- `private-subnet-a/b` → Route Table shows `0.0.0.0/0 → nat-xxxx`

Two different route tables. Two different threat profiles. This is what you built.

---

## Step 7: Architecture Reflection

Before cleaning up, think through these questions — they're your written deliverables for this part.

**Why does the NAT Gateway live in a public subnet?** The NAT Gateway needs to receive traffic from private instances AND forward it to the internet. Only public subnets have a route to the Internet Gateway — so the NAT Gateway must live there.

**What's the difference between an IGW and a NAT Gateway?** Both connect the VPC to the internet, but in different directions. The IGW is bidirectional — resources with public IPs can both receive inbound connections and initiate outbound ones. The NAT Gateway is outbound-only — private instances can initiate outbound requests, but the internet cannot initiate connections to them because there's no public IP to route to.

**What does "private" actually mean in AWS networking?** It means the subnet is associated with a route table that sends default traffic to a NAT Gateway instead of an Internet Gateway. There's no magic flag — it's purely a routing decision.

---

## Step 8: Cleanup — Destroy Before You Leave

```bash
pulumi destroy
```

Confirm with `yes`. Watch the destruction order: instances first, then security groups, then route tables, then NAT Gateway (~2 minutes to delete), then IGW, then subnets, then VPC.

> **Why we destroy now, not next week:** The NAT Gateway costs approximately **$0.045/hour** just to exist, plus data transfer fees. Leaving it running for a week costs each student ~$7 — on a $50 budget, that's 14% of your total credits for *one idle resource*. You'll rebuild in Part 2 at the start of class — `pulumi up` takes 4-6 minutes, and your instructor will cover objectives while it deploys.

**Take your D5 screenshot** — the `pulumi destroy` completion showing all resources destroyed with 0 errors.

**Verify the NAT Gateway is gone** in the AWS Console (VPC → NAT Gateways) before you leave. This is the resource that costs money when running.

---

## Troubleshooting

**`NameError: name 'private_rt' is not defined`**
You have a TODO that's still commented out. Check that all five TODOs are complete and that nothing is still wrapped in a comment block.

**`pulumi up` is stuck on NAT Gateway for more than 8 minutes**
This occasionally happens in AWS Academy. Press Ctrl+C, run `pulumi destroy`, wait for it to complete fully, then run `pulumi up` again.

**`pulumi preview` shows 0 resources**
Make sure you ran `pulumi stack init dev` first, and that `PULUMI_CONFIG_PASSPHRASE=""` is set in your environment.

**"No valid credential sources found"**
Your AWS Academy session expired. Refresh credentials from the AWS Academy portal and update `~/.aws/credentials`.

---

## 📋 Part 1 Deliverables

**45 points total.** Capture these during the lab — they cannot be recreated after `pulumi destroy`.

| # | What to capture | Step | How to verify | Points |
|---|-----------------|------|---------------|--------|
| **D1** | Terminal: `pulumi up` completing — must show all 16+ resources created and all 5 outputs (`bastionPublicDns`, `natEip`, `privateInstanceIp`, `sshCommand`, `sshHopCommand`) | Step 3 | Resource count visible, all outputs listed | 10 |
| **D2** | AWS Console: Private Route Table showing both routes (`10.0.0.0/16 → local` and `0.0.0.0/0 → nat-xxxx`) | Step 4 | Both entries clearly visible in the Routes tab | 10 |
| **D5** | Terminal: `pulumi destroy` completing with 0 errors | Step 8 | Must show "X resources destroyed, 0 errors" | 5 |

**Written responses — include in your submission PDF:**

| # | Question | Length | Points |
|---|----------|--------|--------|
| **D3** | What is the difference between an Internet Gateway and a NAT Gateway? Why can't private instances just use the Internet Gateway directly? | 3–5 sentences | 10 |
| **D4** | Why does the bastion host pattern exist? What problem does it solve, and what is one concrete improvement you could make to reduce the security risk the bastion itself introduces? | 3–5 sentences | 10 |

---

## What's Next

In **Part 2** (Week 4), you'll rebuild this infrastructure at the start of class and then do the hands-on proof: SSH agent forwarding, the bastion → private instance hop, and the key experiment — verifying that the private instance's outbound traffic exits through the NAT EIP.
