from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
)
from constructs import Construct


class OrderServiceStack(Stack):
    """The Order Service — one microservice of a larger restaurant application.

    A full restaurant app would also have Menu, Payments, and Kitchen services;
    we build only this one, end to end. The narrow scope is deliberate.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

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

        # One domain Lambda, two routes. Code.from_asset zips src/ (just app.py;
        # boto3 is already in the runtime, so NO pip/Docker bundling) and CDK
        # ships it. handler="app.handler" → file app.py, function handler().
        # The fixed name shows as "OrderService" in the console; redeploys update
        # it in place (drop function_name to let CDK auto-name if ever needed).
        self.fn = lambda_.Function(
            self,
            "OrderServiceFunction",
            function_name="OrderService",
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.ARM_64,
            handler="app.handler",
            code=lambda_.Code.from_asset("src"),
            memory_size=256,
            timeout=Duration.seconds(10),
            environment={"TABLE_NAME": self.table.table_name},
        )
