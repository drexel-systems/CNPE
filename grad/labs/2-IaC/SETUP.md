# Lab 2 Setup: Installing Pulumi and Connecting to AWS

This document walks you through everything you need before running a single lab command. Complete all six sections in order — it takes about 15 minutes the first time. You'll return to **Section 3** at the start of every lab session to refresh your AWS credentials.

---

## Section 1: Install Pulumi

Pulumi is a command-line tool. Install it once on your machine using the instructions for your operating system.

### Mac

The easiest way is via Homebrew:

```bash
brew install pulumi/tap/pulumi
```

If you don't have Homebrew, install it first at [brew.sh](https://brew.sh), or use the curl method below.

### Windows

**Option A — winget (Windows 11 / updated Windows 10):**
```powershell
winget install pulumi
```

**Option B — Chocolatey:**
```powershell
choco install pulumi
```

**Option C — Direct installer:**
Download the MSI from [pulumi.com/docs/install](https://www.pulumi.com/docs/iac/download-install/) and run it.

### Linux

```bash
curl -fsSL https://get.pulumi.com | sh
```

After the script completes, add Pulumi to your PATH:
```bash
echo 'export PATH=$PATH:$HOME/.pulumi/bin' >> ~/.bashrc
source ~/.bashrc
```

### Verify Installation

```bash
pulumi version
```

You should see a version number like `v3.x.x`. If you get "command not found", close and reopen your terminal and try again.

---

## Section 2: How Pulumi Uses AWS Credentials

Before writing any code, it helps to understand how these tools connect.

```
  Your Code              Pulumi Engine              AWS
  (__main__.py)    →     (pulumi CLI)       →      API
                              │
                              │  reads credentials from
                              ▼
                    ~/.aws/credentials
                    (or environment variables)
```

Pulumi does **not** have its own AWS authentication system. It reads your AWS credentials from the same place the AWS CLI does — the `~/.aws/credentials` file on your machine (or environment variables if you prefer). This means:

- If `aws s3 ls` works in your terminal, `pulumi up` can also reach AWS
- If your credentials expire, both stop working at the same time
- Refreshing credentials for one automatically fixes both

In AWS Academy (Vocareum), credentials are **temporary** — they expire every few hours when your Learner Lab session ends. You must refresh them at the start of each session. Section 3 shows you exactly how.

---

## Section 3: The Vocareum Credential Workflow

> **You will repeat this section at the start of every lab session.** AWS Academy provides fresh temporary credentials each time you start a lab, and they expire when the session timer runs out.

### Step 1: Start Your Learner Lab

Log into [AWS Academy](https://awsacademy.instructure.com), navigate to your course, and open the **Learner Lab**. Click **Start Lab** and wait for the circle indicator in the top-left to turn **green**.

> ⚠️ Don't proceed until the indicator is green. A yellow or red indicator means the environment isn't ready yet.

### Step 2: Open AWS Details

Click the **AWS Details** button at the top of the lab panel. Then click **Show** next to "AWS CLI".

You'll see a credentials block that looks like this:

```
[default]
aws_access_key_id=ASIA...
aws_secret_access_key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
aws_session_token=IQoJb3JpZ2luX2VjEA...  (very long string)
```

> 🔑 **All three lines are required.** The `aws_session_token` is what makes these temporary credentials work — it's not present with regular long-lived IAM user keys. If you only copy the first two lines, authentication will fail.

### Step 3: Copy Credentials Into Your Credentials File

**Mac / Linux:**
```bash
mkdir -p ~/.aws
nano ~/.aws/credentials
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.aws"
notepad "$env:USERPROFILE\.aws\credentials"
```

Replace the **entire contents** of the file with the three lines you copied from AWS Details. The file should look exactly like this — nothing else:

```
[default]
aws_access_key_id=ASIA...
aws_secret_access_key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
aws_session_token=IQoJb3JpZ2luX2VjEA...
```

Save and close the file.

### Step 4: Verify Access

```bash
aws sts get-caller-identity
```

You should see a JSON response with your AWS account ID and a role ARN containing `LabRole`:

```json
{
    "UserId": "AROA...",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/LabRole/..."
}
```

If you see an error, go back and make sure you copied all three credential lines and that there are no extra spaces or characters in the file.

### What to Do When Your Session Expires Mid-Lab

If `aws` or `pulumi` commands suddenly return `InvalidClientTokenId` or `ExpiredTokenException`, your Vocareum session has ended. Recovery takes under two minutes:

1. Go back to AWS Academy and click **Start Lab** again
2. Click **AWS Details → Show** to get fresh credentials
3. Overwrite `~/.aws/credentials` with the new three-line block
4. Run `aws sts get-caller-identity` to confirm you're reconnected
5. Resume your Pulumi work — no other changes needed

> 💡 Pulumi saves its state locally, so your infrastructure record is preserved even when your AWS session expires. Refreshing credentials and running `pulumi up` again will pick up right where you left off.

---

## Section 4: Download Your SSH Key

To SSH into EC2 instances in the labs, you need the `labsuser.pem` key that AWS Academy provides. You only need to do this once — the key doesn't change between sessions.

In the **AWS Details** panel (same place as the credentials), look for **"SSH Key"** and click **Download PEM**.

Then move it into place and lock down its permissions:

**Mac / Linux:**
```bash
mv ~/Downloads/labsuser.pem ~/.ssh/labsuser.pem
chmod 400 ~/.ssh/labsuser.pem
```

**Windows (Git Bash or WSL):**
```bash
mv /mnt/c/Users/<YourName>/Downloads/labsuser.pem ~/.ssh/labsuser.pem
chmod 400 ~/.ssh/labsuser.pem
```

> `chmod 400` makes the file read-only for your user only. SSH will refuse to use a key file that other users can read — this is a security requirement enforced by the SSH client, not something you can skip.

> 💡 On Windows, managing `.pem` file permissions can be tricky with native PowerShell. Using **Git Bash** or **WSL** to run SSH commands is generally much smoother — both behave like Linux terminals.

---

## Section 5: Configure Pulumi for Local State Storage

Pulumi stores a **state file** to track the infrastructure it has created. Think of it as Pulumi's memory — it records every resource so it knows what to change or delete on future runs.

```
Your Code (__main__.py)
       │
       ▼
  Pulumi Engine ──── reads/writes ────▶  State File  (~/.pulumi/)
       │
       ▼
  AWS API ──── creates/modifies ────▶  Real Resources (EC2, S3, IAM...)
```

Pulumi can store state in Pulumi Cloud (requires a free account) or locally on your machine. For this course, **we use local storage** — no account, no sign-up, nothing leaves your machine.

### Log In to the Local Backend

```bash
pulumi login --local
```

Expected output:
```
Logged in to local as <your-username> (file:///Users/you/.pulumi)
```

### Set the Passphrase Variable

When using local storage, Pulumi encrypts any secrets in the state file and needs a passphrase to do so. Since our labs don't store real production secrets, we'll use an empty passphrase — but we need to tell Pulumi this explicitly so it doesn't pause and ask you interactively during every command.

**Mac / Linux — add to your shell profile so it persists across sessions:**
```bash
echo 'export PULUMI_CONFIG_PASSPHRASE=""' >> ~/.bashrc
source ~/.bashrc
```

If you use zsh (the default on newer Macs):
```bash
echo 'export PULUMI_CONFIG_PASSPHRASE=""' >> ~/.zshrc
source ~/.zshrc
```

**Windows PowerShell — persist across sessions:**
```powershell
[System.Environment]::SetEnvironmentVariable("PULUMI_CONFIG_PASSPHRASE", "", "User")
```

Or just for the current session:
```powershell
$env:PULUMI_CONFIG_PASSPHRASE=""
```

> ⚠️ Set this **before** running any Pulumi command. If Pulumi prompts you for a passphrase interactively, just press Enter to use an empty string — then set the variable afterward to avoid being prompted again.

---

## Section 6: Final Verification Checklist

Run these four commands. All four should succeed before you open any lab guide.

```bash
# 1. Pulumi is installed
pulumi version

# 2. AWS credentials are valid (Vocareum session is active)
aws sts get-caller-identity

# 3. Pulumi is logged in to the local backend
pulumi whoami

# 4. Passphrase variable is set (should print: PULUMI_CONFIG_PASSPHRASE is set to: '')
echo "PULUMI_CONFIG_PASSPHRASE is set to: '$PULUMI_CONFIG_PASSPHRASE'"
```

| Command | What a Good Result Looks Like |
|---|---|
| `pulumi version` | `v3.x.x` (any version 3 or higher) |
| `aws sts get-caller-identity` | JSON with your account ID and `LabRole` in the ARN |
| `pulumi whoami` | Your local machine username (not an email address) |
| `echo $PULUMI_CONFIG_PASSPHRASE` | A blank line (correctly set to empty string) |

All four passing? Open **`lab-guide-p1.md`** and start building.

---

## Quick Reference — Every Session

Tape this to your monitor:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  START OF EVERY SESSION (credentials expire!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Start Learner Lab in AWS Academy → wait for green dot
  2. AWS Details → Show → copy all 3 credential lines
  3. Paste into ~/.aws/credentials (replace everything)
  4. aws sts get-caller-identity   ← verify it works

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FIRST TIME ONLY (done after completing this guide)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  pulumi login --local
  export PULUMI_CONFIG_PASSPHRASE=""  (added to shell profile)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  EACH LAB (run inside the lab-pX/ directory)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  pulumi stack init dev
  pulumi config set aws:region us-east-1
  pulumi install              ← installs Python packages (once per directory)
  pulumi preview              ← always preview first
  pulumi up                   ← deploy
  pulumi destroy              ← ALWAYS run before ending a lab!
```

---

## Common Problems

**`pulumi: command not found`**
Close your terminal, reopen it, and try again. On Linux/Mac, make sure `~/.pulumi/bin` is in your `$PATH` (the install script should have added it to your shell profile).

**`ExpiredTokenException` or `InvalidClientTokenId`**
Your Vocareum session expired. Go back to AWS Academy → Start Lab → copy fresh credentials → overwrite `~/.aws/credentials`.

**`Unable to locate credentials`**
The `~/.aws/credentials` file doesn't exist or is in the wrong location. Follow Section 3 again from Step 3.

**Pulumi asks for a passphrase interactively**
Press Enter (uses empty string), then run `export PULUMI_CONFIG_PASSPHRASE=""` and add it to your shell profile (Section 5) so it doesn't happen again.

**SSH: `WARNING: UNPROTECTED PRIVATE KEY FILE`**
Run `chmod 400 ~/.ssh/labsuser.pem`. This error means the file is too permissive — SSH won't use it until you fix the permissions.

**SSH: `Permission denied (publickey)`**
Three things to check: (1) you're using `ec2-user` as the username, (2) the path to your `.pem` file is correct, (3) the EC2 instance has fully started (wait 60 seconds after `pulumi up`).
