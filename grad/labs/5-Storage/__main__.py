"""
NovaSpark Technologies — Orders API
Lab 5: Storage — DynamoDB + Lambda Integration

This template extends Lab 4's status API with a DynamoDB table and a new
GET /orders/{id} route. Unlike Lab 4, this template will NOT deploy without
your changes — locate each TODO and complete it before running pulumi up.

Your task before running pulumi up:
1. Read every resource definition and its comments
2. Complete TODO 1: provision the DynamoDB table
3. Complete TODO 2: inject the table name into Lambda's environment
4. Complete TODO 3: add the GET /orders/{id} route to API Gateway
5. Complete TODO 4: export the table name as a stack output

Design decisions to be prepared to defend (for your ADD):
- Why PAY_PER_REQUEST billing mode instead of PROVISIONED?
- Why is the TABLE_NAME injected as an environment variable, not hardcoded?
- Why does the Lambda function need no new IAM configuration to read DynamoDB?
- Why does GET /orders/{id} route to the same Lambda as GET /status?
"""

import pulumi
import pulumi_aws as aws


# =============================================================
# IAM: Lambda Execution Role (unchanged from Lab 4)
#
# LabRole already includes AmazonDynamoDBFullAccess — no new IAM
# configuration is needed to give this Lambda DynamoDB access.
#
# This is the Lab 4 pattern unchanged. In a production account you
# would create a scoped role with only the DynamoDB actions this
# function actually uses (dynamodb:GetItem, dynamodb:PutItem, etc.),
# scoped to the specific table ARN — not *.
#
# The execution role analysis you wrote in Lab 4 (D5) provides the
# foundation for ADD Section 4 (Security pillar) — the gap between
# LabRole and least-privilege is the concrete security finding.
# =============================================================

lambda_role = aws.iam.get_role(name="LabRole")


# =============================================================
# TODO 1: DynamoDB Table
#
# Provision the NovaSpark orders table. This table will persist every
# order placed through the API. The key design decision is access pattern:
# the primary key must support the access patterns your API requires.
#
# Required attributes:
#   name         = "novaspark-orders"   (the DynamoDB table name in AWS)
#   hash_key     = "order_id"           (partition key — string type)
#   billing_mode = "PAY_PER_REQUEST"    (on-demand — no capacity planning)
#
# You must also define the hash_key attribute in the attributes list:
#   aws.dynamodb.TableAttributeArgs(name="order_id", type="S")
#
# Why PAY_PER_REQUEST?
#   PROVISIONED billing requires you to specify read/write capacity units
#   in advance. Underprovisioning causes throttling; overprovisioning wastes
#   money. PAY_PER_REQUEST scales automatically with traffic at a higher
#   per-request cost but zero operational overhead — correct for a new
#   service with unknown traffic patterns.
#
# Tags to include: Project="NovaSpark", Lab="5", Course="CS545"
#
# Example structure:
#   orders_table = aws.dynamodb.Table(
#       "novaSpark-orders-table",
#       name="novaspark-orders",
#       ...
#   )
# =============================================================

# TODO 1: Create the DynamoDB table here
# orders_table = aws.dynamodb.Table(...)


# =============================================================
# Lambda Function
#
# The function definition carries forward from Lab 4 with two changes:
#   1. The description is updated to reflect the new scope
#   2. TABLE_NAME is added to the environment variables (TODO 2)
#
# The handler code in app/handler.py has also changed — it now reads
# TABLE_NAME and dispatches on the route key to handle both GET /status
# and GET /orders/{id}. Review handler.py before deploying.
#
# timeout is increased to 15s to accommodate DynamoDB I/O overhead.
# =============================================================

lambda_fn = aws.lambda_.Function(
    "novaSpark-orders-fn",
    description="NovaSpark Orders API for Lab 5",
    runtime="python3.12",
    role=lambda_role.arn,
    handler="handler.lambda_handler",
    code=pulumi.FileArchive("app"),
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "ENVIRONMENT": "dev",
            "SERVICE": "orders-api",
            # TODO 2: Add TABLE_NAME here, injected from the table resource.
            #
            # This follows 12-Factor Factor III: store config in the environment.
            # The Lambda handler reads TABLE_NAME via os.environ["TABLE_NAME"]
            # to construct its DynamoDB Table reference. Hardcoding the table
            # name in handler.py would couple the code to a specific deployment
            # environment — injecting it as an env var lets the same code run
            # against dev, staging, and prod tables without modification.
            #
            # Syntax: "TABLE_NAME": orders_table.name
            # Note: orders_table.name is a Pulumi Output[str], not a plain
            # string. Pulumi resolves it to the actual table name at deploy time.
        }
    ),
    timeout=15,
    memory_size=128,
    tags={"Project": "NovaSpark", "Lab": "5", "Course": "CS545"}
)


# =============================================================
# API Gateway HTTP API (v2)
#
# Same API resource as Lab 4. This lab adds a second route that uses
# the same integration (AWS_PROXY to the same Lambda function).
#
# The Lambda handler uses event["routeKey"] to dispatch to the correct
# handler — see handler.py for how this works.
# =============================================================

http_api = aws.apigatewayv2.Api(
    "novaSpark-orders-api",
    protocol_type="HTTP",
    tags={"Project": "NovaSpark", "Lab": "5"}
)

integration = aws.apigatewayv2.Integration(
    "novaSpark-lambda-integration",
    api_id=http_api.id,
    integration_type="AWS_PROXY",
    integration_uri=lambda_fn.invoke_arn,
    payload_format_version="2.0"
)

# Existing route from Lab 4 — still functional
status_route = aws.apigatewayv2.Route(
    "novaSpark-status-route",
    api_id=http_api.id,
    route_key="GET /status",
    target=integration.id.apply(lambda id: f"integrations/{id}")
)

# TODO 3: Add the GET /orders/{id} route
#
# This route uses path parameter syntax — the {id} portion becomes
# a path parameter that API Gateway extracts and passes to Lambda
# in event["pathParameters"]["id"].
#
# Use the same integration as status_route. The handler in handler.py
# reads event["routeKey"] to distinguish which route matched and
# dispatches to the appropriate handler function.
#
# Syntax mirrors the status route above — the only difference is
# the route_key value: "GET /orders/{id}"
#
# orders_route = aws.apigatewayv2.Route(
#     "novaSpark-orders-id-route",
#     api_id=http_api.id,
#     route_key="GET /orders/{id}",
#     target=integration.id.apply(lambda id: f"integrations/{id}")
# )


stage = aws.apigatewayv2.Stage(
    "novaSpark-default-stage",
    api_id=http_api.id,
    name="$default",
    auto_deploy=True
)


# =============================================================
# Lambda Resource-Based Policy (unchanged from Lab 4)
#
# The wildcard /* /* scopes invocation permission to any method on
# any route of this specific API — not any API in the account.
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
pulumi.export("orders_base_url", http_api.api_endpoint.apply(lambda e: f"{e}/orders"))
pulumi.export("lambda_arn", lambda_fn.arn)
pulumi.export("lambda_role_arn", lambda_role.arn)

# TODO 4: Export the table name
#
# Add a "table_name" stack output so you can confirm the table was
# created and reference it in your submission PDF.
#
# Syntax: pulumi.export("table_name", orders_table.name)
