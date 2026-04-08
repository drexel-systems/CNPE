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
# SDK Docs:
#   BucketV2:               https://www.pulumi.com/registry/packages/aws/api-docs/s3/bucketv2/
#   BucketPublicAccessBlock: https://www.pulumi.com/registry/packages/aws/api-docs/s3/bucketpublicaccessblock/
#   → Click the Python tab → read the Args section for each
#
# Hint: aws.s3.BucketV2(...) and aws.s3.BucketPublicAccessBlock(...)
# ---------------------------------------------------------------------------

# bucket = aws.s3.BucketV2(...)   # <-- uncomment and complete this

# aws.s3.BucketPublicAccessBlock(...)   # <-- uncomment and complete this


# ---------------------------------------------------------------------------
# PROVIDED: IAM Trust Policy — defines WHO can assume this role
#
# Every IAM role has two parts:
#   1. A trust policy: WHO is allowed to assume (use) this role
#   2. A permission policy: WHAT the role is allowed to do (TODO 3)
#
# This trust policy says: "The EC2 service is allowed to assume this role."
# AWS requires this exact JSON structure — the Version, Statement, Effect,
# Principal, and Action fields are all mandatory. Don't change this.
#
# "sts:AssumeRole" is the AWS action that lets a service "put on" a role
# and get temporary credentials. Without this, EC2 can't use the role at all.
# ---------------------------------------------------------------------------
assume_role_policy = json.dumps({
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Service": "ec2.amazonaws.com"  # Only EC2 instances can assume this role
        },
        "Action": "sts:AssumeRole"
    }]
})

# ---------------------------------------------------------------------------
# TODO 2: Create the IAM Role using the trust policy above
#
# The trust policy is already written for you. Your job is to create the
# Role resource that uses it.
#
# SDK Docs: https://www.pulumi.com/registry/packages/aws/api-docs/iam/role/
#   → Click the Python tab → the assume_role_policy argument is what connects
#     the trust policy above to this resource
#
# Hint: aws.iam.Role("ec2-s3-read-role", assume_role_policy=assume_role_policy, ...)
# ---------------------------------------------------------------------------

# role = aws.iam.Role(...)   # <-- uncomment and complete this


# ---------------------------------------------------------------------------
# TODO 3: Attach a Permission Policy to the Role
#
# SDK Docs: https://www.pulumi.com/registry/packages/aws/api-docs/iam/rolepolicy/
#   → Click the Python tab → note how policy expects a JSON string, not a dict
#
# Now define WHAT the role can do. Grant read-only access to your S3 bucket.
#
# AWS S3 ARN format — two shapes, both required:
#   arn:aws:s3:::bucket-name        ← the bucket itself   (needed for ListBucket)
#   arn:aws:s3:::bucket-name/*      ← objects inside it   (needed for GetObject)
#
# The bucket name isn't known until Pulumi creates the bucket, so we use
# .apply() to build the policy string once the real name is available.
# Here is the exact structure to follow — fill in the Resource values:
#
#   role_policy = aws.iam.RolePolicy(
#       "ec2-s3-read-policy",
#       role=role.id,
#       policy=bucket.id.apply(lambda name: json.dumps({
#           "Version": "2012-10-17",
#           "Statement": [
#               {
#                   "Effect": "Allow",
#                   "Action": "s3:ListBucket",
#                   "Resource": f"arn:aws:s3:::{name}",      # ← bucket itself
#               },
#               {
#                   "Effect": "Allow",
#                   "Action": "s3:GetObject",
#                   "Resource": f"arn:aws:s3:::{name}/*",    # ← objects inside
#               },
#           ],
#       }))
#   )
#
# Do NOT add s3:PutObject or s3:DeleteObject — read-only is all we need.
# ---------------------------------------------------------------------------

# role_policy = aws.iam.RolePolicy(...)   # <-- uncomment and complete this


# ---------------------------------------------------------------------------
# TODO 4: Create an IAM Instance Profile
#
# You cannot attach an IAM Role directly to an EC2 instance.
# EC2 requires an Instance Profile — a wrapper that holds exactly one role.
# Think of it as the ID badge that lets the role "walk through the door."
#
# SDK Docs: https://www.pulumi.com/registry/packages/aws/api-docs/iam/instanceprofile/
#   → Click the Python tab → note the role argument takes role.name, not role.id
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
# SDK Docs: https://www.pulumi.com/registry/packages/aws/api-docs/ec2/instance/
#   → Search for iam_instance_profile in the Args section
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
