"""
NovaSpark Technologies — Serverless Status API
Lab 4: Lambda + API Gateway

This file deploys NovaSpark's first serverless service using Pulumi.
Complete the TODOs below. When all TODOs are filled in, `pulumi up`
should create ~9 resources with no errors.

When you're done, this stack is your capstone foundation.
DO NOT run `pulumi destroy` at the end of this lab.
"""

import json
import pulumi
import pulumi_aws as aws


# =============================================================
# IAM: Lambda Execution Role
# (This section is provided for you — no TODO here.)
# =============================================================
# Lambda needs an IAM role so AWS can execute it on your behalf.
# This role controls what AWS services the function is allowed to call.
#
# AWS Academy Learner Labs restrict iam:CreateRole — you cannot create
# new IAM roles in the sandbox. Instead, every Learner Lab account comes
# with a pre-existing role called "LabRole" that already has the
# permissions Lambda needs (CloudWatch Logs, DynamoDB, and more).
#
# get_role() is a read-only lookup — it finds the existing role by name
# without creating anything. This is the same pattern used in Lab 2
# for the EC2 instance profile.
#
# In a real AWS account (outside Academy) you would create a tightly
# scoped role instead:
#
#   lambda_role = aws.iam.Role("novaSpark-lambda-role",
#       assume_role_policy=json.dumps({
#           "Version": "2012-10-17",
#           "Statement": [{"Effect": "Allow",
#               "Principal": {"Service": "lambda.amazonaws.com"},
#               "Action": "sts:AssumeRole"}]
#       })
#   )
#   aws.iam.RolePolicyAttachment("novaSpark-lambda-logs",
#       role=lambda_role.name,
#       policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
#   )
#
# The scoped version would grant ONLY:
#   logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents
# LabRole grants much more. You'll look at this difference in Step 3.6.

lambda_role = aws.iam.get_role(name="LabRole")


# =============================================================
# Lambda Function
# =============================================================

# TODO 1: Package the Lambda code
# Pulumi needs to upload your code as a zip archive to AWS.
# Use pulumi.FileArchive to point to the "app" folder.
# The entire contents of app/ will be zipped and uploaded as the function code.
#
#   lambda_archive = pulumi.FileArchive("app")
#
lambda_archive = None  # Replace this line


# TODO 2: Create the Lambda function
# Use aws.lambda_.Function() with the following arguments:
#
#   resource name:  "novaSpark-status-fn"
#   runtime:        "python3.12"
#   role:           lambda_role.arn
#   handler:        "handler.lambda_handler"
#               (matches the filename handler.py and function lambda_handler)
#   code:           lambda_archive
#   environment:    aws.lambda_.FunctionEnvironmentArgs(
#                       variables={"ENVIRONMENT": "dev", "SERVICE": "status-api"}
#                   )
#   timeout:        10   (seconds; default is 3, which is too short for cold starts)
#   memory_size:    128  (MB; smallest available — fine for a status endpoint)
#   tags:           {"Project": "NovaSpark", "Lab": "4"}
#
lambda_fn = None  # Replace this line


# =============================================================
# API Gateway (HTTP API v2)
# =============================================================
# API Gateway is the managed front door: it handles HTTPS, routing,
# and throttling. The HTTP API (v2) is cheaper and simpler than
# the REST API (v1) — use v2 unless you need v1-specific features.

# TODO 3: Create the HTTP API
# Use aws.apigatewayv2.Api() with:
#
#   resource name:  "novaSpark-status-api"
#   name:           "novaSpark-status-api"
#   protocol_type:  "HTTP"
#   tags:           {"Project": "NovaSpark", "Lab": "4"}
#
http_api = None  # Replace this line


# TODO 4: Create a Lambda integration
# The integration tells API Gateway how to call your Lambda.
# Use aws.apigatewayv2.Integration() with:
#
#   resource name:           "novaSpark-lambda-integration"
#   api_id:                  http_api.id
#   integration_type:        "AWS_PROXY"
#   integration_uri:         lambda_fn.invoke_arn
#   payload_format_version:  "2.0"
#       (must match what your handler returns — see handler.py)
#
integration = None  # Replace this line


# TODO 5: Create a route: GET /status → your Lambda
# A route maps an HTTP method + path to an integration.
# Use aws.apigatewayv2.Route() with:
#
#   resource name:  "novaSpark-status-route"
#   api_id:         http_api.id
#   route_key:      "GET /status"
#   target:         integration.id.apply(lambda id: f"integrations/{id}")
#       (API Gateway expects "integrations/<integration_id>" as the target string)
#
route = None  # Replace this line


# TODO 6: Create a $default stage with auto-deploy enabled
# The stage is the deployment unit — what actually makes your API accessible.
# Use aws.apigatewayv2.Stage() with:
#
#   resource name:  "novaSpark-default-stage"
#   api_id:         http_api.id
#   name:           "$default"
#   auto_deploy:    True
#
stage = None  # Replace this line


# TODO 7: Give API Gateway permission to invoke the Lambda
# Without this, API Gateway gets a 403 Forbidden when it tries to call your function.
# Use aws.lambda_.Permission() with:
#
#   resource name:  "novaSpark-apigw-permission"
#   action:         "lambda:InvokeFunction"
#   function:       lambda_fn.name
#   principal:      "apigateway.amazonaws.com"
#   source_arn:     http_api.execution_arn.apply(lambda arn: f"{arn}/*/*")
#       (the /* /* scope limits this permission to any method + any route on THIS API only)
#
permission = None  # Replace this line


# =============================================================
# Outputs
# =============================================================

# TODO 8: Export the live endpoint URL
# Combine http_api.api_endpoint with "/status" to produce the full URL.
# Use .apply() to transform the Output value:
#
#   pulumi.export("api_url", http_api.api_endpoint.apply(lambda e: f"{e}/status"))
#
# After pulumi up, run: pulumi stack output api_url
# That URL is what you curl in D5.
#
# pulumi.export("api_url", ???)   ← uncomment and complete this line
