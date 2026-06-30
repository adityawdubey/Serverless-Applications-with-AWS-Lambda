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
    """The Order Service — one microservice of a larger restaurant application.

    A full restaurant app would also have Menu, Payments, and Kitchen services;
    we build only this one, end to end. The narrow scope is deliberate.

    Production-shaped: the single-page frontend is hosted on a private S3 bucket
    served over HTTPS through CloudFront; the API is API Gateway → Lambda →
    DynamoDB. The frontend reaches the API via a generated config.js, so there is
    no manual URL paste step.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------------------ data
        # On-demand table; DESTROY enables easy teardown.
        # NOTE: RemovalPolicy.DESTROY deletes the data on `cdk destroy` — not for
        # production.
        self.table = dynamodb.Table(
            self,
            "OrdersTable",
            partition_key=dynamodb.Attribute(
                name="orderId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # --------------------------------------------------------------- compute
        # One domain Lambda, two routes. Code.from_asset zips the handler folder
        # (just handler.py; boto3 is already in the runtime, so NO pip/Docker
        # bundling) and CDK ships it. handler="handler.handler" → file handler.py,
        # function handler(). The fixed name shows as "OrderService" in the
        # console; redeploys update it in place (drop function_name to let CDK
        # auto-name if ever needed).
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

        # Least privilege — CDK generates a scoped IAM policy for exactly this
        # table (deck: "the #1 cause of real-world Lambda failures is
        # permissions; give each function only what it needs"). grant_read_write
        # is the narrowest method that covers both routes (put + scan).
        self.table.grant_read_write_data(self.fn)

        # ---------------------------------------------------------- static site
        # Private bucket — NOT publicly readable. CloudFront reaches it via
        # Origin Access Control; all public traffic goes through CloudFront/HTTPS.
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

        # ------------------------------------------------------------------- api
        # HTTP API (simpler/cheaper than REST). CORS is configured HERE and only
        # here — the single source of truth (deck's #1 gotcha) — and locked to the
        # CloudFront origin that actually serves the page.
        http_api = apigwv2.HttpApi(
            self,
            "OrderHttpApi",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=[f"https://{distribution.distribution_domain_name}"],
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.OPTIONS,
                ],
                allow_headers=["*"],
            ),
        )

        integration = integrations.HttpLambdaIntegration("OrderIntegration", handler=self.fn)
        http_api.add_routes(
            path="/orders", methods=[apigwv2.HttpMethod.POST], integration=integration
        )
        http_api.add_routes(
            path="/orders", methods=[apigwv2.HttpMethod.GET], integration=integration
        )

        # -------------------------------------------------------------- deploy FE
        # Upload web/ to the bucket, plus a generated config.js that carries the
        # live API URL (resolved at deploy time), then invalidate the CloudFront
        # cache so the new version is served. This removes any manual paste step.
        s3deploy.BucketDeployment(
            self,
            "DeployWebsite",
            sources=[
                s3deploy.Source.asset("web"),
                s3deploy.Source.data(
                    "config.js",
                    f'window.APP_CONFIG = {{ apiBase: "{http_api.url}" }};',
                ),
            ],
            destination_bucket=site_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        # --------------------------------------------------------------- outputs
        CfnOutput(self, "SiteUrl", value=f"https://{distribution.distribution_domain_name}")
        CfnOutput(self, "ApiUrl", value=http_api.url or "")
        CfnOutput(self, "TableName", value=self.table.table_name)
