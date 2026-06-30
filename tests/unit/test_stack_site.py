import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from stacks.order_service_stack import OrderServiceStack


def _template():
    app = cdk.App()
    return Template.from_stack(OrderServiceStack(app, "TestStack"))


def test_site_bucket_blocks_public_access():
    # The site bucket must be private — CloudFront serves it, not the public.
    _template().has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }
        },
    )


def test_cloudfront_distribution_serves_index():
    _template().has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": Match.object_like(
                {"DefaultRootObject": "index.html"}
            )
        },
    )


def test_frontend_is_deployed_to_the_bucket():
    # BucketDeployment renders as a custom resource that uploads web/.
    _template().resource_count_is("Custom::CDKBucketDeployment", 1)


def test_api_routed_through_cloudfront():
    # /orders is served by the same distribution as the page (same-origin).
    _template().has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": Match.object_like(
                {
                    "CacheBehaviors": Match.array_with(
                        [Match.object_like({"PathPattern": "/orders"})]
                    )
                }
            )
        },
    )
