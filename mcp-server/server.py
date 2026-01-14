"""
Hellio HR Templates MCP Server
Provides document template management tools for HR workflows
"""

from pathlib import Path
from typing import Any
import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Hellio HR Templates")

# Paths
TEMPLATES_DIR = Path(__file__).parent / "templates"
SCHEMAS_DIR = Path(__file__).parent / "schemas"


@mcp.tool()
def list_templates() -> list[dict[str, str]]:
    """
    List all available HR document templates.

    Returns:
        List of templates with name and description
    """
    templates = []

    # Scan schemas directory for template metadata
    for schema_file in SCHEMAS_DIR.glob("*.yaml"):
        try:
            with open(schema_file, "r") as f:
                schema = yaml.safe_load(f)
                templates.append({
                    "name": schema.get("name", schema_file.stem),
                    "description": schema.get("description", "No description available")
                })
        except Exception as e:
            # If schema fails, try to find template file
            template_name = schema_file.stem
            if (TEMPLATES_DIR / f"{template_name}.j2").exists():
                templates.append({
                    "name": template_name,
                    "description": f"Template: {template_name} (schema load failed)"
                })

    return templates


@mcp.tool()
def get_template_schema(template_name: str) -> dict[str, Any]:
    """
    Get the required and optional fields for a specific template.

    Args:
        template_name: Name of the template

    Returns:
        Schema with required_fields and optional_fields lists
    """
    schema_file = SCHEMAS_DIR / f"{template_name}.yaml"

    if not schema_file.exists():
        return {
            "error": f"Schema not found for template: {template_name}",
            "available_templates": [t["name"] for t in list_templates()]
        }

    try:
        with open(schema_file, "r") as f:
            schema = yaml.safe_load(f)
            return {
                "name": schema.get("name", template_name),
                "description": schema.get("description", ""),
                "required_fields": schema.get("required_fields", []),
                "optional_fields": schema.get("optional_fields", [])
            }
    except Exception as e:
        return {"error": f"Failed to load schema: {str(e)}"}


@mcp.tool()
def fill_template(template_name: str, field_values: dict[str, Any]) -> str:
    """
    Generate a document from a template by filling in field values.

    Args:
        template_name: Name of the template to use
        field_values: Dictionary of field names and their values

    Returns:
        Rendered document text, or error message if validation fails
    """
    # Load schema to validate fields
    schema = get_template_schema(template_name)

    if "error" in schema:
        return f"ERROR: {schema['error']}"

    # Validate required fields
    required_fields = schema.get("required_fields", [])
    missing_fields = [field for field in required_fields if field not in field_values]

    if missing_fields:
        return f"ERROR: Missing required fields: {', '.join(missing_fields)}\n\nRequired fields: {', '.join(required_fields)}"

    # Load and render template
    try:
        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
        template = env.get_template(f"{template_name}.j2")
        rendered = template.render(**field_values)
        return rendered
    except TemplateNotFound:
        return f"ERROR: Template file not found: {template_name}.j2"
    except Exception as e:
        return f"ERROR: Failed to render template: {str(e)}"


if __name__ == "__main__":
    # Run MCP server
    mcp.run()
