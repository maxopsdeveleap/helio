# Hellio HR - Claude Code Work Rules

## Project Context
Hellio HR is an intelligent hiring operations assistant built as part of Develeap's Agenteer Boot Camp. The system helps manage candidates and job positions using a FastAPI backend, PostgreSQL database, and modern frontend with SQL-RAG chat capabilities.

## Tech Stack
- **Backend**: FastAPI (Python 3.12), SQLAlchemy, PostgreSQL
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **AI**: Claude API (Anthropic) for SQL-RAG chat, match explanations, and LLM extraction
- **Embeddings**: Voyage AI (voyage-2 model, 1024 dimensions)
- **Infrastructure**: Docker Compose
- **Database**: PostgreSQL with pgvector extension for vector similarity search
- **Agent Framework**: Strands Agents SDK (v1.21.0) for autonomous workflows
- **MCP Servers**:
  - Gmail MCP server for email integration (stdio transport)
  - HR Templates MCP server for document generation (SSE transport, port 8002)
- **Template Engine**: Jinja2 for HR document templates
- **MCP Framework**: FastMCP for simplified MCP server development

## Code Style & Standards

### JavaScript
- Use modern ES6+ syntax (const/let, arrow functions, template literals)
- Use async/await for asynchronous operations
- Prefer functional programming patterns where appropriate
- Add comments only for complex logic, not obvious code
- Use descriptive variable names (no single letters except loop counters)

### Python
- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Use FastAPI best practices (dependency injection, Pydantic models)
- Organize code: routers, services, models, api
- Add docstrings for public functions/classes

### File Organization
```
hellio-hr-max/
├── .claude/              # Claude Code configuration
├── agent/
│   ├── .strands.json    # MCP server configuration (Gmail, HR Templates)
│   ├── hr_agent_v2.py   # Main Strands agent with MCP integration
│   └── tools.py         # Custom tools (DB, backend API)
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints (candidates, positions, notifications)
│   │   ├── routers/      # Additional routers (chat)
│   │   ├── models/       # SQLAlchemy models
│   │   └── services/     # Business logic (LLM, SQL-RAG, embeddings, similarity, matching)
│   ├── migrations/       # Database migrations (pgvector)
│   └── scripts/          # Utility scripts (ingest_cv, backfill_embeddings)
├── data/
│   └── candidates/       # PDF CVs for ingestion
├── docs/                 # Documentation
├── mcp-server/           # HR Templates MCP Server (Exercise 7)
│   ├── templates/        # Jinja2 templates (offer_letter, rejection_email, etc.)
│   ├── schemas/          # YAML schemas defining template fields
│   ├── server.py         # FastMCP server implementation
│   ├── Dockerfile        # Container for MCP server
│   └── pyproject.toml    # Dependencies (fastmcp, jinja2, pyyaml)
├── public/               # Frontend
│   ├── css/             # Styles
│   └── js/              # JavaScript (notifications.js for agent alerts)
└── docker-compose.yml    # Container orchestration (backend, postgres, mcp-server)
```

## Git Commit Guidelines
- Use present tense ("Add feature" not "Added feature")
- First line: concise summary (50 chars max)
- Body: bullet points for multiple changes
- **No Claude Code attribution or emojis** (as per user preference)
- Example:
  ```
  feat: implement SQL-RAG chat with Claude API

  - Add schema inspector for DB context
  - Implement SQL validator for security
  - Create 4-step RAG pipeline
  - Add modal chat UI
  ```

## Development Workflow

### Before Making Changes
1. Read existing code to understand patterns
2. Check for similar implementations in codebase
3. Ask user for clarification if requirements are ambiguous

### When Writing Code
- Prefer editing existing files over creating new ones
- Keep solutions simple - avoid over-engineering
- Don't add features not explicitly requested
- Test changes after implementation

### Error Handling
- Always wrap fetch calls in try-catch
- Show user-friendly error messages
- Log errors to console for debugging
- Fail gracefully - don't break the whole app

## Tool Usage Preferences

### File Operations
- Use Read before Edit or Write
- Use Glob for finding files by pattern
- Use Grep for searching file contents
- Avoid bash cat/grep when dedicated tools exist

### Testing
- Backend: Run in Docker via `docker compose up`
- Frontend: Access via http://localhost:8000/public/index.html
- Check browser console for errors
- Test API via http://localhost:8001/docs

## Project-Specific Rules

### CV Ingestion (Exercise 3)
- Uses multimodal LLM to extract structured data from PDFs
- Validates required fields before database insertion
- Stores in PostgreSQL with proper relationships

### SQL-RAG Chat (Exercise 4)
- 4-step pipeline: classify → generate SQL → execute → generate answer
- Defense-in-depth security: prompts guide, validator enforces
- Grounding: LLM answers strictly from query results
- Modal-based UI for seamless UX

### Semantic Search (Exercise 5)
- Vector embeddings using Voyage AI (1024 dimensions)
- pgvector extension for similarity search using cosine distance
- Hybrid filtering: semantic similarity + experience level matching
- Claude Haiku generates human-readable match explanations
- Browser SessionStorage caching for instant repeat loads
- Bidirectional: positions suggest candidates, candidates suggest positions

### Security
- SQL injection prevention: SELECT-only, no semicolons, forbidden keywords
- XSS prevention: HTML escaping on frontend
- Read-only database user for chat queries (recommended)

### Performance
- Lazy load large datasets
- Minimize API calls
- Cache data when appropriate
- Use LIMIT in SQL queries

## Bootcamp Progress

### ✅ Completed Exercises
- **Exercise 1** (Days 1-2): Candidate Management UI
- **Exercise 2** (Days 3-4): FastAPI Backend
- **Exercise 3** (Days 5-6): CV Ingestion with Claude
- **Exercise 4** (Days 7-8): SQL-RAG Chat
- **Exercise 5**: Semantic Candidate Search with Vector Embeddings
- **Exercise 6**: Intelligent HR Agent with Strands
- **Exercise 7**: MCP Server for HR Document Templates

### 🚧 Current Status
All exercises through 7 complete. System fully functional with:
- Candidate/Position management
- CV ingestion from PDFs
- Natural language SQL chat
- Semantic search with AI-powered matching
- Vector embeddings and hybrid filtering
- Modal-based UI
- Autonomous HR agent with Gmail integration
- Human-in-the-loop notification system
- MCP server for professional HR document generation

### 📋 Next Up
- **Exercise 8**: Migration to AWS AgentCore (production deployment)

### HR Agent (Exercise 6)
- **Agent Framework**: Strands Agents SDK for autonomous workflows
- **Email Integration**: Gmail MCP server for monitoring inbox
- **Processing**:
  - Candidate applications (sent to `email+candidates@develeap.com`)
  - Position announcements (sent to `email+positions@develeap.com`)
  - Automatic CV download and ingestion
  - Draft email generation following HR best practices
- **Human-in-the-Loop**: Agent creates drafts, never auto-sends
- **Notification System**:
  - UI notifications panel with real-time updates
  - Action buttons for quick access (Review Draft, View Candidate, View Position)
  - Metadata-driven button generation
  - 10-second polling for new notifications
- **State Management**:
  - `agent_processed_emails` table tracks processed emails
  - `agent_notifications` table stores pending actions
  - Avoids reprocessing duplicate emails
- **File Storage**: CVs stored in `/tmp/` (temporary, works for dev/testing)

### MCP Server for HR Templates (Exercise 7)
- **Framework**: FastMCP (simplified MCP server development)
- **Transport**: SSE (Server-Sent Events) on port 8002
- **Purpose**: Provides reusable HR document templates to any MCP-compatible agent
- **Templates** (Jinja2 with variable substitution):
  - `offer_letter.j2` - Job offer with salary, benefits, start date
  - `rejection_email.j2` - Candidate rejection with optional feedback
  - `interview_invitation.j2` - Interview scheduling details
  - `nda.j2` - Non-disclosure agreement for candidates
  - `position_confirmation.j2` - Confirmation to hiring manager when position received
- **MCP Tools**:
  - `list_templates()` - Returns all available templates with descriptions
  - `get_template_schema(template_name)` - Returns required/optional fields for a template
  - `fill_template(template_name, field_values)` - Generates filled document from template
- **Schema Files**: YAML files define required/optional fields for each template
- **Integration**: Agent connects via `.strands.json` configuration, loads tools at startup
- **Dockerized**: Runs as separate container in docker-compose
- **Benefits**:
  - Agent uses professional, standardized templates instead of hardcoded text
  - Templates can be updated without changing agent code
  - Demonstrates MCP server creation and integration
  - Educational: shows when to use MCP vs direct function calls

## Known Issues & Future Improvements

### 🚨 Critical Issues
1. **Backend API Credits Exhausted**
   - **Issue**: `ingest_position_from_email` endpoint failing with "credit balance too low"
   - **Cause**: Backend uses Anthropic API to parse unstructured position emails into structured data
   - **Impact**: Agent cannot automatically create positions from emails (falls back to manual draft)
   - **Fix**: Add credits to Anthropic account or update `ANTHROPIC_API_KEY` environment variable
   - **File**: `backend/app/services/llm_service.py` (line 19: `parse_position_details()`)

2. **Port 8000 Conflict**
   - **Issue**: Python HTTP server blocking port 8000 (PID 86830)
   - **Impact**: Backend runs on port 8001 instead of 8000
   - **Fix**: Kill process `kill 86830` or use port 8001 consistently
   - **Status**: Working around it (backend on 8001, BACKEND_URL correctly set)

### High Priority
3. **Proper CV Storage**
   - Create dedicated storage directory: `/home/develeap/hellio-hr-max/storage/cvs/`
   - Organize by date or candidate ID (e.g., `2026-01/candidate_001.pdf`)
   - Set proper file permissions (read-only for web server)
   - Add CV preview links in notifications
   - Consider S3/cloud storage for production

4. **Fix Duplicate Position Issue**
   - Delete duplicate Junior SRE position (position_005)
   - Agent should check for existing positions before creating

### Medium Priority
4. **Add position_processed Icon**
   - Update `getNotificationIcon()` in notifications.js to include `position_processed` type

5. **Enhanced Notification Actions**
   - Add "View CV" button to candidate notifications (requires CV storage fix)
   - Add "Download CV" option
   - Add timestamp for when notification was created

6. **Email Account Handling**
   - Gmail draft links open in currently logged-in account
   - Consider OAuth flow for consistent account switching
   - Or fetch draft content via API and display in-app

### Low Priority
7. **Notification Improvements**
   - Mark notifications as read when action is taken
   - Add "Dismiss" button for non-actionable notifications
   - Add notification filtering (by type, date, read/unread)
   - Add notification search

8. **Agent Enhancements**
   - Add urgency detection for time-sensitive emails
   - Implement email threading to track conversation history
   - Add manual override UI for approving/rejecting agent actions
   - Create agent dashboard showing processed emails, success rate

9. **Performance**
   - Reduce notification polling from 10s to 30s or use WebSockets
   - Cache notification list to avoid redundant API calls
   - Add pagination for notification history

## User Preferences
- User: Max (Junior DevOps at Develeap)
- Prefers concise commit messages without attribution
- Wants to verify each step
- Learning to use AI tools effectively
- F5 doesn't work (brightness control) - use Ctrl+R to refresh browser

## API Endpoints

### Candidates
- `GET /api/candidates/` - List all candidates
- `GET /api/candidates/{id}` - Get candidate details
- `PUT /api/candidates/{id}` - Update candidate
- `POST /api/candidates/ingest` - Ingest CV from PDF
- `GET /api/candidates/{id}/suggest-positions` - Get top 3 similar positions with AI explanations

### Positions
- `GET /api/positions/` - List all positions
- `GET /api/positions/{id}` - Get position details
- `PUT /api/positions/{id}` - Update position
- `GET /api/positions/{id}/suggest-candidates` - Get top 3 similar candidates using semantic search

### Chat
- `POST /api/chat/ask` - Ask natural language question
- `GET /api/chat/examples` - Get example questions

### Notifications
- `GET /api/notifications/` - List all notifications (newest first)
- `GET /api/notifications/unread/count` - Get count of unread notifications
- `PATCH /api/notifications/{id}/read` - Mark notification as read
- `PATCH /api/notifications/read-all` - Mark all notifications as read

## Environment Variables
```bash
# .env file (docker-compose.yml pulls from these)
DATABASE_URL=postgresql://user:password@db:5432/helliodb
ANTHROPIC_API_KEY=sk-ant-...  # Used by backend for LLM parsing (currently out of credits!)
VOYAGE_API_KEY=pa-...         # For vector embeddings
```

## Ports & Services
- **Frontend**: http://localhost:8000/public/index.html (served by Python HTTP server on 8000)
- **Backend API**: http://localhost:8001 (FastAPI, container port 8000 mapped to host 8001)
- **Backend Docs**: http://localhost:8001/docs (Swagger UI)
- **MCP Server**: http://localhost:8002/sse (HR Templates MCP, SSE transport)
- **PostgreSQL**: localhost:5432 (exposed for local connections)
- **Agent**: Runs via `uv run agent/hr_agent_v2.py` (not containerized yet)

## Database Schema
See `docs/database_schema.md` for complete schema documentation.
