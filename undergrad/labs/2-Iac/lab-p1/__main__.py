"""
Lab 2 — Part 1: Your First Infrastructure Deployment
-----------------------------------------------------
Your task: complete the TODOs below to deploy an EC2 instance
that serves the NovaSpark website on port 8080.

The AMI lookup is done for you. You need to write:
  1. A Security Group that allows SSH (port 22) and web traffic (port 8080)
  2. An EC2 Instance using the AMI above, connected to the security group

Run before deploying:
  pulumi config set aws:region us-east-1
  pulumi preview   ← always preview before deploying
  pulumi up
"""
import pulumi
import pulumi_aws as aws

# ---------------------------------------------------------------------------
# PROVIDED: AMI Lookup — Amazon Linux 2 (ARM64 / Graviton)
#
# This finds the specific AMI we need. The owner ID (137112412989) is
# Amazon's official AWS account — we specify it to avoid pulling a
# random community AMI with the same name.
# ---------------------------------------------------------------------------
ami = aws.ec2.get_ami(
    owners=["137112412989"],
    filters=[
        {
            "name": "image-id",
            "values": ["ami-0a101d355d07a638e"],
        }
    ]
)

# ---------------------------------------------------------------------------
# TODO 1: Define a Security Group
#
# Create a SecurityGroup resource named 'ssh-web-access' that allows:
#   - Inbound TCP on port 22 from anywhere (SSH)
#   - Inbound TCP on port 8080 from anywhere (web server)
#
# SDK Docs: https://www.pulumi.com/registry/packages/aws/api-docs/ec2/securitygroup/
#   → Click the Python tab → read the Args section → look at ingress
#
# Hint: use aws.ec2.SecurityGroup(...)
#   ingress is a list of dicts with keys:
#     protocol, from_port, to_port, cidr_blocks, description
#
# Why port 8080 instead of 80?
# Port 80 requires root privileges to bind to. Running a web server as
# root is a security risk — port 8080 lets us run as a normal user.
# ---------------------------------------------------------------------------

# sec_group = aws.ec2.SecurityGroup(...)   # <-- uncomment and complete this


# ---------------------------------------------------------------------------
# TODO 2: Define an EC2 Instance
#
# Create an Instance resource named 'lab-instance' with:
#   - instance_type: 't4g.micro'  (ARM Graviton — must match the ARM AMI)
#   - ami: use ami.id from the lookup above
#   - vpc_security_group_ids: attach your security group from TODO 1
#   - key_name: 'vockey'  (the pre-created key pair in your Learner Lab)
#
# SDK Docs: https://www.pulumi.com/registry/packages/aws/api-docs/ec2/instance/
#   → Click the Python tab → read the Args section
#
# Hint: use aws.ec2.Instance(...)
# Why t4g.micro? The 'g' in t4g = Graviton (ARM). Using a t3.micro (x86)
# with an ARM AMI will fail. Architecture must match.
# ---------------------------------------------------------------------------

# server = aws.ec2.Instance(...)   # <-- uncomment and complete this


# ---------------------------------------------------------------------------
# PROVIDED: Export outputs
#
# These will print after `pulumi up` so you have a ready-to-run SSH command
# and website URL without hunting through the AWS console.
#
# NOTE: This section will error until you define `server` above.
# ---------------------------------------------------------------------------
pulumi.export('publicIp', server.public_ip)
pulumi.export('publicDns', server.public_dns)
pulumi.export('sshCommand', server.public_dns.apply(
    lambda dns: f"ssh -i ~/.ssh/labsuser.pem ec2-user@{dns}"
))
pulumi.export('websiteUrl', server.public_dns.apply(
    lambda dns: f"http://{dns}:8080"
))

# REMEMBER TO RUN `pulumi destroy` when done — do not leave instances running!
