#!/usr/bin/env bash
# Deploy the Order Service stack and wire the live API URL into the frontend.
#
#   ./scripts/deploy.sh
#
# Prerequisites: cdk CLI (npm install -g aws-cdk), aws CLI with credentials,
# and Python 3.12. Safe to re-run — bootstrap and deploy are idempotent.
set -euo pipefail

# Run from the CDK project root (this script lives in scripts/).
cd "$(dirname "$0")/.."

echo "==> Checking prerequisites"
command -v cdk >/dev/null || { echo "ERROR: cdk CLI not found. Install: npm install -g aws-cdk"; exit 1; }
command -v aws >/dev/null || { echo "ERROR: aws CLI not found."; exit 1; }

# Create the virtualenv on first run, then activate and install CDK's deps.
if [ ! -d .venv ]; then
  echo "==> Creating virtualenv (.venv)"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

echo "==> Verifying AWS credentials"
aws sts get-caller-identity >/dev/null 2>&1 || {
  echo "ERROR: no usable AWS credentials. Run 'aws sso login' or 'aws configure' first."
  exit 1
}

echo "==> Bootstrapping the environment (idempotent)"
cdk bootstrap

echo "==> Deploying OrderServiceStack"
# The deploy uploads web/ to S3 and generates config.js with the live API URL,
# so there is no manual paste step.
cdk deploy --require-approval never --outputs-file cdk-outputs.json

# Read the stack outputs and print the public site + API URLs.
read -r SITE_URL API_URL <<<"$(python3 -c "
import json
o = next(iter(json.load(open('cdk-outputs.json')).values()))
print(o['SiteUrl'], o['ApiUrl'])
")"

echo
echo "Done."
echo "  Site (open this):  $SITE_URL"
echo "  API:               $API_URL"
echo
echo "First deploy? Give CloudFront a few minutes to finish provisioning."
echo "Tear down later with:  ./scripts/delete.sh"
