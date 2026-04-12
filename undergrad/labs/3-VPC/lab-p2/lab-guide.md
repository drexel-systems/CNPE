# Lab 3, Part 2: SSH Patterns and NAT Verification

**Week:** 4
**Estimated Time:** 60–75 minutes
**Pulumi Directory:** `../lab-p1/` (same infrastructure as Part 1 — no new Pulumi code)

---

## The Scenario

You destroyed the infrastructure at the end of last week to save credits. Today you'll rebuild it in minutes and then do what you couldn't do yet in Part 1: get *inside* the network and prove it works the way you think it does.

Ben has one ask before you leave today:

> "I want to see you SSH into the private instance and show me the curl output from inside it. If the NAT Gateway is set up right, the IP address the internet sees should match the NAT EIP we exported from Pulumi. That's the proof."

That's the goal for today.

---

## Learning Objectives (Week 4)

By the end of Part 2, you will be able to:

- Use SSH agent forwarding to authenticate through a bastion host without copying private keys to a server
- SSH from a bastion host into a private instance with no public IP
- Prove a private instance has outbound internet access exclusively through NAT, with no inbound exposure
- Install software on a private instance to demonstrate NAT's real-world purpose
- Use `nc` to prove security groups enforce port-level access control even within the VPC
- Explain the SSH agent forwarding security model and why it's safer than copying `.pem` files

---

## Step 1: Rebuild the Infrastructure

> **Start this immediately when class begins** — the NAT Gateway takes 4–6 minutes to provision. Your instructor will cover objectives while it deploys.

```bash
cd lab-p1/
pulumi up
```

You should not need to re-init the stack — if you destroyed cleanly last week, Pulumi remembers your stack configuration. If you get an error about a missing stack, run:

```bash
pulumi stack init dev
pulumi config set aws:region us-east-1
pulumi up
```

Confirm with `yes`. While the deployment runs, make sure your SSH key is ready:

```bash
# Verify your key file is there
ls -la ~/.ssh/labsuser.pem
# Should show permissions and the file
```

When `pulumi up` completes, copy your outputs — you'll reference these throughout the lab:
```
bastionPublicDns  : "ec2-XX-XX-XX-XX.compute-1.amazonaws.com"
bastionPublicIp   : "XX.XX.XX.XX"
natEip            : "54.XX.XX.XX"            ← write this down
privateInstanceIp : "10.0.11.XXX"
sshCommand        : "ssh -A -i ~/.ssh/labsuser.pem ec2-user@..."
sshHopCommand     : "ssh ec2-user@10.0.11.XXX"
```

---

## Step 2: Set Up SSH Agent Forwarding

This is a new concept and it's worth understanding before you SSH anywhere.

**The problem:** You need to SSH from your laptop → bastion → private instance. Both hops require the `labsuser.pem` key. You could copy the `.pem` file onto the bastion, but then your private key is sitting on a server — if the bastion is compromised, so is the key.

**The solution: SSH Agent Forwarding.** You tell your local SSH agent to hold the key in memory. When you SSH to the bastion with the `-A` flag, the agent "forwards" its authentication capability to the bastion session. The bastion can then prove your identity to the private instance — without the actual key file ever leaving your laptop.

```
Your laptop          Bastion              Private Instance
(holds key)   ──▶   (no key!)  ────▶     (authenticated!)
                         ↑
              SSH Agent Forwarding bridges the gap
```

### On Mac / Linux

```bash
eval $(ssh-agent -s)
ssh-add ~/.ssh/labsuser.pem
```

Verify the key was added:
```bash
ssh-add -l
# Should show: 2048 SHA256:... /path/to/labsuser.pem (RSA)
```

**Take your D6 screenshot here** — `ssh-add -l` showing your key loaded.

### On Windows (Git Bash)

```bash
eval $(ssh-agent -s)
ssh-add ~/.ssh/labsuser.pem
```

### On Windows (PowerShell with OpenSSH)

```powershell
Start-Service ssh-agent
ssh-add "$env:USERPROFILE\.ssh\labsuser.pem"
```

---

## Step 3: SSH Into the Bastion and Verify Its Network

Use the `sshCommand` from your Pulumi output — it already includes the `-A` flag:

```bash
ssh -A -i ~/.ssh/labsuser.pem ec2-user@<your-bastion-dns>
```

Once connected, you'll see the Amazon Linux 2 prompt. Now verify the bastion's outbound IP:

```bash
curl -s https://checkip.amazonaws.com
```

The IP address returned should match `bastionPublicIp` from your Pulumi outputs. This traffic goes directly out through the Internet Gateway — the bastion is in a public subnet with a public IP.

**Take your D7 screenshot here** — the `curl` output showing the IP, alongside your terminal prompt that shows you're on the bastion. The IP must match your `bastionPublicIp` Pulumi output.

You can also check the default route to see where traffic flows:
```bash
ip route show default
# Output: default via 10.0.1.1 dev eth0
# 10.0.1.1 is the VPC router, which sends traffic to the Internet Gateway
```

---

## Step 4: Prove the Private Instance Has No Public IP

Before hopping to the private instance, let's confirm what the Pulumi outputs already implied: there's no way to reach it directly from the internet.

From your **local machine** (not the bastion — open a second terminal), try:

```bash
ssh -i ~/.ssh/labsuser.pem ec2-user@10.0.11.XXX
```

This will hang indefinitely (press Ctrl+C to cancel). The `10.0.11.x` address only exists inside the VPC. From the internet, there's no route to it — the packet never arrives.

Now hop over to the private instance from your bastion session:

```bash
# You're on the bastion — run this:
ssh ec2-user@10.0.11.XXX
```

Because you used `-A` when connecting to the bastion, your SSH agent's keys are forwarded. The bastion can authenticate you to the private instance without the `.pem` file ever being present on the bastion.

You're now inside a private EC2 instance — no public IP, not reachable from the internet.

Confirm your location:

```bash
# Show the instance's IP — should be a 10.0.11.x internal address
hostname -I
```

**Take your D8 screenshot here** — `hostname -I` from inside the private instance showing `10.0.11.x`.

Now check whether the instance has a public IP via the metadata service:

```bash
curl -s --max-time 3 http://169.254.169.254/latest/meta-data/public-ipv4 || echo "No public IP"
```

**Take your D9 screenshot here** — this command returning `No public IP` (or timing out). This confirms from *inside the instance* that AWS never assigned it a public address.

---

## Step 5: The Key Experiment — Verify the NAT Gateway

This is the proof Ben asked for. The private instance has no public IP, but it should be able to make outbound internet requests through the NAT Gateway. Let's verify.

```bash
# From inside the private instance:
curl -s https://checkip.amazonaws.com
```

You'll see an IP address. Now compare it to the `natEip` output from your Pulumi stack. **They must match.**

What you just demonstrated: the private instance made a request to an external service, that request was forwarded through the NAT Gateway, and the response came back — but from the internet's perspective, the request came from the NAT Gateway's Elastic IP, not from any instance. The private instance is invisible.

This is why companies use Elastic IPs on NAT Gateways: when you need to whitelist your outbound IP with a third-party API, you give them the NAT EIP. All your private instances share that single outbound identity, regardless of how many there are.

**Take your D10 screenshot here** — `curl -s https://checkip.amazonaws.com` from inside the private instance, with the returned IP clearly visible. You'll need to show this alongside your Pulumi outputs (in your submission, note which output it matches).

**Now prove NAT works for its actual real-world use case — package installation.** Private instances need to pull OS updates and install software. That traffic goes out through NAT, just like the curl did:

```bash
sudo dnf install -y tree
tree --version
```

You'll see `dnf` resolve package metadata from AWS repositories, download, and install — all through the NAT Gateway, with no public IP on this instance.

---

## Step 6: Security Group Defense-in-Depth Proof *(Extra Credit — 10 pts)*

You're still SSH'd into the private instance. This step proves that the security group is doing real work — not just the absence of a public IP. It is **optional** and worth 10 extra credit points.

The private SG only allows port 22 from `10.0.0.0/16`. All other ports are silently dropped, even from inside the VPC. Let's verify this from the bastion.

Open a new terminal and SSH into the bastion (without hopping to the private instance):

```bash
ssh -A -i ~/.ssh/labsuser.pem ec2-user@<your-bastion-dns>
```

Install `nc` (netcat) on the bastion — it is not present by default on Amazon Linux 2023:

```bash
sudo dnf install -y nmap-ncat
```

From the bastion, test a few ports on the private instance:

```bash
# Port 22 (SSH) — allowed by the private SG
nc -zvw 3 10.0.11.XXX 22
# Expected: "Connection to 10.0.11.XXX 22 port [tcp/ssh] succeeded!"

# Port 80 (HTTP) — NOT in the private SG rules
nc -zvw 3 10.0.11.XXX 80
# Expected: hangs then times out — the security group drops the packet silently

# Port 8080 — also NOT allowed
nc -zvw 3 10.0.11.XXX 8080
# Expected: same timeout
```

The difference between port 22 (succeeds) and port 80 (times out) is entirely the security group rule. The security group drops the packet before it even reaches the instance's network stack.

This is **defense in depth**: the network isolation (private subnet) and the access control (security group) are two independent layers. A misconfigured security group on a private instance does not suddenly expose it to the internet — both layers would need to fail.

**Take your D12 screenshot here (Extra Credit).** Capture your terminal showing both results: port 22 succeeding and port 80 timing out. Your prompt must confirm you are on the bastion (not inside the private instance). A single wide screenshot showing both `nc` commands and their output is ideal.

---

## Step 7: Exit and Clean Up

Exit both SSH sessions:

```bash
exit   # exits private instance → back to bastion
exit   # exits bastion → back to your machine
```

Then destroy all infrastructure:

```bash
cd lab-p1/
pulumi destroy
```

Confirm with `yes`. Watch the destruction order: instances first, security groups, route table associations, routes, route tables, then NAT Gateway (~2 minutes), then IGW, then subnets, then VPC.

**Take your D11 screenshot here** — `pulumi destroy` completion showing all resources destroyed with 0 errors.

**Verify the NAT Gateway is gone** in the AWS Console (VPC → NAT Gateways) before you leave.

> **Note:** If you opened a second terminal to SSH into the bastion in Step 6, exit that session too before running destroy.

---

## Troubleshooting

**`Permission denied (publickey)` on the SSH hop from bastion to private instance**
Your SSH agent wasn't running or the key wasn't added before you connected to the bastion. Exit the bastion, run `eval $(ssh-agent -s) && ssh-add ~/.ssh/labsuser.pem`, then reconnect with `ssh -A`.

**`curl: (6) Could not resolve host` from the private instance**
The NAT Gateway may not have fully initialized. Wait 30 seconds and try again. If it persists, check VPC → Route Tables → Private RT in the console and verify the `0.0.0.0/0 → nat-xxxx` route exists.

**Outbound IP from private instance does NOT match natEip**
Check which NAT Gateway is in the Private Route Table. Go to VPC → NAT Gateways and compare the Elastic IP column with your `natEip` output.

**`No public IP` check returns an IP instead**
The instance may have accidentally ended up in a public subnet. Check the instance's subnet in EC2 → Instances → your private instance → Subnet ID, and verify it matches one of the private subnet IDs from your Pulumi outputs.

**SSH connection to bastion times out after rebuild**
Wait 60 seconds after `pulumi up` completes — the instance may still be initializing. Verify the key: `chmod 400 ~/.ssh/labsuser.pem`.

---

## 📋 Part 2 Deliverables

**55 points total** (+ 10 pts optional extra credit — see D12 below). You need both the terminal context (which machine you're on) and the specific output to be visible in each screenshot.

| # | What to capture | Step | How to verify | Points |
|---|-----------------|------|---------------|--------|
| **D6** | Terminal: `ssh-add -l` showing `labsuser.pem` loaded in the agent | Step 2 | Must show the key fingerprint and filename | 5 |
| **D7** | Terminal: `curl -s https://checkip.amazonaws.com` from the **bastion** | Step 3 | Returned IP must match `bastionPublicIp` from Pulumi outputs | 10 |
| **D8** | Terminal: `hostname -I` from inside the **private instance** | Step 4 | Must show a `10.0.11.x` address — no public IP present | 10 |
| **D9** | Terminal: metadata check returning `No public IP` from private instance | Step 4 | `curl --max-time 3 http://169.254.169.254/.../public-ipv4` times out or returns nothing | 5 |
| **D10** | Terminal: `curl -s https://checkip.amazonaws.com` from the **private instance** | Step 5 | Returned IP must match `natEip` from Pulumi outputs — this is the key proof | 15 |
| **D11** | Terminal: `pulumi destroy` completing with 0 errors | Step 7 | Must show "X resources destroyed, 0 errors" | 10 |
| **D12 *(Extra Credit)*** | Terminal: `nc -zvw 3` from the **bastion** — port 22 succeeds, port 80 times out | Step 6 | Both results visible; prompt confirms you are on the bastion | +10 |
