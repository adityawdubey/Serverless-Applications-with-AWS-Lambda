import aws_cdk as cdk
from aws_cdk.assertions import Template

from order_service.stack import OrderServiceStack


def _template():
    app = cdk.App()
    stack = OrderServiceStack(app, "TestStack")
    return Template.from_stack(stack)


def test_dynamodb_table_is_on_demand_with_orderid_key():
    template = _template()
    template.has_resource_properties(
        "AWS::DynamoDB::Table",
        {
            "BillingMode": "PAY_PER_REQUEST",
            "KeySchema": [{"AttributeName": "orderId", "KeyType": "HASH"}],
        },
    )


def test_dynamodb_table_destroyed_on_teardown():
    # RemovalPolicy.DESTROY renders as DeletionPolicy: Delete on the CFN resource.
    _template().has_resource("AWS::DynamoDB::Table", {"DeletionPolicy": "Delete"})
