import importlib
import json
import uuid

import boto3
import pytest
from moto import mock_aws

TABLE_NAME = "Orders-test"


@pytest.fixture
def app_module():
    # Start the DynamoDB mock, create the table the handler expects, then
    # (re)import the handler so its module-level `table` binds inside the mock.
    with mock_aws():
        boto3.client("dynamodb").create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "orderId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "orderId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        import handler
        importlib.reload(handler)
        yield handler


def test_create_order_returns_201_and_persists(app_module):
    event = {"body": json.dumps({"customer": "Asha", "item": "Cold coffee", "quantity": 2})}
    out = app_module.create_order(event)
    assert out["statusCode"] == 201
    body = json.loads(out["body"])
    assert body["status"] == "New"
    assert body["customer"] == "Asha"
    assert body["quantity"] == 2
    uuid.UUID(body["orderId"])  # raises if not a valid uuid
    # It is actually stored.
    stored = boto3.resource("dynamodb").Table(TABLE_NAME).scan()["Items"]
    assert len(stored) == 1 and stored[0]["customer"] == "Asha"


def test_create_order_rejects_invalid_json(app_module):
    out = app_module.create_order({"body": "{not json"})
    assert out["statusCode"] == 400


def test_create_order_rejects_empty_body(app_module):
    assert app_module.create_order({"body": ""})["statusCode"] == 400
    assert app_module.create_order({})["statusCode"] == 400
