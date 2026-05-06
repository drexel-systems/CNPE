# Lab 5 Setup — Prerequisites

## What You Need From Lab 4

Lab 5 extends your Lab 4 Pulumi stack. **Do not start this lab unless your Lab 4 stack is deployed and working.**

Confirm your Lab 4 stack is healthy before continuing:

```bash
cd path/to/4-Serverless/ugrad
export PULUMI_CONFIG_PASSPHRASE=""
pulumi stack output api_url
```

You should get back a URL. Test it:

```bash
curl $(pulumi stack output api_url)
```

You should see the NovaSpark status JSON response. If you get an error, resolve Lab 4 first.

---

## Lab 5 Project Setup

Create your Lab 5 working directory:

```bash
mkdir -p 5-API/ugrad && cd 5-API/ugrad
```

Copy your completed Lab 4 `__main__.py` and `app/` directory into `5-API/ugrad/`:

```bash
cp path/to/4-Serverless/ugrad/__main__.py .
cp -r path/to/4-Serverless/ugrad/app ./app
```

The Pulumi project is already initialized in this directory (`Pulumi.yaml` is pre-populated). Set the passphrase and you're ready to go:

```bash
export PULUMI_CONFIG_PASSPHRASE=""
```

Install dependencies:

```bash
pip install pulumi pulumi-aws --break-system-packages
```

Add the new handler directories provided for this lab:

```bash
# Your directory should look like:
# 5-API/ugrad/
# ├── __main__.py         ← Lab 4 code + Lab 5 TODOs
# ├── app/
# │   ├── handler.py      ← Lab 4 status handler (unchanged)
# │   ├── orders/
# │   │   └── handler.py  ← Lab 5: order submission Lambda
# │   └── processor/
# │       └── handler.py  ← Lab 5: SQS processor Lambda
# └── SETUP.md
```

---

## AWS Region

Confirm your region is `us-east-1` in the console and in your Pulumi AWS config:

```bash
pulumi config set aws:region us-east-1
```

---

## No New Costs

SQS, Lambda, and API Gateway are all free tier for the volumes used in this lab.
SQS: first 1 million requests/month free.
