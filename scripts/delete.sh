#!/usr/bin/env bash
# Tear down the Order Service stack (deletes the Orders table's data too).
#   ./scripts/delete.sh
set -euo pipefail
cd "$(dirname "$0")/.."

[ -d .venv ] && source .venv/bin/activate

# CloudFormation can only delete an EMPTY bucket, so empty the site bucket first.
# (We do this explicitly rather than via an auto-delete custom-resource Lambda.)
BUCKET=$(aws cloudformation describe-stack-resources --stack-name OrderServiceStack \
  --query "StackResources[?ResourceType=='AWS::S3::Bucket'].PhysicalResourceId | [0]" \
  --output text 2>/dev/null || true)
if [ -n "${BUCKET:-}" ] && [ "$BUCKET" != "None" ]; then
  echo "Emptying s3://$BUCKET ..."
  aws s3 rm "s3://$BUCKET" --recursive || true
fi

cdk destroy --force
rm -f cdk-outputs.json
