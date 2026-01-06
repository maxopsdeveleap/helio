from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models import get_db
from app.models.position import Position, PositionRequirement, PositionResponsibility, PositionSkill
from app.schemas.position import PositionResponse, PositionCreate, PositionUpdate

router = APIRouter()

def format_position_response(position: Position) -> dict:
    """Convert database position to JSON format matching Exercise 1"""
    # Separate required and nice-to-have requirements
    requirements = []
    nice_to_have = []
    for req in sorted(position.requirements, key=lambda x: x.order_index):
        if req.is_required:
            requirements.append(req.requirement)
        else:
            nice_to_have.append(req.requirement)

    return {
        "id": position.id,
        "status": position.status,
        "title": position.title,
        "company": position.company,
        "location": position.location,
        "work_arrangement": position.work_arrangement,
        "experience": position.experience,
        "description": position.description,
        "compensation": position.compensation,
        "timeline": position.timeline,
        "urgency": position.urgency,
        "contact_person": {
            "name": position.contact_person_name,
            "title": position.contact_person_title,
            "email": position.contact_person_email
        },
        "notes": position.notes,
        "requirements": requirements,
        "nice_to_have": nice_to_have,
        "responsibilities": [
            resp.responsibility
            for resp in sorted(position.responsibilities, key=lambda x: x.order_index)
        ],
        "skills": [skill.skill_name for skill in position.skills],
        "created_at": position.created_at,
        "updated_at": position.updated_at
    }

@router.get("/", response_model=List[dict])
async def get_all_positions(db: Session = Depends(get_db)):
    """Get all positions"""
    positions = db.query(Position).all()
    return [format_position_response(position) for position in positions]

@router.get("/{position_id}", response_model=dict)
async def get_position(position_id: str, db: Session = Depends(get_db)):
    """Get a single position by ID"""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return format_position_response(position)

@router.post("/", response_model=dict, status_code=201)
async def create_position(position_data: PositionCreate, db: Session = Depends(get_db)):
    """Create a new position"""
    # Check if position already exists
    existing = db.query(Position).filter(Position.id == position_data.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Position with this ID already exists")

    # Create position
    position = Position(**position_data.dict())
    db.add(position)
    db.commit()
    db.refresh(position)

    return format_position_response(position)

@router.put("/{position_id}", response_model=dict)
async def update_position(position_id: str, position_data: PositionUpdate, db: Session = Depends(get_db)):
    """Update an existing position"""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    # Update only provided fields
    update_data = position_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(position, key, value)

    db.commit()
    db.refresh(position)

    return format_position_response(position)

@router.delete("/{position_id}", status_code=204)
async def delete_position(position_id: str, db: Session = Depends(get_db)):
    """Delete a position"""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    db.delete(position)
    db.commit()

    return None
