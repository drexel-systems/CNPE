"""
Lab 3 — NovaSpark Production VPC
----------------------------------
This Pulumi program builds a standard two-tier network architecture:

  Public subnets:   Internet-facing resources (load balancers, bastion hosts)
  Private subnets:  Application servers and databases — no direct internet exposure

Resources created:
  1. VPC                  10.0.0.0/16
  2. Public Subnet AZ-A   10.0.1.0/24
  3. Public Subnet AZ-B   10.0.2.0/24
  4. Private Subnet AZ-A  10.0.11.0/24
  5. Private Subnet AZ-B  10.0.12.0/24
  6. Internet Gateway     — public subnets route outbound traffic here
  7. Elastic IP           — static public IP for the NAT Gateway
  8. NAT Gateway          — private subnets route outbound traffic here
  9. Public Route Table   — 0.0.0.0/0 → Internet Gateway
  10. Private Route Table — 0.0.0.0/0 → NAT Gateway
  11. Bastion Host        — public EC2 instance, SSH entry point into VPC
  12. Private Instance    — private EC2 instance, no public IP, reachable only from within VPC

Architecture:
  Internet
    │
    ▼
  Internet Gateway
    │
    ▼
  Public Subnet ──── Bastion EC2 ──── (SSH hop) ────▶ Private Instance
    │                                                       │
    │ (NAT Gateway handles outbound traffic                 ▼
    │  from private subnets)                        can reach internet
    └──── NAT Gateway ◀─────────────────────────── via NAT (not directly)

⚠️ COST WARNING: The NAT Gateway costs ~$0.045/hour + data transfer fees.
   Always run `pulumi destroy` when finished with the lab!

SETUP:
  export PULUMI_CONFIG_PASSPHRASE=""
  pulumi stack init dev
  pulumi config set aws:region us-east-1

DEPLOY:
  pulumi preview
  pulumi up    (takes 4-6 minutes — NAT Gateway provisioning is slow)

CLEANUP:
  pulumi destroy
"""

import pulumi
import pulumi_aws as aws

# ---------------------------------------------------------------------------
# 1. AMI — Amazon Linux 2 (ARM64 / Graviton), consistent with Lab 2
#    t4g.micro is the cheapest general-purpose instance type in AWS.
# ---------------------------------------------------------------------------
ami = aws.ec2.get_ami(
    owners=["137112412989"],  # Amazon's official account ID
    filters=[{
        "name": "image-id",
        "values": ["ami-0a101d355d07a638e"],  # Amazon Linux 2 ARM64, us-east-1
    }],
    most_recent=True,
)

# ---------------------------------------------------------------------------
# 2. VPC — the private network boundary for all NovaSpark resources
#
#    CIDR 10.0.0.0/16 gives us 65,536 addresses to carve into subnets.
#    DNS hostnames are enabled so EC2 instances get human-readable names.
# ---------------------------------------------------------------------------
vpc = aws.ec2.Vpc(
    "novaspark-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,   # instances get a DNS name like ip-10-0-1-x.ec2.internal
    enable_dns_support=True,
    tags={"Name": "NovaSpark-VPC", "Lab": "3"},
)

# ---------------------------------------------------------------------------
# 3. Subnets
#
#    Public subnets (.1.x, .2.x):  resources here get public IPs automatically.
#    Private subnets (.11.x, .12.x): no public IPs — only accessible within VPC
#                                    (or through the NAT Gateway for outbound traffic).
#
#    The gap between .2.x and .11.x is intentional — it makes private and
#    public ranges visually distinct and leaves room for expansion.
#
#    Two AZs (us-east-1a, us-east-1b) is the minimum for high availability.
#    If one AZ has an outage, resources in the other continue running.
# ---------------------------------------------------------------------------
public_subnet_a = aws.ec2.Subnet(
    "public-subnet-a",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-east-1a",
    map_public_ip_on_launch=True,   # instances in this subnet get public IPs
    tags={"Name": "NovaSpark-Public-A", "Type": "Public", "Lab": "3"},
)

public_subnet_b = aws.ec2.Subnet(
    "public-subnet-b",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-east-1b",
    map_public_ip_on_launch=True,
    tags={"Name": "NovaSpark-Public-B", "Type": "Public", "Lab": "3"},
)

private_subnet_a = aws.ec2.Subnet(
    "private-subnet-a",
    vpc_id=vpc.id,
    cidr_block="10.0.11.0/24",
    availability_zone="us-east-1a",
    map_public_ip_on_launch=False,  # no public IPs — private subnet
    tags={"Name": "NovaSpark-Private-A", "Type": "Private", "Lab": "3"},
)

private_subnet_b = aws.ec2.Subnet(
    "private-subnet-b",
    vpc_id=vpc.id,
    cidr_block="10.0.12.0/24",
    availability_zone="us-east-1b",
    map_public_ip_on_launch=False,
    tags={"Name": "NovaSpark-Private-B", "Type": "Private", "Lab": "3"},
)

# ---------------------------------------------------------------------------
# 4. Internet Gateway — the VPC's connection to the public internet
#
#    Without an IGW, a VPC is completely isolated. Attaching one allows
#    resources in public subnets to send and receive internet traffic.
#    Private subnets do NOT route through the IGW — they use the NAT Gateway.
# ---------------------------------------------------------------------------
igw = aws.ec2.InternetGateway(
    "novaspark-igw",
    vpc_id=vpc.id,
    tags={"Name": "NovaSpark-IGW", "Lab": "3"},
)

# ---------------------------------------------------------------------------
# 5. Elastic IP + NAT Gateway
#
#    Private instances can't receive inbound internet connections, but they
#    still need OUTBOUND internet access (to pull package updates, reach AWS
#    APIs, etc.). The NAT Gateway provides this.
#
#    Flow: Private Instance → NAT Gateway → Internet Gateway → Internet
#          Internet → (dropped, unless it's a response to outbound traffic)
#
#    The Elastic IP gives the NAT Gateway a stable, known public IP address.
#    When private instances make outbound requests, the internet sees this IP.
#    This is useful for IP allowlisting (e.g., "only allow NovaSpark's NAT IP").
#
#    ⚠️ NAT Gateways cost ~$0.045/hour. Destroy when done!
# ---------------------------------------------------------------------------
nat_eip = aws.ec2.Eip(
    "nat-eip",
    domain="vpc",
    tags={"Name": "NovaSpark-NAT-EIP", "Lab": "3"},
)

nat_gateway = aws.ec2.NatGateway(
    "novaspark-nat",
    subnet_id=public_subnet_a.id,   # NAT Gateway lives in a PUBLIC subnet
    allocation_id=nat_eip.id,
    tags={"Name": "NovaSpark-NAT", "Lab": "3"},
    opts=pulumi.ResourceOptions(depends_on=[igw]),  # IGW must exist first
)

# ---------------------------------------------------------------------------
# 6. Route Tables and Associations
#
#    A route table is like a GPS for network packets — it tells them where
#    to go based on their destination IP address.
#
#    Public Route Table:
#      10.0.0.0/16 → local (VPC internal traffic, implicit)
#      0.0.0.0/0   → Internet Gateway (everything else goes to the internet)
#
#    Private Route Table:
#      10.0.0.0/16 → local (VPC internal traffic, implicit)
#      0.0.0.0/0   → NAT Gateway (outbound goes through NAT, inbound is blocked)
# ---------------------------------------------------------------------------

# --- Public Route Table (provided as a model) ---
public_rt = aws.ec2.RouteTable(
    "public-rt",
    vpc_id=vpc.id,
    tags={"Name": "NovaSpark-Public-RT", "Lab": "3"},
)

public_route = aws.ec2.Route(
    "public-default-route",
    route_table_id=public_rt.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=igw.id,   # all internet traffic → Internet Gateway
)

aws.ec2.RouteTableAssociation("public-rt-assoc-a",
    subnet_id=public_subnet_a.id,
    route_table_id=public_rt.id,
)

aws.ec2.RouteTableAssociation("public-rt-assoc-b",
    subnet_id=public_subnet_b.id,
    route_table_id=public_rt.id,
)

# ---------------------------------------------------------------------------
# TODO 1: Private Route Table
#
#   Create a RouteTable resource for the private subnets, attached to `vpc.id`.
#   Name it "private-rt" and give it the tag Name="NovaSpark-Private-RT".
#
#   The Public Route Table above is the model — write the equivalent for private.
# ---------------------------------------------------------------------------
# private_rt = aws.ec2.RouteTable(...)


# ---------------------------------------------------------------------------
# TODO 2: Private Default Route
#
#   Create a Route resource for "private-default-route" that sends all traffic
#   (destination_cidr_block="0.0.0.0/0") to nat_gateway.id.
#
#   IMPORTANT: Use `nat_gateway_id` (not `gateway_id`) — that's the correct
#   argument when routing to a NAT Gateway instead of an Internet Gateway.
#
#   Route it through: private_rt.id → nat_gateway.id
# ---------------------------------------------------------------------------
# private_route = aws.ec2.Route(...)


# ---------------------------------------------------------------------------
# TODO 3: Private Route Table Associations
#
#   Associate the private route table with BOTH private subnets.
#   Follow the exact same pattern as public-rt-assoc-a and public-rt-assoc-b,
#   but use private_subnet_a, private_subnet_b, and private_rt instead.
#
#   Name them "private-rt-assoc-a" and "private-rt-assoc-b".
# ---------------------------------------------------------------------------
# aws.ec2.RouteTableAssociation("private-rt-assoc-a", ...)
# aws.ec2.RouteTableAssociation("private-rt-assoc-b", ...)


# ---------------------------------------------------------------------------
# 7. Security Groups
#
#    Bastion SG (provided as a model):
#      Port 22 from internet — it's the intended entry point.
#      In production you'd restrict this to your office IP.
#
# ---------------------------------------------------------------------------
bastion_sg = aws.ec2.SecurityGroup(
    "bastion-sg",
    vpc_id=vpc.id,
    description="Bastion host — SSH from internet",
    ingress=[{
        "protocol": "tcp",
        "from_port": 22,
        "to_port": 22,
        "cidr_blocks": ["0.0.0.0/0"],
        "description": "SSH from anywhere — restrict to your IP in production",
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
        "description": "All outbound",
    }],
    tags={"Name": "NovaSpark-Bastion-SG", "Lab": "3"},
)

# ---------------------------------------------------------------------------
# TODO 4: Private Security Group
#
#   Create a SecurityGroup named "private-sg" attached to vpc.id.
#   It should allow:
#     - INBOUND: TCP port 22 only from "10.0.0.0/16" (the VPC CIDR)
#                NOT from 0.0.0.0/0 — this instance is only reachable from
#                inside the VPC, not from the internet
#     - OUTBOUND: All traffic allowed (protocol="-1", from_port=0, to_port=0,
#                 cidr_blocks=["0.0.0.0/0"]) — outbound goes through the NAT Gateway
#
#   Description: "Private instance — SSH from within VPC only, no internet inbound"
#   Tag: Name="NovaSpark-Private-SG"
#
#   Use bastion_sg above as a model. The only difference is the ingress cidr_blocks.
# ---------------------------------------------------------------------------
# private_sg = aws.ec2.SecurityGroup(...)


# ---------------------------------------------------------------------------
# 8. EC2 Instances
#
#    Bastion Host (provided as a model):
#      - Gets a public IP automatically (map_public_ip_on_launch=True on subnet)
#      - This is the SSH entry point into the VPC
# ---------------------------------------------------------------------------
bastion = aws.ec2.Instance(
    "bastion",
    ami=ami.id,
    instance_type="t4g.micro",
    subnet_id=public_subnet_a.id,
    vpc_security_group_ids=[bastion_sg.id],
    key_name="vockey",
    tags={"Name": "NovaSpark-Bastion", "Lab": "3", "Role": "Bastion"},
)

# ---------------------------------------------------------------------------
# TODO 5: Private EC2 Instance
#
#   Create an Instance named "private-instance" using the same ami.id and
#   instance_type="t4g.micro".
#
#   Key differences from the bastion:
#     - subnet_id should be private_subnet_a.id  (private subnet, not public)
#     - vpc_security_group_ids should use [private_sg.id]  (the SG you just wrote)
#     - key_name="vockey"  (same key — you'll use SSH agent forwarding in Part 2)
#
#   Tags: Name="NovaSpark-Private", Lab="3", Role="Private"
#
#   Notice there's no associate_public_ip_address argument needed — the subnet
#   already has map_public_ip_on_launch=False, so no public IP is assigned.
# ---------------------------------------------------------------------------
# private_instance = aws.ec2.Instance(...)


# ---------------------------------------------------------------------------
# Outputs — everything needed to explore the lab
#
# NOTE: These will fail with a NameError until you complete the TODOs above.
#       Once private_rt and private_instance are defined, they will work.
# ---------------------------------------------------------------------------

# Network
pulumi.export("vpcId", vpc.id)
pulumi.export("vpcCidr", vpc.cidr_block)
pulumi.export("natEip", nat_eip.public_ip)   # compare this to private instance's outbound IP!

# Subnet IDs
pulumi.export("publicSubnetA", public_subnet_a.id)
pulumi.export("publicSubnetB", public_subnet_b.id)
pulumi.export("privateSubnetA", private_subnet_a.id)
pulumi.export("privateSubnetB", private_subnet_b.id)

# Bastion (public instance)
pulumi.export("bastionPublicIp", bastion.public_ip)
pulumi.export("bastionPublicDns", bastion.public_dns)
pulumi.export("sshCommand", bastion.public_dns.apply(
    lambda dns: f"ssh -A -i ~/.ssh/labsuser.pem ec2-user@{dns}"
))

# Private instance — uncomment once TODO 5 is complete
# pulumi.export("privateInstanceIp", private_instance.private_ip)
# pulumi.export("sshHopCommand", private_instance.private_ip.apply(
#     lambda ip: f"ssh ec2-user@{ip}   # run this FROM the bastion, after SSH-ing in with -A"
# ))

# ⚠️ CLEANUP:
# pulumi destroy
# This will take ~2 minutes as the NAT Gateway is deprovisioned.
