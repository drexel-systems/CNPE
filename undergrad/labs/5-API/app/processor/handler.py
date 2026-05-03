"""
NovaSpark Technologies — Order Processor
Lab 5: Async APIs with SQS

This Lambda is triggered by SQS — NOT by API Gateway.
When a message lands in the orders queue, Lambda receives it
as a batch of "Records" and this handler processes each one.

SQS trigger mechanics:
- Lambda polls the queue automatically (you don't write the poll loop)
- Each invocation receives up to 10 messages (configurable batch size)
- If this function returns successfully, SQS deletes the messages
- If this function raises an exception, the messages become visible again
  after the visibility timeout and will be retried
- After maxReceiveCount failures, messages move to the Dead Letter Queue (DLQ)

Current behavior: log the order to CloudWatch.

Notice what is missing: we have no way to look up an order after it is
processed. The order exists in CloudWatch logs but cannot be queried by
order_id. This is intentional for Lab 5 — you will fix it in the
storage lab by writing each order to DynamoDB.

For now, this gap is the point. Ben asked where the orders are going.
The answer right now is: CloudWatch logs. That is not production-ready.
"""

import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    records = event.get("Records", [])
    logger.info(f"Processing batch of {len(records)} order(s)")

    for record in records:
        # Each SQS record has a "body" field containing the message string
        order = json.loads(record["body"])

        order_id = order.get("order_id", "unknown")
        item = order.get("item", "unknown")
        quantity = order.get("quantity", 0)

        logger.info(
            f"[ORDER RECEIVED] order_id={order_id} | item={item} | qty={quantity}"
        )

        # TODO (Lab 6 — Storage): persist this order to DynamoDB.
        # Right now this record exists only in CloudWatch logs.
        # A real production system needs durable storage so orders
        # can be retrieved by ID, listed, and updated as they ship.
        #
        # table.put_item(Item={
        #     "order_id": order_id,
        #     "item": item,
        #     "quantity": quantity,
        #     "status": "processing",
        # })

        logger.info(f"[ORDER LOGGED] order_id={order_id} — logged only, not persisted")

    # Returning normally signals SQS to delete the processed messages.
    # If an exception were raised here, the messages would reappear
    # in the queue after the visibility timeout and be retried.
    return {"statusCode": 200, "processed": len(records)}
