# Code and environment for python setup using 
#        pulumi new aws-python
import pulumi
import pulumi_aws as aws

# 0. Force the region to us-east-1 for the Learner Lab
#    The best way to do this is to run `pulumi config set aws:region us-east-1` in your terminal before
#    running `pulumi up`.  This ensures that all resources are created in us-east-1.
#    
# You could also hard code it into this file using:
#     lab_provider = aws.Provider("lab-provider", region="us-east-1")
# and then adding `opts=pulumi.ResourceOptions(provider=lab_provider)` to each resource.

# 1. Lookup the latest ARM based amazon linux AMI
#    - Start by using the AWS console to fine the AMI ID that you want to use, in our case 
#      we are using the Amazon Linux 2 AMI (ARM64) with ID ami-0a101d355d07a638e in us-east-1
#    - Then use the aws cli to find the other AMI details such as the owner ID:
#        aws ec2 describe-images --image-ids ami-0a101d355d07a638e --region us-east-1
#      provides all of the details, if you just want to get the owner ID you can use:
#        aws ec2 describe-images --image-ids ami-0a101d355d07a638e --region us-east-1 --query 'Images[0].OwnerId'
# 2. Note with the AMI ID you can also get the owner from the GUI via the AMIs tab under EC2 by pasting 
#    AMI ID = ami-0a101d355d07a638e into the search box and looking at the details pane.
# 3. With the owner ID and AMI ID you can use the get_ami data source to look it up using Pulumi aws.ec2.get_ami()

ami = aws.ec2.get_ami(
    owners=["137112412989"],
    filters=[
        {
            "name": "image-id",
            "values": ["ami-0a101d355d07a638e"],
        }
    ]
)

# 2. Define a Security Group to allow SSH access
sec_group = aws.ec2.SecurityGroup('ssh-access',
    description='Enable SSH access',
    ingress=[{
        'protocol': 'tcp',
        'from_port': 22,
        'to_port': 22,
        'cidr_blocks': ['0.0.0.0/0'], # For better security, replace with your IP: 'your.ip.ad.dr/32'
    }]
)

# 3. Provision the EC2 instance using the pre-existing 'vockey' key
# Note this step defines the physical hardware type that will be used to run the AMI.  Since we are using
# an ARM based AMI we need to use an ARM based instance type such as t4g.micro.  The "g" in t4g.micro indicates
# that it is ARM based (Graviton).  If you try to use an x86 based instance type such as t3.micro with an ARM
# based AMI you will get an error during instance launch.
server = aws.ec2.Instance('lab-instance',
    instance_type='t4g.micro',
    vpc_security_group_ids=[sec_group.id],
    ami=ami.id,
    key_name='vockey' # This matches the labsuser.pem/ppk you downloaded
)

# 4. Export the Public IP to use for SSH
pulumi.export('publicIp', server.public_ip)
pulumi.export('publicDns', server.public_dns)
pulumi.export('sshCommand', server.public_dns.apply(
    lambda dns: f"ssh -i  ~/.ssh/labsuser.pem ec2-user@{dns}"
))


# REMEMBER TO RUN
# 1. pulumi config set aws:region us-east-1
# 2. pulumi preview
# 3. pulumi up
#
# INVESTIGATE
#    ssh -i ~/.ssh/labsuser.pem ec2-user@ec2-98-91-214-24.compute-1.amazonaws.com
#
# When done DO NOT FORGET to run `pulumi destroy` to avoid ongoing charges
# to keep your known hosts file clearn of old entries you can run:
#    ssh-keygen -R <publicDns> for example:
#    ssh-keygen -R ec2-98-91-214-24.compute-1.amazonaws.com

