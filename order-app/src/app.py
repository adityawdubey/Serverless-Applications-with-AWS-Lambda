import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3

# Clients are created OUTSIDE the handler so warm invocations reuse them.
# (deck: "Lambda freezes & reuses the execution environment — anything created
# out here is reused on warm calls.")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def _to_jsonable(value):
    # DynamoDB's resource API returns numbers as Decimal, which json.dumps
    # cannot serialize. Collapse whole numbers to int, otherwise float.
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def _resp(status, body):
    # CORS is configured on the API Gateway HTTP API (see the stack). Per AWS,
    # when CORS is configured on an HTTP API, API Gateway adds the CORS headers
    # and IGNORES any returned by the function — so we keep CORS in exactly one
    # place (the API). This is the deck's "#1 gotcha: enable CORS on the API".
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=_to_jsonable),
    }


def create_order(event):
    raw = event.get("body") or ""
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return _resp(400, {"message": "invalid JSON body"})
    if not data:
        return _resp(400, {"message": "empty body"})

    item = {
        "orderId": str(uuid.uuid4()),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "status": "New",
        "customer": data.get("customer"),
        "item": data.get("item"),
        "quantity": data.get("quantity"),
    }
    table.put_item(Item=item)
    return _resp(201, item)








