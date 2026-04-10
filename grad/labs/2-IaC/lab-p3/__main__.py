"""
Lab 2 — Part 3: Fully Automated NovaSpark Deployment
------------------------------------------------------
This Pulumi program automates EVERYTHING from Part 2:
  1. S3 Bucket              — created programmatically
  2. Website Files          — uploaded from the local website/ directory
  3. IAM Role + Profile     — created and attached automatically
  4. EC2 Instance           — provisioned with the IAM role attached
  5. Web Server Bootstrap   — installed and started via user_data (no SSH needed!)

When you run `pulumi up`, the entire NovaSpark website will be running
in roughly 90 seconds — no SSH, no manual steps, no forgotten config.

That's the point of Infrastructure as Code.

SETUP (one time):
  export PULUMI_CONFIG_PASSPHRASE=""
  pulumi stack init dev
  pulumi config set aws:region us-east-1

DEPLOY:
  pulumi up

VERIFY (wait ~90s after deploy):
  open $(pulumi stack output websiteUrl)   # or paste the URL in a browser

CLEANUP:
  pulumi destroy    # Pulumi empties the bucket for you, then deletes everything
"""

import os
import pulumi
import pulumi_aws as aws

# ---------------------------------------------------------------------------
# 1. AMI — Amazon Linux 2 (ARM64 / Graviton)
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
# 2. S3 Bucket — website content storage
# ---------------------------------------------------------------------------
bucket = aws.s3.BucketV2(
    "novaspark-website",
    force_destroy=True,   # Lets Pulumi empty and delete the bucket on `pulumi destroy`
    tags={
        "Name": "novaspark-website",
        "Lab": "2-Part3",
        "ManagedBy": "Pulumi",
    },
)

# Block all public access — EC2 reads from S3 via IAM role, not public URLs
aws.s3.BucketPublicAccessBlock(
    "novaspark-website-block-public",
    bucket=bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# ---------------------------------------------------------------------------
# 3. Upload website files from the local website/ directory
#
#    Pulumi treats these as FileAssets — it computes a hash of each file
#    and only uploads changed files on subsequent `pulumi up` runs.
#    Try it: edit index.html and re-run `pulumi up` — only that file updates.
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
# 4. IAM Role + Instance Profile
#    Same pattern as Part 2, but now fully automated (no manual console clicks)
#    AWS Academy restricts iam:CreateRole — use the pre-existing LabRole instead
# ---------------------------------------------------------------------------
lab_role = aws.iam.get_role(name="LabRole")

instance_profile = aws.iam.InstanceProfile(
    "ec2-instance-profile",
    role=lab_role.name,
)

# ---------------------------------------------------------------------------
# 5. Security Group
# ---------------------------------------------------------------------------
sec_group = aws.ec2.SecurityGroup(
    "novaspark-web-sg",
    description="NovaSpark web server - SSH and port 8080",
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
            "description": "Web server",
        },
    ],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
    }],
    tags={"Name": "lab2-part3-sg", "Lab": "2-Part3"},
)

# ---------------------------------------------------------------------------
# 6. User Data Script
#
#    user_data runs as root once when the instance first boots. It's our
#    "bootstrap" script — it installs software, copies files, and starts
#    services without anyone ever needing to SSH in.
#
#    We use Pulumi's .apply() to substitute the real bucket name into
#    the script at deployment time (before it's sent to AWS).
#
#    The server script is injected as a heredoc and the bucket name is
#    passed to it via a systemd Environment= directive — a clean pattern
#    that works identically across dev, staging, and prod environments.
# ---------------------------------------------------------------------------
def make_user_data(bucket_name: str) -> str:
    # Read the web server script from our local project directory
    script_path = os.path.join(os.path.dirname(__file__), "s3_webserver.py")
    with open(script_path, "r") as f:
        server_script = f.read()

    return f"""#!/bin/bash
set -euo pipefail
exec > >(tee /var/log/user-data.log) 2>&1

echo "=== NovaSpark Bootstrap Starting ==="
echo "Bucket: {bucket_name}"

# Update and install pip
dnf update -y
dnf install -y python3-pip

# Install boto3 (AWS SDK for Python)
pip3 install boto3

# Write the web server script
cat > /home/ec2-user/s3_webserver.py << 'PYEOF'
{server_script}
PYEOF

chmod +x /home/ec2-user/s3_webserver.py
chown ec2-user:ec2-user /home/ec2-user/s3_webserver.py

# Create a systemd service so the server starts automatically on boot
# The bucket name is passed in as an environment variable — no hardcoding!
cat > /etc/systemd/system/novaspark-web.service << 'SVCEOF'
[Unit]
Description=NovaSpark S3 Web Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user
Environment=S3_BUCKET_NAME={bucket_name}
ExecStart=/usr/bin/python3 /home/ec2-user/s3_webserver.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

# Enable and start the service
systemctl daemon-reload
systemctl enable novaspark-web.service
systemctl start novaspark-web.service

echo "=== NovaSpark Bootstrap Complete ==="
echo "Web server started. Check: systemctl status novaspark-web"
"""

user_data = bucket.id.apply(make_user_data)

# ---------------------------------------------------------------------------
# 7. EC2 Instance — fully configured, no SSH required after deploy
# ---------------------------------------------------------------------------
server = aws.ec2.Instance(
    "novaspark-server",
    instance_type="t4g.micro",
    vpc_security_group_ids=[sec_group.id],
    ami=ami.id,
    key_name="vockey",                          # Still included so you CAN ssh in to verify
    iam_instance_profile=instance_profile.name,
    user_data=user_data,                        # Bootstrap script runs on first boot
    user_data_replace_on_change=True,           # Replace instance if user_data changes
    tags={
        "Name": "lab2-part3-automated",
        "Lab": "2-Part3",
        "ManagedBy": "Pulumi",
    },
)

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
pulumi.export("publicIp", server.public_ip)
pulumi.export("publicDns", server.public_dns)
pulumi.export("bucketName", bucket.id)
pulumi.export("websiteUrl", server.public_dns.apply(
    lambda dns: f"http://{dns}:8080"
))
pulumi.export("sshCommand", server.public_dns.apply(
    lambda dns: f"ssh -i ~/.ssh/labsuser.pem ec2-user@{dns}"
))

# Helpful commands to check the server status after deploy
pulumi.export("checkBootstrap", server.public_dns.apply(
    lambda dns: f"ssh -i ~/.ssh/labsuser.pem ec2-user@{dns} 'sudo journalctl -u novaspark-web -n 30'"
))
