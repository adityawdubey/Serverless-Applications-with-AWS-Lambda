import json
from decimal import Decimal

import handler


def test_resp_shape_and_headers():
    out = handler._resp(201, {"ok": True})
    assert out["statusCode"] == 201
    # CORS lives only on the API — the function sets Content-Type and nothing else.
    assert out["headers"] == {"Content-Type": "application/json"}
    assert json.loads(out["body"]) == {"ok": True}


def test_resp_serializes_dynamodb_decimal():
    # DynamoDB returns numbers as Decimal; the response must still be valid JSON.
    out = handler._resp(200, [{"quantity": Decimal("2")}])
    assert json.loads(out["body"]) == [{"quantity": 2}]
