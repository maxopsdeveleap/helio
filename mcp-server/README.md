# Hellio HR Templates MCP Server

MCP server providing HR document template management tools for automated document generation.

## Overview

This MCP server exposes 3 tools that allow any AI agent (Claude Desktop, Strands agents, etc.) to:
- List available HR document templates
- Get template schemas (required/optional fields)
- Fill templates with data to generate documents

## Available Templates

1. **offer_letter** - Standard job offer letter
2. **rejection_email** - Candidate rejection email
3. **interview_invitation** - Interview scheduling invitation
4. **nda** - Non-Disclosure Agreement for candidates

## Tools

### `list_templates()`
Lists all available HR document templates.

**Returns:**
```json
[
  {"name": "offer_letter", "description": "Standard job offer letter"},
  {"name": "rejection_email", "description": "Candidate rejection email"},
  ...
]
```

### `get_template_schema(template_name: str)`
Get required and optional fields for a template.

**Example:**
```python
get_template_schema("offer_letter")
```

**Returns:**
```json
{
  "name": "offer_letter",
  "description": "Standard job offer letter for successful candidates",
  "required_fields": ["candidate_name", "position_title", "salary", "start_date", "manager_name", "sender_name"],
  "optional_fields": ["benefits_summary", "equity_details", "work_location"]
}
```

### `fill_template(template_name: str, field_values: dict)`
Generate a document from a template by filling in field values.

**Example:**
```python
fill_template("offer_letter", {
    "candidate_name": "Jane Smith",
    "position_title": "Senior DevOps Engineer",
    "salary": "$150,000/year",
    "start_date": "February 1, 2026",
    "manager_name": "John Doe",
    "sender_name": "Sarah HR"
})
```

**Returns:** Rendered document text

## Running the Server

### Local Development
```bash
cd mcp-server
uv pip install -r pyproject.toml
python -m fastmcp run server.py --transport sse --port 8002
```

### Docker (Recommended)
```bash
# From project root
docker compose up mcp-server
```

Server will be available at: `http://localhost:8002`

## Testing with Claude Desktop

1. Configure Claude Desktop to connect to the MCP server
2. Edit `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "hellio-hr-templates": {
      "url": "http://localhost:8002/sse"
    }
  }
}
```

3. Test in Claude Desktop:
```
User: "What document templates are available?"
Claude: [calls list_templates]

User: "Generate an offer letter for Jane Smith as Senior DevOps Engineer at $150k, starting Feb 1"
Claude: [calls get_template_schema, then fill_template]
```

## Adding New Templates

1. Create template file: `templates/my_template.j2` (Jinja2 format)
2. Create schema file: `schemas/my_template.yaml`
3. Restart server - template automatically available

## Architecture

- **FastMCP**: Simplified MCP server framework
- **Jinja2**: Template rendering engine
- **YAML**: Schema definitions
- **HTTP/SSE**: Transport layer for MCP protocol

## Integration with Hellio Agent

Add to your Strands agent configuration to enable document generation in HR workflows:

```python
# In agent config
mcp_servers = {
    "hellio-templates": "http://localhost:8002/sse"
}
```

Agent can now generate standardized documents during candidate/position processing.
