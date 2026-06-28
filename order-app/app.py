#!/usr/bin/env python3
# CDK app entry point (referenced by cdk.json: "app": "python3 app.py").
# NOTE: there are two app.py files — this root one is the CDK app entry; the
# one in src/ is the Lambda handler, loaded from its own asset folder.
import aws_cdk as cdk

from order_service.stack import OrderServiceStack

app = cdk.App()
OrderServiceStack(app, "OrderServiceStack")
app.synth()
