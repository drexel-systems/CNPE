"""
NovaSpark Technologies — Serverless Status API
Lab 4: Lambda + API Gateway — Starter Template

This template is complete and will deploy without modification.

Your task before running pulumi up:
1. Read every resource definition and its comments
2. Be able to explain what each resource does and why it's needed
3. Identify at least one design decision that is conservative for this lab
   but would need to change for a production workload

The deliverables will ask you to explain specific choices made here —
particularly the IAM execution role scope and the API Gateway v2 configuration.
"""

import json
import pulumi
import pulumi_aws as aws


# =============================================================
# IAM: Lambda Execution Role
#
# AWS Academy Learner Labs restrict iam:CreateRole — students cannot
# create new IAM roles. Instead, every Learner Lab account comes with
# a pre-existing role called "LabRole" that has broad permissions
# including CloudWatch Logs, DynamoDB, S3, and Lambda execution.
#
# We look it up with get_role() — a read-only data source that finds
# an existing role by name without creating anything new.
#
# AWS Academy constraint vs. production best practice:
#   LabRole is deliberately over-permissioned for lab convenience.
#   In a real AWS account, you would create a tightly scoped role:
#
#     lambda_role = aws.iam.Role("novaSpark-lambda-role",
#         assume_role_policy=json.dumps({
#             "Version": "2012-10-17",
#             "Statement": [{"Effect": "Allow",
#                 "Principal": {"Service": "lambda.amazonaws.com"},
#                 "Action": "sts:AssumeRole"}]
#         })
#     )
#     aws.iam.RolePolicyAttachment("novaSpark-lambda-logs",
#         role=lambda_role.name,
#         policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
#     )
#
#   AWSLambdaBasicExecutionRole grants exactly three actions:
#     logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents
#   That is all. Nothing else. The execution role analysis in Step 3
#   asks you to reason about what LabRole grants vs. what a properly
#   scoped role would grant — and what the difference means.
# =============================================================

lambda_role = aws.iam.get_role(name="LabRole")


# =============================================================
# Lambda Function
#
# Design decisions to note:
# - runtime python3.12: current stable; avoid python3.8/3.9 in new functions
# - memory_size 128: minimum available; appropriate for a lightweight status
#   endpoint. Increasing memory also increases CPU allocation proportionally —
#   if this function ever does CPU-intensive work, bumping to 256 or 512 is
#   the first tuning lever.
# - timeout 10: generous for a function that currently just returns a string,
#   but reasonable headroom for when DynamoDB reads are added in Lab 5.
# - handler "handler.lambda_handler": matches filename handler.py + function name
# =============================================================

lambda_fn = aws.lambda_.Function(
    "novaSpark-status-fn",
    runtime="python3.12",
    role=lambda_role.arn,
    handler="handler.lambda_handler",
    code=pulumi.FileArchive("app"),
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "ENVIRONMENT": "dev",
            "SERVICE": "status-api"
        }
    ),
    timeout=10,
    memory_size=128,
    tags={"Project": "NovaSpark", "Lab": "4", "Course": "CS545"}
)


# =============================================================
# API Gateway HTTP API (v2)
#
# Design decision: HTTP API (v2) over REST API (v1).
#
# HTTP API:
#   - ~$1.00 per million requests (vs. ~$3.50 for REST API)
#   - Lower latency (no intermediate transformation layer)
#   - Simpler integration model (AWS_PROXY only)
#   - No API keys, usage plans, or request/response transformation
#
# REST API (v1) would be appropriate if NovaSpark needed:
#   - API key management for external partners
#   - Request validation or transformation before Lambda
#   - Usage plans with throttling per-key
#
# For an internal status endpoint, HTTP API is the right call.
# =============================================================

http_api = aws.apigatewayv2.Api(
    "novaSpark-status-api",
    protocol_type="HTTP",
    tags={"Project": "NovaSpark", "Lab": "4"}
)

# AWS_PROXY integration: API Gateway passes the entire HTTP request
# to Lambda as the event object and returns Lambda's response directly
# to the caller. No transformation happens at the API Gateway layer.
# payload_format_version "2.0" is the current format — the handler.py
# response envelope matches this format.
integration = aws.apigatewayv2.Integration(
    "novaSpark-lambda-integration",
    api_id=http_api.id,
    integration_type="AWS_PROXY",
    integration_uri=lambda_fn.invoke_arn,
    payload_format_version="2.0"
)

route = aws.apigatewayv2.Route(
    "novaSpark-status-route",
    api_id=http_api.id,
    route_key="GET /status",
    target=integration.id.apply(lambda id: f"integrations/{id}")
)

# The $default stage with auto_deploy=True means every Pulumi update
# to the API configuration is immediately live — no manual "deploy to stage"
# step required. For a production API you might want a separate staging
# environment with a promotion workflow before traffic hits $default.
stage = aws.apigatewayv2.Stage(
    "novaSpark-default-stage",
    api_id=http_api.id,
    name="$default",
    auto_deploy=True
)


# =============================================================
# Lambda Resource-Based Policy
#
# This is a separate resource from the IAM execution role above.
# The execution role controls what Lambda CAN DO (write logs).
# This permission controls who CAN INVOKE Lambda (API Gateway).
#
# source_arn scope: the /* /* wildcard permits any method on any route
# of THIS API only. Without this, any API Gateway API in the account
# could invoke this function — a subtle but real overpermission.
# =============================================================

permission = aws.lambda_.Permission(
    "novaSpark-apigw-permission",
    action="lambda:InvokeFunction",
    function=lambda_fn.name,
    principal="apigateway.amazonaws.com",
    source_arn=http_api.execution_arn.apply(lambda arn: f"{arn}/*/*")
)


# =============================================================
# Outputs
# =============================================================

pulumi.export("api_url", http_api.api_endpoint.apply(lambda e: f"{e}/status"))
pulumi.export("lambda_arn", lambda_fn.arn)
pulumi.export("lambda_role_arn", lambda_role.arn)   # LabRole ARN — inspect this in the IAM console for Step 3
