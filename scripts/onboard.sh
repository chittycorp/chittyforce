#!/bin/bash
set -euo pipefail
echo "=== chittyforce Onboarding ==="
curl -s -X POST "${GETCHITTY_ENDPOINT:-https://get.chitty.cc/api/onboard}" \
  -H "Content-Type: application/json" \
  -d '{"service_name":"chittyforce","organization":"CHITTYCORP","type":"service","tier":4,"domains":["force.chitty.cc"]}' | jq .
