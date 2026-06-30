from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct


class OrderServiceStack(Stack):
    """The Order Service — one microservice of a restaurant application.

    Frontend on a private S3 bucket served via CloudFront; data path is
    API Gateway -> Lambda -> DynamoDB.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # On-demand table. DESTROY deletes the data on `cdk destroy` (demo, not prod).
        self.table = dynamodb.Table(
            self,
            "OrdersTable",
            partition_key=dynamodb.Attribute(
                name="orderId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # One Lambda handling both routes. from_asset zips the folder; boto3 is in
        # the runtime, so there's nothing to bundle (no Docker).
        self.fn = lambda_.Function(
            self,
            "OrderServiceFunction",
            function_name="OrderService",
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.ARM_64,
            handler="handler.handler",
            code=lambda_.Code.from_asset("lambda_functions/order_service"),
            memory_size=256,
            timeout=Duration.seconds(10),
            environment={"TABLE_NAME": self.table.table_name},
        )

        # Least privilege: a scoped policy for just this table, just read + write.
        self.table.grant_read_write_data(self.fn)

        # Private bucket; CloudFront reaches it via Origin Access Control (no
        # public access), and serves the page over HTTPS.
        site_bucket = s3.Bucket(
            self,
            "SiteBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,  # empty the bucket on `cdk destroy`
        )

        distribution = cloudfront.Distribution(
            self,
            "SiteDistribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(site_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
        )

        # No CORS needed: the page and the API end up same-origin because both
        # are served by the CloudFront distribution (the /orders behavior below).
        http_api = apigwv2.HttpApi(self, "OrderHttpApi")

        integration = integrations.HttpLambdaIntegration("OrderIntegration", handler=self.fn)
        http_api.add_routes(
            path="/orders", methods=[apigwv2.HttpMethod.POST], integration=integration
        )
        http_api.add_routes(
            path="/orders", methods=[apigwv2.HttpMethod.GET], integration=integration
        )

        # Route /orders through the same CloudFront domain as the page, so the
        # browser sees one origin. Don't cache API responses; forward the request
        # unchanged (minus the Host header, which API Gateway sets itself).
        distribution.add_behavior(
            "/orders",
            origins.HttpOrigin(
                f"{http_api.api_id}.execute-api.{self.region}.amazonaws.com"
            ),
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
            origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        )

        # Upload web/ to the bucket and invalidate the CloudFront cache.
        s3deploy.BucketDeployment(
            self,
            "DeployWebsite",
            sources=[s3deploy.Source.asset("web")],
            destination_bucket=site_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        CfnOutput(self, "SiteUrl", value=f"https://{distribution.distribution_domain_name}")
        CfnOutput(self, "ApiUrl", value=http_api.url or "")
        CfnOutput(self, "TableName", value=self.table.table_name)
