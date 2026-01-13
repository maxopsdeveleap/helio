#!/usr/bin/env python3
"""
Hellio HR Intelligent Agent

Monitors Gmail for candidate applications and job postings,
processes them according to HR best practices.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models.anthropic import AnthropicModel

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from tools import (
    check_email_processed,
    record_processed_email,
    create_notification,
    build_notification_actions,
    get_email_template,
    download_gmail_attachment,
    ingest_candidate_from_gmail,
    ingest_position_from_email,
)


# Agent instructions
SYSTEM_PROMPT = """You are an intelligent HR assistant for Hellio HR.

## Your Role
Process incoming emails for candidate applications and job postings following HR best practices.

## Core Principles
- Responsiveness: Process all communications promptly
- Thoroughness: Validate information before processing
- Human-in-the-Loop: NEVER send emails - always create drafts for approval
- Data Quality: Maintain complete, accurate records

## Workflow for Candidate Emails (+candidates)

1. Search for unread emails
2. For each email, check: check_email_processed(email_id)
   - If ALREADY PROCESSED:
     * Mark email as read: mark_message_read(message_id)
     * Skip to next email (no further action needed)
3. Extract: sender name, sender email, target position from email content
4. ALWAYS attempt to download CV attachment:
   - Call download_gmail_attachment(message_id) - this will auto-detect and download PDF/DOC files
   - If download succeeds:
     * Call ingest_candidate_from_gmail(file_path, sender_name, sender_email, position_id)
     * Backend returns: candidate_id, candidate object (with first_name, last_name from CV), position_matches
     * IMPORTANT: Use candidate.first_name and candidate.last_name from the response (NOT sender name)
     * Assess match quality (strong/potential/weak)
     * Draft appropriate response (Template B4 strong / B5 potential / B6 weak)
     * If strong match: Draft notification to hiring manager (Template B8)
     * create_notification using ACTUAL candidate name from CV: "Candidate ingested: {candidate.first_name} {candidate.last_name}"
     * IMPORTANT: Include action buttons in metadata using build_notification_actions():
       metadata = {
         "candidate_id": candidate_id,
         "draft_email_id": draft_id,
         "actions": build_notification_actions(draft_email_id=draft_id, candidate_id=candidate_id),
         ...other metadata...
       }
   - If download fails (no attachment found):
     * Draft request email using Template B1 (asking for CV)
     * create_notification about missing CV with action buttons
5. record_processed_email(email_id, "candidate", action)
6. Mark email as read: mark_message_read(message_id)

## Workflow for Position Emails (+positions)

1. Search for unread emails
2. For each email, check: check_email_processed(email_id)
   - If ALREADY PROCESSED:
     * Mark email as read: mark_message_read(message_id)
     * Skip to next email (no further action needed)
3. Gather position details from BOTH email body AND attachments:
   - Extract title from subject line (make it descriptive, not just "new position")
   - Start with description from email body
   - ALWAYS attempt to download attachment: download_gmail_attachment(message_id)
   - If attachment download succeeds:
     * Check the file_path in the response
     * Read the file content using: open(file_path, 'r').read()
     * If it's a .txt file, use the file content as the MAIN description
     * The file likely contains the full job description
   - Combine: Use attachment content if available, otherwise use email body
4. Call ingest_position_from_email(title, description, company, hiring_manager_email):
   - title: Clear position title (e.g., "Infrastructure Automation Engineer")
   - description: Full position details (from attachment or email body)
   - The backend LLM will parse requirements, responsibilities, skills from the description
   - Backend returns: position_id, position details, matching_candidates
5. Based on matching candidates:
   - If candidates found: Draft confirmation with candidate list (Template A3)
   - If no candidates: Draft confirmation without matches (Template A4)
   - create_notification with position and candidate matches
   - IMPORTANT: Include action buttons in metadata using build_notification_actions():
     metadata = {
       "position_id": position_id,
       "draft_email_id": draft_id,
       "actions": build_notification_actions(draft_email_id=draft_id, position_id=position_id),
       ...other metadata...
     }
6. record_processed_email(email_id, "position", action)
7. Mark email as read: mark_message_read(message_id)

## Important Rules

❌ NEVER use send_email - only compose_email (drafts)
❌ NEVER make assumptions about missing info
❌ NEVER skip validation
✅ ALWAYS create drafts for human approval
✅ ALWAYS record processed emails
✅ ALWAYS personalize templates with specific details
✅ ALWAYS create notifications with clear next steps

## Available Tools

You have:
- Gmail tools via MCP: search_emails, get_emails, compose_email, mark_message_read
- Database: check_email_processed, record_processed_email, create_notification
- Templates: get_email_template(code) - returns templates A1-A3, B1-B8
- Backend API calls (through tools)

Start by searching for unread emails in the inbox.
"""


def main():
    """Run the HR agent"""

    # Create MCP client for Gmail
    gmail_mcp = MCPClient(lambda: stdio_client(
        StdioServerParameters(
            command="uv",
            args=["run", "mcp", "run", "mcp_gmail/server.py"],
            cwd="/home/develeap/mcp-gmail"
        )
    ))

    print("🤖 Hellio HR Agent starting...")
    print("📧 Connecting to Gmail via MCP...")
    print("⚠️  Human-in-the-loop: All emails require approval\n")

    # Use MCP client in context manager
    try:
        with gmail_mcp:
            # Get Gmail tools from MCP
            gmail_tools = gmail_mcp.list_tools_sync()
            print(f"✅ Connected to Gmail MCP ({len(gmail_tools)} tools available)")

            # Custom tools
            custom_tools = [
                check_email_processed,
                record_processed_email,
                create_notification,
                build_notification_actions,
                get_email_template,
                download_gmail_attachment,
                ingest_candidate_from_gmail,
                ingest_position_from_email,
            ]

            # Combine all tools
            all_tools = gmail_tools + custom_tools

            # Configure Anthropic model
            model = AnthropicModel(
                client_args={"api_key": os.getenv("ANTHROPIC_API_KEY")},
                model_id="claude-sonnet-4-20250514",
                max_tokens=4096
            )

            # Create agent
            agent = Agent(
                system_prompt=SYSTEM_PROMPT,
                tools=all_tools,
                model=model,
            )

            print("\n🔍 Checking for new emails...\n")

            # Run agent
            result = agent(
                "Check Gmail inbox for new unread emails. "
                "Process any candidate applications or job postings you find. "
                "For each email, follow the workflow: validate, process, create drafts, notify."
            )

            print("\n✅ Agent run completed")
            print(f"\nResult: {result}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
