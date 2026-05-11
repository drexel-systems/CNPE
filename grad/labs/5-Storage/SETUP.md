# Lab Setup

Complete this checklist before starting the lab guide.

---

## 1. Pulumi and AWS CLI

Confirm both are still working:

```bash
pulumi version      # should print v3.x.x or later
aws --version       # should print aws-cli/2.x.x
```

If either command fails, refer back to the Lab 1 setup instructions.

---

## 2. AWS Credentials

Learner Lab credentials expire when your session ends. Refresh them before starting:

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

## 3. Create a New Pulumi Project

Lab 5 starts from a fresh stack — Lab 4's stack was destroyed at the end of that lab. Create a new Pulumi project in the `5-Storage/` directory of your course repo:

```bash
cd your-course-repo
mkdir 5-Storage && cd 5-Storage
```

Copy the starter files over from the course github repository into this directory on your local machine.

---

## 4. Setup Pulumi with the starter files

```bash
export PULUMI_CONFIG_PASSPHRASE=""
pulumi login --local
pullumi install
pulumi stack init dev
```

---

## 5. Important: Read Before Deploying

This lab's template files contain explicit `# TODO` comments marking what you must implement before running `pulumi up`. Unlike Lab 4, this template will **not** deploy successfully without your changes. The lab guide walks you through each TODO in order.  Dont forget that you can make sure everything is ok via the `pulumi preview` command.

---

## Ready?

If all commands above ran without errors, open [`lab-guide.md`](lab-guide.md) and begin with Part 1.
