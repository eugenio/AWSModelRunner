"""EC2 t3.micro running Tailscale as a subnet router into the VPC."""

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2, aws_iam as iam
from constructs import Construct


class TailscaleStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.IVpc,
        bedrock_endpoint_sg: ec2.ISecurityGroup,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Tailscale auth key — pass via context: cdk deploy -c tailscale_auth_key=tskey-auth-...
        tailscale_auth_key_value = self.node.try_get_context("tailscale_auth_key")
        if not tailscale_auth_key_value:
            raise ValueError(
                "Missing context variable 'tailscale_auth_key'. "
                "Deploy with: cdk deploy ModelRunnerTailscale -c tailscale_auth_key=tskey-auth-..."
            )

        # Security group for the Tailscale subnet router
        tailscale_sg = ec2.SecurityGroup(
            self, "TailscaleSg",
            vpc=vpc,
            description="Tailscale subnet router - WireGuard UDP and outbound HTTPS",
            allow_all_outbound=True,
        )
        # Tailscale uses UDP 41641 for direct connections
        tailscale_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.udp(41641),
            description="Tailscale WireGuard",
        )

        # Allow Tailscale instance to reach Bedrock VPC endpoint
        bedrock_endpoint_sg.add_ingress_rule(
            peer=tailscale_sg,
            connection=ec2.Port.tcp(443),
            description="Tailscale subnet router to Bedrock endpoint",
        )

        # IAM role for the EC2 instance
        instance_role = iam.Role(
            self, "TailscaleInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="Tailscale subnet router instance role",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
            ],
        )

        # User data script: install Tailscale, configure as subnet router
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "#!/bin/bash",
            "set -euo pipefail",
            "",
            "# Install Tailscale",
            "curl -fsSL https://tailscale.com/install.sh | sh",
            "",
            "# Enable IP forwarding (required for subnet router)",
            "echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.d/99-tailscale.conf",
            "echo 'net.ipv6.conf.all.forwarding = 1' >> /etc/sysctl.d/99-tailscale.conf",
            "sysctl -p /etc/sysctl.d/99-tailscale.conf",
            "",
            "# Block IMDS from forwarded traffic (SSRF protection)",
            "iptables -A FORWARD -d 169.254.169.254 -j DROP",
            "iptables-save > /etc/iptables/rules.v4 || true",
            "",
            "# Start Tailscale as subnet router advertising VPC CIDR",
            f'VPC_CIDR=$(curl -s -H "X-aws-ec2-metadata-token: $(curl -s -X PUT http://169.254.169.254/latest/api/token -H \'X-aws-ec2-metadata-token-ttl-seconds: 60\')" http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s -H "X-aws-ec2-metadata-token: $(curl -s -X PUT http://169.254.169.254/latest/api/token -H \'X-aws-ec2-metadata-token-ttl-seconds: 60\')" http://169.254.169.254/latest/meta-data/mac)/vpc-ipv4-cidr-block)',
            f'tailscale up --authkey={tailscale_auth_key_value} --advertise-routes=$VPC_CIDR --accept-dns=false --hostname=model-runner-router',
        )

        # EC2 instance: t3.micro (cheapest, sufficient for routing)
        self.instance = ec2.Instance(
            self, "TailscaleRouter",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            security_group=tailscale_sg,
            role=instance_role,
            user_data=user_data,
            require_imdsv2=True,  # IMDSv2 only — mitigates SSRF
            instance_name="model-runner-tailscale-router",
        )

        # Disable source/dest check (required for routing)
        cfn_instance = self.instance.node.default_child
        cfn_instance.add_property_override("SourceDestCheck", False)

        cdk.Tags.of(self.instance).add("Project", "model-runner")
        cdk.Tags.of(self.instance).add("Role", "tailscale-subnet-router")

        cdk.CfnOutput(self, "InstanceId", value=self.instance.instance_id)
        cdk.CfnOutput(
            self, "TailscaleSetup",
            value="After deploy: approve subnet routes in Tailscale admin console at https://login.tailscale.com/admin/machines",
        )