"""
NovaSpark Technologies — Orders API
Lambda handler for Lab 5: Storage.

This file extends the Lab 4 status handler with DynamoDB integration
and a new GET /orders/{id} route.

Four TODOs in this file — complete them in order:
  TODO A: Import boto3 at module level
  TODO B: Initialize the DynamoDB resource and table client at module level
  TODO C: Add route dispatch in lambda_handler
  TODO D: Implement handle_get_order_by_id

The GET /status route from Lab 4 is retained and fully functional.
The GET /orders/{id} route is your implementation target for this lab.

Design principles to carry into your ADD:
- boto3 clients belong at module level — initialized once per cold start,
  reused across all warm invocations (same pattern as Lab 4's created_at timestamp)
- Route dispatch on event["routeKey"] keeps a single Lambda handling multiple
  routes without a separate function per route — cost and operational simplicity
- Explicit 404 handling: missing items return a structured error body,
  not an unhandled exception that produces a 502
"""

import json
import os
import logging
import datetime

# TODO A: Import boto3
#
# boto3 is the AWS SDK for Python. It is pre-installed in all Lambda
# runtimes — no requirements.txt entry needed.
#
# Add this line with the other imports above:
#   import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------
# MODULE-LEVEL (GLOBAL) SCOPE — runs once per cold start
#
# From Lab 4: env_create_time is set here and stays frozen across warm
# invocations, proving that module-level code does not re-run.
#
# The same principle governs boto3 clients. Constructing a DynamoDB client
# inside the handler (on every invocation) adds latency and wastes resources.
# Constructed here, it is reused across every warm invocation at no cost.
# ---------------------------------------------------------------

env_create_time = datetime.datetime.now()
print(f"--- GLOBAL INIT: Environment created at {env_create_time} ---")


# ---------------------------------------------------------------
# Custom JSON encoder for DynamoDB Decimal values
#
# DynamoDB returns numeric attributes as Python Decimal objects,
# which json.dumps() cannot serialize by default — even when the
# value is integer-valued. Convert Decimal to int when there is
# no fractional part, otherwise to float.  The need for this and 
# how to use it are described in the lab-guide, please refer to
# that.
# ---------------------------------------------------------------
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)





# TODO B: Initialize DynamoDB client and table reference at module level
#
# Two lines to add here, after env_create_time:
#
#   dynamodb = boto3.resource("dynamodb")
#   table = dynamodb.Table(os.environ["TABLE_NAME"])
#
# boto3.resource("dynamodb") creates a DynamoDB service resource — a
# high-level object that wraps the low-level API client. It is thread-safe
# and designed to be initialized once and shared.
#
# dynamodb.Table(name) creates a Table object bound to "novaspark-orders"
# (the value of TABLE_NAME, injected via Pulumi in __main__.py).
# TABLE_NAME is read from the environment here, at module load time, so
# a missing environment variable causes an immediate, obvious failure
# rather than a confusing runtime error on the first DynamoDB call.
#
# Why this placement matters:
#   - Cold start: 1 boto3.resource() call + 1 Table() call (adds ~10ms)
#   - Warm invocation: 0 additional calls — table is already initialized
#   This is the same lesson as env_create_time: module scope = once per
#   execution environment. See Lab 4 D4 analysis for the full argument.


def lambda_handler(event, context):
    """
    Dispatches incoming API Gateway events to the appropriate handler.

    event["routeKey"] identifies which API route matched:
      "GET /status"       → handle_status
      "GET /orders/{id}"  → handle_get_order_by_id

    This single-Lambda / multi-route pattern keeps the deployment simple
    at NovaSpark's current scale. If routes grow significantly in number
    or need independent scaling, splitting into per-route functions is a
    natural next step — but that's a later optimization.
    """

    logger.info(f"Event received: {json.dumps(event)}")

    route_key = event.get("routeKey", "GET /status")

    # TODO C: Add route dispatch
    #
    # Replace the single return statement below with an if/elif/else block
    # that dispatches on route_key:
    #
    #   if route_key == "GET /status":
    #       return handle_status(event, context)
    #   elif route_key == "GET /orders/{id}":
    #       return handle_get_order_by_id(event)
    #   else:
    #       return {
    #           "statusCode": 404,
    #           "headers": {"Content-Type": "application/json"},
    #           "body": json.dumps({"error": f"Route not found: {route_key}"}),
    #       }
    #
    # The else branch is important: any route not explicitly handled should
    # return 404, not fall through to undefined behavior.

    return handle_status(event, context)


def handle_status(event, context):
    """
    Returns the NovaSpark system status. Identical to Lab 4.
    """
    environment = os.environ.get("ENVIRONMENT", "unknown")
    service_name = os.environ.get("SERVICE", "orders-api")

    env_age = (datetime.datetime.now() - env_create_time).total_seconds()
    logger.info(f"Environment age: {env_age:.2f}s")

    response_body = {
        "service": service_name,
        "status": "operational",
        "environment": environment,
        "created_at": env_create_time.isoformat(),
        "message": "All systems go.",
    }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response_body),
    }


# TODO D: Implement handle_get_order_by_id
#
# This function retrieves a single order from DynamoDB by order_id.
#
# Steps:
#   1. Extract the order ID from the event:
#        order_id = event["pathParameters"]["id"]
#      API Gateway places path parameters (the {id} in "GET /orders/{id}")
#      in event["pathParameters"]. The key name matches the placeholder.
#
#   2. Call get_item on the module-level table object:
#        response = table.get_item(Key={"order_id": order_id})
#      get_item performs a strongly consistent read by default (equivalent
#      to DynamoDB's ConsistentRead=True). It returns a dict that may or
#      may not contain an "Item" key.
#
#   3. Check whether the item exists:
#        item = response.get("Item")
#        if item is None:
#            return { 404 response }
#      DynamoDB does not raise an exception for a missing key — it simply
#      omits "Item" from the response. response.get("Item") returns None
#      rather than raising KeyError, which is the correct way to check.
#
#   4. Return the item on success — but watch out for the Decimal
#      gotcha described below.
#
# 404 response body should be:
#   {"error": f"Order {order_id} not found"}
#
# ---------------------------------------------------------------
# THE DECIMAL GOTCHA — read carefully
# ---------------------------------------------------------------
# DynamoDB returns numeric attributes as decimal.Decimal objects,
# which are NOT JSON-serializable by default — not even when the
# value is an integer. A naive json.dumps(item) will fail with:
#
#   TypeError: Object of type Decimal is not JSON serializable
#
# Your seeded test item has quantity=3, which boto3 returns as
# Decimal("3"). The 200 response path will crash with a 502 at
# the gateway unless you handle this. The cleanest production
# pattern is a custom JSON encoder. Add this near your imports:
#
#   from decimal import Decimal
#
#   class DecimalEncoder(json.JSONEncoder):
#       def default(self, obj):
#           if isinstance(obj, Decimal):
#               return int(obj) if obj % 1 == 0 else float(obj)
#           return super().default(obj)
#
# Then serialize the item with the encoder:
#
#   return {
#       "statusCode": 200,
#       "headers": {"Content-Type": "application/json"},
#       "body": json.dumps(item, cls=DecimalEncoder),
#   }
#
# Why this matters for your ADD: every boto3 + Lambda + JSON
# stack hits this. The abstraction leaks. Section 5 of your ADD
# (Operational Considerations) is where you would note quirks
# like this if they affect operations at scale.
#
# def handle_get_order_by_id(event):
#     ...
