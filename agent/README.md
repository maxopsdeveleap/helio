# Hellio HR Intelligent Agent

Autonomous HR agent that monitors Gmail for candidate applications and job postings, processes them according to best practices, and notifies humans for approval.

## Features

- **Email Monitoring**: Watches Gmail inbox for candidate applications (+candidates) and job postings (+positions)
- **Intelligent Processing**: Validates information, ingests CVs, creates positions, matches candidates
- **Human-in-the-Loop**: Never sends emails automatically - always creates drafts for approval
- **State Management**: Tracks processed emails to avoid duplicates
- **Notifications**: Alerts operators of actions taken with clear next steps

## Setup

### 1. Environment Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your actual values
```

Required variables:
- `ANTHROPIC_API_KEY`: Your Claude API key
- `DB_PASSWORD`: PostgreSQL password for hellio user
- Gmail MCP paths (already configured if you followed Exercise 6 setup)

### 2. Install Dependencies

The agent uses strands-agents which is already in the backend requirements.txt.

```bash
cd /home/develeap/hellio-hr-max/backend
pip install -r requirements.txt
```

### 3. Verify Database Tables

Ensure agent tables are created (done during Exercise 6 setup):
- `agent_processed_emails`
- `agent_notifications`

### 4. Test Gmail MCP Connection

The Gmail MCP server should already be configured at `/home/develeap/mcp-gmail/`.

Test it:
```bash
cd /home/develeap/mcp-gmail
uv run python scripts/test_gmail_setup.py
```

## Usage

### Running the Agent

```bash
cd /home/develeap/hellio-hr-max/agent
python hr_agent.py
```

The agent will:
1. Check Gmail inbox for new emails
2. Process candidate applications sent to `yourname+candidates@develeap.com`
3. Process position announcements sent to `yourname+positions@develeap.com`
4. Create email drafts (never sends automatically)
5. Create notifications for human review

### Testing the Agent

Send test emails to your configured Gmail account:

**Test Candidate Application:**
```
To: max.hellio.project+candidates@gmail.com
Subject: Application for DevOps Engineer
Body: I'm interested in the DevOps Engineer position
Attachment: your_cv.pdf
```

**Test Position Announcement:**
```
To: max.hellio.project+positions@gmail.com
Subject: New Opening - Senior SRE
Body: We have a new Senior SRE position...
[Include job details]
```

### Monitoring Agent Actions

Check notifications created by the agent:

```bash
psql -U hellio -d hellio_hr -c "SELECT * FROM agent_notifications WHERE status='pending' ORDER BY created_at DESC;"
```

Check processed emails:

```bash
psql -U hellio -d hellio_hr -c "SELECT * FROM agent_processed_emails ORDER BY processed_at DESC LIMIT 10;"
```

## Architecture

### Components

1. **hr_agent.py**: Main agent with Strands framework integration
2. **tools.py**: Custom tools for database and backend API interaction
3. **.strands.json**: MCP server configuration for Gmail access

### Agent Workflow

```
Email Received
    ↓
Check if already processed (agent_processed_emails)
    ↓
Extract & Validate information
    ↓
[If candidate] → Ingest CV → Match to positions → Draft response
[If position] → Create position → Search candidates → Draft confirmation
    ↓
Create email drafts in Gmail (NEVER send)
    ↓
Record processed email
    ↓
Create notification for human
    ↓
Human reviews drafts and approves/edits
```

### Tools Available to Agent

**Gmail (via MCP):**
- `search_emails`: Find emails by query
- `get_emails`: Retrieve email content
- `compose_email`: Create draft (never `send_email`)
- `mark_message_read`: Mark as processed

**Database:**
- `check_email_processed`: Avoid duplicates
- `record_processed_email`: Track state
- `create_notification`: Alert humans
- `get_pending_notifications`: View queue

**Backend API:**
- `ingest_candidate_cv`: Process CV attachments
- `create_position`: Add job posting
- `search_candidates_for_position`: Semantic matching
- `search_positions_for_candidate`: Find alternatives
- `get_all_positions`: List openings

**Templates:**
- `get_email_template`: HR workflow templates (A1-A3, B1-B8)

## Customization

### Adjusting Agent Behavior

Edit `hr_agent.py` instructions to modify:
- Max turns (agent loop iterations)
- Processing rules
- Validation criteria
- Notification priorities

### Adding New Email Types

To handle additional email types beyond candidates/positions:
1. Add new email tag routing logic
2. Create workflow in agent instructions
3. Add templates in `tools.py`
4. Update database schema if needed

### Modifying Templates

Email templates are in `tools.py` → `get_email_template()` function.
Based on HR workflow document templates (A1-A3 for hiring managers, B1-B8 for candidates).

## Troubleshooting

### Agent not finding emails

- Check Gmail MCP server is running
- Verify OAuth token is valid (`/home/develeap/mcp-gmail/token.json`)
- Test with `uv run python /home/develeap/mcp-gmail/scripts/test_gmail_setup.py`

### Database connection errors

- Verify Docker containers are running: `docker ps`
- Check DB_PASSWORD in `.env` matches docker-compose.yml
- Test connection: `psql -U hellio -d hellio_hr -h localhost`

### Agent exceeding max turns

- Reduce `max_turns` in `hr_agent.py` create_agent()
- Simplify agent instructions
- Check for infinite loops in workflow logic

### Backend API not reachable

- Ensure backend container is running: `docker compose ps`
- Verify BACKEND_URL in `.env` (default: `http://localhost:8001`)
- Test API: `curl http://localhost:8001/api/positions/`

## Development

### Running in Development Mode

For testing with verbose output:

```python
agent.run(task, verbose=True)
```

### Debugging Agent Decisions

Strands provides built-in tracing. Check agent reasoning in output logs.

### Testing Individual Tools

You can test tools directly:

```python
from tools import check_email_processed, create_notification

# Test checking email status
result = check_email_processed("test-email-id-123")
print(result)

# Test creating notification
notification = create_notification(
    notification_type="test",
    summary="Test notification",
    action_url="http://localhost:3000/candidates/1"
)
print(notification)
```

## Safety & Best Practices

- **Never use send_email**: Agent only creates drafts
- **Always validate**: Don't skip information checks
- **Human approval required**: All outbound emails need review
- **State tracking**: Always record processed emails
- **Error handling**: Agent failures don't corrupt data
- **Audit trail**: All actions logged in database

## Next Steps (Exercise 7)

In Exercise 7, you'll build MCP servers instead of agents to:
- Allow any agent (not just yours) to use Hellio HR
- Enable quick experimentation with Claude Desktop
- Create shareable, reusable tools across teams
