# Lab 2, Part 1: Your First Infrastructure Deployment

**Estimated Time:** 45–60 minutes
**Pulumi Directory:** `lab-p1/`

---

## The Scenario

It's your first week at **NovaSpark Technologies**, a scrappy cloud startup with big ambitions and a website that currently lives on someone's laptop. Your manager, Janet, stops by your desk:

> "Hey — I'm doing an investor demo next Thursday and I need to show them a live website on AWS. Nothing fancy. Just prove we can deploy to the cloud. Can you get something up today?"

You've got an EC2 instance, a terminal, and Pulumi. Let's go.

---

## Learning Objectives

By the end of Part 1, you will be able to:

- Explain what Pulumi is doing when you run `pulumi up`
- Deploy an EC2 instance using Infrastructure as Code
- SSH into a cloud instance and run a basic web server
- Understand what a security group is and why it matters
- Articulate the key difference between IaC and "clicking in the console"

---

## Before You Start

Make sure you've completed **`SETUP.md`** — particularly the `pulumi login --local` step and the `PULUMI_CONFIG_PASSPHRASE` environment variable. If you skip this, Pulumi will stop and ask you for a passphrase at every command.

Also verify your AWS credentials are active:
```bash
aws sts get-caller-identity
```
You should see your AWS account ID. If you get an error, refresh your AWS Academy session.

---

## Step 1: Write the Code — Complete the TODOs in `__main__.py`

Open `lab-p1/__main__.py`. The AMI lookup is provided at the top. Your job is to complete the two TODO sections.

**What's provided: AMI Lookup**
```python
ami = aws.ec2.get_ami(
    owners=["137112412989"],
    filters=[{"name": "image-id", "values": ["ami-0a101d355d07a638e"]}]
)
```
This finds a specific Amazon Machine Image — the OS "snapshot" your EC2 instance boots from. We're using Amazon Linux 2 (ARM64). The `owners` field is Amazon's official AWS account ID — we specify it to avoid accidentally pulling a community AMI with a similar name.

**TODO 1: Write the Security Group**

A security group is a virtual firewall. AWS blocks *all* inbound traffic by default — you must explicitly open the ports you need.

Write an `aws.ec2.SecurityGroup` resource that opens:
- Port 22 (SSH) — so you can connect
- Port 8080 (HTTP) — so you can view the website

Each ingress rule is a dict with: `protocol`, `from_port`, `to_port`, `cidr_blocks`, `description`. Use `0.0.0.0/0` for cidr_blocks to allow traffic from anywhere.

> **Why port 8080 and not port 80?** Port 80 requires root privileges to bind to. Running a web server as root is a security risk — port 8080 lets us run as a normal user.

**TODO 2: Write the EC2 Instance**

Write an `aws.ec2.Instance` resource with:
- `instance_type='t4g.micro'` — ARM Graviton. The `g` in `t4g` = Graviton. **This must match the ARM AMI** — using `t3.micro` (x86) with an ARM AMI will fail at launch.
- `ami=ami.id` — from the lookup above
- `vpc_security_group_ids=[sec_group.id]` — attach your security group
- `key_name='vockey'` — the pre-created key pair in your Learner Lab

**What's provided: Outputs**

The `pulumi.export(...)` lines at the bottom print your SSH command and website URL after deployment. They will error until you define `server` in TODO 2 — that's expected.

---

## Step 2: Preview the Deployment (Dry Run)

```bash
cd lab-p1/
pulumi stack init dev
pulumi config set aws:region us-east-1
pulumi install              # installs pulumi-aws and other Python packages
pulumi preview
```

`pulumi preview` is your "what would happen" command. It connects to AWS, figures out what needs to be created, and shows you a plan — without creating anything.

You should see output like:
```
Previewing update (dev):

     Type                      Name              Plan
 +   pulumi:pulumi:Stack       lab-p1-dev        create
 +   ├─ aws:ec2:SecurityGroup  ssh-access        create
 +   └─ aws:ec2:Instance       lab-instance      create

Resources:
    + 2 to create

Do you want to perform this update? [yes/no]:
```

The `+` symbols mean "will be created." Take a moment to verify the resource types and names match what you read in the code.

> **Habit to build:** Always run `pulumi preview` before `pulumi up`. This is your last chance to catch mistakes before real resources (and real costs) are created.

---

## Step 3: Deploy

```bash
pulumi up
```

When prompted, type `yes` to confirm.

You'll see Pulumi create resources in order — first the security group (because the instance needs it to exist first), then the instance. This automatic dependency resolution is one of the key features of IaC tools.

After a minute or two, you'll see:
```
Outputs:
    publicDns  : "ec2-XX-XX-XX-XX.compute-1.amazonaws.com"
    publicIp   : "XX.XX.XX.XX"
    sshCommand : "ssh -i ~/.ssh/labsuser.pem ec2-user@ec2-XX-XX-XX-XX..."
    websiteUrl : "http://ec2-XX-XX-XX-XX.compute-1.amazonaws.com:8080"
```

**Congratulations — you just deployed your first piece of cloud infrastructure with code.**

> **Sanity check:** Open the AWS Console, navigate to EC2 → Instances, and you should see your instance spinning up. Notice how every resource Pulumi created is tagged or named in a way that makes it identifiable. This is the IaC advantage — your code *is* your documentation.

---

## Step 4: SSH Into Your Instance

Copy the `sshCommand` output and run it. It will look like:

```bash
ssh -i ~/.ssh/labsuser.pem ec2-user@ec2-XX-XX-XX-XX.compute-1.amazonaws.com
```

If you get a `WARNING: UNPROTECTED PRIVATE KEY FILE` error:
```bash
chmod 400 ~/.ssh/labsuser.pem
```
Then try the SSH command again.

Once connected, you'll see the Amazon Linux 2 welcome banner. You're in.

---

## Step 5: Create the NovaSpark Website

Now let's build the website Janet wants. On the EC2 instance:

```bash
mkdir ~/website
cd ~/website
```

Create the homepage (`index.html`):

```bash
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovaSpark Technologies</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; }
        header { background: #1e293b; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #6366f1; }
        header .logo { font-size: 1.4rem; font-weight: 800; color: #6366f1; }
        nav a { color: #94a3b8; text-decoration: none; margin-left: 1.5rem; font-size: 0.9rem; }
        .hero { text-align: center; padding: 5rem 2rem; }
        .hero h1 { font-size: 2.8rem; font-weight: 800; margin-bottom: 1rem; }
        .hero h1 span { color: #6366f1; }
        .hero p { color: #94a3b8; font-size: 1.1rem; max-width: 520px; margin: 0 auto 2rem; line-height: 1.7; }
        .badge { display: inline-block; background: #6366f1; color: white; padding: 0.6rem 1.5rem; border-radius: 8px; font-weight: 600; text-decoration: none; }
        footer { background: #1e293b; text-align: center; padding: 1.5rem; color: #475569; font-size: 0.8rem; margin-top: 4rem; border-top: 1px solid #334155; }
    </style>
</head>
<body>
    <header>
        <div class="logo">⚡ NovaSpark</div>
        <nav><a href="index.html">Home</a><a href="about.html">About</a></nav>
    </header>
    <section class="hero">
        <h1>Cloud Infrastructure,<br><span>Automated.</span></h1>
        <p>We help engineering teams build, deploy, and scale cloud-native systems faster and safer than ever before.</p>
        <a href="about.html" class="badge">Meet the Team →</a>
    </section>
    <footer>
        <p>⚡ NovaSpark Technologies · Deployed on AWS EC2 · Part 1 of 3</p>
    </footer>
</body>
</html>
EOF
```

Create the About page (`about.html`):

```bash
cat > about.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About — NovaSpark</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; }
        header { background: #1e293b; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #6366f1; }
        header .logo { font-size: 1.4rem; font-weight: 800; color: #6366f1; }
        nav a { color: #94a3b8; text-decoration: none; margin-left: 1.5rem; font-size: 0.9rem; }
        .content { max-width: 700px; margin: 4rem auto; padding: 0 2rem; }
        h1 { font-size: 2rem; margin-bottom: 1rem; }
        p { color: #94a3b8; line-height: 1.8; margin-bottom: 1rem; }
        a { color: #6366f1; text-decoration: none; }
        footer { background: #1e293b; text-align: center; padding: 1.5rem; color: #475569; font-size: 0.8rem; margin-top: 4rem; border-top: 1px solid #334155; }
    </style>
</head>
<body>
    <header>
        <div class="logo">⚡ NovaSpark</div>
        <nav><a href="index.html">Home</a><a href="about.html">About</a></nav>
    </header>
    <div class="content">
        <h1>About NovaSpark</h1>
        <p>NovaSpark was founded by a team of platform engineers who believe infrastructure should be as well-crafted as the applications that run on it.</p>
        <p>Every resource in our stack is version-controlled, code-reviewed, and reproducible with a single command. We're an AWS-first shop using Pulumi for Infrastructure as Code.</p>
        <p><a href="index.html">← Back to Home</a></p>
    </div>
    <footer>
        <p>⚡ NovaSpark Technologies · Deployed on AWS EC2 · Part 1 of 3</p>
    </footer>
</body>
</html>
EOF
```

---

## Step 6: Start the Web Server

Python 3 is pre-installed on Amazon Linux 2. Start a simple HTTP server from inside your `website/` directory:

```bash
python3 -m http.server 8080
```

You'll see:
```
Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...
```

Leave this running and **open a second terminal** (don't close your SSH session).

---

## Step 7: Visit the NovaSpark Website

In a web browser, navigate to the `websiteUrl` from your Pulumi output:
```
http://ec2-XX-XX-XX-XX.compute-1.amazonaws.com:8080
```

Or test it from your local terminal:
```bash
curl http://ec2-XX-XX-XX-XX.compute-1.amazonaws.com:8080
```

You should see the NovaSpark homepage HTML. Try navigating to `about.html` as well.

> Congratulations — NovaSpark is online. Janet will be pleased.

When you see the request come in on your SSH terminal, you'll notice the server logging each hit:
```
ec2-XX-XX-XX-XX.compute-1.amazonaws.com - - [10/Mar/2026 ...] "GET / HTTP/1.1" 200 -
```

---

## Step 8: Stop and Think — What's the Problem?

Press `Ctrl+C` to stop the Python server. Go back to your SSH window and run:

```bash
ls ~/website/
```

The files are still there — stored on the EC2 instance's **local disk**.

Now ask yourself: **what happens to these files if...**
- The instance is rebooted for a security patch?
- The instance crashes and AWS replaces it automatically?
- You need to scale to two instances to handle traffic?
- Someone accidentally terminates the instance?

In all four cases, **your website disappears**. The content is tied to the instance. If the instance goes away, so does the site.

This is the problem Part 2 solves by separating compute (EC2) from storage (S3).

---

## Pulumi Concepts: What Did You Just Do?

Let's pause and internalize what Pulumi actually did when you ran `pulumi up`:

**Declarative Infrastructure:** You described *what* you wanted (an EC2 instance with certain properties), not *how* to create it. Pulumi figured out the "how" — what API calls to make, in what order.

**State Tracking:** Pulumi recorded everything it created in a local state file (`~/.pulumi/`). On the next `pulumi up`, it compares the desired state (your code) to the current state (what's actually in AWS) and only changes what's different.

**Dependency Resolution:** Pulumi knew to create the security group *before* the EC2 instance, because the instance references the security group. This automatic ordering is the difference between IaC and a shell script.

**Outputs:** The exported values (`sshCommand`, `websiteUrl`) are computed from the actual deployed resources — not hardcoded. This is why the DNS name in your output matched the real instance.

---

## Cleanup

**Important:** Always destroy resources when done with a lab to avoid charges.

First, stop the Python server (`Ctrl+C`) and exit your SSH session:
```bash
exit
```

Then from your local machine:
```bash
cd lab-p1/
pulumi destroy
```

Confirm with `yes` when prompted. You'll see Pulumi delete both the instance and the security group.

> **Notice:** `pulumi destroy` cleans up everything Pulumi created — in reverse dependency order (instance first, then security group). You don't have to remember what you created or hunt for it in the console.

---

## Troubleshooting

**SSH connection refused or times out**
The instance may still be starting up (takes 1-2 minutes). Also verify the key permissions: `chmod 400 ~/.ssh/labsuser.pem`

**Website not loading in browser**
Make sure the Python server is still running in your SSH session. Check the URL matches the `websiteUrl` output exactly (including port 8080). Verify you're using `http://` not `https://`.

**"pulumi: command not found"**
Pulumi isn't installed or isn't in your PATH. Revisit the course environment setup.

**"No valid credential sources found"**
Your AWS Academy session expired. Go back to the AWS Academy portal and start a new session, then copy the fresh credentials.

---

## What's Next

In **Part 2**, Janet comes back with a problem: the instance got rebooted for security patches and the entire website vanished. You'll discover why EC2 instances can't access AWS services by default, learn about the dangers of hard-coded credentials, and move the NovaSpark website to S3 — where it survives any instance lifecycle event.

---

## 📋 Part 1 Deliverables

**10 points total.** Capture these as you work — don't try to recreate them after the fact.

Each screenshot must show **your own deployment** (your DNS name, your instance IP, your terminal prompt).

| # | What to capture | How to verify | Points |
|---|-----------------|---------------|--------|
| **D1** | Terminal output of `pulumi up` completing successfully | Must show: all resources created, `publicIp`, `publicDns`, `sshCommand`, and `websiteUrl` outputs | 5 |
| **D2** | Browser screenshot of the NovaSpark homepage at `http://<your-dns>:8080` | Must show: full URL in address bar, page content visible | 5 |

> **Grader note:** D1 is pass/fail — either all 4 outputs are visible or not. D2 confirms the URL includes `:8080` and the correct DNS name.
