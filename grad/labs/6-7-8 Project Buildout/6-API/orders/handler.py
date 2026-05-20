"""
NovaSpark Orders Lambda Handler
Course: CS 545 — Cloud Native Platform Engineering

This handler is complete — no modifications needed for Week 8.
Your work is in __main__.py (the three TODOs).

Routes handled:
  POST   /orders        Validate body, enqueue to SQS, return 202 Accepted
  GET    /orders/{id}   Fetch one order from DynamoDB, return 200 or 404
  GET    /orders        Scan DynamoDB; supports optional ?customer_id=X filter
  PATCH  /orders/{id}   501 Not Implemented (stub)
  DELETE /orders/{id}   501 Not Implemented (stub)

API context note:
  This API is publicly addressable — any client with the URL can reach it.
  The customer_id field is accepted as caller-supplied input, which is
  appropriate for an internal tool (e.g., a customer service agent querying
  on behalf of a customer). For an external deployment where customers
  interact with the API directly, customer_id would be extracted from a
  verified JWT token rather than trusted from the request body. That
  authentication pattern is outside the scope of this course; document
  the gap in ADD Section 1c (Constraints) and ADD Section 4 (Security pillar).
"""

import json
import os
import uuid
from datetime import datetime
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

# ── AWS clients ───────────────────────────────────────────────────────────────
# Initialized at module level so they survive across warm Lambda invocations.
# TABLE_NAME and QUEUE_URL are injected via environment variables (TODO 2 in
# __main__.py). If either is missing, the Lambda will fail at the first
# call that uses it — check CloudWatch Logs for "KeyError" or empty string.
dynamodb = boto3.resource("dynamodb")
sqs      = boto3.client("sqs")

TABLE_NAME = os.environ.get("TABLE_NAME", "")
QUEUE_URL  = os.environ.get("QUEUE_URL", "")

table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None


# ── Helpers ───────────────────────────────────────────────────────────────────

class DecimalEncoder(json.JSONEncoder):
    """DynamoDB returns numbers as Decimal. Convert to int or float for JSON."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def _not_implemented(route: str) -> dict:
    return _response(501, {"error": f"{route} is not yet implemented"})


# ── Route handlers ────────────────────────────────────────────────────────────

def handle_post_order(event: dict) -> dict:
    """
    POST /orders

    Required body fields:
      item        (string)          — what is being ordered
      quantity    (positive int)    — how many
      customer_id (string)          — which customer is placing the order

    Returns 202 Accepted with order_id on success.
    Returns 400 Bad Request if any required field is missing or invalid.

    This handler enqueues the order to SQS and returns immediately — it does
    NOT write to DynamoDB directly. The processor Lambda handles the write
    asynchronously. This is what makes the 202 semantics work: the response
    time is decoupled from DynamoDB write latency.
    """
    # Parse body
    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return _response(400, {"error": "Request body must be valid JSON"})

    # Validate: item
    item = body.get("item")
    if not item or not isinstance(item, str) or not item.strip():
        return _response(400, {"error": "'item' is required and must be a non-empty string"})

    # Validate: quantity
    quantity = body.get("quantity")
    if (
        quantity is None
        or isinstance(quantity, bool)
        or not isinstance(quantity, int)
        or quantity <= 0
    ):
        return _response(400, {"error": "'quantity' is required and must be a positive integer"})

    # Validate: customer_id
    # Required for data scoping — stored in DynamoDB and used by GET /orders
    # filtering. See the API context note at the top of this file.
    customer_id = body.get("customer_id")
    if not customer_id or not isinstance(customer_id, str) or not customer_id.strip():
        return _response(400, {"error": "'customer_id' is required and must be a non-empty string"})

    # Build the order record
    order_id   = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"

    order = {
        "order_id":    order_id,
        "item":        item.strip(),
        "quantity":    quantity,
        "customer_id": customer_id.strip(),
        "status":      "received",
        "created_at":  created_at,
    }

    # Enqueue to SQS — the processor Lambda will write this to DynamoDB
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(order),
    )

    return _response(202, {
        "message":     "Order received",
        "order_id":    order_id,
        "customer_id": customer_id.strip(),
    })


def handle_get_order_by_id(order_id: str) -> dict:
    """
    GET /orders/{id}

    Returns 200 with the full order record (including customer_id) if found.
    Returns 404 if the order does not exist in DynamoDB.

    Note on eventual consistency: if you call this immediately after POST /orders,
    you may receive a 404 — the order is in SQS but not yet written by the
    processor Lambda. This is the pipeline consistency window. Record how long
    it persists during your Postman testing (Test 2 in the lab guide).
    """
    response = table.get_item(Key={"order_id": order_id})
    item = response.get("Item")

    if not item:
        return _response(404, {"error": f"Order '{order_id}' not found"})

    return _response(200, item)


def handle_list_orders(event: dict) -> dict:
    """
    GET /orders

    Returns all orders in DynamoDB. Supports optional ?customer_id=X filter.

    With ?customer_id=X:  returns only orders where customer_id == X
    Without filter:       returns all orders (internal / admin behavior)

    An unrecognized customer_id returns 200 with an empty list — not 404.

    Note on scan(): this implementation performs a full table scan on every
    call. At NovaSpark's current scale (low double-digit orders per day) this
    is acceptable. At millions of orders, scan() becomes a cost and latency
    problem. Document this as a Conscious Tradeoff in ADD Section 4
    (Performance Efficiency pillar) and name the fix (GSI on customer_id).
    """
    query_params = event.get("queryStringParameters") or {}
    customer_id  = query_params.get("customer_id")

    if customer_id:
        response = table.scan(
            FilterExpression=Attr("customer_id").eq(customer_id)
        )
    else:
        response = table.scan()

    orders = response.get("Items", [])
    return _response(200, {"orders": orders, "count": len(orders)})


def handle_patch_order(event: dict) -> dict:
    """PATCH /orders/{id} — not implemented. Returns 501."""
    return _not_implemented("PATCH /orders/{id}")


def handle_delete_order(event: dict) -> dict:
    """DELETE /orders/{id} — not implemented. Returns 501."""
    return _not_implemented("DELETE /orders/{id}")


# ── Main dispatcher ───────────────────────────────────────────────────────────

def handler(event: dict, context) -> dict:
    """
    Lambda entry point. Routes based on HTTP method and path.

    API Gateway HTTP API (payload format version 2.0) provides the method
    and path under event['requestContext']['http'].
    """
    http_ctx = event.get("requestContext", {}).get("http", {})
    method   = http_ctx.get("method", "")
    path     = http_ctx.get("path", "")

    if method == "POST" and path == "/orders":
        return handle_post_order(event)

    if method == "GET" and path.startswith("/orders/"):
        order_id = path[len("/orders/"):]
        return handle_get_order_by_id(order_id)

    if method == "GET" and path == "/orders":
        return handle_list_orders(event)

    if method == "PATCH" and path.startswith("/orders/"):
        return handle_patch_order(event)

    if method == "DELETE" and path.startswith("/orders/"):
        return handle_delete_order(event)

    return _response(404, {"error": f"Route not found: {method} {path}"})
