"""
Lab 2 — Part 3: Full Automation with Pulumi
--------------------------------------------
Your task: complete the TODO below to make the deployment fully automated.

The S3 bucket, file uploads, IAM role, and security group are provided.
Your job is to write the `make_user_data` function that generates the
bootstrap script — the piece that installs and starts the web server
automatically when the EC2 instance boots for the first time.

This is the payoff of the whole lab: one `pulumi up` deploys everything,
no SSH required to configure the instance.

Run before deploying:
  pulumi config set aws:region us-east-1
  pulumi preview
  pulumi up
  # Wait ~90 seconds, then visit the websiteUrl output
"""
import json
import os
import pulumi
import pulumi_aws as aws

# ---------------------------------------------------------------------------
# PROVIDED: AMI Lookup
# ---------------------------------------------------------------------------
ami = aws.ec2.get_ami(
    owners=["137112412989"],
    filters=[{"name": "image-id", "values": ["ami-0a101d355d07a638e"]}],
    most_recent=True,
)

# ---------------------------------------------------------------------------
# PROVIDED: S3 Bucket + public access block
# ---------------------------------------------------------------------------
bucket = aws.s3.BucketV2(
    "novaspark-website",
    force_destroy=True,
    tags={"Name": "novaspark-website", "Lab": "2-Part3", "ManagedBy": "Pulumi"},
)

aws.s3.BucketPublicAccessBlock(
    "novaspark-website-block-public",
    bucket=bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# ---------------------------------------------------------------------------
# PROVIDED: Upload website files from website/ directory
#
# Pulumi hashes each file and only re-uploads files that have changed.
# Try it: edit website/index.html and re-run `pulumi up` — only that
# file gets updated, nothing else changes.
# ---------------------------------------------------------------------------
website_files = {
    "index.html": "text/html",
    "about.html": "text/html",
}

for filename, content_type in website_files.items():
    aws.s3.BucketObject(
        filename,
        bucket=bucket.id,
        key=filename,
        source=pulumi.FileAsset(os.path.join("website", filename)),
        content_type=content_type,
    )

# ---------------------------------------------------------------------------
# PROVIDED: IAM Role + Instance Profile (same as Part 2)
# ---------------------------------------------------------------------------
assume_role_policy = json.dumps({
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ec2.amazonaws.com"},
        "Action": "sts:AssumeRole",
    }],
})

role = aws.iam.Role(
    "ec2-s3-read-role",
    assume_role_policy=assume_role_policy,
    description="Allows EC2 to read from the NovaSpark website S3 bucket",
    tags={"Lab": "2-Part3", "ManagedBy": "Pulumi"},
)

aws.iam.RolePolicy(
    "ec2-s3-read-policy",
    role=role.id,
    policy=bucket.id.apply(
        lambda bucket_name: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": "s3:ListBucket",
                 "Resource": f"arn:aws:s3:::{bucket_name}"},
                {"Effect": "Allow", "Action": "s3:GetObject",
                 "Resource": f"arn:aws:s3:::{bucket_name}/*"},
            ],
        })
    ),
)

instance_profile = aws.iam.InstanceProfile(
    "ec2-instance-profile",
    role=role.name,
    tags={"Lab": "2-Part3", "ManagedBy": "Pulumi"},
)

# ---------------------------------------------------------------------------
# PROVIDED: Security Group
# ---------------------------------------------------------------------------
sec_group = aws.ec2.SecurityGroup(
    "novaspark-web-sg",
    description="NovaSpark web server — SSH and port 8080",
    ingress=[
        {"protocol": "tcp", "from_port": 22, "to_port": 22,
         "cidr_blocks": ["0.0.0.0/0"], "description": "SSH"},
        {"protocol": "tcp", "from_port": 8080, "to_port": 8080,
         "cidr_blocks": ["0.0.0.0/0"], "description": "Web server"},
    ],
    egress=[{"protocol": "-1", "from_port": 0, "to_port": 0,
             "cidr_blocks": ["0.0.0.0/0"]}],
    tags={"Name": "lab2-part3-sg", "Lab": "2-Part3"},
)

# ---------------------------------------------------------------------------
# TODO: Write the make_user_data function
#
# This function receives the actual S3 bucket name (resolved at deploy time
# by Pulumi's .apply()) and must return a bash script string that:
#
#   1. Installs python3-pip and boto3
#      (use: dnf update -y && dnf install -y python3-pip && pip3 install boto3)
#
#   2. Writes s3_webserver.py to /home/ec2-user/s3_webserver.py
#      Read the file from disk using: open("s3_webserver.py", "r").read()
#      Write it to the instance using a heredoc in the bash script
#
#   3. Creates a systemd service at /etc/systemd/system/novaspark-web.service
#      The service must pass the bucket name via an Environment= directive:
#         Environment=S3_BUCKET_NAME=<bucket_name>
#      ExecStart should run: /usr/bin/python3 /home/ec2-user/s3_webserver.py
#
#   4. Enables and starts the service:
#      systemctl daemon-reload
#      systemctl enable novaspark-web.service
#      systemctl start novaspark-web.service
#
# The script must start with: #!/bin/bash
# Add logging with: exec > >(tee /var/log/user-data.log) 2>&1
# This lets you check bootstrap progress via: sudo cat /var/log/user-data.log
#
# IMPORTANT: The bucket name is only known after S3 creates the bucket.
# That's why this is a function — Pulumi calls it via .apply() once the
# real bucket name is available.
# ---------------------------------------------------------------------------
def make_user_data(bucket_name: str) -> str:
    # Read the web server script from the local project directory
    script_path = os.path.join(os.path.dirname(__file__), "s3_webserver.py")
    with open(script_path, "r") as f:
        server_script = f.read()

    # TODO: Build and return a bash script string that does the 4 steps above.
    # Use an f-string so you can substitute bucket_name and server_script.
    # Hint: use heredocs (cat > /path/to/file << 'EOF' ... EOF) to write
    # multi-line files inside a bash script.

    raise NotImplementedError("Complete the make_user_data function")


# ---------------------------------------------------------------------------
# PROVIDED: EC2 Instance — uses your make_user_data function
#
# bucket.id.apply(make_user_data) calls your function with the real bucket
# name once Pulumi knows it (after creating the bucket).
# user_data_replace_on_change=True means: if the bootstrap script changes,
# Pulumi replaces the instance entirely (immutable infrastructure pattern).
# ---------------------------------------------------------------------------
user_data = bucket.id.apply(make_user_data)

server = aws.ec2.Instance(
    "novaspark-server",
    instance_type="t4g.micro",
    vpc_security_group_ids=[sec_group.id],
    ami=ami.id,
    key_name="vockey",
    iam_instance_profile=instance_profile.name,
    user_data=user_data,
    user_data_replace_on_change=True,
    tags={"Name": "lab2-part3-automated", "Lab": "2-Part3", "ManagedBy": "Pulumi"},
)

# ---------------------------------------------------------------------------
# PROVIDED: Outputs
# ---------------------------------------------------------------------------
pulumi.export("publicIp", server.public_ip)
pulumi.export("publicDns", server.public_dns)
pulumi.export("bucketName", bucket.id)
pulumi.export("websiteUrl", server.public_dns.apply(lambda dns: f"http://{dns}:8080"))
pulumi.export("sshCommand", server.public_dns.apply(
    lambda dns: f"ssh -i ~/.ssh/labsuser.pem ec2-user@{dns}"
))
pulumi.export("checkBootstrap", server.public_dns.apply(
    lambda dns: f"ssh -i ~/.ssh/labsuser.pem ec2-user@{dns} 'sudo journalctl -u novaspark-web -n 30'"
))

# CLEANUP: pulumi destroy  (force_destroy=True handles the bucket automatically)
