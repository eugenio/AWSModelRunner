#!/usr/bin/env python3
"""CDK app entry point for AWS Model Runner infrastructure."""

import aws_cdk as cdk

from stacks.network_stack import NetworkStack
from stacks.bedrock_stack import BedrockStack
from stacks.tailscale_stack import TailscaleStack

app = cdk.App()

env = cdk.Environment(region="eu-west-2")

network = NetworkStack(app, "ModelRunnerNetwork", env=env)

bedrock = BedrockStack(
    app,
    "ModelRunnerBedrock",
    vpc=network.vpc,
    env=env,
)

# Tailscale stack only created when auth key is provided via context
# Deploy with: cdk deploy ModelRunnerTailscale -c tailscale_auth_key=tskey-auth-...
if app.node.try_get_context("tailscale_auth_key"):
    tailscale = TailscaleStack(
        app,
        "ModelRunnerTailscale",
        vpc=network.vpc,
        bedrock_endpoint_sg=bedrock.endpoint_sg,
        env=env,
    )

app.synth()
