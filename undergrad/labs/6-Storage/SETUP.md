# Lab 6 Setup — Prerequisites

## What You Need From Lab 5

Lab 6 extends your Lab 5 Pulumi stack. **Lab 5 must be completed and submitted before starting this lab.**

You do not need your Lab 5 stack to still be running — if you ran `pulumi destroy` after submitting, that is correct. Lab 6 starts from a fresh Pulumi stack using the provided template, which already contains the complete Lab 5 infrastructure.

---

## Lab 6 Project Setup

Navigate into the provided Lab 6 directory:

```bash
cd path/to/6-Storage
```

Your directory structure should look like:

```
6-Storage/
├── __main__.py         ← Lab 5 code + Lab 6 TODOs
├── Pulumi.yaml
├── requirements.txt
├── SETUP.md
└── app/
    ├── handler.py      ← Lab 4 status handler (unchanged)
    ├── orders/
    │   └── handler.py  ← Lab 6: GET /orders/{id} and GET /orders TODOs
    └── processor/
        └── handler.py  ← Lab 6: DynamoDB put_item TODO
```

Initialize a new Pulumi project (separate stack from Lab 5):

```bash
export PULUMI_CONFIG_PASSPHRASE=""
pulumi login --local
pulumi install
pulumi stack init dev
```


When you are ready you can use the standard `pulumi` commands:

```bash
pulumi preview
pulumi up
```

---

## Verify Before Starting

Confirm your AWS region and credentials are active in the Learner Lab:

```bash
aws sts get-caller-identity
```

You should see your account ID and the `LabRole` ARN. If this fails, your Learner Lab session has expired — start a new session and re-export credentials before continuing.

---

## No New Costs

DynamoDB on-demand mode has no idle costs. The free tier covers 25 GB storage and 25 WCU/RCU permanently — far more than this lab uses. Combined with Lambda and API Gateway free tiers, Lab 6 costs $0.
