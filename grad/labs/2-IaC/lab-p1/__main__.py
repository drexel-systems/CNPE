"""
Lab 2 — Part 1: Your First Infrastructure Deployment
------------------------------------------------------
This Pulumi program deploys a minimal EC2 instance that serves the NovaSpark
website manually via SSH. It is intentionally simple — the fragility of this
approach is the point. By the end of Part 3, everything here will be automated.

As you read this code, ask yourself:
  - Why is the AMI owner ID specified? What risk does that mitigate?
  - Why are two separate ingress rules needed instead of one?
  - What happens to the website if this instance is terminated or rebooted?
  - What's missing here that Part 2 adds?

SETUP:
  pulumi stack init dev
  pulumi config set aws:region us-east-1

DEPLOY:
  pulumi preview    ← always preview before committing
  pulumi up

CLEANUP:
  pulumi destroy
"""
import pulumi
import pulumi_aws as aws

# ---------------------------------------------------------------------------
# 1. AMI Lookup — Amazon Linux 2 (ARM64 / Graviton)
#
# We pin to a specific AMI ID rather than using `most_recent=True` with a
# name filter. Pinning guarantees reproducibility — the same AMI is used
# every time regardless of when `pulumi up` runs. Using `most_recent` can
# silently pull a different OS version between deploys.
#
# The owner ID (137112412989) is Amazon's official AWS account. Specifying
# it prevents accidentally matching a community AMI with the same name that
# could contain modified or malicious software.
# ---------------------------------------------------------------------------
ami = aws.ec2.get_ami(
    owners=["137112412989"],
    filters=[{
        "name": "image-id",
        "values": ["ami-0a101d355d07a638e"],  # Amazon Linux 2 ARM64 in us-east-1
    }],
    most_recent=True,
)

# ---------------------------------------------------------------------------
# 2. Security Group — the virtual firewall for this instance
#
# AWS blocks ALL inbound traffic by default. Every port that needs to be
# reachable must be explicitly opened here. This default-deny posture is
# a foundational AWS security principle — contrast it with on-premises
# environments where the default is often "allow unless blocked."
#
# Port 22  — SSH, so we can connect and configure the instance manually.
# Port 8080 — Python's built-in HTTP server. Port 80 requires root privileges
#             to bind to; running a web server as root is a security risk.
#             Port 8080 lets us serve as a normal user.
#
# Design tradeoff: cidr_blocks=["0.0.0.0/0"] allows SSH from anywhere.
# In production, this would be locked to a specific IP or VPN CIDR.
# ---------------------------------------------------------------------------
sec_group = aws.ec2.SecurityGroup(
    "ssh-web-access",
    description="Allow SSH (22) and web server (8080) inbound",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "SSH — tighten to your IP in production",
        },
        {
            "protocol": "tcp",
            "from_port": 8080,
            "to_port": 8080,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Python HTTP server",
        },
    ],
    egress=[{
        "protocol": "-1",   # -1 = all protocols
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
        "description": "Allow all outbound",
    }],
    tags={"Name": "lab2-part1-sg", "Lab": "2-Part1"},
)

# ---------------------------------------------------------------------------
# 3. EC2 Instance
#
# instance_type="t4g.micro": the "g" in t4g = Graviton (ARM). This must
# match the ARM AMI above — mixing architectures causes a launch failure.
# Graviton is ~20% cheaper than the equivalent x86 (t3.micro) for the
# same workload, which matters at scale.
#
# key_name="vockey": the pre-provisioned key pair in your Learner Lab.
# This is what lets `ssh -i labsuser.pem` work. Without it, the instance
# launches but is unreachable via SSH.
#
# Notice what's NOT here: no IAM role, no user_data, no tags beyond the
# default. Part 2 adds the IAM role. Part 3 adds user_data and full tagging.
# ---------------------------------------------------------------------------
server = aws.ec2.Instance(
    "lab-instance",
    instance_type="t4g.micro",
    vpc_security_group_ids=[sec_group.id],
    ami=ami.id,
    key_name="vockey",
    tags={"Name": "lab2-part1-webserver", "Lab": "2-Part1"},
)

# ---------------------------------------------------------------------------
# Outputs — printed after `pulumi up` so you have everything you need
# without hunting through the AWS console.
# ---------------------------------------------------------------------------
pulumi.export("publicIp", server.public_ip)
pulumi.export("publicDns", server.public_dns)
pulumi.export("sshCommand", server.public_dns.apply(
    lambda dns: f"ssh -i ~/.ssh/labsuser.pem ec2-user@{dns}"
))
pulumi.export("websiteUrl", server.public_dns.apply(
    lambda dns: f"http://{dns}:8080"
))

# CLEANUP: pulumi destroy
# To avoid stale SSH known_hosts entries after destroy:
#   ssh-keygen -R <publicDns>
