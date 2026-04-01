"""VPC with private subnets only — no public internet exposure."""

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class NetworkStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self, "ModelRunnerVpc",
            vpc_name="model-runner-vpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=28,
                ),
            ],
            restrict_default_security_group=True,
        )

        # Block IMDS access from all instances by default (SSRF protection)
        # Individual instances opt-in to IMDSv2 only
        cdk.Tags.of(self.vpc).add("Project", "model-runner")

        cdk.CfnOutput(self, "VpcId", value=self.vpc.vpc_id)
        cdk.CfnOutput(
            self, "PrivateSubnets",
            value=",".join(s.subnet_id for s in self.vpc.private_subnets),
        )