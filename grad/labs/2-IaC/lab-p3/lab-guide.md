# Lab 2, Part 3: Full Automation with Pulumi

**Estimated Time:** 45–60 minutes
**Pulumi Directory:** `lab-p3/`

---

## The Scenario

It's three weeks after the investor demo. NovaSpark got funded. Janet calls you into a meeting with Ben and Linda.

> "We're expanding. We need a dev environment, a staging environment, and production running by end of month. Two new engineers are joining next week. Every time we spin up a new environment, it takes you 45 minutes of manual SSH commands — and last time Ben did it, it came up wrong because he missed a step. I need this to be one command. No manual steps. No SSH required to get it running."
>
> Ben nods. "Immutable infrastructure. The instance should come up fully configured, automatically."
>
> Linda adds: "And if we have to SSH in to fix something, that's a smell. The bootstrapping should be in code."

This is the moment Pulumi was built for.

---

## Learning Objectives

By the end of Part 3, you will be able to:

- Explain what `user_data` is and how it acts as a server bootstrap mechanism
- Describe how Pulumi manages resource dependencies automatically
- Deploy a complete, production-pattern infrastructure with a single command
- Make infrastructure changes and understand how Pulumi handles partial updates
- Clean up an entire environment with `pulumi destroy`
- Articulate the concrete business value of Infrastructure as Code

---

## What You'll Build

Everything from Part 2, fully automated:

```
pulumi up
    │
    ├── S3 Bucket  ──────────────────────────────────────────────┐
    │     └── uploads index.html, about.html from website/        │
    │                                                              │
    ├── IAM Role + Instance Profile                               │
    │     └── grants EC2 permission to read the bucket            │
    │                                                              │
    └── EC2 Instance (t4g.micro)                                  │
          ├── IAM profile attached                                 │
          └── user_data script runs on boot:                      │
                ├── installs boto3                                  │
                ├── writes s3_webserver.py                         │
                ├── configures systemd service with BUCKET ────────┘
                └── starts the service

~90 seconds later: website is live, no SSH required
```

---

## Before You Start

Make sure you've run `pulumi destroy` in `lab-p2/` — you don't want two instances running. Then verify your environment:

```bash
export PULUMI_CONFIG_PASSPHRASE=""
aws sts get-caller-identity
```

---

## Step 1: Explore the Project Structure

Look at what's in `lab-p3/`:

```
lab-p3/
├── __main__.py        ← The Pulumi program (read this carefully!)
├── Pulumi.yaml        ← Project metadata
├── requirements.txt   ← Python dependencies (pulumi, pulumi-aws)
├── s3_webserver.py    ← The web server script (will be deployed to EC2)
└── website/
    ├── index.html     ← NovaSpark homepage
    └── about.html     ← About page
```

This structure is the full picture: the Pulumi code, the web server, and the website content all live together. Everything Pulumi needs to provision a complete environment is in this directory.

---

## Step 2: Read `__main__.py` — All of It

Open `lab-p3/__main__.py`. Walk through each section:

**The S3 Bucket**
```python
bucket = aws.s3.BucketV2("novaspark-website", force_destroy=True, ...)
```
Notice `force_destroy=True` — this lets `pulumi destroy` empty and delete the bucket in one step. In Part 2, you had to manually `aws s3 rm` before destroying. In production, you'd probably leave this off (safety net), but for a lab it's convenient.

**File Uploads**
```python
for filename, content_type in website_files.items():
    aws.s3.BucketObject(filename, bucket=bucket.id,
        source=pulumi.FileAsset(os.path.join("website", filename)), ...)
```
Pulumi reads the local `website/` directory and uploads each file to S3. On the first `pulumi up`, both files are uploaded. On subsequent runs, Pulumi hashes each file and only re-uploads files that have actually changed. This is the `FileAsset` type at work — it tracks file contents, not just filenames.

**IAM Role and Policy**
Same structure as Part 2 — but now it's all defined in code that you can review, version-control, and share. Linda from the security team can review the exact permissions in a pull request. No one has to click through the IAM console to figure out what the role does.

**The `make_user_data` Function — Key Concept**
```python
def make_user_data(bucket_name: str) -> str:
    with open("s3_webserver.py", "r") as f:
        server_script = f.read()
    return f"""#!/bin/bash
    ...
    cat > /home/ec2-user/s3_webserver.py << 'PYEOF'
    {server_script}
    PYEOF
    ...
    Environment=S3_BUCKET_NAME={bucket_name}
    ...
    systemctl enable novaspark-web.service
    systemctl start novaspark-web.service
    """
```

This function is called with the actual S3 bucket name (which Pulumi only knows after the bucket is created) and returns a bash script. Pulumi passes this script to EC2 as `user_data`.

**The EC2 Instance**
```python
user_data = bucket.id.apply(make_user_data)

server = aws.ec2.Instance("novaspark-server",
    ...
    iam_instance_profile=instance_profile.name,
    user_data=user_data,
    user_data_replace_on_change=True,
)
```

Notice `bucket.id.apply(make_user_data)` — this is Pulumi's way of saying "once you know the bucket's actual ID, call `make_user_data` with it and use the result as `user_data`." Pulumi handles the async dependency automatically. `user_data_replace_on_change=True` means if you change the user_data script, Pulumi will replace the instance (which is the correct behavior for immutable infrastructure).

---

## Step 3: What Is `user_data`?

`user_data` is a feature of EC2 that lets you run a script **once, as root, when the instance first boots**. It's the standard mechanism for "bootstrapping" — installing software, configuring services, and starting processes automatically.

The script Pulumi generates does five things:

1. Installs `python3-pip` and `boto3`
2. Writes `s3_webserver.py` to `/home/ec2-user/`
3. Creates a systemd service unit at `/etc/systemd/system/novaspark-web.service`
4. Injects the S3 bucket name as an `Environment=` line in the service file
5. Enables and starts the service

The `systemd` part is important: by creating a proper service, the web server will **restart automatically if it crashes**, and will **start again on instance reboot**. It's not just a process you started in a terminal — it's a managed service.

---

## Step 4: Deploy Everything

```bash
cd lab-p3/
pulumi stack init dev
pulumi config set aws:region us-east-1
pulumi preview
```

Look at the preview carefully. You should see:
- 2 S3 BucketObjects (index.html and about.html)
- 1 BucketPublicAccessBlock
- 1 BucketV2 (the bucket itself)
- 1 InstanceProfile
- 1 Role
- 1 RolePolicy
- 1 SecurityGroup
- 1 Instance

That's 9+ resources created automatically, in the right order, with the right dependencies. Compare that to Part 2 where you spent 45 minutes doing this manually.

```bash
pulumi up
```

Confirm with `yes`. Watch the output as resources are created. You'll notice Pulumi creates them in dependency order — S3 bucket before bucket objects, role before instance profile, instance profile before EC2 instance.

---

## Step 5: Wait for Bootstrap (~90 Seconds)

After `pulumi up` completes, the EC2 instance exists — but the `user_data` script is still running inside it. It needs to install packages and start the service.

`user_data` runs asynchronously after instance launch. Pulumi doesn't wait for it — it just sends the script and marks the instance as ready.

**Wait about 90 seconds**, then test:

```bash
# Get the website URL from Pulumi outputs
pulumi stack output websiteUrl
```

Open that URL in a browser, or test it with curl:
```bash
curl http://$(pulumi stack output publicDns):8080
```

If you get a "connection refused," wait another 30 seconds and try again. The instance is still bootstrapping.

---

## Step 6: Verify Without SSH — Look at the Outputs

Once the site loads, check what Pulumi exported:

```bash
pulumi stack output
```

You should see all your outputs:
```
Current stack outputs (5):
    OUTPUT          VALUE
    bucketName      novaspark-website-xxxxxxxx
    checkBootstrap  ssh -i ~/.ssh/labsuser.pem ec2-user@... 'sudo journalctl ...'
    publicDns       ec2-XX-XX-XX-XX.compute-1.amazonaws.com
    publicIp        XX.XX.XX.XX
    sshCommand      ssh -i ~/.ssh/labsuser.pem ec2-user@...
    websiteUrl      http://ec2-XX-XX-XX-XX.compute-1.amazonaws.com:8080
```

The `checkBootstrap` output is a pre-built command to view the service logs without having to remember the systemd command. Run it if you want to see the bootstrap log:

```bash
eval "$(pulumi stack output checkBootstrap)"
```

You should see something like:
```
=== NovaSpark Bootstrap Starting ===
Bucket: novaspark-website-xxxxxxxx
...
=== NovaSpark Bootstrap Complete ===
Web server started. Check: systemctl status novaspark-web
```

---

## Step 7: Understand the Power — Make a Change

Here's where IaC becomes truly impressive. Let's update the website.

**On your local machine** (not SSH), edit `lab-p3/website/index.html`. Find the footer line and change "Part 3 of 3" to something else, or add a new feature card. Save the file.

Now run:
```bash
pulumi preview
```

Look at the preview output. You'll see something like:
```
~   aws:s3:BucketObject  index.html  update
```

Pulumi hashed the file, detected the change, and knows *only* `index.html` needs to be updated. The EC2 instance, IAM role, and S3 bucket are untouched.

```bash
pulumi up
```

After Pulumi finishes (in seconds), reload the website. Your change is live. No SSH. No file copying. No server restarts.

---

## Step 8: Try Adding a Page

Create a new file locally:
```bash
cat > lab-p3/website/contact.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Contact — NovaSpark</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; }
        header { background: #1e293b; padding: 1rem 2rem; display: flex; justify-content: space-between; border-bottom: 2px solid #6366f1; }
        .logo { font-size: 1.4rem; font-weight: 800; color: #6366f1; }
        nav a { color: #94a3b8; text-decoration: none; margin-left: 1.5rem; font-size: 0.9rem; }
        .content { max-width: 600px; margin: 4rem auto; padding: 0 2rem; }
        h1 { font-size: 2rem; margin-bottom: 1rem; }
        p { color: #94a3b8; line-height: 1.8; margin-bottom: 1rem; }
        .email { color: #6366f1; font-size: 1.1rem; font-weight: 600; }
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
        <h1>Get in Touch</h1>
        <p>Interested in working with NovaSpark? We'd love to hear from you.</p>
        <p class="email">hello@novaspark.io</p>
        <p style="margin-top: 2rem;"><a href="index.html">← Back to Home</a></p>
    </div>
    <footer>⚡ NovaSpark Technologies</footer>
</body>
</html>
EOF
```

You also need to add it to the `website_files` dictionary in `__main__.py`:

```python
website_files = {
    "index.html": "text/html",
    "about.html": "text/html",
    "contact.html": "text/html",    # add this line
}
```

Then:
```bash
pulumi up
```

Pulumi uploads only `contact.html`. Then visit:
```
http://<your-dns>:8080/contact.html
```

The web server fetches it from S3 on demand — no server restart, no SSH, no downtime.

---

## Step 9: The Cleanup — `pulumi destroy`

When you're done:

```bash
pulumi destroy
```

Because `force_destroy=True` is set on the bucket, Pulumi will automatically empty the bucket and delete it, then tear down all other resources in the correct reverse-dependency order.

Watch the output. In roughly 60 seconds, all 9+ resources are gone. The AWS account is clean.

> In Part 2, cleanup required:
> - SSH into instance to stop server
> - Manually empty S3 bucket with `aws s3 rm`
> - Verify bucket was empty
> - Run `pulumi destroy`
>
> In Part 3: just `pulumi destroy`. That's it.

---

## The Full Picture: Parts 1, 2, and 3 Compared

| Aspect | Part 1 | Part 2 | Part 3 |
|---|---|---|---|
| **Content lives on...** | EC2 local disk | S3 | S3 |
| **Credentials** | None | IAM role (manual) | IAM role (automated) |
| **Deploy time** | 45 min | 60 min | 5 min |
| **Reproducible?** | ❌ | Partially | ✅ 100% |
| **SSH required?** | Yes | Yes | No |
| **Version controlled?** | Partially | Partially | Fully |
| **New engineer onboarding** | "Here's a 20-step doc" | "Here's a 30-step doc" | `git clone && pulumi up` |
| **Cleanup** | Manual | Semi-manual | `pulumi destroy` |
| **Survives instance replacement?** | ❌ | ✅ | ✅ |
| **Multiple envs from same code?** | ❌ | Difficult | `pulumi stack init staging` |

---

## Key Concepts to Internalize

**Immutable Infrastructure:** The Part 3 instance is configured at boot, never modified by hand. If you need to change something, you change the code and replace the instance. This eliminates the "configuration drift" problem — where servers gradually diverge from each other through manual changes.

**Idempotency:** Run `pulumi up` ten times and you get the same result each time. Pulumi only changes what's different. This makes deployment safe to repeat.

**Dependency Graph:** Pulumi builds an internal graph of resource dependencies and creates them in the correct order. You declare *what* you want; Pulumi figures out *how* to get there.

**`user_data` as Code:** Treating the bootstrap script as part of your codebase means it gets reviewed, versioned, and tested like everything else. No more "I think someone installed X on that server once."

**Environment Variables as Configuration:** The bucket name is passed to the web server via a systemd `Environment=` directive — not hardcoded in the Python script. The same `s3_webserver.py` script works in any environment. Only the service configuration changes.

---

## Troubleshooting

**Website returns "connection refused" after `pulumi up`**
The user_data script is still running. Wait 60-90 seconds and try again. Run `pulumi stack output checkBootstrap` to view the bootstrap log.

**Website returns a 403 error**
The IAM role may not have propagated fully. Wait 30 seconds. Also verify the bucket name in `S3_BUCKET_NAME` (visible in the journalctl logs) matches the actual bucket.

**Bootstrap seems stuck**
SSH in using `pulumi stack output sshCommand` and check:
```bash
sudo journalctl -u novaspark-web -n 50
sudo cat /var/log/user-data.log
```

**"No module named boto3"**
The bootstrap might have failed before installing boto3. Check `/var/log/user-data.log` for errors.

**`pulumi up` fails with "BucketNotEmpty"**
Make sure `force_destroy=True` is set on the bucket in `__main__.py`, or manually empty the bucket first.

---

## Reflect: What Did You Just Build?

You deployed:
- A globally unique S3 bucket
- A least-privilege IAM role scoped to that specific bucket
- An EC2 instance that self-configures at boot
- A web server that serves content from S3 using temporary, auto-rotating credentials
- A complete environment that any engineer can replicate in 5 minutes

With a single command. Without touching the AWS Console. Without SSHing into anything.

That is modern cloud engineering.

---

## 📋 Part 3 Deliverables

**Screenshots (proof of deployment):**

| # | What to capture | Step | How to verify | Points |
|---|-----------------|------|---------------|--------|
| **D9** | Terminal: `pulumi up` completing with 9+ resources | Step 4 | Must show resource count and all outputs including `checkBootstrap` | 5 |
| **D14** | Terminal: `pulumi destroy` completion for **all 3 parts** | Cleanup | 3 separate screenshots, each showing 0 errors | 5 |

**Analytical deliverable (from the README):**

D12 is the primary analytical deliverable for Part 3. See the [README](../README.md) for the exact prompt and rubric.

| # | Focus | Points |
|---|-------|--------|
| **D12** | Automation analysis: compare Parts 1/2/3; evaluate `user_data_replace_on_change=True` implications | 15 |

**Context Paragraph (CP):**

After completing all three parts and the written deliverables, write your context paragraph. See [`context-paragraph-prompt.md`](../context-paragraph-prompt.md) for the full prompt and grading scale.

| # | Focus | Points |
|---|-------|--------|
| **CP** | Connect one concept from this week's reading to one specific observation from the lab | 25 |

> **Grader note:** D12 earns full credit when it addresses both the comparison across all three parts AND the specific implications of `user_data_replace_on_change=True` as an architectural guarantee. The context paragraph earns full credit only when it makes a specific, original connection — not a surface-level mention of both sources.
