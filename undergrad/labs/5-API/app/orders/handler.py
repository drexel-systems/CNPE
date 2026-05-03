"""
NovaSpark Technologies — Order API Handler
Lab 5: Async APIs with SQS

This Lambda handles ALL routes in the NovaSpark Order API.
It dispatches based on the routeKey field in the API Gateway event.

Routes and their status after each lab:

  POST /orders            — LIVE in Lab 5 (this lab)
  GET  /orders/{id}       — Stubbed (501) in Lab 5, implemented in Lab 6
  GET  /orders            — Stubbed (501) in Lab 5, implemented in Lab 6
  PATCH /orders/{id}      — Stubbed (501), available as a project extension
  DELETE /orders/{id}     — Stubbed (501), available as a project extension

The full API surface is visible from day one so you can see the shape
of what you're building — even before the storage layer exists.

Stubs return 501 Not Implemented, which is correct HTTP semantics:
"This route exists but has not been implemented yet." It is more
informative than 404 (which says "this route doesn't exist at all").

See the Project Roadmap for the full API spec and extension options.
"""

import json
import logging
import os
import uuid

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    route_key = event.get("routeKey", "")
    logger.info(f"Route: {route_key}")

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


# =============================================================
# POST /orders — IMPLEMENTED (Lab 5)
# =============================================================

def handle_post_order(event):
    """
    Accept a new order, validate it, put it on the SQS queue, return 202.

    202 Accepted means: "I got it and I'm working on it" — NOT "it's done."
    This is correct HTTP semantics for async operations.

    The order is processed by a separate Lambda (processor/handler.py)
    triggered from the SQS queue.
    """
    sqs = boto3.client("sqs")
    queue_url = os.environ["QUEUE_URL"]

    # Parse the request body
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Request body must be valid JSON"}),
        }

    # Validate required fields
    item = body.get("item")
    quantity = body.get("quantity")

    if not item or quantity is None:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": "Both 'item' and 'quantity' are required fields"}
            ),
        }

    if not isinstance(quantity, int) or quantity < 1:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "'quantity' must be a positive integer"}),
        }

    # Build the order object
    order_id = str(uuid.uuid4())
    order = {
        "order_id": order_id,
        "item": item,
        "quantity": quantity,
        "status": "received",
    }

    # Put the order onto the SQS queue
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(order),
    )

    logger.info(f"Order queued: {order_id} — {quantity}x {item}")

    # Return 202 Accepted — not 200 OK.
    # The order has been received and queued, not completed.
    return {
        "statusCode": 202,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "order_id": order_id,
                "status": "received",
                "message": "Order accepted and queued for processing.",
            }
        ),
    }


# =============================================================
# GET /orders/{id} — STUB (implemented in Lab 6)
# =============================================================

def handle_get_order_by_id(event):
    """
    Retrieve a specific order by ID from DynamoDB.

    This route is stubbed in Lab 5 — the storage layer doesn't exist yet.
    It will be implemented in Lab 6 when DynamoDB is wired in.

    Lab 6 implementation will look like:
        order_id = event["pathParameters"]["id"]
        table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
        response = table.get_item(Key={"order_id": order_id})
        item = response.get("Item")
        if not item:
            return {"statusCode": 404, "body": json.dumps({"error": "not found"})}
        return {"statusCode": 200, "body": json.dumps(item)}
    """
    order_id = (event.get("pathParameters") or {}).get("id", "unknown")
    return {
        "statusCode": 501,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": "Not Implemented",
            "message": f"GET /orders/{{id}} is not yet implemented. Coming in Lab 6.",
            "order_id": order_id,
        }),
    }


# =============================================================
# GET /orders — STUB (implemented in Lab 6)
# =============================================================

def handle_list_orders(event):
    """
    List all orders, with optional ?status= filter.

    This route is stubbed in Lab 5 — the storage layer doesn't exist yet.
    It will be implemented in Lab 6 using a DynamoDB Scan.

    Lab 6 implementation will look like:
        table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
        response = table.scan()
        return {"statusCode": 200, "body": json.dumps(response["Items"])}
    """
    status_filter = (event.get("queryStringParameters") or {}).get("status")
    return {
        "statusCode": 501,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": "Not Implemented",
            "message": "GET /orders is not yet implemented. Coming in Lab 6.",
            "status_filter": status_filter,
        }),
    }


# =============================================================
# PATCH /orders/{id} — STUB (project extension)
# =============================================================

def handle_patch_order(event):
    """
    Update an order's status.

    This is a project extension route — implement it if you choose this option.

    Implementation hint:
        order_id = event["pathParameters"]["id"]
        body = json.loads(event.get("body") or "{}")
        new_status = body.get("status")
        table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
        table.update_item(
            Key={"order_id": order_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": new_status},
        )
    """
    order_id = (event.get("pathParameters") or {}).get("id", "unknown")
    return {
        "statusCode": 501,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": "Not Implemented",
            "message": "PATCH /orders/{id} is a project extension. Implement it to earn extension credit.",
            "order_id": order_id,
        }),
    }


# =============================================================
# DELETE /orders/{id} — STUB (project extension)
# =============================================================

def handle_delete_order(event):
    """
    Soft-cancel an order by setting status to 'cancelled'.

    This is a project extension route — implement it if you choose this option.

    Note: this is a SOFT delete. The record stays in DynamoDB with
    status='cancelled'. We never remove order records — that would destroy
    the audit trail. Idempotent: cancelling an already-cancelled order
    returns the same 204 response, not an error.

    Implementation hint:
        order_id = event["pathParameters"]["id"]
        table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
        table.update_item(
            Key={"order_id": order_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "cancelled"},
        )
        return {"statusCode": 204, "body": ""}
    """
    order_id = (event.get("pathParameters") or {}).get("id", "unknown")
    return {
        "statusCode": 501,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": "Not Implemented",
            "message": "DELETE /orders/{id} is a project extension. Implement it to earn extension credit.",
            "order_id": order_id,
        }),
    }
