#!/bin/bash
# Test MCP Server Tools via HTTP

echo "=== Testing MCP Server Tools ==="
echo ""

echo "1. Testing list_templates..."
curl -s -X POST http://localhost:8002/mcp/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "list_templates", "arguments": {}}' | jq '.'

echo ""
echo "2. Testing get_template_schema for rejection_email..."
curl -s -X POST http://localhost:8002/mcp/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_template_schema", "arguments": {"template_name": "rejection_email"}}' | jq '.'

echo ""
echo "3. Testing fill_template for rejection_email..."
curl -s -X POST http://localhost:8002/mcp/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "fill_template",
    "arguments": {
      "template_name": "rejection_email",
      "field_values": {
        "candidate_name": "Allie Mata",
        "position_title": "Junior DevOps Engineer",
        "sender_name": "Hellio HR Team"
      }
    }
  }' | jq '.'
