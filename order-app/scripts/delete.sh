#!/usr/bin/env bash
# Tear down the Order Service stack (and the Orders table's data).
#
#   ./scripts/delete.sh
set -euo pipefail

# Run from the CDK project root (this script lives in scripts/).
cd "$(dirname "$0")/.."

command -v cdk >/dev/null || { echo "ERROR: cdk CLI not found. Install: npm install -g aws-cdk"; exit 1; }

# Activate the virtualenv if present (CDK needs its Python deps to synthesise).
if [ -d .venv ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

echo "==> Destroying OrderServiceStack"
cdk destroy --force

# Clean up the local deploy artifact, if any.
rm -f cdk-outputs.json
echo "Done."
