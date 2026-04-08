# Lab 2, Part 2: S3, IAM, and the Right Way to Handle Credentials

**Estimated Time:** 60–90 minutes
**Pulumi Directory:** `lab-p2/`
**Web Server Script:** `lab-p3/s3_webserver.py`

---

## The Scenario

You showed Janet the website from Part 1. She was impressed — for about five minutes. Then Ben from Platform walked by and said, *"You should apply the latest security patches to that instance."* You rebooted. The website vanished.

Janet appears at your desk.

> "The site went down when the instance restarted. All our content was stored directly on the server — that's a single point of failure. I need the website content separate from the compute. And I need it up before the investor demo on Thursday."

She heads to a meeting. Ben leans over and says, *"S3. Move the content to S3. Also please don't hardcode any credentials."*

Welcome to Part 2.

---

## Learning Objectives

By the end of Part 2, you will be able to:

- Explain why EC2 instances cannot access S3 by default (and why that's a good thing)
- Describe what an IAM Role and Instance Profile are and how they differ
- Articulate why hardcoded AWS credentials are dangerous
- Upload files to S3 and verify access using the AWS CLI
- Run a Python web server that fetches content from S3 using IAM role credentials
- Read `aws configure list` to understand where credentials are coming from

---

## What This Part Covers

```
Part 1 Architecture (broken):
  Browser → EC2 → Serves files from local disk
               ↓ instance reboots
             website gone

Part 2 Architecture (what we're building):
  Browser → EC2 → Python Server → S3 (content lives here safely)
               ↑
         IAM Role grants access to S3
```

---

## Before You Start

Make sure you've run `pulumi destroy` from `lab-p1/` — don't leave old resources running. Then verify your AWS session is still active:

```bash
aws sts get-caller-identity
```

---

## Step 1: Write the Part 2 Code — Complete the TODOs in `__main__.py`

Open `lab-p2/__main__.py`. The AMI lookup and security group are provided (same as Part 1). You need to write five new pieces. Here's what each one is and why it exists:

**TODO 1: S3 Bucket**

Create an `aws.s3.BucketV2` resource named `"novaspark-website"`. Pulumi appends a random suffix to ensure global uniqueness. Also add an `aws.s3.BucketPublicAccessBlock` that blocks all public access — the instance will read from S3 via its IAM role, not via public URL.

Notice `force_destroy` is NOT set — you'll have to empty the bucket manually before `pulumi destroy`. This is intentional: it teaches the cleanup step.

**TODO 2: IAM Role**

An IAM Role is a set of permissions that can be *assumed* by an AWS service. You need to define an `assume_role_policy` — a JSON document that says WHO can assume this role. The Principal should be the EC2 service: `{"Service": "ec2.amazonaws.com"}`. The role itself does nothing until a policy is attached.

**TODO 3: IAM Role Policy**

Attach a policy to the role granting `s3:ListBucket` and `s3:GetObject` on your bucket only. Do NOT grant `s3:PutObject` or `s3:DeleteObject` — read-only is all the web server needs. This is "least privilege."

Use `.apply()` to substitute the real bucket name into the policy ARN at deploy time:
```python
policy=bucket.id.apply(lambda name: json.dumps({...}))
```

**TODO 4: IAM Instance Profile**

Here's a detail that trips up many engineers: **you cannot attach an IAM Role directly to an EC2 instance.** EC2 requires an Instance Profile — a wrapper that holds exactly one role. Think of the role as a job description and the instance profile as the ID badge that lets someone walk through the door.

Create `aws.iam.InstanceProfile("ec2-instance-profile", role=role.name, ...)`.

**TODO 5: EC2 Instance with Profile Attached**

Same as Part 1, with one addition: `iam_instance_profile=instance_profile.name`. This single line transforms the instance from "no AWS access at all" to "receives temporary, scoped credentials automatically via the metadata service."

---

## Step 2: Deploy the Part 2 Infrastructure

```bash
cd lab-p2/
pulumi stack init dev
pulumi config set aws:region us-east-1
pulumi preview    # review before you commit
pulumi up
```

You should see 7+ resources being created (more than Part 1, because of the IAM pieces and S3 bucket). Watch the dependency order — Pulumi creates the role before the instance profile, and the instance profile before the EC2 instance.

Copy the outputs:
```
bucketName : "novaspark-website-xxxxxxxx"
sshCommand : "ssh -i ~/.ssh/labsuser.pem ec2-user@..."
websiteUrl : "http://ec2-XX-XX-XX-XX.compute-1.amazonaws.com:8080"
```

---

## Step 3: SSH In and Experience the Default — No Access

Connect to your instance:
```bash
# Use the sshCommand from your Pulumi output
ssh -i ~/.ssh/labsuser.pem ec2-user@<your-public-dns>
```

Now try to access S3:
```bash
aws s3 ls
```

You'll get one of these errors:
```
An error occurred (AccessDenied) when calling the ListBuckets operation: Access Denied
```
or
```
Unable to locate credentials. You can configure credentials by running "aws configure".
```

**This is expected and correct behavior.** This error exists by design — it's called *default-deny* and it's a foundational AWS security principle. Every API call to AWS requires explicit authorization. Being inside AWS doesn't automatically give you access to AWS services.

This might seem frustrating, but consider the alternative: if any EC2 instance could automatically access all S3 buckets in your account, a compromised instance would have access to your entire data lake.

Run this to confirm there are no credentials configured:
```bash
aws configure list
```

All values should show `None` or `not set`. Your instance has no keys, no tokens, no credentials at all — yet.

---

## Step 4: The Wrong Way — A Live Demonstration

> **Note:** This section uses fake credentials to demonstrate the concept. Nothing real is being exposed.

In non-restricted environments, the "quick and dirty" way to give an EC2 instance S3 access is to create an IAM User with access keys and configure them directly on the instance. Let's see why that's a bad idea.

Set some fake credentials as environment variables:

```bash
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

Try S3 access:
```bash
aws s3 ls
```

It fails (because they're fake). But now look at what you've done:

```bash
# Anyone with shell access can see these:
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# They're also now in your shell history:
history | grep AWS
```

If those were *real* credentials, they would now be visible to anyone who runs `env`, reads your shell history, or looks at `/proc`. On a production server with multiple users or monitoring tools, this is a serious exposure.

What if they were configured with `aws configure` instead?
```bash
# If you'd run `aws configure`, credentials would be here:
cat ~/.aws/credentials
# A plaintext file with long-lived access keys sitting on disk.
# It persists through reboots. It gets baked into AMIs. It shows up in backups.
```

**Clean these up immediately:**
```bash
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
aws s3 ls    # should fail again — credentials are gone
```

The problems with hardcoded credentials, in summary:
- Long-lived (don't expire for months/years)
- Stored in plaintext on disk or in environment
- Difficult to rotate across many instances
- Easy to accidentally commit to git or bake into AMIs
- If one instance is compromised, the keys work everywhere

---

## Step 5: The Right Way — IAM Role (Pulumi Already Did the Work)

Here's the moment of revelation. Check your credential source now:

```bash
aws configure list
```

Look at this output carefully:
```
      Name                    Value             Type    Location
      ----                    -----             ----    --------
   profile                <not set>             None    None
access_key     ****************XXXX         iam-role
secret_key     ****************XXXX         iam-role
    region                us-east-1      config-file    ~/.aws/config
```

**`iam-role` as the credential type.** The instance already has credentials — but they weren't configured manually. The IAM role Pulumi attached in `lab-p2/__main__.py` is providing them automatically via the **EC2 Instance Metadata Service** (IMDS).

Try S3 access now:
```bash
aws s3 ls
```

You should see your bucket listed. Now try your specific bucket:
```bash
aws s3 ls s3://$(aws s3 ls | awk '{print $3}' | grep novaspark)
# Or replace with your actual bucket name from pulumi output
```

Let's see the actual temporary credentials the metadata service is providing:

```bash
# Get a session token for IMDSv2
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Get your IAM role name
ROLE_NAME=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/)

echo "IAM Role attached to this instance: $ROLE_NAME"

# See the actual (temporary) credentials
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME | python3 -m json.tool
```

You'll see a JSON response with:
- `AccessKeyId` — a temporary key starting with `ASIA` (temporary keys always start with ASIA, not AKIA)
- `SecretAccessKey` — a temporary secret
- `Token` — a session token (required for temporary creds, not present with long-lived keys)
- `Expiration` — typically 6 hours from now

Key points about these credentials:
- They **expire automatically** — no manual rotation needed
- They are **generated fresh** each time — each instance gets unique credentials
- They are **scoped to the role's permissions** — can only do what the policy allows
- They are **never stored on disk** — fetched from the metadata service on demand
- `boto3` and the AWS CLI retrieve and refresh them **automatically**

Also run:
```bash
aws sts get-caller-identity
```

This shows you're authenticated as an assumed role — not as an IAM user — which is exactly what we want.

---

## Step 6: Upload the NovaSpark Website to S3

Get your bucket name from the Pulumi output (or check `aws s3 ls`). We'll refer to it as `$BUCKET_NAME`:

```bash
BUCKET_NAME="<paste-your-bucket-name-here>"
```

Upload the website files. We'll create them directly on the instance (we'll automate this file creation in Part 3 — for now, let's do it by hand so you feel the pain):

```bash
mkdir ~/website
cd ~/website
```

Create `index.html`:

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
        .served-from { margin-top: 1.5rem; color: #475569; font-size: 0.85rem; }
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
        <p class="served-from">📦 Content served from S3 via IAM role — survives instance restarts!</p>
    </section>
    <footer>
        <p>⚡ NovaSpark Technologies · Content in S3 · Compute on EC2 · Part 2 of 3</p>
    </footer>
</body>
</html>
EOF
```

Create `about.html`:

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
        <p>NovaSpark was founded by platform engineers who believe infrastructure should be treated with the same care as application code — version controlled, reviewed, and reproducible.</p>
        <p>In Part 2 of our deployment journey, we moved website content to S3 so it survives instance restarts. No hardcoded credentials — just IAM roles and temporary tokens.</p>
        <p><a href="index.html">← Back to Home</a></p>
    </div>
    <footer>
        <p>⚡ NovaSpark Technologies · Content in S3 · Compute on EC2 · Part 2 of 3</p>
    </footer>
</body>
</html>
EOF
```

Now upload both files to S3:
```bash
aws s3 cp ~/website/index.html s3://$BUCKET_NAME/
aws s3 cp ~/website/about.html s3://$BUCKET_NAME/
```

Verify they're there:
```bash
aws s3 ls s3://$BUCKET_NAME/
```

You should see both files listed with their sizes.

---

## Step 7: Set Up the S3 Web Server

The `s3_webserver.py` script (located in `lab-p3/` in this repo) serves HTML from S3 rather than from local files. For Part 2, we'll deploy it manually — in Part 3, Pulumi will handle this automatically.

On the EC2 instance, create the server script:

```bash
cat > ~/s3_webserver.py << 'PYEOF'
#!/usr/bin/env python3
import os, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import boto3
from botocore.exceptions import ClientError

BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
PORT = int(os.environ.get("PORT", "8080"))

if not BUCKET_NAME:
    print("ERROR: S3_BUCKET_NAME environment variable is not set.")
    sys.exit(1)

s3_client = boto3.client("s3", region_name="us-east-1")

class S3Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.lstrip("/") or "index.html"
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=path)
            content = response["Body"].read()
            content_type = "text/html; charset=utf-8" if path.endswith(".html") else "text/plain"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("X-Served-From", "S3")
            self.end_headers()
            self.wfile.write(content)
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("NoSuchKey", "404"):
                self.send_error(404, f"Not found: {path}")
            elif code in ("AccessDenied", "403"):
                self.send_error(403, f"Access denied — check IAM role permissions")
            else:
                self.send_error(500, str(e))
    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")

print(f"Serving s3://{BUCKET_NAME} on port {PORT} (IAM role credentials)")
HTTPServer(("", PORT), S3Handler).serve_forever()
PYEOF
```

Install boto3 (the AWS SDK for Python):
```bash
sudo dnf install -y python3-pip
pip3 install boto3 --user
```

Start the server — passing the bucket name as an environment variable:
```bash
export S3_BUCKET_NAME="$BUCKET_NAME"
python3 ~/s3_webserver.py
```

---

## Step 8: Test the S3-Backed Website

From your browser or local terminal, visit:
```
http://<your-public-dns>:8080
```

Or test with curl (the `-v` flag shows response headers):
```bash
curl -v http://<your-public-dns>:8080
```

Look for this in the response headers:
```
< X-Served-From: S3
```

That header confirms the content came from S3, not from local disk.

Now navigate to `about.html`:
```
http://<your-public-dns>:8080/about.html
```

---

## Step 9: Prove the Architecture is Resilient

This is the key test. While the server is running, let's simulate a server process restart:

Press `Ctrl+C` to stop the server. Now restart it:
```bash
python3 ~/s3_webserver.py
```

The website is back immediately — because the content was never on the instance. It was always in S3.

If the instance itself were rebooted (or replaced), you'd just need to restart the web server process and the content would still be there. This is the separation of compute and storage in practice.

> **Challenge:** Try adding a new page. Create a `contact.html` file, upload it to S3 (`aws s3 cp contact.html s3://$BUCKET_NAME/`), and access it at `http://<dns>:8080/contact.html`. The server serves it instantly — no restart needed.

---

## Step 10: Reflect on What Changed

Compare the two architectures:

| Aspect | Part 1 (Local Files) | Part 2 (S3 + IAM) |
|---|---|---|
| Content lives on... | EC2 instance disk | S3 bucket |
| Survives instance reboot? | ❌ No | ✅ Yes |
| Multiple instances can share? | ❌ No (each has its own files) | ✅ Yes (all read the same bucket) |
| Content update requires SSH? | Yes | No (just `aws s3 cp`) |
| Credentials | None (no AWS access) | IAM role — temporary, automatic |
| If instance is compromised | Limited blast radius | Credentials expire in 6 hours |

---

## Cleanup

Stop the server (`Ctrl+C`) and exit the SSH session:
```bash
exit
```

On your local machine, **empty the S3 bucket first** (Pulumi cannot delete a non-empty bucket without `force_destroy`):
```bash
cd lab-p2/
aws s3 rm s3://$(pulumi stack output bucketName) --recursive
```

Verify the bucket is empty:
```bash
aws s3 ls s3://$(pulumi stack output bucketName)
# Should return nothing
```

Then destroy the infrastructure:
```bash
pulumi destroy
```

---

## Troubleshooting

**`aws s3 ls` returns "Access Denied" after IAM role is attached**
Wait 30 seconds and try again. IAM role propagation takes a moment after `pulumi up`. Also verify the output `bucketName` matches what you're testing against.

**`boto3` not found**
Run `pip3 install boto3 --user` and make sure you're using `python3`, not `python`.

**Server starts but shows `403 Access denied — check IAM role permissions`**
The role doesn't have permission to read from this specific bucket. Verify the `bucketName` output from Pulumi matches the bucket name in `$S3_BUCKET_NAME`.

**`Permission denied (publickey)` on SSH**
Check that your `.pem` file has the right permissions: `chmod 400 ~/.ssh/labsuser.pem`

---

## What's Next

In Part 2, setting everything up took 45-60 minutes of SSH commands, manual uploads, and running scripts by hand. In **Part 3**, you'll do *all of this* with a single `pulumi up`. The entire infrastructure — bucket creation, file uploads, IAM role, server installation, service configuration — happens automatically, without you ever SSHing in.

That's the power of Infrastructure as Code taken to its logical conclusion.

---

## 📋 Part 2 Deliverables

**45 points total.** Capture screenshots as you complete each step — the step numbers below match where to take them.

| # | What to capture | Step | How to verify | Points |
|---|-----------------|------|---------------|--------|
| **D3** | Terminal: `aws configure list` output | Step 5 | Must show `iam-role` in the `Type` column for `access_key` | 5 |
| **D4** | Terminal: IMDSv2 curl command + JSON response | Step 5 | Must show `AccessKeyId` starting with `ASIA`, a `Token` field, and an `Expiration` timestamp | 10 |
| **D5** | Terminal: `aws s3 ls s3://<your-bucket>/` | Step 6 | Must show `index.html` and `about.html` listed with file sizes | 5 |
| **D6** | Terminal: `curl -v http://<your-dns>:8080` output | Step 8 | Must show `X-Served-From: S3` in the response headers | 5 |

**Written responses — include these in your submission PDF:**

| # | Question | Length | Points |
|---|----------|--------|--------|
| **D7** | Why can't an EC2 instance access S3 by default? Explain the security principle and why it matters at scale (imagine 500 instances). | 3–5 sentences | 10 |
| **D8** | List 3 specific risks of storing long-lived AWS credentials directly on an EC2 instance. For each risk, write one sentence explaining *what could go wrong in a real production environment*. | Bullet list, 1 sentence per risk | 10 |

> **Grader note:** D4 is the key credential screenshot — the ASIA prefix distinguishes temporary from long-lived keys. Written responses should explain *why*, not just *what*. A response that only says "it's not secure" earns no credit.
