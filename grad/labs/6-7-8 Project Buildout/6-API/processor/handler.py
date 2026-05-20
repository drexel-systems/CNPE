"""
NovaSpark Processor Lambda Handler
Course: CS 545 — Cloud Native Platform Engineering

This handler is complete — no modifications needed for Week 8.
Your work is in __main__.py (the three TODOs).

Trigger: SQS event source mapping (configured in TODO 1 of __main__.py).
When a message arrives in the orders queue, Lambda invokes this function
with the message(s) as the event payload.

Responsibility: Read each order from the SQS event, write it to DynamoDB.

Idempotency:
  SQS standard queues guarantee at-least-once delivery — the same message
  can be delivered more than once. This handler uses a DynamoDB
  ConditionExpression ("attribute_not_exists(order_id)") to make the write
  idempotent: if the order already exists in DynamoDB, the second write is
  silently skipped rather than overwriting or erroring. This is a Conscious
  Tradeoff worth naming in ADD Section 3 (Processor Lambda entry) — it is
  not the same as an explicit idempotency key strategy, but it is correct
  behavior for this access pattern.

Error handling:
  ConditionalCheckFailedException (duplicate) — caught and logged, not raised.
  All other ClientErrors (throttling, unavailable, etc.) — re-raised so SQS
  retries the message. This is the correct behavior: we want failed writes to
  be retried, not silently acknowledged. Without re-raising, a DynamoDB outage
  would cause SQS to mark messages as successfully processed and delete them —
  orders would be permanently lost. Document this in ADD Section 4
  (Reliability pillar).
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

# ── Logging ───────────────────────────────────────────────────────────────────
# print() also works in Lambda — both go to CloudWatch Logs. Using the logging
# module adds log level prefixes (INFO, ERROR) which makes filtering easier.
# This satisfies 12-factor Factor XI (Logs as Streams) in the strict sense.
# For queryable structured logs, JSON-formatted entries would be preferred —
# a gap worth noting in ADD Section 4 (Operational Excellence pillar).
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ── AWS clients ───────────────────────────────────────────────────────────────
# TABLE_NAME is injected via environment variable (TODO 2 in __main__.py).
# If missing, the Lambda will fail on the first put_item call with an error
# about an empty table name — check CloudWatch Logs.
dynamodb   = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "")
table      = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None


# ── Main handler ──────────────────────────────────────────────────────────────

def handler(event: dict, context) -> dict:
    """
    Process a batch of SQS messages. Each message body is one serialized order.

    Batch size is configured in __main__.py TODO 1 — set to 1 for this lab,
    so each invocation processes exactly one order. The loop handles the general
    case in case batch_size is increased later.
    """
    processed = 0

    for record in event.get("Records", []):
        order    = json.loads(record["body"])
        order_id = order.get("order_id", "unknown")

        logger.info(
            f"[ORDER RECEIVED] order_id={order_id} "
            f"customer_id={order.get('customer_id')} "
            f"item={order.get('item')} qty={order.get('quantity')}"
        )

        try:
            table.put_item(
                Item={
                    "order_id":    order_id,
                    "item":        order.get("item"),
                    "quantity":    order.get("quantity"),
                    "customer_id": order.get("customer_id"),
                    "status":      order.get("status", "received"),
                    "created_at":  order.get("created_at"),
                },
                # ConditionExpression makes the write idempotent.
                # If an item with this order_id already exists, DynamoDB raises
                # ConditionalCheckFailedException instead of overwriting it.
                ConditionExpression="attribute_not_exists(order_id)",
            )
            logger.info(f"[ORDER PERSISTED] order_id={order_id}")
            processed += 1

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "ConditionalCheckFailedException":
                # Duplicate SQS delivery — order already in DynamoDB. Safe to
                # acknowledge (not re-raise). Counted as processed.
                logger.info(
                    f"[ORDER DUPLICATE] order_id={order_id} — "
                    f"already in DynamoDB, skipping"
                )
                processed += 1

            else:
                # Genuine failure (throttling, table unavailable, permissions,
                # etc.). Re-raise so SQS does NOT acknowledge the message —
                # it will be redelivered for retry. This is the correct
                # behavior for maintaining reliability.
                logger.error(
                    f"[ORDER FAILED] order_id={order_id} | "
                    f"error_code={error_code} | error={e}"
                )
                raise

    return {
        "statusCode": 200,
        "body": json.dumps({"processed": processed}),
    }
