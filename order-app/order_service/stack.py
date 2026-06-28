from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_dynamodb as dynamodb,
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
