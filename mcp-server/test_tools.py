#!/usr/bin/env python3
"""Quick unit test to verify MCP tools work before Claude Desktop testing"""
import sys
sys.path.insert(0, '/home/develeap/hellio-hr-max/mcp-server')

from server import list_templates, get_template_schema, fill_template

print("Testing MCP Tools...")
print("=" * 80)

# Test 1: list_templates
print("\n1. Testing list_templates()...")
templates = list_templates()
print(f"   ✓ Found {len(templates)} templates:")
for t in templates:
    print(f"     - {t['name']}: {t['description']}")

# Test 2: get_template_schema
print("\n2. Testing get_template_schema('offer_letter')...")
schema = get_template_schema("offer_letter")
print(f"   ✓ Required: {', '.join(schema['required_fields'])}")
print(f"   ✓ Optional: {', '.join(schema.get('optional_fields', []))}")

# Test 3: fill_template
print("\n3. Testing fill_template('offer_letter')...")
result = fill_template("offer_letter", {
    "candidate_name": "Jane Smith",
    "position_title": "Senior DevOps Engineer",
    "salary": "$150,000/year",
    "start_date": "February 1, 2026",
    "manager_name": "John Doe",
    "sender_name": "Sarah HR"
})
print(f"   ✓ Generated {len(result)} characters")
print(f"   Preview: {result[:200]}...")

print("\n" + "=" * 80)
print("✓ All tools working! Ready for Claude Desktop testing.")
print("=" * 80)
