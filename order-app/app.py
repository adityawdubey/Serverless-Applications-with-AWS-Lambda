#!/usr/bin/env python3
# CDK app entry point (referenced by cdk.json: "app": "python3 app.py").
# The Lambda handler lives separately in lambda_functions/order_service/handler.py
# and is loaded from that asset folder by the stack.
import aws_cdk as cdk

from stacks.order_service_stack import OrderServiceStack

app = cdk.App()
OrderServiceStack(app, "OrderServiceStack")
app.synth()
