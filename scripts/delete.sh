#!/usr/bin/env bash
# Tear down the Order Service stack (deletes the Orders table's data too).
#   ./scripts/delete.sh
set -euo pipefail
cd "$(dirname "$0")/.."

[ -d .venv ] && source .venv/bin/activate
cdk destroy --force
rm -f cdk-outputs.json
