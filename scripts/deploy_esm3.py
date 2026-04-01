#!/usr/bin/env python3
"""Script to deploy ESM3 endpoint on SageMaker after CDK infrastructure is ready."""

import boto3
import time
import sys


def deploy_esm3_endpoint(
    instance_type: str = "ml.g6e.xlarge",
    region: str = "eu-west-2",
):
    """Deploy ESM3-open endpoint from AWS Marketplace."""

    sm = boto3.client("sagemaker", region_name=region)

    print("=" * 60)
    print("ESM3 Protein Model Deployment")
    print("=" * 60)

    print("\n1. Subscribing to ESM3-open on AWS Marketplace...")
    print("   URL: https://aws.amazon.com/marketplace/pp/prodview-xbvra5ylcu4xq")
    print("   - Sign in to AWS console")
    print("   - Accept the subscription terms")
    print("   - Wait for subscription to propagate")

    input("\nPress Enter after subscribing to ESM3-open...")

    print("\n2. Getting SageMaker execution role from CDK outputs...")
    cfn = boto3.client("cloudformation", region_name=region)
    try:
        outputs = cfn.describe_stacks(StackName="ESM3Protein")["Stacks"][0]["Outputs"]
        role_arn = next(
            o["OutputValue"] for o in outputs if o["OutputKey"] == "SageMakerRoleArn"
        )
        print(f"   Role ARN: {role_arn}")
    except Exception as e:
        print(f"   Error getting role: {e}")
        print("   Please deploy CDK stack first: cd infra && cdk deploy ESM3Protein")
        return

    print("\n3. Creating SageMaker model and endpoint...")

    model_name = "esm3-open-protein"
    endpoint_config_name = "esm3-open-config"
    endpoint_name = "esm3-protein-endpoint"

    container = {
        "ImageUri": "492479439774.dkr.ecr.eu-west-1.amazonaws.com/evolutionaryscale-esm3:1.0.5",
        "Mode": "SingleModel",
        "Environment": {
            "SAGEMAKER_CONTAINER_LOG_LEVEL": "20",
            "SAGEMAKER_REGION": region,
        },
    }

    try:
        print("   Creating model...")
        sm.create_model(
            ModelName=model_name,
            ExecutionRoleArn=role_arn,
            PrimaryContainer=container,
        )
    except sm.exceptions.ClientError as e:
        if "already exists" in str(e):
            print("   Model already exists, continuing...")
        else:
            print(f"   Error creating model: {e}")
            return

    try:
        print("   Creating endpoint configuration...")
        sm.create_endpoint_config(
            EndpointConfigName=endpoint_config_name,
            ProductionVariants=[
                {
                    "VariantName": "variant-1",
                    "ModelName": model_name,
                    "InstanceType": instance_type,
                    "InitialInstanceCount": 1,
                    "AcceleratorType": "ml.eia1.medium",
                }
            ],
        )
    except sm.exceptions.ClientError as e:
        if "already exists" in str(e):
            print("   Endpoint config already exists, continuing...")
        else:
            print(f"   Error creating endpoint config: {e}")
            return

    try:
        print("   Creating/Updating endpoint...")
        sm.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name,
        )
    except sm.exceptions.ClientError as e:
        if "already exists" in str(e):
            print("   Updating existing endpoint...")
            sm.update_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=endpoint_config_name,
            )
        else:
            print(f"   Error creating endpoint: {e}")
            return

    print("\n4. Waiting for endpoint to be in service...")
    print("   (This can take 10-20 minutes)")

    while True:
        status = sm.describe_endpoint(EndpointName=endpoint_name)["EndpointStatus"]
        print(f"   Status: {status}")

        if status == "InService":
            print("\n✓ ESM3 endpoint is ready!")
            print(f"\n   Endpoint name: {endpoint_name}")
            print(f"   Region: {region}")
            break
        elif status in ["Failed", "CreatingBlocked"]:
            print(f"\n✗ Endpoint creation failed: {status}")
            return
        else:
            time.sleep(30)

    print("\n" + "=" * 60)
    print("Deployment Complete!")
    print("=" * 60)
    print(f"\nEndpoint: {endpoint_name}")
    print(f"Instance: {instance_type}")
    print(
        "\nThe auto-stop Lambda will stop the endpoint after 30 minutes of inactivity."
    )
    print("Use the endpoint when needed - it will restart automatically on invocation.")


if __name__ == "__main__":
    instance_type = "ml.g6e.xlarge"
    region = "eu-west-2"

    if len(sys.argv) > 1:
        instance_type = sys.argv[1]
    if len(sys.argv) > 2:
        region = sys.argv[2]

    deploy_esm3_endpoint(instance_type, region)
