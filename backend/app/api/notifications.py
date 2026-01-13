from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.models import get_db

router = APIRouter()

@router.get("/")
async def get_notifications(db: Session = Depends(get_db)):
    """Get all notifications, ordered by newest first"""
    query = text("""
        SELECT
            id,
            type,
            summary,
            action_url,
            is_read,
            related_email_id,
            metadata,
            created_at
        FROM agent_notifications
        ORDER BY created_at DESC
    """)

    result = db.execute(query)
    notifications = []

    for row in result:
        notifications.append({
            "id": row[0],
            "type": row[1],
            "summary": row[2],
            "action_url": row[3],
            "is_read": row[4],
            "related_email_id": row[5],
            "metadata": row[6],
            "created_at": row[7].isoformat() if row[7] else None
        })

    return notifications

@router.get("/unread/count")
async def get_unread_count(db: Session = Depends(get_db)):
    """Get count of unread notifications"""
    query = text("""
        SELECT COUNT(*)
        FROM agent_notifications
        WHERE is_read = false
    """)

    result = db.execute(query)
    count = result.scalar()

    return {"unread_count": count}

@router.patch("/{notification_id}/read")
async def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark a notification as read"""
    query = text("""
        UPDATE agent_notifications
        SET is_read = true
        WHERE id = :notification_id
        RETURNING id
    """)

    result = db.execute(query, {"notification_id": notification_id})
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"status": "success"}

@router.patch("/read-all")
async def mark_all_read(db: Session = Depends(get_db)):
    """Mark all notifications as read"""
    query = text("""
        UPDATE agent_notifications
        SET is_read = true
        WHERE is_read = false
    """)

    result = db.execute(query)
    db.commit()

    return {"status": "success", "updated": result.rowcount}
