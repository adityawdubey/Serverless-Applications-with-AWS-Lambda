import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from stacks.order_service_stack import OrderServiceStack


def _template():
    app = cdk.App()
    return Template.from_stack(OrderServiceStack(app, "TestStack"))


def test_http_api_has_cors():
    # Cross-origin (S3 http page -> execute-api https); the API enables CORS.
    _template().has_resource_properties(
        "AWS::ApiGatewayV2::Api",
        {
            "ProtocolType": "HTTP",
            "CorsConfiguration": Match.object_like(
                {
                    "AllowOrigins": ["*"],
                    "AllowMethods": Match.array_with(["GET", "POST"]),
                }
            ),
        },
    )


def test_exactly_two_routes():
    _template().resource_count_is("AWS::ApiGatewayV2::Route", 2)


def test_outputs_present():
    outputs = _template().find_outputs("*")
    assert "ApiUrl" in outputs
    assert "SiteUrl" in outputs
