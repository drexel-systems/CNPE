# VPC Demo — SSM Access Model (Go)

This demo builds the same two-tier VPC architecture from Lab 3 with one deliberate change: EC2 instances are accessed via **AWS Systems Manager Session Manager** instead of SSH. No port 22. No key pair. No bastion hop.

It also demonstrates **Pulumi's polyglot nature** — the same infrastructure you wrote in Python, expressed in Go. The resources, the concepts (outputs, `DependsOn`, resource options), and the deployment workflow are identical. Only the language changes.

---

## What changed from Lab 3

| | Lab 3 (Python, SSH) | This demo (Go, SSM) |
|---|---|---|
| **Access method** | SSH key pair (`vockey`) | SSM Session Manager |
| **Port 22 open** | Yes — `0.0.0.0/0` on bastion SG | No — removed entirely |
| **Key management** | Manual (`.pem` file) | None — IAM identity |
| **Session audit** | `auth.log` timestamps only | Full command log in CloudWatch |
| **Inbound traffic** | Instance accepts on port 22 | Instance accepts nothing — SSM agent phones home outbound |
| **Language** | Python | Go |

The SSH security groups from Lab 3 are preserved as **commented-out code** in `main.go`. Find the section labeled `ORIGINAL SSH SECURITY GROUPS` to see exactly what was removed and why.

---

## How SSM Session Manager works

```
Your terminal ──── HTTPS ────► AWS Systems Manager ──── outbound ────► EC2 Instance
               (IAM auth)       (service endpoint)       (SSM agent
                                                          phones home)
```

The SSM agent inside the instance opens an **outbound** HTTPS connection to the AWS SSM service endpoint. You connect to the AWS service — not directly to the instance. The instance never accepts inbound traffic from anyone. This is why the security groups in this demo have no inbound rules at all.

Authentication is via IAM identity (your CLI credentials), not a key file. Access is revocable per user in seconds. Every command run in the session is logged to CloudWatch.

---

## Prerequisites

- AWS CLI configured with credentials (`aws configure` or Academy session)
- Pulumi CLI installed (`brew install pulumi` or equivalent)
- Go 1.21+ installed (`go version` to check)
- Session Manager plugin for the AWS CLI:
  ```
  https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html
  ```

---

## Setup and deploy

Get the go dependencies for pulumi and aws:

```bash
go get github.com/pulumi/pulumi/sdk/v3
go get github.com/pulumi/pulumi-aws/sdk/v6
```

Get ready to build stack:

```bash
# 1. Set a blank passphrase (AWS Academy accounts don't use Pulumi Cloud)
export PULUMI_CONFIG_PASSPHRASE=""

# 2. Initialize the stack
pulumi stack init dev

# 3. Set region
pulumi config set aws:region us-east-1

# 4. Resolve Go dependencies
go mod tidy

# 5. Preview what will be created
pulumi preview

# 6. Deploy (takes 4-6 minutes — NAT Gateway provisioning is slow)
pulumi up
```

---

## Accessing instances

After `pulumi up` completes, get your ready-to-run session commands:

```bash
pulumi stack output ssmPublicCommand
# → aws ssm start-session --target i-0abc123...

pulumi stack output ssmPrivateCommand
# → aws ssm start-session --target i-0def456...
```

Copy and run either command. You will land in a shell on the instance with no SSH key, no open port, and a full audit trail being written to CloudWatch in your account.

To verify the private instance routes outbound traffic through the NAT Gateway:

```bash
# From inside the private instance session:
curl https://checkip.amazonaws.com
# Should match: pulumi stack output natEip
```

---

## AWS Academy note

If `pulumi up` fails on IAM resource creation with `AccessDeniedException`, your Academy sandbox may restrict `iam:CreateRole`. Workaround:

1. Comment out the `ssmRole`, `policyAttachment`, and `instanceProfile` resource blocks in `main.go`
2. In the AWS Console, go to IAM → Instance Profiles and find the name of the LabRole instance profile
3. On both `ec2.NewInstance` calls, replace `IamInstanceProfile: instanceProfile.Name` with:
   ```go
   IamInstanceProfile: pulumi.String("LabInstanceProfile"),
   ```
   (substitute the actual profile name you found in the console)

LabRole already carries `AmazonSSMManagedInstanceCore` permissions, so SSM access will work.

---

## Cleanup

The NAT Gateway costs approximately **$0.045/hour** plus data transfer. Always destroy when finished:

```bash
pulumi destroy
```

This takes about 2 minutes as the NAT Gateway deprovisions.

---

## Connection to the WAF audit

The change from SSH to SSM closes two of the Security pillar gaps your Week 8 audit identifies:

**Gap 1 — Key lifecycle** is eliminated. There is no key to distribute, copy, lose, or rotate. IAM handles identity — remove a user's `ssm:StartSession` permission and their access is gone in seconds.

**Gap 2 — Session audit** is resolved. Every command run in an SSM session is logged to CloudWatch Logs with the IAM identity, timestamp, and full command text. "Who connected" and "what did they do" are both answered.

The bastion SG strength from Lab 3 — limiting inbound to port 22 only — is retained and improved: the new security groups have no inbound rules at all.

This is the production pattern for EC2 admin access that your ADR Option 3 describes.
