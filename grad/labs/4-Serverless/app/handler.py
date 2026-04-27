"""
NovaSpark Technologies — Status API
Lambda handler for the /status endpoint.

This file is complete. Read it before you deploy.

Design decisions to note:
- Environment variables used for all configuration (no hardcoded values)
- Structured logging via Python's logging module (visible in CloudWatch)
- context metadata logged explicitly to support cold start analysis
- Response format matches API Gateway HTTP API payload format version 2.0

When you extend this function in Lab 5 to write to DynamoDB,
you will modify this file to import boto3 and add a DynamoDB client
at module level (outside the handler) — this is intentional for
connection reuse across warm invocations.
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
        event: The event dict from the invoker. When called via API Gateway,
               this includes the HTTP method, path, headers, and query params.
        context: Lambda runtime metadata — function name, memory limit,
                 remaining execution time. Useful for cold start analysis.
    """

    # Log the full event so you can trace what API Gateway sends
    logger.info(f"Event received: {json.dumps(event)}")

    # Read configuration from environment (12-factor Factor III)
    # These values are set in the Pulumi template — no values are hardcoded here
    environment = os.environ.get("ENVIRONMENT", "unknown")
    service_name = os.environ.get("SERVICE", "status-api")

    # Log Lambda runtime metadata
    # The context.get_remaining_time_in_millis() value in CloudWatch
    # helps you understand execution duration relative to the timeout setting
    logger.info(f"Function: {context.function_name}")
    logger.info(f"Memory limit: {context.memory_limit_in_mb} MB")
    logger.info(f"Time remaining: {context.get_remaining_time_in_millis()} ms")

    response_body = {
        "service": service_name,
        "status": "operational",
        "environment": environment,
        "message": "All systems go.",
    }

    # API Gateway HTTP API (v2) requires this response envelope format
    # statusCode, headers, and body are all required
    # body must be a string (json.dumps), not a dict
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(response_body),
    }
