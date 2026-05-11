"""
NovaSpark Technologies — Order Processor
Lab 6: DynamoDB Integration

This Lambda is triggered by SQS — NOT by API Gateway.
When messages arrive in the orders queue, Lambda receives them
as a batch of Records and this handler processes each one.

Lab 5 left a TODO here: orders were logged to CloudWatch but never
persisted. Lab 6 fills that gap — each order is written to DynamoDB
so it can be retrieved by order_id.

There is ONE TODO in this file (TODO A).
"""

import json
import logging
import os
import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------
# MODULE-LEVEL (GLOBAL) SCOPE — runs once per cold start
#
# Creating the DynamoDB resource here means it is reused across
# warm invocations instead of being recreated on every call.
# This is the same pattern as any expensive initialisation:
# boto3 clients, DB connections, config loading.
# ---------------------------------------------------------------
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def lambda_handler(event, context):
    records = event.get("Records", [])
    logger.info(f"Processing batch of {len(records)} order(s)")

    for record in records:
        order = json.loads(record["body"])

        order_id  = order.get("order_id", "unknown")
        item      = order.get("item", "unknown")
        quantity  = order.get("quantity", 0)
        status    = order.get("status", "received")
        created_at = order.get("created_at", "")

        logger.info(
            f"[ORDER RECEIVED] order_id={order_id} | item={item} | qty={quantity}"
        )

        # TODO A: Persist this order to DynamoDB.
        #
        # Write the order to the novaspark-orders table using table.put_item().
        # Include all fields from the order dict:
        #   order_id, item, quantity, status, created_at
        #
        # After a successful write, log a confirmation line:
        #   logger.info(f"[ORDER PERSISTED] order_id={order_id}")
        #
        # Use a try/except block to handle boto3 errors gracefully.
        # If the write fails, log the error and re-raise the exception
        # so SQS knows the message was not processed successfully.
        # SQS will then re-deliver the message after the visibility timeout.
        #
        # Pattern:
        #   try:
        #       table.put_item(Item={...})
        #       logger.info(f"[ORDER PERSISTED] order_id={order_id}")
        #   except Exception as e:
        #       logger.error(f"[ORDER FAILED] order_id={order_id} | error={e}")
        #       raise
        #
        pass  # TODO A — remove this line when you implement the above

    # Returning normally signals SQS to delete the processed messages.
    # Raising an exception causes them to reappear after the visibility timeout.
    return {"statusCode": 200, "processed": len(records)}
