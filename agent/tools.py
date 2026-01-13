"""
Custom tools for Hellio HR Agent to interact with backend and database
"""

import os
import json
import requests
import psycopg2
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from strands import tool
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "hellio_hr"),
    "user": os.getenv("DB_USER", "hellio"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)


# ===== Database State Management Tools =====

@tool
def check_email_processed(email_id: str) -> Dict[str, Any]:
    """
    Check if an email has already been processed.

    Args:
        email_id: Gmail message ID

    Returns:
        Dict with 'processed' bool and 'details' if found
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT email_id, processed_at, email_type, action_taken, metadata "
                "FROM agent_processed_emails WHERE email_id = %s",
                (email_id,)
            )
            row = cur.fetchone()

            if row:
                return {
                    "processed": True,
                    "details": {
                        "email_id": row[0],
                        "processed_at": row[1].isoformat(),
                        "email_type": row[2],
                        "action_taken": row[3],
                        "metadata": row[4],
                    }
                }
            return {"processed": False}
    finally:
        conn.close()


@tool
def record_processed_email(
    email_id: str,
    email_type: str,
    action_taken: str,
    metadata: Dict[str, Any]
) -> Dict[str, str]:
    """
    Record that an email has been processed.

    Args:
        email_id: Gmail message ID
        email_type: 'candidate', 'position', or 'other'
        action_taken: Description of action
        metadata: Additional context (sender, subject, etc.)

    Returns:
        Success status
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_processed_emails
                (email_id, email_type, action_taken, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email_id) DO UPDATE
                SET action_taken = EXCLUDED.action_taken,
                    metadata = EXCLUDED.metadata
                """,
                (email_id, email_type, action_taken, json.dumps(metadata))
            )
            conn.commit()
            return {"status": "success", "email_id": email_id}
    finally:
        conn.close()


def build_notification_actions(
    draft_email_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
    position_id: Optional[str] = None,
    frontend_base_url: str = "http://localhost:3000"
) -> List[Dict[str, Any]]:
    """
    Build action buttons for notifications.

    Args:
        draft_email_id: Gmail draft ID
        candidate_id: Candidate ID
        position_id: Position ID
        frontend_base_url: Base URL for frontend links

    Returns:
        List of action button configurations
    """
    actions = []

    if draft_email_id:
        # View draft in Gmail
        actions.append({
            "label": "View Draft Email",
            "url": f"https://mail.google.com/mail/#drafts?compose={draft_email_id}",
            "type": "gmail_draft",
            "icon": "📧",
            "primary": False
        })

        # Quick send action (would need backend implementation)
        actions.append({
            "label": "Send Email",
            "url": f"{frontend_base_url}/api/send-draft/{draft_email_id}",
            "type": "gmail_send",
            "icon": "✉️",
            "primary": True,
            "confirm": "Are you sure you want to send this email?"
        })

    if candidate_id:
        actions.append({
            "label": "View Candidate Profile",
            "url": f"{frontend_base_url}/candidates/{candidate_id}",
            "type": "frontend_link",
            "icon": "👤",
            "primary": not draft_email_id  # Primary if no draft
        })

    if position_id:
        actions.append({
            "label": "View Position",
            "url": f"{frontend_base_url}/positions/{position_id}",
            "type": "frontend_link",
            "icon": "💼",
            "primary": not draft_email_id  # Primary if no draft
        })

    return actions


@tool
def create_notification(
    notification_type: str,
    summary: str,
    action_url: str,
    related_email_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a notification for human operator.

    Args:
        notification_type: Type of notification
        summary: Human-readable summary
        action_url: Link to take action
        related_email_id: Associated email ID
        metadata: Additional context (draft content, recommendations, etc.)

    Returns:
        Created notification with ID
    """
    # Enhance metadata with action buttons if not already present
    if metadata is None:
        metadata = {}

    # If metadata has draft_email_id, candidate_id, or position_id but no structured action_buttons,
    # automatically build action buttons
    if 'action_buttons' not in metadata:
        draft_id = metadata.get('draft_email_id')
        candidate_id = metadata.get('candidate_id')
        position_id = metadata.get('position_id')

        if draft_id or candidate_id or position_id:
            action_buttons = build_notification_actions(
                draft_email_id=draft_id,
                candidate_id=candidate_id,
                position_id=position_id
            )
            metadata['action_buttons'] = action_buttons

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_notifications
                (type, summary, action_url, related_email_id, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    notification_type,
                    summary,
                    action_url,
                    related_email_id,
                    json.dumps(metadata)
                )
            )
            notification_id = cur.fetchone()[0]
            conn.commit()
            return {
                "status": "success",
                "notification_id": notification_id,
                "summary": summary
            }
    finally:
        conn.close()


def get_pending_notifications() -> List[Dict[str, Any]]:
    """
    Get all pending notifications for the operator.

    Returns:
        List of pending notifications
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, created_at, type, summary, action_url, metadata
                FROM agent_notifications
                WHERE status = 'pending'
                ORDER BY created_at DESC
                """
            )
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "created_at": row[1].isoformat(),
                    "type": row[2],
                    "summary": row[3],
                    "action_url": row[4],
                    "metadata": row[5],
                }
                for row in rows
            ]
    finally:
        conn.close()


# ===== Backend API Tools =====

def ingest_candidate_cv(
    cv_file_path: str,
    candidate_name: str,
    email: str,
    position_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ingest a candidate's CV through the backend API.

    Args:
        cv_file_path: Path to CV file (PDF/DOCX)
        candidate_name: Candidate's full name
        email: Candidate's email
        position_id: Optional position they're applying for

    Returns:
        API response with candidate ID and profile
    """
    with open(cv_file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'name': candidate_name,
            'email': email,
        }
        if position_id:
            data['position_id'] = position_id

        response = requests.post(
            f"{BACKEND_URL}/api/candidates/ingest",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()


def create_position(position_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new position in the system.

    Args:
        position_data: Position details (title, department, requirements, etc.)

    Returns:
        Created position with ID
    """
    response = requests.post(
        f"{BACKEND_URL}/api/positions/",
        json=position_data
    )
    response.raise_for_status()
    return response.json()


def search_candidates_for_position(position_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for candidates matching a position using semantic search.

    Args:
        position_id: Position ID to match against
        limit: Maximum number of candidates to return

    Returns:
        List of matching candidates with scores
    """
    response = requests.get(
        f"{BACKEND_URL}/api/positions/{position_id}/suggest-candidates",
        params={"limit": limit}
    )
    response.raise_for_status()
    return response.json()


def search_positions_for_candidate(candidate_id: int, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Search for positions matching a candidate using semantic search.

    Args:
        candidate_id: Candidate ID to match against
        limit: Maximum number of positions to return

    Returns:
        List of matching positions with scores
    """
    response = requests.get(
        f"{BACKEND_URL}/api/candidates/{candidate_id}/suggest-positions",
        params={"limit": limit}
    )
    response.raise_for_status()
    return response.json()


def get_all_positions() -> List[Dict[str, Any]]:
    """
    Get all open positions.

    Returns:
        List of all positions
    """
    response = requests.get(f"{BACKEND_URL}/api/positions/")
    response.raise_for_status()
    return response.json()


def get_position_by_id(position_id: int) -> Dict[str, Any]:
    """
    Get position details by ID.

    Args:
        position_id: Position ID

    Returns:
        Position details
    """
    response = requests.get(f"{BACKEND_URL}/api/positions/{position_id}")
    response.raise_for_status()
    return response.json()


# ===== Email Template Tools =====

@tool
def get_email_template(template_code: str) -> str:
    """
    Get an email template by code (A1, A2, A3, B1-B8).

    Args:
        template_code: Template identifier (e.g., 'B4', 'A2')

    Returns:
        Template text with placeholders
    """
    # Templates from the HR workflow document
    templates = {
        "A1": """Subject: Additional Information Needed - {job_title} Position

Dear {hiring_manager_name},

Thank you for submitting the {job_title} position. I'm excited to help you find the right candidate for your team.

To ensure we attract the best-qualified applicants and conduct effective searches, I need a few additional details:

{missing_items}

Could you provide this information by {deadline}? This will allow me to begin sourcing candidates immediately and create an effective job posting.

I'm here to support you through this process. Feel free to call me if you'd like to discuss these details.

Best regards,
Hellio HR Agent""",

        "A2": """Subject: Confirmation - {job_title} Position Ready for Sourcing

Dear {hiring_manager_name},

Thank you for providing all the details for the {job_title} position. I've confirmed the following information:

**Position Summary:**
{position_summary}

**Next Steps:**
1. I will enter this position into our system today
2. I'll draft a social media posting for your approval (see separate email)
3. I'll search our current candidate pool and share any immediate matches
4. Active sourcing will begin this week, with weekly updates on candidates

Please confirm this information is accurate, or let me know if any adjustments are needed.

Looking forward to finding great candidates for your team!

Best regards,
Hellio HR Agent""",

        "A3": """Subject: {job_title} Position Active - {match_count} Potential Candidates Identified

Dear {hiring_manager_name},

Great news! The {job_title} position is now active in our system and we're ready to begin sourcing.

**Social Media Posting - Please Review:**

{social_media_post}

Please review and approve this posting, or let me know if you'd like any changes.

**Current Candidate Pool Results:**

{candidate_results}

**Timeline:**
- I will provide weekly updates on new candidates
- Strong candidates will be shared as soon as they're identified

Let me know if you have any questions or would like to discuss the search strategy.

Best regards,
Hellio HR Agent""",

        "B1": """Subject: CV Needed - {position_title} Application

Dear {candidate_name},

Thank you for your interest in the {position_title} role!

I'd love to review your application, but I noticed your CV/resume wasn't attached to your email. Could you please reply to this message with your CV attached as a PDF or Word document?

Once I have your CV, I'll review your qualifications and get back to you within 3-5 business days with next steps.

Looking forward to learning more about your background!

Best regards,
Hellio HR Agent""",

        "B2": """Subject: Clarification Needed - Your Application

Dear {candidate_name},

Thank you for reaching out! {positive_note}

To best evaluate how we can help, could you let me know which of our current open positions you're most interested in?

**Current Openings:**
{current_openings}

Alternatively, if you're open to exploring opportunities more broadly, please let me know what type of role you're seeking and I'll identify the best fit.

I look forward to hearing from you!

Best regards,
Hellio HR Agent""",

        "B3": """Subject: Contact Information Needed - {position_title} Application

Dear {candidate_name},

Thank you for applying to the {position_title} position! I'm reviewing your CV and would like to discuss next steps.

To move forward, could you please provide:
- Your phone number (for scheduling calls/interviews)
- Your LinkedIn profile (if available)
- Your current location and availability to start

You can reply directly to this email with these details.

Looking forward to connecting!

Best regards,
Hellio HR Agent""",

        "B4": """Subject: Your Application for {position_title} - Next Steps

Dear {candidate_name},

Thank you for applying for the {position_title} position! I've reviewed your CV and I'm impressed by your {standout_quality}.

Your background aligns well with what we're looking for. Here's what happens next:

**Our Hiring Process:**
1. **Initial Review** (Current stage) - We're reviewing your profile with the hiring manager
2. **Phone Screen** (If selected) - 30-minute conversation about your experience and the role
3. **Technical Interview** (If selected) - Deeper dive into technical skills
4. **Final Interview** (If selected) - Meet the team and discuss fit

**Timeline:**
You can expect to hear from us within 3-5 business days about next steps.

In the meantime, if you have any questions about the role or our company, feel free to reach out!

Best regards,
Hellio HR Agent""",

        "B5": """Subject: Your Application for {position_title} - Under Review

Dear {candidate_name},

Thank you for applying for the {position_title} position! I've reviewed your CV and appreciate your background in {relevant_area}.

Your profile shows promise, particularly your {positive_aspect}. We're currently reviewing all applications and will be in touch within 5-7 business days to discuss next steps.

In the meantime, please feel free to reach out if you have any questions about the role or our hiring process.

Best regards,
Hellio HR Agent""",

        "B6": """Subject: Alternative Opportunities - {original_position_title}

Dear {candidate_name},

Thank you for your application for the {position_title} position! I've carefully reviewed your CV and your background in {their_strength}.

For this specific role, we're looking for {missing_requirement}. However, I noticed your strong background in {their_strength} would be an excellent fit for these other positions we're currently filling:

**Potentially Better Fits:**
{alternative_positions}

Would you be interested in being considered for either of these roles instead? If so, just reply to this email and I'll process your application accordingly.

We appreciate your interest and hope to find the right match for your skills!

Best regards,
Hellio HR Agent""",

        "B7": """Subject: Thank You for Your Application - {position_title}

Dear {candidate_name},

Thank you for your interest in the {position_title} position. I've reviewed your CV and appreciate you taking the time to apply.

After careful consideration, we've decided to move forward with candidates whose backgrounds more closely align with the specific requirements for this role, particularly {key_gap}.

However, we're always growing and adding new positions. I encourage you to:
- Check our careers page regularly for new opportunities
- Connect with us on LinkedIn to stay updated

We'll keep your CV on file for 6 months, and if a position opens that matches your background, we'll reach out.

Thank you again for your interest, and I wish you the best in your job search!

Best regards,
Hellio HR Agent""",

        "B8": """Subject: Strong Candidate for {position_title} - {candidate_name}

Dear {hiring_manager_name},

I wanted to share an exciting candidate who just applied for the {position_title} position:

**Candidate**: {candidate_name}

**Background Highlights:**
{background_highlights}

**Why They're a Strong Match:**
{match_reasoning}

**Profile Link**: {profile_link}

**Recommended Next Steps:**
I suggest scheduling a phone screen within the next week while this candidate is actively interviewing.

Would you like me to coordinate a phone screen, or would you prefer to review their full profile first?

Let me know how you'd like to proceed!

Best regards,
Hellio HR Agent""",
    }

    return templates.get(template_code, "Template not found")


# ===== Gmail Attachment Tools =====

def get_gmail_service():
    """Create Gmail API service using existing OAuth token."""
    token_path = Path("/home/develeap/mcp-gmail/token.json")

    if not token_path.exists():
        raise FileNotFoundError(f"Gmail OAuth token not found at {token_path}")

    creds = Credentials.from_authorized_user_file(str(token_path))

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build('gmail', 'v1', credentials=creds)


@tool
def download_gmail_attachment(
    message_id: str,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download email attachments from Gmail.

    Args:
        message_id: Gmail message ID
        filename: Optional desired filename (uses original if not provided)

    Returns:
        Dict with file_path and status
    """
    try:
        service = get_gmail_service()

        # Get message to find attachments
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        # Find attachments in message parts
        attachments = []
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part.get('filename') and part['body'].get('attachmentId'):
                    attachments.append({
                        'filename': part['filename'],
                        'attachment_id': part['body']['attachmentId'],
                        'mime_type': part['mimeType']
                    })

        if not attachments:
            return {
                "status": "error",
                "error": "No attachments found in email",
                "message_id": message_id
            }

        # Download first attachment (usually the CV)
        att = attachments[0]
        attachment = service.users().messages().attachments().get(
            userId='me',
            messageId=message_id,
            id=att['attachment_id']
        ).execute()

        # Decode base64 data
        file_data = base64.urlsafe_b64decode(attachment['data'])

        # Use provided filename or original
        save_filename = filename or att['filename']
        save_path = Path("/tmp") / save_filename
        save_path.write_bytes(file_data)

        return {
            "status": "success",
            "file_path": str(save_path),
            "size_bytes": len(file_data),
            "filename": save_filename,
            "original_filename": att['filename'],
            "mime_type": att['mime_type']
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message_id": message_id
        }


@tool
def ingest_candidate_from_gmail(
    cv_file_path: str,
    candidate_name: str,
    email: str,
    position_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ingest a candidate's CV through the backend API (reuses Exercise 3 logic).

    Args:
        cv_file_path: Path to downloaded CV file
        candidate_name: Candidate's full name
        email: Candidate's email
        position_id: Optional position they're applying for

    Returns:
        Backend API response with candidate ID and profile
    """
    try:
        with open(cv_file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'name': candidate_name,
                'email': email,
            }
            if position_id:
                data['position_id'] = position_id

            response = requests.post(
                f"{BACKEND_URL}/api/candidates/ingest",
                files=files,
                data=data
            )
            response.raise_for_status()
            return {
                "status": "success",
                **response.json()
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "cv_file_path": cv_file_path
        }


@tool
def ingest_position_from_email(
    title: str,
    description: str,
    company: str = "Hellio",
    hiring_manager_email: str = None
) -> Dict[str, Any]:
    """
    Create a job position from email content. The backend will use LLM to parse the details.

    Args:
        title: Position title (from email subject)
        description: Full position description (from email body)
        company: Company name (default: Hellio)
        hiring_manager_email: Email of hiring manager who sent the request

    Returns:
        Backend API response with position ID, position details, and matching candidates
    """
    try:
        data = {
            'title': title,
            'description': description,
            'company': company
        }
        if hiring_manager_email:
            data['hiring_manager_email'] = hiring_manager_email

        response = requests.post(
            f"{BACKEND_URL}/api/positions/ingest",
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            return {
                "status": "success",
                **response.json()
            }
        else:
            return {
                "status": "error",
                "error": f"Backend returned {response.status_code}: {response.text}"
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
