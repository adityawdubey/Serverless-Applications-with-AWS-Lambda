#!/usr/bin/env bash
# Deploy the Order Service stack. Safe to re-run (bootstrap + deploy are idempotent).
#   ./scripts/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."

# Python env that CDK needs.
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt

cdk bootstrap                        # one-time per account/region
cdk deploy --require-approval never   # prints SiteUrl / ApiUrl / TableName

echo
echo "Done — open the SiteUrl above (the http:// S3 website endpoint)."
