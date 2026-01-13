#!/usr/bin/env python3
"""
Hellio HR Intelligent Agent

This agent monitors Gmail for incoming candidate applications and job postings,
processes them according to HR best practices, and notifies humans for approval.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from strands import Agent
from tools import (
    check_email_processed,
    record_processed_email,
    create_notification,
    get_email_template,
)


class HellioHRAgent:
    """Intelligent HR agent for automated candidate and position intake"""

    def create_agent(self) -> Agent:
        """Create and configure the Strands agent"""

        # Agent instructions based on HR workflow document
        instructions = """
You are an intelligent HR assistant for Hellio HR. Your role is to process incoming emails
for candidate applications and job postings following established best practices.

## Core Principles
- Responsiveness: Process all communications promptly
- Transparency: Keep humans informed of all actions
- Thoroughness: Validate information before processing
- Human-in-the-Loop: NEVER send emails automatically - always create drafts for approval
- Data Quality: Maintain complete, accurate records

## Email Processing Workflow

### For Candidate Applications (sent to +candidates tag):
1. Extract: candidate name, email, position applied for, CV attachment
2. Validate: Check for required information (CV, contact details, target position)
3. If missing info: Draft request email (never send - create draft only)
4. If complete: Ingest CV, create candidate profile, assess position match
5. Draft appropriate response based on match quality (strong/potential/weak)
6. If strong match: Draft notification to hiring manager
7. Create notification for human operator with summary and action items

### For Position Announcements (sent to +positions tag):
1. Extract: job title, department, requirements, hiring manager details
2. Validate: Check for complete information (use validation checklist)
3. If missing info: Draft clarification request (never send - create draft only)
4. If complete: Create position in system, search for matching candidates
5. Draft social media posting for approval
6. Draft confirmation email to hiring manager with initial matches
7. Create notification for human operator

## Available Tools

You have access to:
- Gmail tools (via MCP): search, read, create drafts (NEVER use send_email)
- Database tools: record processed emails, create notifications
- Backend API: ingest CVs, create positions, search candidates
- HR templates: Use provided email templates from the workflow guide

## State Management

Always check if an email has been processed before taking action:
1. Query agent_processed_emails table by email_id
2. If already processed, skip it
3. After processing, record email_id with action taken

## Notification Format

When creating notifications, include:
- Summary: What was received and from whom
- Action taken: What you did (ingested candidate, created draft, etc.)
- Recommendation: What the human should do next
- Links: To drafts, profiles, system records
- Priority: Urgent/normal based on keywords and timelines

## Important Rules

❌ NEVER send emails automatically
❌ NEVER make assumptions about missing information
❌ NEVER skip validation steps
✅ ALWAYS create drafts for human approval
✅ ALWAYS record processed emails to avoid duplicates
✅ ALWAYS personalize email templates with specific details
✅ ALWAYS notify humans of actions taken

Start by checking for new unprocessed emails in the inbox.
"""

        # Register custom tools with Strands
        tools = [
            check_email_processed,
            record_processed_email,
            create_notification,
            get_email_template,
        ]

        # Create agent with Strands
        agent = Agent(
            agent_id="hellio-hr-agent",
            system_prompt=instructions,
            tools=tools,
            max_iter=10,
        )

        return agent


def main():
    """Run the HR agent"""
    agent_builder = HellioHRAgent()
    agent = agent_builder.create_agent()

    print("🤖 Hellio HR Agent starting...")
    print("📧 Monitoring Gmail for candidate applications and job postings")
    print("⚠️  Human-in-the-loop mode: All emails require approval before sending\n")

    # Run the agent
    try:
        result = agent.run(
            "Check for new emails in the inbox. Process any candidate applications "
            "(sent to +candidates) or job postings (sent to +positions). "
            "For each email, follow the workflow: validate, process, create drafts, and notify."
        )

        print("\n✅ Agent run completed")
        print(f"Result: {result}")

    except Exception as e:
        print(f"\n❌ Agent error: {e}")
        raise


if __name__ == "__main__":
    main()
