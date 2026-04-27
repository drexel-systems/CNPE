# Lab Setup

Complete this checklist before starting the lab guide. Most of this was covered in earlier labs — this is a quick confirmation.

---

## 1. Pulumi and AWS CLI

You should have both installed from prior labs. Confirm they're still working:

```bash
pulumi version      # should print v3.x.x or later
aws --version       # should print aws-cli/2.x.x
```

If either command fails, refer back to the Lab 1 setup instructions.

---

## 2. AWS Credentials

Learner Lab credentials expire when your session ends. Refresh them each time you start a new session:

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

## 3. Create a Pulumi Project

This lab uses a **new Pulumi project** separate from your Lab 2 and Lab 3 stacks. Create it in the `4-Serverless/` directory of your course repo:

```bash
cd your-course-repo
mkdir 4-Serverless && cd 4-Serverless
pulumi new aws-python --name novaSpark-serverless --stack dev
```

When prompted for the passphrase, press Enter to leave it blank. When prompted for the AWS region, enter `us-east-1`.

This creates a `__main__.py` with example content. **Replace it entirely** with the provided `__main__.py` from the lab materials before running `pulumi up`.

Set the passphrase environment variable so you aren't prompted each time:

```bash
export PULUMI_CONFIG_PASSPHRASE=""
```

---

## 4. Install the Pulumi AWS Provider

```bash
pip install pulumi pulumi-aws --break-system-packages
```

---

## 5. Copy the Lab Files

Copy the `app/` directory and `__main__.py` from the lab materials into your `4-Serverless/` directory:

```
4-Serverless/
  app/
    handler.py      ← Lambda handler (complete — read before deploying)
  __main__.py       ← complete Pulumi template (read before deploying)
  Pulumi.yaml       ← created by pulumi new
  requirements.txt  ← created by pulumi new
```

---

## Ready?

If all commands above ran without errors, open [`lab-guide.md`](lab-guide.md) and begin at the "Before You Deploy" section.
