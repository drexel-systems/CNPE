"""
NovaSpark Technologies — Status API
Lambda handler for the /status endpoint.

This file is complete. You do not need to modify it in Parts 1–3.
In the capstone project, you will extend this handler to support
additional routes (POST, GET by ID) and DynamoDB reads/writes.
"""

import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Returns the current NovaSpark system status as JSON.

    Args:
        event: The event dict from the invoker (API Gateway passes HTTP request info here).
        context: Runtime information — function name, memory limit, time remaining.
    """

    # Log the full event so you can see what API Gateway sends (visible in CloudWatch)
    logger.info(f"Event received: {json.dumps(event)}")

    # Read configuration from environment variables (12-factor Factor III)
    environment = os.environ.get("ENVIRONMENT", "unknown")
    service_name = os.environ.get("SERVICE", "status-api")

    # Log Lambda runtime metadata — useful for observing cold start behavior
    logger.info(f"Function: {context.function_name}")
    logger.info(f"Memory limit: {context.memory_limit_in_mb} MB")
    logger.info(f"Time remaining: {context.get_remaining_time_in_millis()} ms")

    # Build the response body
    response_body = {
        "service": service_name,
        "status": "operational",
        "environment": environment,
        "message": "All systems go.",
    }

    # Lambda response format required by API Gateway HTTP API (payload format version 2.0)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(response_body),
    }
