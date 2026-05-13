"""
NovaSpark Technologies — Order API
Lab 6: DynamoDB Integration

This Lambda handles all five Order API routes via routeKey dispatching.
POST /orders was fully implemented in Lab 5.
In Lab 6 you implement the first two stub routes:
  GET /orders/{id}  — retrieve a single order by ID
  GET /orders       — list all orders (with optional ?status= filter)

PATCH /orders/{id} and DELETE /orders/{id} remain 501 stubs.
They are listed in the project roadmap as extension work.

There are TWO TODOs in this file (TODO B and TODO C).
"""

import json
import logging
import os
import uuid
import datetime
import decimal
import boto3
from boto3.dynamodb.conditions import Attr


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------
# MODULE-LEVEL (GLOBAL) SCOPE — runs once per cold start
#
# Both the SQS client (for POST) and the DynamoDB table (for GET)
# are initialised here so they are reused on warm invocations.
# ---------------------------------------------------------------
sqs    = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
table  = dynamodb.Table(os.environ["TABLE_NAME"])


def lambda_handler(event, context):
    logger.info(f"Event received: {json.dumps(event)}")
    route_key = event.get("routeKey", "")

    if route_key == "POST /orders":
        return handle_post_order(event)
    elif route_key == "GET /orders/{id}":
        return handle_get_order_by_id(event)
    elif route_key == "GET /orders":
        return handle_list_orders(event)
    elif route_key == "PATCH /orders/{id}":
        return handle_patch_order(event)
    elif route_key == "DELETE /orders/{id}":
        return handle_delete_order(event)
    else:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Route not found: {route_key}"}),
        }


# ---------------------------------------------------------------
# POST /orders — fully implemented in Lab 5, do not modify
# ---------------------------------------------------------------

def handle_post_order(event):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _error(400, "Request body must be valid JSON")

    item     = body.get("item")
    quantity = body.get("quantity")

    if not item or quantity is None:
        return _error(400, "Both 'item' and 'quantity' are required fields")

    if not isinstance(quantity, int) or quantity < 1:
        return _error(400, "'quantity' must be a positive integer")

    order = {
        "order_id":   str(uuid.uuid4()),
        "item":       item,
        "quantity":   quantity,
        "status":     "received",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
    }

    queue_url = os.environ["QUEUE_URL"]
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(order))
    logger.info(f"Order queued: {order['order_id']}")

    return {
        "statusCode": 202,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "order_id": order["order_id"],
            "status":   "received",
            "message":  "Order accepted and queued for processing",
        }),
    }


# ---------------------------------------------------------------
# GET /orders/{id}
# ---------------------------------------------------------------

def handle_get_order_by_id(event):
    # TODO B: Retrieve a single order by order_id from DynamoDB.
    #
    # Steps:
    #   1. Get the order_id from the path parameters.
    #      It lives at: event["pathParameters"]["id"]
    #
    #   2. Call table.get_item() with the partition key:
    #      response = table.get_item(Key={"order_id": order_id})
    #
    #   3. Extract the item:
    #      order = response.get("Item")
    #
    #   4. If no item was found (order is None or falsy), return 404:
    #      return _error(404, f"Order {order_id} not found")
    #
    #   5. If the item was found, return 200 with the order as JSON:
    #      return {"statusCode": 200,
    #              "headers": {"Content-Type": "application/json"},
    #              "body": json.dumps(order)}
    #
    #   6. Wrap the whole thing in try/except and return 500 on error.
    #      Log the error before returning.
    #
    # Replace the line below with your implementation.
    return _not_implemented("GET /orders/{id}")


# ---------------------------------------------------------------
# GET /orders
# ---------------------------------------------------------------

def handle_list_orders(event):
    # TODO C: List orders from DynamoDB, with an optional status filter.
    #
    # Steps:
    #   1. Check for an optional ?status= query parameter:
    #      params = event.get("queryStringParameters") or {}
    #      status_filter = params.get("status")
    #
    #   2a. If status_filter is provided, use table.scan() with a
    #       FilterExpression to return only matching orders:
    #
    #       response = table.scan(
    #           FilterExpression=Attr("status").eq(status_filter)
    #       )
    #
    #   2b. If no status_filter, do a plain scan for all orders:
    #       response = table.scan()
    #
    #   3. Return 200 with the items list:
    #      orders = response.get("Items", [])
    #      return {"statusCode": 200,
    #              "headers": {"Content-Type": "application/json"},
    #              "body": json.dumps({"orders": orders, "count": len(orders)})}
    #
    #   4. Wrap in try/except and return 500 on error.
    #
    # Note on scan(): scan() reads every item in the table and is perfectly
    # fine for small tables like this one. In a production system with
    # millions of orders you would use a GSI and query() instead — but that
    # is an extension topic covered in W3 of this lab's written deliverables.
    #
    # Replace the line below with your implementation.
    return _not_implemented("GET /orders")


# ---------------------------------------------------------------
# PATCH /orders/{id} — stub (Lab extension)
# ---------------------------------------------------------------

def handle_patch_order(event):
    # Extension work — update order status (e.g. received → processing → shipped)
    # Requires a table.update_item() call with an UpdateExpression.
    # See project roadmap for the extension specification.
    return _not_implemented("PATCH /orders/{id}")


# ---------------------------------------------------------------
# DELETE /orders/{id} — stub (Lab extension)
# ---------------------------------------------------------------

def handle_delete_order(event):
    # Extension work — soft-delete by setting status = "cancelled"
    # rather than removing the item from the table.
    # See project roadmap for the extension specification.
    return _not_implemented("DELETE /orders/{id}")


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def _error(status_code, message):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": message}),
    }


def _not_implemented(route):
    return {
        "statusCode": 501,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": "Not implemented",
            "route": route,
            "hint": "This route is a Lab 6 TODO — see handler.py for instructions",
        }),
    }
