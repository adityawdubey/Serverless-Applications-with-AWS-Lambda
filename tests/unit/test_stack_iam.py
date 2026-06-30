import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from stacks.order_service_stack import OrderServiceStack


def _template():
    app = cdk.App()
    return Template.from_stack(OrderServiceStack(app, "TestStack"))


def _assert_action_granted(action):
    # Match.array_with matches a contiguous, ordered run, so check one action at
    # a time (single-element membership) to stay order-independent.
    _template().has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": Match.object_like(
                {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": Match.array_with([action]),
                                    "Effect": "Allow",
                                }
                            )
                        ]
                    )
                }
            )
        },
    )


def test_iam_policy_grants_write_access():
    _assert_action_granted("dynamodb:PutItem")


def test_iam_policy_grants_read_access():
    _assert_action_granted("dynamodb:Scan")
