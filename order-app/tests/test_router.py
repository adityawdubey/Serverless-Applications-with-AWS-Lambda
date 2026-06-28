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


def test_router_post(app_module):
    event = {"routeKey": "POST /orders", "body": json.dumps({"customer": "Ravi", "item": "Paneer wrap", "quantity": 1})}
    assert app_module.handler(event, None)["statusCode"] == 201


def test_router_get(app_module):
    assert app_module.handler({"routeKey": "GET /orders"}, None)["statusCode"] == 200


def test_router_unknown_route_404(app_module):
    out = app_module.handler({"routeKey": "DELETE /orders"}, None)
    assert out["statusCode"] == 404
    assert json.loads(out["body"]) == {"message": "not found"}
