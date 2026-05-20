"""
NovaSpark Order API — Week 8 Pulumi Stack
Course: CS 545 — Cloud Native Platform Engineering

This near-complete stack wires together the NovaSpark async order pipeline.
Everything below is defined and should not require modification — except the
three TODO blocks, which are the architecturally significant connection points
you are responsible for configuring:

  # TODO 1  Wire SQS trigger to processor Lambda  (EventSourceMapping)
  # TODO 2  Set environment variables on both Lambdas
  # TODO 3  Add DynamoDB PutItem permission to processor role

Each TODO has a comment block explaining what it does, why it matters, and a
link to the relevant Pulumi and AWS documentation. Work through them in order.

Prerequisite: Lab 5 stack deployed. Your DynamoDB table (novaspark-orders)
and Lambda execution role must already exist in your AWS account.
Run `pulumi stack output` from your Lab 5 directory to confirm.
"""

import json

import pulumi
import pulumi_aws as aws

# ── Lab 5 prerequisite: DynamoDB table ───────────────────────────────────────
# Reference the table you provisioned in Lab 5 by name.
# If pulumi up errors with "resource not found", your Lab 5 stack is not
# deployed — run `pulumi up` from your Lab 5 directory first.
orders_table = aws.dynamodb.Table.get(
    "novaspark-orders",
    "novaspark-orders",
)

# ── Lambda execution role ─────────────────────────────────────────────────────
# Both Lambdas use the AWS Academy LabRole, which carries the DynamoDB read
# permissions (GetItem, Scan) established in Lab 5.
# The processor Lambda's write permission is added in TODO 3 below.
lab_role = aws.iam.get_role(name="LabRole")

# ── SQS Queue ─────────────────────────────────────────────────────────────────
# Standard queue — at-least-once delivery, durable, supports event source
# mapping to Lambda.
#
# visibility_timeout_seconds=30: a message being processed is hidden from other
# consumers for 30 seconds. This must be >= the processor Lambda's timeout (25s)
# so that in-flight messages are not redelivered while processing is underway.
#
# message_retention_seconds=86400: unprocessed messages are held for 24 hours
# before expiring. In a production system you would add a Dead Letter Queue
# to catch messages that fail after the maximum number of retries — a finding
# worth noting in your ADD Section 4 (Reliability pillar).
orders_queue = aws.sqs.Queue(
    "novaspark-orders-queue",
    visibility_timeout_seconds=30,
    message_retention_seconds=86400,
)

# ── Orders Lambda ─────────────────────────────────────────────────────────────
# Handles all five routes:
#   POST   /orders        — validate body, enqueue to SQS, return 202
#   GET    /orders/{id}   — read from DynamoDB, return 200 / 404
#   GET    /orders        — scan DynamoDB (supports ?customer_id=X filter)
#   PATCH  /orders/{id}   — 501 Not Implemented
#   DELETE /orders/{id}   — 501 Not Implemented
#
# The handler is complete (orders/handler.py). Your job is TODO 2: inject the
# environment variables the handler reads at runtime.
orders_function = aws.lambda_.Function(
    "orders-function",
    runtime="python3.11",
    handler="handler.handler",
    role=lab_role.arn,
    timeout=30,
    memory_size=128,
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./orders"),
    }),
    # ── TODO 2: Set environment variables on this Lambda ─────────────────────
    # The orders Lambda reads two environment variables at startup:
    #   QUEUE_URL   — where to send new orders (the SQS queue URL)
    #   TABLE_NAME  — where to read orders from (the DynamoDB table name)
    #
    # Use Pulumi output references — not hardcoded strings:
    #   orders_queue.url   → the SQS queue URL
    #   orders_table.name  → the DynamoDB table name
    #
    # Why environment variables, not hardcoded strings?
    # 12-factor Factor III: config that varies between environments (dev, prod,
    # staging) belongs in the environment, not in code. If you deploy a second
    # stack for a different environment, each gets a different QUEUE_URL
    # injected automatically — no code change required. This is worth one
    # sentence in ADD Section 1d (12-Factor Compliance Hooks).
    #
    # Uncomment and complete this block:
    #
    # environment=aws.lambda_.FunctionEnvironmentArgs(
    #     variables={
    #         "TABLE_NAME": orders_table.name,
    #         "QUEUE_URL":  orders_queue.url,
    #     }
    # ),
    opts=pulumi.ResourceOptions(depends_on=[orders_queue, orders_table]),
)

# ── Processor Lambda ──────────────────────────────────────────────────────────
# Triggered by SQS (wired in TODO 1 below). Reads each order message and writes
# it — including customer_id — to DynamoDB. Handles duplicate SQS delivery
# idempotently using a DynamoDB ConditionExpression.
#
# timeout=25s: must be lower than the queue visibility_timeout (30s) so that
# if the processor crashes, the message becomes visible again for retry before
# the visibility window expires.
#
# The handler is complete (processor/handler.py). Your job is TODO 2: inject
# the environment variable the handler reads at runtime.
processor_function = aws.lambda_.Function(
    "processor-function",
    runtime="python3.11",
    handler="handler.handler",
    role=lab_role.arn,
    timeout=25,
    memory_size=128,
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./processor"),
    }),
    # ── TODO 2: Set environment variables on this Lambda ─────────────────────
    # The processor Lambda reads one environment variable at startup:
    #   TABLE_NAME  — where to write orders to (the DynamoDB table name)
    #
    # Use the same Pulumi output reference as above:
    #   orders_table.name  → the DynamoDB table name
    #
    # environment=aws.lambda_.FunctionEnvironmentArgs(
    #     variables={
    #         "TABLE_NAME": orders_table.name,
    #     }
    # ),
    opts=pulumi.ResourceOptions(depends_on=[orders_table]),
)

# ─────────────────────────────────────────────────────────────────────────────
# TODO 1: Wire SQS trigger to processor Lambda
# ─────────────────────────────────────────────────────────────────────────────
# Add an aws.lambda_.EventSourceMapping resource that connects the SQS queue
# as a trigger for the processor Lambda. When a message arrives in the queue,
# Lambda polls the queue and invokes the processor function with the message(s)
# as the event payload.
#
# Key parameters:
#   event_source_arn — the ARN of the SQS queue
#                      Use orders_queue.arn (Pulumi output reference, not a
#                      hardcoded string — the ARN isn't known until deployment)
#   function_name    — the processor Lambda's name
#                      Use processor_function.name
#   batch_size       — set to 1
#                      One message per invocation. At NovaSpark's current scale
#                      this is fine, and it makes CloudWatch Logs much easier
#                      to read — each log stream corresponds to exactly one
#                      order. Why not batch_size=10? Document your reasoning
#                      in ADD Section 3 (Processor Lambda entry).
#
# Pulumi docs:
#   https://www.pulumi.com/registry/packages/aws/api-docs/lambda/eventsourcemapping/
# AWS docs:
#   https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
#
# event_source_mapping = aws.lambda_.EventSourceMapping(
#     "orders-queue-trigger",
#     event_source_arn=orders_queue.arn,
#     function_name=processor_function.name,
#     batch_size=1,
# )

# ─────────────────────────────────────────────────────────────────────────────
# TODO 3: Add DynamoDB PutItem permission to processor role
# ─────────────────────────────────────────────────────────────────────────────
# The processor Lambda must be able to write orders to DynamoDB.
# The orders Lambda already has GetItem and Scan (from Lab 5). Add only
# what is missing for the processor: dynamodb:PutItem on the orders table.
#
# Why not dynamodb:* ?
# Least privilege. The processor only writes — granting dynamodb:* would give
# it permissions it never uses. The orders Lambda only reads — granting it
# PutItem would be equally unnecessary. A role with more permissions than
# needed is exactly the kind of finding that surfaces in a Security pillar
# audit. Document this decision in ADD Section 3 (Processor Lambda entry)
# and ADD Section 4 (Security pillar).
#
# In this AWS Academy environment, LabRole already satisfies the permission
# requirement. Define the policy anyway: it documents the minimum required
# permission scope and is the artifact your ADD Sections 3 and 4 will cite.
# In a production account with a dedicated execution role, this policy would
# be the only DynamoDB permission the processor role carries.
#
# Pulumi docs:
#   https://www.pulumi.com/registry/packages/aws/api-docs/iam/rolepolicy/
#
# processor_dynamodb_policy = aws.iam.RolePolicy(
#     "processor-dynamodb-policy",
#     role=lab_role.name,
#     policy=orders_table.arn.apply(lambda arn: json.dumps({
#         "Version": "2012-10-17",
#         "Statement": [{
#             "Effect":   "Allow",
#             "Action":   ["dynamodb:PutItem"],
#             "Resource": arn,
#         }],
#     })),
# )

# ── API Gateway HTTP API ───────────────────────────────────────────────────────
# HTTP API (not REST API) — lower cost, lower latency, sufficient for this use
# case. The API Gateway endpoint is publicly addressable over HTTPS — any
# client with the URL can reach it. This is the external API pattern, appropriate
# for a customer-facing or partner-accessible service. See the API context note
# in the lab guide and ADD Section 3 (API Gateway entry).
api = aws.apigatewayv2.Api(
    "novaspark-api",
    protocol_type="HTTP",
)

# Lambda integration — AWS_PROXY passes the full HTTP request context to the
# Lambda function. The handler reads method and path from the event and routes
# internally. payload_format_version="2.0" is the current format for HTTP APIs.
orders_integration = aws.apigatewayv2.Integration(
    "orders-integration",
    api_id=api.id,
    integration_type="AWS_PROXY",
    integration_uri=orders_function.invoke_arn,
    payload_format_version="2.0",
)

# Resource-based permission allowing API Gateway to invoke the orders Lambda
aws.lambda_.Permission(
    "api-orders-permission",
    action="lambda:InvokeFunction",
    function=orders_function.name,
    principal="apigateway.amazonaws.com",
    source_arn=pulumi.Output.concat(api.execution_arn, "/*/*"),
)

# Routes — five routes, all dispatched to the orders Lambda.
# The Lambda handler routes internally based on HTTP method and path.
# PATCH and DELETE are stubbed (501) — available as optional extensions.
for method, path in [
    ("POST",   "/orders"),
    ("GET",    "/orders/{id}"),
    ("GET",    "/orders"),
    ("PATCH",  "/orders/{id}"),
    ("DELETE", "/orders/{id}"),
]:
    safe_key = (
        f"{method.lower()}-"
        + path.lstrip("/").replace("/", "-").replace("{", "").replace("}", "")
    )
    aws.apigatewayv2.Route(
        f"route-{safe_key}",
        api_id=api.id,
        route_key=f"{method} {path}",
        target=orders_integration.id.apply(lambda i: f"integrations/{i}"),
    )

# Auto-deploy stage — changes deploy immediately on pulumi up without a
# separate manual deployment step.
stage = aws.apigatewayv2.Stage(
    "default-stage",
    api_id=api.id,
    name="$default",
    auto_deploy=True,
)

# ── Outputs ───────────────────────────────────────────────────────────────────
# orders_url is your API Gateway base URL. Use it in Postman and curl.
# Set {{api_url}} in your Postman environment to this value.
pulumi.export("orders_url",  stage.invoke_url)
pulumi.export("table_name",  orders_table.name)
pulumi.export("queue_url",   orders_queue.url)
