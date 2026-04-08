"""
Lab 2 — Part 2: EC2 + S3 + IAM Role
-------------------------------------
This Pulumi program builds on Part 1 by adding the AWS infrastructure
needed to serve website content from S3:

  1. A Security Group          — SSH (22) and web server (8080) access
  2. An S3 Bucket              — stores the NovaSpark HTML files
  3. An IAM Role               — trusted by EC2, grants read access to the bucket
  4. An IAM Instance Profile   — wraps the role so it can attach to an EC2 instance
  5. An EC2 Instance           — t4g.micro with the instance profile attached

NOTE: This program provisions the INFRASTRUCTURE only. Students will manually:
  - SSH into the instance
  - Upload HTML files to the S3 bucket via the AWS CLI
  - Copy s3_webserver.py from lab-p3/ and run it manually

The goal is to understand each piece before Part 3 automates everything.

REMEMBER to run before deploying:
  export PULUMI_CONFIG_PASSPHRASE=""
  pulumi config set aws:region us-east-1
"""

import json
import pulumi
import pulumi_aws as aws

# ---------------------------------------------------------------------------
# 1. AMI — Amazon Linux 2 (ARM64 / Graviton)
#    Using a specific AMI ID for reproducibility in the Learner Lab.
#    t4g.micro is ARM-based (Graviton), which is cheaper and more efficient
#    than x86 equivalents — but requires an ARM AMI.
# ---------------------------------------------------------------------------
ami = aws.ec2.get_ami(
    owners=["137112412989"],  # Amazon's official AWS account ID
    filters=[{
        "name": "image-id",
        "values": ["ami-0a101d355d07a638e"],  # Amazon Linux 2 ARM64 in us-east-1
    }],
    most_recent=True,
)

# ---------------------------------------------------------------------------
# 2. Security Group — allow SSH and web server traffic
# ---------------------------------------------------------------------------
sec_group = aws.ec2.SecurityGroup(
    "web-ssh-access",
    description="Allow SSH (22) and web server (8080) inbound, all outbound",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "SSH from anywhere (tighten this in production!)",
        },
        {
            "protocol": "tcp",
            "from_port": 8080,
            "to_port": 8080,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Python web server",
        },
    ],
    egress=[{
        "protocol": "-1",   # -1 means ALL protocols
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
        "description": "Allow all outbound (required for S3 API calls)",
    }],
    tags={
        "Name": "lab2-part2-sg",
        "Lab": "2-Part2",
    },
)

# ---------------------------------------------------------------------------
# 3. S3 Bucket — stores the NovaSpark website HTML files
#    Pulumi appends a random suffix to the name to ensure global uniqueness.
# ---------------------------------------------------------------------------
bucket = aws.s3.BucketV2(
    "novaspark-website",
    tags={
        "Name": "novaspark-website",
        "Lab": "2-Part2",
    },
)

# Block all public access — the EC2 instance will read from S3 using
# its IAM role, not public URLs. This is the secure pattern.
aws.s3.BucketPublicAccessBlock(
    "novaspark-website-block-public",
    bucket=bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# ---------------------------------------------------------------------------
# 4. IAM Role — defines WHAT can assume this role and WHAT it can do
#
#    Two-part setup:
#      a) Assume Role Policy: WHO can use this role (EC2 service)
#      b) Role Policy:        WHAT this role can do (read from our bucket)
#
#    This is the "right way" to grant AWS access to EC2 instances.
#    No access keys. No secrets. Temporary credentials only.
# ---------------------------------------------------------------------------
assume_role_policy = json.dumps({
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Service": "ec2.amazonaws.com",  # Only EC2 instances can assume this role
        },
        "Action": "sts:AssumeRole",
    }],
})

role = aws.iam.Role(
    "ec2-s3-read-role",
    assume_role_policy=assume_role_policy,
    description="Allows EC2 to read from the NovaSpark website S3 bucket",
    tags={"Lab": "2-Part2"},
)

# Attach a policy that grants GetObject and ListBucket on OUR bucket only.
# This is "least privilege" — the instance can't touch other S3 buckets.
role_policy = aws.iam.RolePolicy(
    "ec2-s3-read-policy",
    role=role.id,
    policy=bucket.id.apply(
        lambda bucket_name: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "s3:ListBucket",
                    "Resource": f"arn:aws:s3:::{bucket_name}",
                },
                {
                    "Effect": "Allow",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*",
                },
            ],
        })
    ),
)

# ---------------------------------------------------------------------------
# 5. IAM Instance Profile — the "adapter" that lets an EC2 instance use a role
#    You can't attach an IAM Role directly to an EC2 instance.
#    You must wrap it in an Instance Profile first.
# ---------------------------------------------------------------------------
instance_profile = aws.iam.InstanceProfile(
    "ec2-instance-profile",
    role=role.name,
    tags={"Lab": "2-Part2"},
)

# ---------------------------------------------------------------------------
# 6. EC2 Instance — with the instance profile attached
# ---------------------------------------------------------------------------
server = aws.ec2.Instance(
    "lab2-part2-server",
    instance_type="t4g.micro",
    vpc_security_group_ids=[sec_group.id],
    ami=ami.id,
    key_name="vockey",
    iam_instance_profile=instance_profile.name,  # <-- This is what Part 1 was missing!
    tags={
        "Name": "lab2-part2-webserver",
        "Lab": "2-Part2",
    },
)

# ---------------------------------------------------------------------------
# Outputs — everything students need to work with this infrastructure
# ---------------------------------------------------------------------------
pulumi.export("publicIp", server.public_ip)
pulumi.export("publicDns", server.public_dns)
pulumi.export("instanceId", server.id)
pulumi.export("bucketName", bucket.id)

pulumi.export("sshCommand", server.public_dns.apply(
    lambda dns: f"ssh -i ~/.ssh/labsuser.pem ec2-user@{dns}"
))
pulumi.export("websiteUrl", server.public_dns.apply(
    lambda dns: f"http://{dns}:8080"
))
pulumi.export("uploadCommand", bucket.id.apply(
    lambda name: f"aws s3 cp ./website/ s3://{name}/ --recursive"
))

# CLEANUP REMINDER:
# Before running `pulumi destroy`, empty the bucket first:
#   aws s3 rm s3://$(pulumi stack output bucketName) --recursive
# Then:
#   pulumi destroy
