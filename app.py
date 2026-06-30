#!/usr/bin/env python3
# CDK app entry point (see cdk.json: "app": "python3 app.py").
import aws_cdk as cdk

from stacks.order_service_stack import OrderServiceStack

app = cdk.App()
OrderServiceStack(app, "OrderServiceStack")
app.synth()
