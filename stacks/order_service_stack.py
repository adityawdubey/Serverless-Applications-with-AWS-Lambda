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
)
from constructs import Construct


class OrderServiceStack(Stack):
    """The Order Service — one microservice of a restaurant application.

    Frontend on a public S3 static-website bucket (HTTP); data path is
    API Gateway -> Lambda -> DynamoDB. The page (S3, http) and the API
    (execute-api, https) are different origins, so the HTTP API enables CORS
    and the page is told the API base via a deploy-time config.js.
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

        # The page is served from S3 (a different origin than execute-api), so the
        # browser makes a cross-origin request — CORS on the API is required.
        http_api = apigwv2.HttpApi(
            self,
            "OrderHttpApi",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                ],
                allow_headers=["Content-Type"],
            ),
        )

        integration = integrations.HttpLambdaIntegration("OrderIntegration", handler=self.fn)
        http_api.add_routes(
            path="/orders", methods=[apigwv2.HttpMethod.POST], integration=integration
        )
        http_api.add_routes(
            path="/orders", methods=[apigwv2.HttpMethod.GET], integration=integration
        )

        # Public S3 static website. No CloudFront: the website endpoint is
        # HTTP-only and the bucket must allow public reads. Fine for a demo.
        site_bucket = s3.Bucket(
            self,
            "SiteBucket",
            website_index_document="index.html",
            website_error_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,  # empty the bucket on `cdk destroy`
        )

        # Upload web/ plus a generated config.js that carries the real API base
        # (a deploy-time value), so the static page knows where to call.
        s3deploy.BucketDeployment(
            self,
            "DeployWebsite",
            sources=[
                s3deploy.Source.asset("web"),
                s3deploy.Source.data(
                    "config.js", f"window.API_BASE = '{http_api.api_endpoint}';"
                ),
            ],
            destination_bucket=site_bucket,
        )

        CfnOutput(self, "SiteUrl", value=site_bucket.bucket_website_url)
        CfnOutput(self, "ApiUrl", value=http_api.url or "")
        CfnOutput(self, "TableName", value=self.table.table_name)
