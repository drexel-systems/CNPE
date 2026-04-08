"""
Lab 2 — Part 2: S3, IAM, and the Right Way to Handle Credentials
-----------------------------------------------------------------
Your task: complete the TODOs below to add an S3 bucket and IAM role
so the EC2 instance can access S3 using temporary credentials.

The AMI lookup and security group are provided (same as Part 1).
You need to write:
  1. An S3 bucket to store website content
  2. An IAM Role that allows EC2 to assume it
  3. An IAM Role Policy granting read access to your bucket
  4. An IAM Instance Profile (wraps the role for attachment to EC2)
  5. An EC2 Instance with the instance profile attached

Run before deploying:
  pulumi config set aws:region us-east-1
  pulumi preview
  pulumi up
"""
import json
import pulumi
import pulumi_aws as aws

# ---------------------------------------------------------------------------
# PROVIDED: AMI Lookup
# ---------------------------------------------------------------------------
ami = aws.ec2.get_ami(
    owners=["137112412989"],
    filters=[{
        "name": "image-id",
        "values": ["ami-0a101d355d07a638e"],
    }],
    most_recent=True,
)

# ---------------------------------------------------------------------------
# PROVIDED: Security Group (SSH + web server)
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
            "description": "SSH",
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
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
        "description": "Allow all outbound (required for S3 API calls)",
    }],
    tags={"Name": "lab2-part2-sg", "Lab": "2-Part2"},
)

# ---------------------------------------------------------------------------
# TODO 1: Create an S3 Bucket
#
# Create a BucketV2 resource named "novaspark-website".
# Pulumi will append a random suffix to ensure the name is globally unique.
#
# Also create a BucketPublicAccessBlock to block all public access.
# The EC2 instance will read from S3 via its IAM role — not via public URL.
# This is the secure pattern: never expose a bucket publicly unless required.
#
# Hint: aws.s3.BucketV2(...) and aws.s3.BucketPublicAccessBlock(...)
# ---------------------------------------------------------------------------

# bucket = aws.s3.BucketV2(...)   # <-- uncomment and complete this

# aws.s3.BucketPublicAccessBlock(...)   # <-- uncomment and complete this


# ---------------------------------------------------------------------------
# TODO 2: Create an IAM Role
#
# An IAM Role is a set of permissions that can be *assumed* by an AWS service.
# You need to define WHO can assume this role (an assume_role_policy).
#
# The assume_role_policy is a JSON document. The Principal should be
# the EC2 service: {"Service": "ec2.amazonaws.com"}
# The Action should be: "sts:AssumeRole"
#
# Hint: json.dumps({...}) to serialize the policy
#       aws.iam.Role("ec2-s3-read-role", assume_role_policy=..., ...)
# ---------------------------------------------------------------------------

# assume_role_policy = json.dumps({...})   # <-- complete this
# role = aws.iam.Role(...)                 # <-- uncomment and complete this


# ---------------------------------------------------------------------------
# TODO 3: Attach a Policy to the Role
#
# Define WHAT the role can do. Grant it:
#   - s3:ListBucket on the bucket ARN (format: arn:aws:s3:::bucket-name)
#   - s3:GetObject on all objects in the bucket (format: arn:aws:s3:::bucket-name/*)
#
# Scope this to YOUR bucket only — not all of S3. This is "least privilege."
# Note: do NOT grant s3:PutObject or s3:DeleteObject — read-only.
#
# Hint: aws.iam.RolePolicy(..., role=role.id, policy=bucket.id.apply(lambda name: json.dumps({...})))
# The .apply() pattern lets you use the bucket's actual name (known only after deploy)
# inside the policy JSON.
# ---------------------------------------------------------------------------

# role_policy = aws.iam.RolePolicy(...)   # <-- uncomment and complete this


# ---------------------------------------------------------------------------
# TODO 4: Create an IAM Instance Profile
#
# You cannot attach an IAM Role directly to an EC2 instance.
# EC2 requires an Instance Profile — a wrapper that holds exactly one role.
# Think of it as the ID badge that lets the role "walk through the door."
#
# Hint: aws.iam.InstanceProfile("ec2-instance-profile", role=role.name, ...)
# ---------------------------------------------------------------------------

# instance_profile = aws.iam.InstanceProfile(...)   # <-- uncomment and complete this


# ---------------------------------------------------------------------------
# TODO 5: Create the EC2 Instance with the Instance Profile Attached
#
# Same as Part 1, with one addition: attach the instance profile.
# Use iam_instance_profile=instance_profile.name on the Instance resource.
#
# This single line is what transforms the instance from "no AWS access"
# to "gets temporary, scoped credentials automatically."
# ---------------------------------------------------------------------------

# server = aws.ec2.Instance(...)   # <-- uncomment and complete this


# ---------------------------------------------------------------------------
# PROVIDED: Outputs
# NOTE: This section will error until you define `server` and `bucket` above.
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

# CLEANUP: Before `pulumi destroy`, empty the bucket first:
#   aws s3 rm s3://$(pulumi stack output bucketName) --recursive
# Then: pulumi destroy
