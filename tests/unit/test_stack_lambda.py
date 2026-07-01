import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from stacks.order_service_stack import OrderServiceStack


def _template():
    app = cdk.App()
    return Template.from_stack(OrderServiceStack(app, "TestStack"))


def test_lambda_runtime_arch_and_config():
    _template().has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Runtime": "python3.12",
            "Architectures": ["arm64"],
            "Handler": "handler.handler",
            "MemorySize": 256,
            "Timeout": 10,
            "FunctionName": "OrderService",
        },
    )


def test_lambda_has_table_name_env():
    _template().has_resource_properties(
        "AWS::Lambda::Function",
        {"Environment": {"Variables": Match.object_like({"TABLE_NAME": Match.any_value()})}},
    )


def test_exactly_one_domain_lambda():
    # CDK adds helper Lambdas for the static-site deployment (BucketDeployment,
    # auto-delete-objects), so assert exactly one *domain* function (ours) by
    # its FunctionName rather than a raw total count.
    fns = _template().find_resources(
        "AWS::Lambda::Function", {"Properties": {"FunctionName": "OrderService"}}
    )
    assert len(fns) == 1
