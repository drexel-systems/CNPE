// NovaSpark VPC Demo - AWS Systems Manager Access
// Course: CS 463 - Cloud Native Platform Engineering
//
// This program builds the same two-tier VPC architecture from Lab 3, with one
// key change: EC2 instances are accessed via AWS Systems Manager Session Manager
// instead of SSH. No port 22. No key pair. No bastion hop required.
//
// The infrastructure problem is identical to what you built in Python. The
// access model is different - and that difference is exactly what your WAF
// Security pillar audit surfaces. Compare the commented-out SSH security groups
// below to the SSM versions that replaced them.
//
// This is also a demonstration of Pulumi's polyglot nature: the same cloud
// resources, the same Pulumi concepts (outputs, depends_on, resource options),
// expressed in Go instead of Python. The mental model transfers directly.
//
// Resources created:
//   VPC (10.0.0.0/16), public subnets (A/B), private subnets (A/B),
//   Internet Gateway, NAT Gateway, route tables, security groups (SSM model),
//   IAM role + instance profile, public EC2 instance, private EC2 instance
//
// SSM access model:
//   aws ssm start-session --target <instance-id>
//   No SSH key. No open port. Full session audit trail in CloudWatch.
//
// SETUP:
//   export PULUMI_CONFIG_PASSPHRASE=""
//   pulumi stack init dev
//   pulumi config set aws:region us-east-1
//   go mod tidy
//
// DEPLOY:
//   pulumi preview
//   pulumi up          (takes 4-6 minutes - NAT Gateway provisioning is slow)
//
// ACCESS:
//   pulumi stack output ssmPublicCommand   → copy and run
//   pulumi stack output ssmPrivateCommand  → copy and run
//
// CLEANUP - important, NAT Gateway costs ~$0.045/hr:
//   pulumi destroy

package main

import (
	"fmt"

	"github.com/pulumi/pulumi-aws/sdk/v6/go/aws/ec2"
	"github.com/pulumi/pulumi-aws/sdk/v6/go/aws/ssm"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {

		// ── AMI ───────────────────────────────────────────────────────────────
		// Resolved via AWS SSM Parameter Store rather than a hardcoded ID.
		// AMI IDs are region-scoped and periodically retired; the SSM path
		// always points to the latest Amazon Linux 2023 ARM64 image, so this
		// works across accounts and stays current without maintenance.
		// t4g.micro requires an ARM64 AMI - the parameter path encodes that.
		amiParam, err := ssm.LookupParameter(ctx, &ssm.LookupParameterArgs{
			Name: "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64",
		})
		if err != nil {
			return fmt.Errorf("AMI SSM parameter lookup: %w", err)
		}

		// ── VPC ───────────────────────────────────────────────────────────────
		// 10.0.0.0/16 gives 65,536 addresses to carve into subnets.
		// DNS hostnames on so instances get names like ip-10-0-1-x.ec2.internal.
		vpc, err := ec2.NewVpc(ctx, "novaspark-vpc", &ec2.VpcArgs{
			CidrBlock:          pulumi.String("10.0.0.0/16"),
			EnableDnsHostnames: pulumi.Bool(true),
			EnableDnsSupport:   pulumi.Bool(true),
			Tags:               pulumi.StringMap{"Name": pulumi.String("NovaSpark-VPC"), "Lab": pulumi.String("3")},
		})
		if err != nil {
			return fmt.Errorf("VPC: %w", err)
		}

		// ── Subnets ───────────────────────────────────────────────────────────
		// Public (.1.x, .2.x): instances get public IPs automatically.
		// Private (.11.x, .12.x): no public IPs - outbound via NAT only.
		// Two AZs gives the network layer the minimum for high availability.
		publicSubnetA, err := ec2.NewSubnet(ctx, "public-subnet-a", &ec2.SubnetArgs{
			VpcId:               vpc.ID(),
			CidrBlock:           pulumi.String("10.0.1.0/24"),
			AvailabilityZone:    pulumi.String("us-east-1a"),
			MapPublicIpOnLaunch: pulumi.Bool(true),
			Tags:                pulumi.StringMap{"Name": pulumi.String("NovaSpark-Public-A"), "Type": pulumi.String("Public"), "Lab": pulumi.String("3")},
		})
		if err != nil {
			return fmt.Errorf("public subnet A: %w", err)
		}

		publicSubnetB, err := ec2.NewSubnet(ctx, "public-subnet-b", &ec2.SubnetArgs{
			VpcId:               vpc.ID(),
			CidrBlock:           pulumi.String("10.0.2.0/24"),
			AvailabilityZone:    pulumi.String("us-east-1b"),
			MapPublicIpOnLaunch: pulumi.Bool(true),
			Tags:                pulumi.StringMap{"Name": pulumi.String("NovaSpark-Public-B"), "Type": pulumi.String("Public"), "Lab": pulumi.String("3")},
		})
		if err != nil {
			return fmt.Errorf("public subnet B: %w", err)
		}

		privateSubnetA, err := ec2.NewSubnet(ctx, "private-subnet-a", &ec2.SubnetArgs{
			VpcId:               vpc.ID(),
			CidrBlock:           pulumi.String("10.0.11.0/24"),
			AvailabilityZone:    pulumi.String("us-east-1a"),
			MapPublicIpOnLaunch: pulumi.Bool(false),
			Tags:                pulumi.StringMap{"Name": pulumi.String("NovaSpark-Private-A"), "Type": pulumi.String("Private"), "Lab": pulumi.String("3")},
		})
		if err != nil {
			return fmt.Errorf("private subnet A: %w", err)
		}

		privateSubnetB, err := ec2.NewSubnet(ctx, "private-subnet-b", &ec2.SubnetArgs{
			VpcId:               vpc.ID(),
			CidrBlock:           pulumi.String("10.0.12.0/24"),
			AvailabilityZone:    pulumi.String("us-east-1b"),
			MapPublicIpOnLaunch: pulumi.Bool(false),
			Tags:                pulumi.StringMap{"Name": pulumi.String("NovaSpark-Private-B"), "Type": pulumi.String("Private"), "Lab": pulumi.String("3")},
		})
		if err != nil {
			return fmt.Errorf("private subnet B: %w", err)
		}

		// ── Internet Gateway ──────────────────────────────────────────────────
		// Without an IGW the VPC is fully isolated. Public subnets route
		// outbound internet traffic here. Private subnets do not.
		igw, err := ec2.NewInternetGateway(ctx, "novaspark-igw", &ec2.InternetGatewayArgs{
			VpcId: vpc.ID(),
			Tags:  pulumi.StringMap{"Name": pulumi.String("NovaSpark-IGW"), "Lab": pulumi.String("3")},
		})
		if err != nil {
			return fmt.Errorf("internet gateway: %w", err)
		}

		// ── NAT Gateway ───────────────────────────────────────────────────────
		// Private instances need outbound internet access for software updates
		// and AWS API calls. The SSM agent also uses HTTPS outbound to reach
		// the SSM service endpoint - NAT Gateway enables this for private instances.
		//
		// Flow: Private Instance → NAT Gateway → Internet Gateway → Internet
		//       Internet → (dropped unless it is a response to outbound traffic)
		//
		// ⚠️  NAT Gateway costs ~$0.045/hr. Run `pulumi destroy` when done!
		natEip, err := ec2.NewEip(ctx, "nat-eip", &ec2.EipArgs{
			Domain: pulumi.String("vpc"),
			Tags:   pulumi.StringMap{"Name": pulumi.String("NovaSpark-NAT-EIP"), "Lab": pulumi.String("3")},
		})
		if err != nil {
			return fmt.Errorf("NAT EIP: %w", err)
		}

		natGateway, err := ec2.NewNatGateway(ctx, "novaspark-nat", &ec2.NatGatewayArgs{
			SubnetId:     publicSubnetA.ID(), // NAT Gateway lives in a PUBLIC subnet
			AllocationId: natEip.ID(),
			Tags:         pulumi.StringMap{"Name": pulumi.String("NovaSpark-NAT"), "Lab": pulumi.String("3")},
		}, pulumi.DependsOn([]pulumi.Resource{igw})) // IGW must exist first
		if err != nil {
			return fmt.Errorf("NAT gateway: %w", err)
		}

		// ── Route Tables ──────────────────────────────────────────────────────
		// Public: 0.0.0.0/0 → Internet Gateway
		// Private: 0.0.0.0/0 → NAT Gateway
		publicRt, err := ec2.NewRouteTable(ctx, "public-rt", &ec2.RouteTableArgs{
			VpcId: vpc.ID(),
			Tags:  pulumi.StringMap{"Name": pulumi.String("NovaSpark-Public-RT"), "Lab": pulumi.String("3")},
		})
		if err != nil {
			return fmt.Errorf("public route table: %w", err)
		}

		if _, err = ec2.NewRoute(ctx, "public-default-route", &ec2.RouteArgs{
			RouteTableId:         publicRt.ID(),
			DestinationCidrBlock: pulumi.String("0.0.0.0/0"),
			GatewayId:            igw.ID(),
		}); err != nil {
			return fmt.Errorf("public default route: %w", err)
		}

		if _, err = ec2.NewRouteTableAssociation(ctx, "public-rt-assoc-a", &ec2.RouteTableAssociationArgs{
			SubnetId:     publicSubnetA.ID(),
			RouteTableId: publicRt.ID(),
		}); err != nil {
			return fmt.Errorf("public RT assoc A: %w", err)
		}

		if _, err = ec2.NewRouteTableAssociation(ctx, "public-rt-assoc-b", &ec2.RouteTableAssociationArgs{
			SubnetId:     publicSubnetB.ID(),
			RouteTableId: publicRt.ID(),
		}); err != nil {
			return fmt.Errorf("public RT assoc B: %w", err)
		}

		privateRt, err := ec2.NewRouteTable(ctx, "private-rt", &ec2.RouteTableArgs{
			VpcId: vpc.ID(),
			Tags:  pulumi.StringMap{"Name": pulumi.String("NovaSpark-Private-RT"), "Lab": pulumi.String("3")},
		})
		if err != nil {
			return fmt.Errorf("private route table: %w", err)
		}

		if _, err = ec2.NewRoute(ctx, "private-default-route", &ec2.RouteArgs{
			RouteTableId:         privateRt.ID(),
			DestinationCidrBlock: pulumi.String("0.0.0.0/0"),
			NatGatewayId:         natGateway.ID(),
		}); err != nil {
			return fmt.Errorf("private default route: %w", err)
		}

		if _, err = ec2.NewRouteTableAssociation(ctx, "private-rt-assoc-a", &ec2.RouteTableAssociationArgs{
			SubnetId:     privateSubnetA.ID(),
			RouteTableId: privateRt.ID(),
		}); err != nil {
			return fmt.Errorf("private RT assoc A: %w", err)
		}

		if _, err = ec2.NewRouteTableAssociation(ctx, "private-rt-assoc-b", &ec2.RouteTableAssociationArgs{
			SubnetId:     privateSubnetB.ID(),
			RouteTableId: privateRt.ID(),
		}); err != nil {
			return fmt.Errorf("private RT assoc B: %w", err)
		}

		// ── Security Groups ───────────────────────────────────────────────────
		//
		// ── ORIGINAL SSH SECURITY GROUPS (Lab 3 - commented out) ─────────────
		// This is what Lab 3 deployed. The bastion SG allows port 22 from
		// 0.0.0.0/0 - the Conscious Tradeoff your WAF Security audit names.
		// The private SG allows port 22 from the VPC CIDR only (bastion hop).
		// The SSM security groups below replace both of these entirely.
		//
		// bastionSgSsh, _ := ec2.NewSecurityGroup(ctx, "bastion-sg-ssh", &ec2.SecurityGroupArgs{
		// 	VpcId:       vpc.ID(),
		// 	Description: pulumi.String("Bastion host - SSH from internet"),
		// 	Ingress: ec2.SecurityGroupIngressArray{
		// 		&ec2.SecurityGroupIngressArgs{
		// 			Protocol:    pulumi.String("tcp"),
		// 			FromPort:    pulumi.Int(22),
		// 			ToPort:      pulumi.Int(22),
		// 			CidrBlocks:  pulumi.StringArray{pulumi.String("0.0.0.0/0")},
		// 			Description: pulumi.String("SSH from anywhere - Conscious Tradeoff, restrict to known CIDR in production"),
		// 		},
		// 	},
		// 	Egress: ec2.SecurityGroupEgressArray{
		// 		&ec2.SecurityGroupEgressArgs{
		// 			Protocol:   pulumi.String("-1"),
		// 			FromPort:   pulumi.Int(0),
		// 			ToPort:     pulumi.Int(0),
		// 			CidrBlocks: pulumi.StringArray{pulumi.String("0.0.0.0/0")},
		// 		},
		// 	},
		// 	Tags: pulumi.StringMap{"Name": pulumi.String("NovaSpark-Bastion-SG-SSH"), "Lab": pulumi.String("3")},
		// })
		//
		// privateSgSsh, _ := ec2.NewSecurityGroup(ctx, "private-sg-ssh", &ec2.SecurityGroupArgs{
		// 	VpcId:       vpc.ID(),
		// 	Description: pulumi.String("Private instance - SSH from VPC CIDR only"),
		// 	Ingress: ec2.SecurityGroupIngressArray{
		// 		&ec2.SecurityGroupIngressArgs{
		// 			Protocol:    pulumi.String("tcp"),
		// 			FromPort:    pulumi.Int(22),
		// 			ToPort:      pulumi.Int(22),
		// 			CidrBlocks:  pulumi.StringArray{pulumi.String("10.0.0.0/16")},
		// 			Description: pulumi.String("SSH from VPC CIDR only - bastion hop required"),
		// 		},
		// 	},
		// 	Egress: ec2.SecurityGroupEgressArray{
		// 		&ec2.SecurityGroupEgressArgs{
		// 			Protocol:   pulumi.String("-1"),
		// 			FromPort:   pulumi.Int(0),
		// 			ToPort:     pulumi.Int(0),
		// 			CidrBlocks: pulumi.StringArray{pulumi.String("0.0.0.0/0")},
		// 		},
		// 	},
		// 	Tags: pulumi.StringMap{"Name": pulumi.String("NovaSpark-Private-SG-SSH"), "Lab": pulumi.String("3")},
		// })
		// ── END ORIGINAL SSH SECURITY GROUPS ─────────────────────────────────

		// SSM security groups: no inbound ports at all.
		//
		// The SSM agent inside the instance opens an OUTBOUND HTTPS connection
		// to the SSM service endpoint - the instance never accepts inbound
		// connections from anyone. There is no port 22 rule to exploit, no key
		// file to lose track of, and no IP restriction to maintain.
		publicSg, err := ec2.NewSecurityGroup(ctx, "public-sg-ssm", &ec2.SecurityGroupArgs{
			VpcId:       vpc.ID(),
			Description: pulumi.String("Public instance - SSM access, no inbound ports"),
			Egress: ec2.SecurityGroupEgressArray{
				&ec2.SecurityGroupEgressArgs{
					Protocol:    pulumi.String("-1"),
					FromPort:    pulumi.Int(0),
					ToPort:      pulumi.Int(0),
					CidrBlocks:  pulumi.StringArray{pulumi.String("0.0.0.0/0")},
					Description: pulumi.String("All outbound - SSM agent phones home over HTTPS to AWS endpoint"),
				},
			},
			Tags: pulumi.StringMap{"Name": pulumi.String("NovaSpark-Public-SG"), "Lab": pulumi.String("3")},
		})
		if err != nil {
			return fmt.Errorf("public SG: %w", err)
		}

		privateSg, err := ec2.NewSecurityGroup(ctx, "private-sg-ssm", &ec2.SecurityGroupArgs{
			VpcId:       vpc.ID(),
			Description: pulumi.String("Private instance - SSM access, no inbound ports"),
			Egress: ec2.SecurityGroupEgressArray{
				&ec2.SecurityGroupEgressArgs{
					Protocol:    pulumi.String("-1"),
					FromPort:    pulumi.Int(0),
					ToPort:      pulumi.Int(0),
					CidrBlocks:  pulumi.StringArray{pulumi.String("0.0.0.0/0")},
					Description: pulumi.String("All outbound - SSM agent phones home over HTTPS via NAT Gateway"),
				},
			},
			Tags: pulumi.StringMap{"Name": pulumi.String("NovaSpark-Private-SG"), "Lab": pulumi.String("3")},
		})
		if err != nil {
			return fmt.Errorf("private SG: %w", err)
		}

		// ── IAM Instance Profile for SSM ──────────────────────────────────────
		// SSM Session Manager requires the instance to carry an IAM instance
		// profile with AmazonSSMManagedInstanceCore permissions. In a production
		// account you would create a dedicated role scoped to exactly that policy.
		//
		// AWS Academy sandboxes restrict iam:CreateRole, so we reference the
		// pre-provisioned LabInstanceProfile instead. LabRole already carries
		// AmazonSSMManagedInstanceCore, so SSM access works without any
		// additional configuration.
		//
		// Production pattern: replace "LabInstanceProfile" with a dedicated
		// role carrying only AmazonSSMManagedInstanceCore - nothing broader.
		const instanceProfile = "LabInstanceProfile"

		// ── EC2 Instances ─────────────────────────────────────────────────────
		// No KeyName field - SSM is the only access path. There is no SSH key
		// to create, distribute, rotate, or accidentally check into a repo.
		//
		// Amazon Linux 2 ships with the SSM agent pre-installed. Once the
		// instance profile is attached, the agent starts automatically and
		// registers with the SSM service. No additional setup required.
		publicInstance, err := ec2.NewInstance(ctx, "public-instance", &ec2.InstanceArgs{
			Ami:                 pulumi.String(amiParam.Value),
			InstanceType:        pulumi.String("t4g.micro"),
			SubnetId:            publicSubnetA.ID(),
			VpcSecurityGroupIds: pulumi.StringArray{publicSg.ID()},
			IamInstanceProfile:  pulumi.String(instanceProfile),
			Tags:                pulumi.StringMap{"Name": pulumi.String("NovaSpark-Public"), "Lab": pulumi.String("3"), "Role": pulumi.String("Public")},
		})
		if err != nil {
			return fmt.Errorf("public instance: %w", err)
		}

		privateInstance, err := ec2.NewInstance(ctx, "private-instance", &ec2.InstanceArgs{
			Ami:                 pulumi.String(amiParam.Value),
			InstanceType:        pulumi.String("t4g.micro"),
			SubnetId:            privateSubnetA.ID(),
			VpcSecurityGroupIds: pulumi.StringArray{privateSg.ID()},
			IamInstanceProfile:  pulumi.String(instanceProfile),
			Tags:                pulumi.StringMap{"Name": pulumi.String("NovaSpark-Private"), "Lab": pulumi.String("3"), "Role": pulumi.String("Private")},
		})
		if err != nil {
			return fmt.Errorf("private instance: %w", err)
		}

		// ── Outputs ───────────────────────────────────────────────────────────
		// Network
		ctx.Export("vpcId", vpc.ID())
		ctx.Export("vpcCidr", vpc.CidrBlock)
		ctx.Export("natEip", natEip.PublicIp) // private instance outbound IP should match this

		// Subnets
		ctx.Export("publicSubnetA", publicSubnetA.ID())
		ctx.Export("publicSubnetB", publicSubnetB.ID())
		ctx.Export("privateSubnetA", privateSubnetA.ID())
		ctx.Export("privateSubnetB", privateSubnetB.ID())

		// Instance IDs - needed for SSM session commands
		ctx.Export("publicInstanceId", publicInstance.ID())
		ctx.Export("privateInstanceId", privateInstance.ID())

		// Ready-to-run SSM commands. Copy from `pulumi stack output` and paste.
		ctx.Export("ssmPublicCommand", publicInstance.ID().ApplyT(func(id string) string {
			return "aws ssm start-session --target " + id + " --region us-east-1"
		}).(pulumi.StringOutput))

		ctx.Export("ssmPrivateCommand", privateInstance.ID().ApplyT(func(id string) string {
			return "aws ssm start-session --target " + id + " --region us-east-1"
		}).(pulumi.StringOutput))

		return nil
	})
}
