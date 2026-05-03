"""
NovaSpark Technologies — Async Order API
Lab 5: RESTful APIs + SQS

This file extends the Lab 4 Pulumi stack.

The Lab 4 section (IAM, status Lambda, API Gateway scaffold) is provided
and complete — do not modify it. Your job is the Lab 5 TODOs below it:
add an SQS queue, a second Lambda for order submission, a new route,
and a third Lambda triggered from the queue.

When all TODOs are filled in, `pulumi up` should create ~11 new resources
on top of the 9 from Lab 4, for roughly 20 total (the extra 4 are the
additional API Gateway routes for the stub endpoints).

Run `pulumi destroy` when you've completed all deliverables.
The next lab starts from a fresh provided template.
"""

import json
import pulumi
import pulumi_aws as aws


# =============================================================
# LAB 4 SECTION — PROVIDED, DO NOT MODIFY
# =============================================================

# IAM: LabRole lookup (same pattern as Lab 4)
# AWS Academy restricts iam:CreateRole — LabRole provides the permissions
# both Lambdas need: CloudWatch Logs, SQS read/write, and more.
# See Lab 4 comments for the least-privilege alternative.
lambda_role = aws.iam.get_role(name="LabRole")

# Status Lambda (Lab 4 — unchanged)
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
    tags={"Project": "NovaSpark", "Lab": "5"},
)

# API Gateway HTTP API (Lab 4 — unchanged)
http_api = aws.apigatewayv2.Api(
    "novaSpark-api",
    protocol_type="HTTP",
    tags={"Project": "NovaSpark", "Lab": "5"},
)

# GET /status integration + route (Lab 4 — unchanged)
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


# =============================================================
# LAB 5 SECTION — YOUR TODOS START HERE
# =============================================================

# TODO 1: Create an SQS queue for orders
# Use aws.sqs.Queue() with:
#
#   resource name:          "novaSpark-orders-queue"
#   name:                   "novaSpark-orders"
#   visibility_timeout_seconds: 30
#       (how long a message is hidden after a consumer receives it;
#        must be longer than your processor Lambda's timeout)
#   message_retention_seconds: 86400
#       (keep unprocessed messages for 24 hours)
#   tags:                   {"Project": "NovaSpark", "Lab": "5"}
#
# AWS Academy note: LabRole already has sqs:SendMessage, sqs:ReceiveMessage,
# sqs:DeleteMessage, and sqs:GetQueueAttributes — no policy attachment needed.
#
# In a real account you would scope queue access to specific roles:
#
#   aws.sqs.QueuePolicy("orders-queue-policy",
#       queue_url=orders_queue.url,
#       policy=orders_queue.arn.apply(lambda arn: json.dumps({
#           "Version": "2012-10-17",
#           "Statement": [{
#               "Effect": "Allow",
#               "Principal": {"AWS": orders_fn_role.arn},
#               "Action": "sqs:SendMessage",
#               "Resource": arn
#           }]
#       }))
#   )
#
orders_queue = None  # Replace this line


# TODO 2: Package the order submission Lambda code
# Use pulumi.FileArchive pointing to the "app/orders" folder.
#
#   orders_archive = pulumi.FileArchive("app/orders")
#
orders_archive = None  # Replace this line


# TODO 3: Create the order submission Lambda
# Use aws.lambda_.Function() with:
#
#   resource name:  "novaSpark-orders-fn"
#   runtime:        "python3.12"
#   role:           lambda_role.arn
#   handler:        "handler.lambda_handler"
#   code:           orders_archive
#   environment:    aws.lambda_.FunctionEnvironmentArgs(
#                       variables={
#                           "QUEUE_URL": orders_queue.url,
#                               (passes the queue URL into the Lambda at runtime —
#                                the handler reads this via os.environ["QUEUE_URL"])
#                       }
#                   )
#   timeout:        10
#   memory_size:    128
#   tags:           {"Project": "NovaSpark", "Lab": "5"}
#
orders_fn = None  # Replace this line


# TODO 4: Create an API Gateway integration for the orders Lambda
# Use aws.apigatewayv2.Integration() with:
#
#   resource name:           "novaSpark-orders-integration"
#   api_id:                  http_api.id
#   integration_type:        "AWS_PROXY"
#   integration_uri:         orders_fn.invoke_arn
#   payload_format_version:  "2.0"
#
orders_integration = None  # Replace this line


# TODO 5: Create routes for the full NovaSpark Order API
#
# The orders Lambda handles ALL five routes via routeKey dispatching.
# POST /orders is live; the others return 501 (Not Implemented) as stubs.
# This gives you the full API shape from day one.
#
# Create one aws.apigatewayv2.Route() for each of the following route_keys:
#
#   "POST /orders"          (live — implemented in orders Lambda)
#   "GET /orders/{id}"      (stub — returns 501, implemented in Lab 6)
#   "GET /orders"           (stub — returns 501, implemented in Lab 6)
#   "PATCH /orders/{id}"    (stub — returns 501, project extension)
#   "DELETE /orders/{id}"   (stub — returns 501, project extension)
#
# All five routes use the same integration (orders_integration).
# Pattern:
#
#   aws.apigatewayv2.Route(
#       "novaSpark-<method>-orders-route",
#       api_id=http_api.id,
#       route_key="<METHOD> /orders<suffix>",
#       target=orders_integration.id.apply(lambda id: f"integrations/{id}"),
#   )
#
# Note: "POST /orders" — not "/createOrder", not "/submitOrder".
# The HTTP method IS the verb. The path names the resource (plural noun).
#
orders_route = None         # POST /orders — replace this line
orders_get_by_id = None     # GET /orders/{id} — replace this line
orders_list = None          # GET /orders — replace this line
orders_patch = None         # PATCH /orders/{id} — replace this line
orders_delete = None        # DELETE /orders/{id} — replace this line


# TODO 6: Give API Gateway permission to invoke the orders Lambda
# Use aws.lambda_.Permission() with:
#
#   resource name:  "novaSpark-orders-apigw-permission"
#   action:         "lambda:InvokeFunction"
#   function:       orders_fn.name
#   principal:      "apigateway.amazonaws.com"
#   source_arn:     http_api.execution_arn.apply(lambda arn: f"{arn}/*/*")
#
orders_permission = None  # Replace this line


# TODO 7: Package the processor Lambda code
# Use pulumi.FileArchive pointing to the "app/processor" folder.
#
#   processor_archive = pulumi.FileArchive("app/processor")
#
processor_archive = None  # Replace this line


# TODO 8: Create the processor Lambda
# This function is triggered by SQS — NOT by API Gateway.
# Use aws.lambda_.Function() with:
#
#   resource name:  "novaSpark-processor-fn"
#   runtime:        "python3.12"
#   role:           lambda_role.arn
#   handler:        "handler.lambda_handler"
#   code:           processor_archive
#   timeout:        25
#       (must be less than visibility_timeout_seconds on the queue —
#        if processing takes longer than visibility timeout, SQS will
#        re-deliver the message and you'll process it twice)
#   memory_size:    128
#   tags:           {"Project": "NovaSpark", "Lab": "5"}
#
processor_fn = None  # Replace this line


# TODO 9: Connect the SQS queue to the processor Lambda
# An EventSourceMapping tells Lambda to poll the queue and invoke
# your processor function when messages arrive.
# Use aws.lambda_.EventSourceMapping() with:
#
#   resource name:        "novaSpark-sqs-trigger"
#   event_source_arn:     orders_queue.arn
#   function_name:        processor_fn.name
#   batch_size:           5
#       (process up to 5 messages per invocation)
#   enabled:              True
#
# How it works: Lambda polls SQS on your behalf (you don't write the poll loop).
# When messages arrive, Lambda invokes your processor with a batch.
# On success, Lambda deletes the messages. On failure, they reappear
# after the visibility timeout for retry.
#
event_source_mapping = None  # Replace this line


# =============================================================
# Outputs
# =============================================================

# TODO 10: Export the two live endpoint URLs
#
# Status endpoint (from Lab 4):
#   pulumi.export("status_url", http_api.api_endpoint.apply(lambda e: f"{e}/status"))
#
# Orders endpoint (new):
#   pulumi.export("orders_url", http_api.api_endpoint.apply(lambda e: f"{e}/orders"))
#
# After pulumi up, run:
#   pulumi stack output orders_url
# That URL is what you curl in D3.
#
# pulumi.export(...)   ← uncomment and complete both lines
