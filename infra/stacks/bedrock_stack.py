"""Bedrock VPC endpoint, IAM role, and CloudWatch config (prompt logging disabled)."""

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2, aws_iam as iam, aws_logs as logs
from constructs import Construct

# The three Bedrock model ARNs we use (eu-west-1)
BEDROCK_MODEL_ARNS = [
    "arn:aws:bedrock:eu-west-1::foundation-model/qwen.qwen3-coder-30b-a3b-instruct",
    "arn:aws:bedrock:eu-west-1::foundation-model/mistral.mistral-large-3-675b-instruct",
    "arn:aws:bedrock:eu-west-1::foundation-model/moonshotai.kimi-k2-thinking",
]


class BedrockStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.IVpc,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Security group for VPC endpoint — only allows inbound from VPC CIDR
        self.endpoint_sg = ec2.SecurityGroup(
            self, "BedrockEndpointSg",
            vpc=vpc,
            description="Allow HTTPS to Bedrock VPC endpoint from VPC only",
            allow_all_outbound=False,
        )
        self.endpoint_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(443),
            description="HTTPS from VPC CIDR",
        )

        # VPC endpoint for Bedrock Runtime (interface type)
        self.bedrock_endpoint = ec2.InterfaceVpcEndpoint(
            self, "BedrockRuntimeEndpoint",
            vpc=vpc,
            service=ec2.InterfaceVpcEndpointService(
                f"com.amazonaws.{self.region}.bedrock-runtime", port=443
            ),
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.endpoint_sg],
            private_dns_enabled=True,
        )

        # IAM role for invoking Bedrock — least privilege
        self.invoke_role = iam.Role(
            self, "BedrockInvokeRole",
            role_name=f"model-runner-bedrock-invoke-{self.region}",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ec2.amazonaws.com"),
                iam.AccountRootPrincipal(),
            ),
            description="Allows invoking specific Bedrock models only",
        )

        self.invoke_role.add_to_policy(
            iam.PolicyStatement(
                sid="InvokeBedrockModels",
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                resources=BEDROCK_MODEL_ARNS,
            )
        )

        # Deny all other Bedrock actions explicitly
        self.invoke_role.add_to_policy(
            iam.PolicyStatement(
                sid="DenyBedrockAdmin",
                effect=iam.Effect.DENY,
                actions=[
                    "bedrock:CreateModel*",
                    "bedrock:DeleteModel*",
                    "bedrock:UpdateModel*",
                    "bedrock:PutModelInvocationLoggingConfiguration",
                ],
                resources=["*"],
            )
        )

        # CloudWatch log group for operational metrics only (NO prompt logging)
        self.log_group = logs.LogGroup(
            self, "ModelRunnerLogs",
            log_group_name="/model-runner/operations",
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Outputs
        cdk.CfnOutput(self, "BedrockEndpointId", value=self.bedrock_endpoint.vpc_endpoint_id)
        cdk.CfnOutput(self, "InvokeRoleArn", value=self.invoke_role.role_arn)
        cdk.CfnOutput(
            self, "SecurityNote",
            value="Bedrock model invocation logging is NOT configured — prompts are not stored in CloudWatch",
        )