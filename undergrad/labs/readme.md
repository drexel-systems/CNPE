# Lab 1: AWS Setup and Toolchain Verification
## CS 463 — Cloud Native Platform Engineering

**Weight:** 5% of final grade
**Deliverables:** Four screenshots — see bottom of this guide for the complete list
**Due:** End of Week 1

---

## Overview

Before you can build anything in this course, you need four things working correctly: your GitHub Classroom repository set up and accessible, access to AWS, a working command-line toolchain, and a verified SSH connection to an EC2 instance. This lab walks through all four.

This last step matters more than it might seem. In Week 3 you will SSH through a bastion host into a private EC2 instance inside a custom VPC. If your SSH client, key file, or permissions are misconfigured, you want to find out now — not in the middle of that lab.

---

## Part 1: AWS CLI Setup

### Step 1 — Install the AWS CLI

**Mac (Homebrew):**
```bash
brew install awscli
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install -y curl unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"   # Intel/AMD
curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"  # ARM (Apple M1/M2 on Linux)
unzip awscliv2.zip
sudo ./aws/install
```

**Windows:**
Install WSL2 first (recommended for this course), then use the Linux instructions above inside your WSL2 terminal. Native Windows with PowerShell is not recommended — the terminal patterns used throughout this course assume a Unix environment.

Verify the install:
```bash
aws --version
```

---

### Step 2 — Get your AWS credentials from the Learner Lab

1. Go to [AWS Academy](https://awsacademy.instructure.com) and open the Learner Lab for this course
2. Click **Start Lab** and wait for the indicator to turn green
3. Click **AWS Details** — this panel contains your credentials and your SSH key
4. Copy the three credential values shown: `AWS Access Key ID`, `AWS Secret Access Key`, and `AWS Session Token`

> **Important:** Your Learner Lab session expires after a set period. Each time you restart the lab, new credentials are issued. You will need to re-run the configuration step below each session. This is a Learner Lab limitation, not an AWS limitation.

---

### Step 3 — Configure the AWS CLI

```bash
aws configure
```

Enter the values when prompted:
```
AWS Access Key ID:     <paste from Learner Lab>
AWS Secret Access Key: <paste from Learner Lab>
Default region name:   us-east-1
Default output format: json
```

Then add the session token — this step is required for Learner Lab credentials and is easy to miss:

```bash
aws configure set aws_session_token <paste session token from Learner Lab>
```

---

### Step 4 — Verify your CLI access

Run the following command:
```bash
aws sts get-caller-identity
```

You should see output similar to:
```json
{
    "UserId": "AROA...",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/voclabs/user..."
}
```

📸 **Screenshot 1 required:** Your terminal showing the output of `aws sts get-caller-identity`.

---

## Refreshing Credentials — Every Session

> **Bookmark this section.** You will repeat this workflow at the start of every lab for the rest of the course. Learner Lab credentials expire when your session ends — new credentials are issued each time you click **Start Lab**. Running `aws configure` each time is tedious and error-prone. The script below is the faster, reliable alternative.

### How it works

When you click **AWS Details** in the Learner Lab panel, the credentials section displays three values pre-formatted in the AWS credentials file format:

```
[default]
aws_access_key_id=ASIA...
aws_secret_access_key=...
aws_session_token=...
```

The workflow is:
1. Start your Learner Lab session
2. Click **AWS Details** → copy the credentials block
3. Paste it into a local file named `credentials` (in your repo root or a convenient folder)
4. Run the refresh script — it copies the file into place and verifies access

**Do not commit the `credentials` file to GitHub.** Add it to your `.gitignore` now:
```bash
echo "credentials" >> .gitignore
```

---

### Mac / Linux

Save this as `refresh-aws.sh` in your repo root:

```bash
#!/bin/bash
# refresh-aws.sh — run this at the start of every Learner Lab session

cp credentials ~/.aws/credentials
echo "Credentials updated. Verifying..."
aws sts get-caller-identity
```

Make it executable once:
```bash
chmod +x refresh-aws.sh
```

Then each session:
```bash
./refresh-aws.sh
```

---

### Windows — WSL2

The script is identical to Mac/Linux. Save it as `refresh-aws.sh` inside your WSL2 filesystem and follow the same steps above.

When you paste the credentials from the Learner Lab, make sure you're saving the `credentials` file inside WSL2 (e.g., `~/cs463/credentials`) — not on the Windows filesystem under `/mnt/c/...`. Then run the script from the same directory.

---

### Windows — PowerShell (no WSL2)

Save this as `refresh-aws.ps1` in your working folder:

```powershell
# refresh-aws.ps1 — run this at the start of every Learner Lab session

Copy-Item "credentials" "$env:USERPROFILE\.aws\credentials" -Force
Write-Host "Credentials updated. Verifying..."
aws sts get-caller-identity
```

If PowerShell blocks script execution, run this once to allow local scripts:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then each session, open PowerShell in your working folder and run:
```powershell
.\refresh-aws.ps1
```

---

A successful run looks like this regardless of platform:

```json
{
    "UserId": "AROA...",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/voclabs/user..."
}
```

If you see an error like `ExpiredTokenException` or `InvalidClientTokenId`, your credentials file was not saved correctly — go back to the Learner Lab panel, copy the credentials block again, and re-paste into the `credentials` file before re-running the script.

---

## Part 2: GitHub Classroom Repository

This part has four steps. Complete them in order — each step depends on the previous one.

---

### Step 1 — Set up SSH access to GitHub

Before you can clone your private repository, your local machine needs to be able to authenticate to GitHub over SSH. This is a one-time setup.

**Detailed instructions are in `GitHubSetup.pdf`** in this lab folder — follow those instructions completely before continuing. The PDF covers generating an SSH key pair, adding the public key to your GitHub account, and testing the connection.

When your SSH setup is working correctly, the following command will succeed:

```bash
ssh -T git@github.com
```

Expected output:
```
Hi your-username! You've successfully authenticated, but GitHub does not provide shell access.
```

If you see that message, you're ready to move on. If you see `Permission denied (publickey)`, go back to the PDF and check that your public key was added to GitHub correctly.

---

### Step 2 — Accept the GitHub Classroom invitation and claim your repository

Your instructor will post a GitHub Classroom invitation link on Canvas. Click it — you will be taken to a page showing the class roster.

> ⚠️ **This step requires care.** You will see a list of names. Find your own name and click the **"Link to GitHub"** button next to it. Double-check that you are selecting *your* name before confirming — linking to the wrong name assigns you someone else's repository and is difficult to undo. If your name does not appear in the list, stop and contact your instructor before proceeding.

After clicking your name and confirming, GitHub Classroom will create your private repository. This takes a few seconds. When it completes, you will see a confirmation page with a link to your new repo.

---

### Step 3 — Accept the GitHub organization invitation

After claiming your repository, GitHub will send an email to the address associated with your GitHub account. The subject will be something like **"You've been invited to join [course organization] on GitHub."**

Open that email and click the activation link. This step grants you membership in the course's GitHub organization, which is required to access your private repo and submit lab work.

> **Check your spam folder** if the email doesn't arrive within a few minutes. If you don't receive it at all, contact your instructor — the invitation can be resent.

---

### Step 4 — Access and clone your private repository

Once you've accepted the organization invitation, navigate to your repository in the browser. The URL will follow the pattern:

```
https://github.com/drexel-cloud-course/cs463-your-github-username
```

Clone it to your local machine using SSH (not HTTPS — you set up SSH in Step 1 specifically for this):

```bash
git clone git@github.com:drexel-cloud-course/cs463-your-github-username.git
```

Confirm the clone succeeded and you can see the repository contents locally.

📸 **Screenshot 2 required:** Your browser showing your private GitHub Classroom repository homepage — the URL should show the course organization and your username.

---

## Part 3: EC2 Instance — Launch, Connect, and Terminate

This section validates that your SSH client works correctly and that you can connect to an AWS instance using the Learner Lab key pair. You will use the AWS Console (not Pulumi) for this — the goal is toolchain verification, not infrastructure code.

### Step 1 — Download the Learner Lab SSH key

1. In the Learner Lab panel, click **AWS Details**
2. Under **SSH Key**, click **Download PEM** — save the file as `labsuser.pem`
3. Follow the instructions for your operating system below to place the file and set the correct permissions. **SSH will refuse to connect if the key file permissions are too open** — this is a security requirement, not a suggestion.

---

#### Mac / Linux

Move the key to your `.ssh` folder and lock down permissions:

```bash
mv ~/Downloads/labsuser.pem ~/.ssh/labsuser.pem
chmod 400 ~/.ssh/labsuser.pem
```

`chmod 400` means "owner can read, nobody else can do anything." If you skip this step, SSH will print a `WARNING: UNPROTECTED PRIVATE KEY FILE` error and refuse to connect.

---

#### Windows — Option A: WSL2 (recommended for this course)

WSL2 gives you a full Linux terminal on Windows and is the recommended environment for all lab work in this course. If you have WSL2 installed, use it for everything — the Mac/Linux instructions above apply exactly.

**Important:** Copy the key file *into* the WSL2 filesystem, not the Windows filesystem. Key files stored under `/mnt/c/Users/...` cannot have their permissions set correctly from WSL2.

```bash
# Run inside your WSL2 terminal
cp /mnt/c/Users/YourWindowsUsername/Downloads/labsuser.pem ~/.ssh/labsuser.pem
chmod 400 ~/.ssh/labsuser.pem
```

---

#### Windows — Option B: PowerShell (if WSL2 is not installed)

> ⚠️ **Use PowerShell, not Command Prompt.** The old Windows Command Prompt (DOS shell) does not have an SSH client and cannot set file permissions correctly. All Windows SSH work in this course must be done in **PowerShell**.

Windows 10 and 11 include a built-in OpenSSH client accessible from PowerShell. However, PowerShell does not have `chmod` — you must use `icacls` to restrict key file permissions instead.

Move the key somewhere permanent (your user folder works well):

```powershell
# Run in PowerShell
Move-Item "$env:USERPROFILE\Downloads\labsuser.pem" "$env:USERPROFILE\labsuser.pem"
```

Strip inherited permissions and grant read access to your user only:

```powershell
icacls "$env:USERPROFILE\labsuser.pem" /inheritance:r /grant:r "$($env:USERNAME):(R)"
```

If this command succeeds, you should see: `Successfully processed 1 files`. If SSH later complains about unprotected key permissions, re-run this command — it is the PowerShell equivalent of `chmod 400`.

---

### Step 2 — Launch an EC2 instance via the AWS Console

1. Open the [AWS Console](https://console.aws.amazon.com) — use the **AWS** button in the Learner Lab panel to open it with your current session credentials
2. Navigate to **EC2 → Instances → Launch Instances**
3. Configure the instance:
   - **Name:** `lab1-test`
   - **AMI:** Amazon Linux 2023 (free tier eligible)
   - **Instance type:** `t2.micro` (free tier eligible)
   - **Key pair:** Select `vockey` — this is the pre-created key pair that corresponds to the `labsuser.pem` file you downloaded
   - **Network settings:** Leave default VPC and default subnet selected; ensure **Auto-assign public IP** is enabled
   - **Security group:** Create a new security group; allow SSH (port 22) from your IP address (or `0.0.0.0/0` for simplicity in this one-time test)
4. Click **Launch Instance**
5. Wait until the instance state shows **Running** and a public IP address appears

> **Do not create a new key pair.** The `vockey` key pair is pre-created by the Learner Lab and corresponds exactly to the `labsuser.pem` file you downloaded. Creating a new key pair requires IAM permissions that may not be available in the sandbox.

---

### Step 3 — SSH into the instance

Once the instance is running, connect using the public IP address shown in the console. Replace `<public-ip-address>` with the actual IP. When prompted to verify the host fingerprint for the first time, type `yes`.

---

#### Mac / Linux and Windows (WSL2)

```bash
ssh -i ~/.ssh/labsuser.pem ec2-user@<public-ip-address>
```

---

#### Windows (PowerShell — no WSL2)

```powershell
ssh -i "$env:USERPROFILE\labsuser.pem" ec2-user@<public-ip-address>
```

---

You should see an Amazon Linux welcome banner and a prompt like `[ec2-user@ip-... ~]$`. If you see that, your SSH setup is working correctly and you are done with this step.

**Common issues:**

| Error | Likely cause | Fix |
|-------|-------------|-----|
| `WARNING: UNPROTECTED PRIVATE KEY FILE` | Key file permissions too open | Mac/Linux: re-run `chmod 400`; Windows: re-run `icacls` command from Step 1 |
| `Permission denied (publickey)` | Wrong key path, wrong username, or bad permissions | Confirm key path is correct; Amazon Linux uses `ec2-user` (not `ubuntu` or `admin`) |
| `Connection timed out` | Security group not allowing port 22 | Go back to EC2 console → Security Groups → check inbound rule for SSH port 22 |
| `ssh: command not found` (Windows) | Running in Command Prompt, not PowerShell | Close CMD, open PowerShell, retry |

📸 **Screenshot 3 required:** Your terminal showing a successful SSH connection — the Amazon Linux welcome banner and your command prompt inside the instance (e.g., `[ec2-user@ip-... ~]$`).

---

### Step 4 — Terminate the instance

This step is not optional. Leaving instances running burns through your $50 AWS credit budget. Get in the habit of cleaning up after every lab that creates EC2 resources.

1. In the EC2 Console, select your `lab1-test` instance
2. Click **Instance State → Terminate Instance**
3. Confirm termination
4. Wait until the status changes to **Terminated**

📸 **Screenshot 4 required:** The EC2 console showing your `lab1-test` instance with status **Terminated**.

---

## Deliverables Summary

| # | Screenshot | What it must show |
|---|-----------|-------------------|
| 1 | AWS CLI verification | Terminal output of `aws sts get-caller-identity` with your Account ID visible |
| 2 | GitHub repo | Browser showing your GitHub Classroom repository homepage |
| 3 | SSH connection | Terminal showing successful SSH login to EC2 (Amazon Linux banner + prompt) |
| 4 | Instance terminated | EC2 console showing `lab1-test` with status **Terminated** |

Upload all four screenshots to your GitHub Classroom repository under `/1-CourseToolsSetup/`, then submit your GitHub repo link on Canvas to confirm completion.

---

## Need Help?

If you are stuck on any step, do not wait until the due date. Common issues:

- **Credentials expired:** Learner Lab sessions time out. Re-open the Lab, click Start, get fresh credentials, and re-run `aws configure` + `aws configure set aws_session_token`
- **SSH not installed:** Windows users should install WSL2; Mac/Linux users have SSH by default
- **Wrong key pair:** Always use `vockey` / `labsuser.pem` — do not generate new keys in the console
- **Can't find your name in the roster:** Contact the instructor on Canvas before clicking anything — do not select a random name as a placeholder
- **GitHub org invitation email never arrived:** Check your spam folder first; if it's not there, contact the instructor to resend it
- **SSH to GitHub fails (`Permission denied (publickey)`):** Go back to `GitHubSetup.pdf` and verify your public key was added to your GitHub account settings
