from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.models import get_db
from app.models.position import Position, PositionRequirement, PositionResponsibility, PositionSkill, CandidatePosition
from app.models.candidate import Candidate
from app.schemas.position import PositionResponse, PositionCreate, PositionUpdate
from app.services.similarity_service import find_similar_candidates

router = APIRouter()

# Request model for position ingestion from email
class PositionIngestRequest(BaseModel):
    title: str
    description: str
    company: str = "Hellio"
    hiring_manager_email: Optional[str] = None

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

@router.get("/{position_id}/suggest-candidates", response_model=List[dict])
async def suggest_candidates_for_position(position_id: str, db: Session = Depends(get_db)):
    """
    Suggest top 3 candidates for a position using semantic similarity.

    Returns candidates ranked by how well their skills and experience match
    the position requirements, using vector embeddings for semantic search.
    """
    try:
        candidates = find_similar_candidates(
            position_id=position_id,
            db=db,
            limit=3,
            min_similarity=0.5  # Lower threshold for more results
        )

        return candidates

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar candidates: {str(e)}")

@router.post("/{position_id}/candidates/{candidate_id}")
async def add_candidate_to_position(position_id: str, candidate_id: str, db: Session = Depends(get_db)):
    """Add a candidate to a position"""
    # Check if position exists
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    # Check if candidate exists
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Check if already added
    existing = db.query(CandidatePosition).filter(
        CandidatePosition.position_id == position_id,
        CandidatePosition.candidate_id == candidate_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Candidate already added to this position")

    # Add candidate to position
    candidate_position = CandidatePosition(
        candidate_id=candidate_id,
        position_id=position_id,
        application_status="Suggested"
    )
    db.add(candidate_position)

    # Update candidate status to Active when added to a position
    if candidate.status == "New":
        candidate.status = "Active"

    db.commit()

    return {"message": "Candidate added to position successfully", "status_updated": candidate.status}

@router.delete("/{position_id}/candidates/{candidate_id}")
async def remove_candidate_from_position(position_id: str, candidate_id: str, db: Session = Depends(get_db)):
    """Remove a candidate from a position"""
    candidate_position = db.query(CandidatePosition).filter(
        CandidatePosition.position_id == position_id,
        CandidatePosition.candidate_id == candidate_id
    ).first()

    if not candidate_position:
        raise HTTPException(status_code=404, detail="Candidate not found in this position")

    db.delete(candidate_position)
    db.commit()

    return {"message": "Candidate removed from position successfully"}

@router.get("/{position_id}/candidates", response_model=List[dict])
async def get_position_candidates(position_id: str, db: Session = Depends(get_db)):
    """Get all candidates added to a position"""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    candidate_positions = db.query(CandidatePosition).filter(
        CandidatePosition.position_id == position_id
    ).all()

    result = []
    for cp in candidate_positions:
        candidate = db.query(Candidate).filter(Candidate.id == cp.candidate_id).first()
        if candidate:
            result.append({
                "id": candidate.id,
                "first_name": candidate.first_name,
                "last_name": candidate.last_name,
                "email": candidate.email,
                "location": candidate.location,
                "summary": candidate.summary,
                "application_status": cp.application_status,
                "applied_at": cp.applied_at.isoformat() if cp.applied_at else None
            })

    return result

@router.post("/ingest")
async def ingest_position_from_email(
    request: PositionIngestRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest a position from email text using LLM to parse details.
    Used by the agent when processing position emails.
    """
    from app.services.llm_service import parse_position_details
    from app.services.embedding_service import generate_embedding
    import uuid

    # Generate position ID
    # Count existing positions to get next number
    count = db.query(Position).count()
    position_id = f"position_{str(count + 1).zfill(3)}"

    # Use LLM to parse position details
    try:
        parsed = parse_position_details(request.title, request.description)
        print(f"LLM parsed result: {parsed}")  # Debug logging
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse position: {str(e)}")

    # Validate required fields
    required_fields = ['title', 'summary', 'requirements', 'responsibilities']
    missing_fields = [field for field in required_fields if field not in parsed]
    if missing_fields:
        raise HTTPException(status_code=500, detail=f"LLM response missing fields: {missing_fields}. Got: {list(parsed.keys())}")

    # Generate embedding for semantic search
    embedding_text = f"{parsed['title']} {parsed['summary']} {' '.join(parsed['requirements'])} {' '.join(parsed['responsibilities'])}"
    try:
        embedding = generate_embedding(embedding_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")
    
    # Create position
    position = Position(
        id=position_id,
        title=parsed['title'],
        company=request.company,
        location=parsed.get('location', 'Tel Aviv, Israel'),
        work_arrangement=parsed.get('work_arrangement', 'Hybrid'),
        experience=parsed.get('experience', '2-5 years'),
        description=parsed['summary'],  # Use 'description' field, not 'summary'
        urgency=parsed.get('urgency', 'Medium'),
        status='Open',
        embedding=embedding,
        embedding_text=embedding_text
    )
    
    db.add(position)
    db.flush()
    
    # Add requirements
    for idx, req in enumerate(parsed['requirements']):
        requirement = PositionRequirement(
            position_id=position_id,
            requirement=req,
            is_required=idx < len(parsed['requirements']) // 2,  # First half are required
            order_index=idx
        )
        db.add(requirement)
    
    # Add responsibilities
    for idx, resp in enumerate(parsed['responsibilities']):
        responsibility = PositionResponsibility(
            position_id=position_id,
            responsibility=resp,
            order_index=idx
        )
        db.add(responsibility)
    
    # Add skills
    for skill in parsed.get('skills', []):
        skill_obj = PositionSkill(
            position_id=position_id,
            skill_name=skill  # Field is 'skill_name' not 'skill'
        )
        db.add(skill_obj)
    
    db.commit()
    db.refresh(position)
    
    # Find matching candidates
    matching_candidates = []
    try:
        matching_candidates = find_similar_candidates(
            position_id=position_id,
            db=db,
            limit=5,
            min_similarity=0.5
        )
    except Exception:
        pass  # Don't fail if matching fails
    
    return {
        "position_id": position_id,
        "position": format_position_response(position),
        "matching_candidates": matching_candidates,
        "message": f"Position '{parsed['title']}' created successfully"
    }
