"""
NovaSpark Technologies — Storage Backend
Lab 6: DynamoDB Integration

This lab extends the Lab 5 Pulumi stack with a DynamoDB table that persists
orders through the pipeline. There are 4 TODOs in this file (TODO 1–4).

All Lab 5 infrastructure is provided in the section below — do not modify it.
Your work is entirely in the Lab 6 section.

Resources created (~22 total):
  Lab 5 (provided, unchanged):
    - LabRole lookup
    - status Lambda function
    - API Gateway HTTP API
    - GET /status integration + route
    - $default stage
    - Lambda permission (status)
    - SQS queue (novaSpark-orders)

  Lab 6 (student work):
    - DynamoDB table (novaspark-orders)          ← TODO 1
    - orders Lambda (with TABLE_NAME env var)    ← TODO 2
    - orders integration + 5 routes
    - Lambda permission (orders)
    - processor Lambda (with TABLE_NAME env var) ← TODO 3
    - SQS EventSourceMapping

  Outputs:
    - status_url
    - orders_url
    - table_name                                 ← TODO 4
"""

import json
import pulumi
import pulumi_aws as aws


# =============================================================
# LAB 5 SECTION — PROVIDED, DO NOT MODIFY
# =============================================================

lambda_role = aws.iam.get_role(name="LabRole")

status_archive = pulumi.FileArchive("app")
status_fn = aws.lambda_.Function(
    "novaSpark-status-fn",
    runtime="python3.12",
    role=lambda_role.arn,
    handler="handler.lambda_handler",
    code=status_archive,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={"ENVIRONMENT": "dev", "SERVICE": "status-api"}
    ),
    timeout=10,
    memory_size=128,
    tags={"Project": "NovaSpark", "Lab": "6"},
)

http_api = aws.apigatewayv2.Api(
    "novaSpark-api",
    protocol_type="HTTP",
    tags={"Project": "NovaSpark", "Lab": "6"},
)

status_integration = aws.apigatewayv2.Integration(
    "novaSpark-status-integration",
    api_id=http_api.id,
    integration_type="AWS_PROXY",
    integration_uri=status_fn.invoke_arn,
    payload_format_version="2.0",
)

status_route = aws.apigatewayv2.Route(
    "novaSpark-status-route",
    api_id=http_api.id,
    route_key="GET /status",
    target=status_integration.id.apply(lambda id: f"integrations/{id}"),
)

stage = aws.apigatewayv2.Stage(
    "novaSpark-default-stage",
    api_id=http_api.id,
    name="$default",
    auto_deploy=True,
)

status_permission = aws.lambda_.Permission(
    "novaSpark-status-apigw-permission",
    action="lambda:InvokeFunction",
    function=status_fn.name,
    principal="apigateway.amazonaws.com",
    source_arn=http_api.execution_arn.apply(lambda arn: f"{arn}/*/*"),
)

orders_queue = aws.sqs.Queue(
    "novaSpark-orders-queue",
    name="novaSpark-orders",
    visibility_timeout_seconds=30,
    message_retention_seconds=86400,
    tags={"Project": "NovaSpark", "Lab": "6"},
)

orders_archive = pulumi.FileArchive("app/orders")
processor_archive = pulumi.FileArchive("app/processor")


# =============================================================
# LAB 6 SECTION — YOUR WORK STARTS HERE
# =============================================================

# TODO 1: Create a DynamoDB table to store orders
#
# The table should:
#   - Be named "novaspark-orders"
#   - Use "order_id" as the partition key (type "S" for string)
#   - Use on-demand billing — no capacity planning required
#   - Include Project and Lab tags
#
# Resource: aws.dynamodb.Table
# Required args:
#   name="novaspark-orders"
#   attributes=[aws.dynamodb.TableAttributeArgs(name="order_id", type="S")]
#   hash_key="order_id"
#   billing_mode="PAY_PER_REQUEST"
#   tags={...}
#
# Note: Only key attributes go in the attributes list. Fields like item,
# quantity, status, and created_at are NOT declared here — DynamoDB is
# schemaless for non-key attributes, so they are written and read freely.
#
# AWS Academy constraint: LabRole already has DynamoDB permissions.
# Do NOT add aws.iam.RolePolicy or aws.iam.RolePolicyAttachment — those
# operations are blocked in the sandbox and will cause pulumi up to fail.
#
# In a real AWS account you would scope permissions to this table only:
#
#   aws.iam.RolePolicy("lambda-dynamo-policy",
#       role=lambda_role.id,
#       policy=orders_table.arn.apply(lambda arn: json.dumps({
#           "Version": "2012-10-17",
#           "Statement": [{
#               "Effect": "Allow",
#               "Action": [
#                   "dynamodb:PutItem",
#                   "dynamodb:GetItem",
#                   "dynamodb:Query",
#                   "dynamodb:Scan",
#               ],
#               "Resource": arn   # scoped to THIS table, not "*"
#           }]
#       }))
#   )
#
# =============================================================

orders_table = None  # TODO 1 — replace with aws.dynamodb.Table(...)


# TODO 2: Create the orders Lambda
#
# Same as Lab 5, but add TABLE_NAME to the environment variables.
# The orders Lambda needs TABLE_NAME to read orders for GET requests.
# It still needs QUEUE_URL to enqueue new orders on POST.
#
# Environment variables:
#   "QUEUE_URL": orders_queue.url
#   "TABLE_NAME": orders_table.name   ← add this
#
# Keep all other settings the same as Lab 5:
#   name="novaSpark-orders-fn"
#   runtime="python3.12", handler="handler.lambda_handler"
#   code=orders_archive, timeout=10, memory_size=128
#   tags={"Project": "NovaSpark", "Lab": "6"}
#
# =============================================================

orders_fn = None  # TODO 2 — replace with aws.lambda_.Function(...)


# These resources depend on orders_fn — complete TODO 2 before running pulumi up.
orders_integration = aws.apigatewayv2.Integration(
    "novaSpark-orders-integration",
    api_id=http_api.id,
    integration_type="AWS_PROXY",
    integration_uri=orders_fn.invoke_arn,
    payload_format_version="2.0",
)

orders_route = aws.apigatewayv2.Route(
    "novaSpark-post-orders-route",
    api_id=http_api.id,
    route_key="POST /orders",
    target=orders_integration.id.apply(lambda id: f"integrations/{id}"),
)

orders_get_by_id = aws.apigatewayv2.Route(
    "novaSpark-get-orders-by-id-route",
    api_id=http_api.id,
    route_key="GET /orders/{id}",
    target=orders_integration.id.apply(lambda id: f"integrations/{id}"),
)

orders_list = aws.apigatewayv2.Route(
    "novaSpark-get-orders-route",
    api_id=http_api.id,
    route_key="GET /orders",
    target=orders_integration.id.apply(lambda id: f"integrations/{id}"),
)

orders_patch = aws.apigatewayv2.Route(
    "novaSpark-patch-orders-route",
    api_id=http_api.id,
    route_key="PATCH /orders/{id}",
    target=orders_integration.id.apply(lambda id: f"integrations/{id}"),
)

orders_delete = aws.apigatewayv2.Route(
    "novaSpark-delete-orders-route",
    api_id=http_api.id,
    route_key="DELETE /orders/{id}",
    target=orders_integration.id.apply(lambda id: f"integrations/{id}"),
)

orders_permission = aws.lambda_.Permission(
    "novaSpark-orders-apigw-permission",
    action="lambda:InvokeFunction",
    function=orders_fn.name,
    principal="apigateway.amazonaws.com",
    source_arn=http_api.execution_arn.apply(lambda arn: f"{arn}/*/*"),
)


# TODO 3: Create the processor Lambda
#
# Same as Lab 5, but add TABLE_NAME to the environment variables.
# The processor Lambda needs TABLE_NAME to write orders to DynamoDB.
# It does NOT need QUEUE_URL — SQS delivers messages to it automatically.
#
# Environment variables:
#   "TABLE_NAME": orders_table.name   ← the only env var needed
#
# Keep all other settings the same as Lab 5:
#   name="novaSpark-processor-fn"
#   runtime="python3.12", handler="handler.lambda_handler"
#   code=processor_archive, timeout=25, memory_size=128
#   tags={"Project": "NovaSpark", "Lab": "6"}
#
# Important: timeout=25 must remain strictly less than
# visibility_timeout_seconds=30 on the SQS queue. If the processor
# runs longer than the queue's visibility window, SQS re-delivers
# the message — causing duplicate processing.
#
# =============================================================

processor_fn = None  # TODO 3 — replace with aws.lambda_.Function(...)


# These resources depend on processor_fn — complete TODO 3 before running pulumi up.
event_source_mapping = aws.lambda_.EventSourceMapping(
    "novaSpark-sqs-trigger",
    event_source_arn=orders_queue.arn,
    function_name=processor_fn.name,
    batch_size=5,
    enabled=True,
)


# =============================================================
# TODO 4: Export stack outputs
#
# The existing exports below give you the API URLs.
# Add one more export for the DynamoDB table name:
#
#   pulumi.export("table_name", orders_table.name)
#
# This makes the table name accessible via:
#   pulumi stack output table_name
#
# Useful for verifying the table was created and for navigating
# directly to it in the DynamoDB console.
# =============================================================

pulumi.export("status_url", http_api.api_endpoint.apply(lambda e: f"{e}/status"))
pulumi.export("orders_url", http_api.api_endpoint.apply(lambda e: f"{e}/orders"))
# TODO 4: export table_name
