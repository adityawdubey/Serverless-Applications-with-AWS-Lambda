import importlib
import json

import boto3
import pytest
from moto import mock_aws

TABLE_NAME = "Orders-test"


@pytest.fixture
def app_module():
    with mock_aws():
        boto3.client("dynamodb").create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "orderId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "orderId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        import app
        importlib.reload(app)
        yield app


def test_list_orders_returns_newest_first(app_module):
    t = boto3.resource("dynamodb").Table(TABLE_NAME)
    t.put_item(Item={"orderId": "a", "createdAt": "2026-01-01T00:00:00+00:00", "quantity": 1})
    t.put_item(Item={"orderId": "b", "createdAt": "2026-06-01T00:00:00+00:00", "quantity": 3})

    out = app_module.list_orders()
    assert out["statusCode"] == 200
    items = json.loads(out["body"])
    assert [o["orderId"] for o in items] == ["b", "a"]  # newest first
    assert items[0]["quantity"] == 3  # Decimal collapsed to int


def test_list_orders_empty_table(app_module):
    out = app_module.list_orders()
    assert out["statusCode"] == 200
    assert json.loads(out["body"]) == []
