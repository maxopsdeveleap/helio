FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY server.py ./
COPY templates/ ./templates/
COPY schemas/ ./schemas/

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Expose port for HTTP transport
EXPOSE 8002

# Run MCP server with HTTP transport
CMD ["fastmcp", "run", "server.py:mcp", "--transport", "sse", "--port", "8002", "--host", "0.0.0.0"]
