import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3

# Created outside the handler so warm invocations reuse the client.
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def _to_jsonable(value):
    # DynamoDB returns numbers as Decimal, which json.dumps can't handle.
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def _resp(status, body):
    # CORS lives on the API (the stack), not here, so we only set Content-Type.
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


def list_orders():
    # scan() reads the whole table (fine here); use Query with a key in production.
    result = table.scan()
    items = sorted(
        result.get("Items", []),
        key=lambda o: o.get("createdAt", ""),
        reverse=True,
    )
    return _resp(200, items)


def handler(event, context):
    # HTTP API payload v2 gives routeKey values like "POST /orders".
    route = event.get("routeKey")
    if route == "POST /orders":
        return create_order(event)
    if route == "GET /orders":
        return list_orders()
    return _resp(404, {"message": "not found"})




