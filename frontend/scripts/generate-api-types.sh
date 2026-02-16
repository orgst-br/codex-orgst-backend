#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000/api/v1/openapi.json}"
OUTPUT_DIR="packages/api-types/generated"

echo "Fetching OpenAPI schema from $API_URL..."
mkdir -p "$OUTPUT_DIR"
npx openapi-typescript "$API_URL" -o "$OUTPUT_DIR/api.ts"
echo "Types generated at $OUTPUT_DIR/api.ts"
