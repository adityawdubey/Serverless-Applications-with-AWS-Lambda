import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from stacks.order_service_stack import OrderServiceStack


def _template():
    app = cdk.App()
    return Template.from_stack(OrderServiceStack(app, "TestStack"))


def test_site_bucket_is_a_public_website():
    # Option B: the page is a public S3 static website (no CloudFront).
    _template().has_resource_properties(
        "AWS::S3::Bucket",
        {
            "WebsiteConfiguration": {"IndexDocument": "index.html"},
            "PublicAccessBlockConfiguration": {
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            },
        },
    )


def test_site_bucket_grants_public_read():
    # A bucket policy makes objects world-readable so the website endpoint works.
    _template().has_resource_properties(
        "AWS::S3::BucketPolicy",
        {
            "PolicyDocument": Match.object_like(
                {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {"Action": "s3:GetObject", "Effect": "Allow"}
                            )
                        ]
                    )
                }
            )
        },
    )


def test_no_cloudfront_distribution():
    # Option B drops CloudFront entirely.
    _template().resource_count_is("AWS::CloudFront::Distribution", 0)


def test_frontend_is_deployed_to_the_bucket():
    # BucketDeployment renders as a custom resource that uploads web/ + config.js.
    _template().resource_count_is("Custom::CDKBucketDeployment", 1)
