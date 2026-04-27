# Lab 4 Setup

Complete this checklist before starting the lab guide. Most of this was covered in earlier labs — this is a quick confirmation.

---

## 1. Pulumi and AWS CLI

You should have both installed from Lab 2. Confirm they're still working:

```bash
pulumi version      # should print v3.x.x or later
aws --version       # should print aws-cli/2.x.x
```

If either command fails, see the Lab 2 setup guide.

---

## 2. AWS Credentials

Learner Lab credentials expire when your session ends. You need to refresh them each time:

1. Open the AWS Academy Learner Lab panel
2. Click **Start Lab** and wait for the green dot
3. Click **AWS Details** → **Show** next to the CLI credentials
4. Run the three `aws configure` commands shown there

Confirm you're connected:

```bash
aws sts get-caller-identity
```

You should see your `UserId`, `Account`, and an ARN containing `assumed-role/voclabs`.

---

## 3. Python

The Lambda runtime in this lab is Python 3.12. You don't need Python 3.12 locally for the Pulumi deployment itself — Pulumi packages and uploads your code as-is — but confirm Python 3.8+ is available:

```bash
python3 --version
```

---

## 4. Create a Pulumi Project

This lab uses a **new Pulumi project** separate from your Lab 2 or Lab 3 stacks. Create it in the `4-Serverless/` directory of your course repo:

```bash
cd your-course-repo
mkdir 4-Serverless && cd 4-Serverless
pulumi new aws-python --name novaSpark-serverless --stack dev
```

When prompted for the passphrase, press Enter to leave it blank (consistent with earlier labs). When prompted for the AWS region, enter `us-east-1`.

This creates a `__main__.py` with example content. **Replace it entirely** with the starter code from the lab's `__main__.py` before proceeding.

```bash
export PULUMI_CONFIG_PASSPHRASE=""
```

Add this to your shell (or include it before every `pulumi` command) so you're not prompted for a passphrase.

---

## 5. Install Pulumi AWS Provider

```bash
pip install pulumi pulumi-aws --break-system-packages
```

If you already have these from Lab 2 or 3, this will be a no-op or a minor upgrade.

---

## 6. Copy the Starter Code

Copy the `app/` directory and `__main__.py` from the lab materials into your `4-Serverless/` directory:

```
4-Serverless/
  app/
    handler.py      ← Lambda handler (provided, complete — don't modify until directed)
  __main__.py       ← Pulumi code with TODOs you'll complete in Part 3
  Pulumi.yaml       ← created by pulumi new
  requirements.txt  ← created by pulumi new
```

---

## Ready?

If all commands above ran without errors, open [`lab-guide.md`](lab-guide.md) and begin at Part 1.
