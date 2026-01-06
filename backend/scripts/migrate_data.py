#!/usr/bin/env python3
"""
Data migration script: Load JSON files into PostgreSQL database
Reads candidate and position JSON files from data/ folder
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import SessionLocal, init_db
from app.models.candidate import (
    Candidate, CandidateSkill, CandidateExperience,
    CandidateEducation, CandidateCertification, CandidateLanguage
)
from app.models.position import (
    Position, PositionRequirement, PositionResponsibility, PositionSkill
)

def load_json_file(file_path):
    """Load and parse JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def migrate_candidate(db, candidate_data):
    """Migrate a single candidate from JSON to database"""
    candidate_id = candidate_data['id']

    # Check if candidate already exists
    existing = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if existing:
        print(f"  ⚠️  Candidate {candidate_id} already exists, skipping...")
        return

    # Extract personal info (nested structure from Exercise 1 JSON)
    personal_info = candidate_data.get('personalInfo', {})

    # Create candidate record
    candidate = Candidate(
        id=candidate_data['id'],
        status=candidate_data['status'],
        first_name=personal_info.get('firstName'),
        last_name=personal_info.get('lastName'),
        email=personal_info.get('email'),
        phone=personal_info.get('phone'),
        location=personal_info.get('location'),
        linkedin=personal_info.get('linkedin'),
        github=personal_info.get('github'),
        summary=candidate_data.get('summary')
    )
    db.add(candidate)

    # Add skills
    for skill_name in candidate_data.get('skills', []):
        skill = CandidateSkill(candidate_id=candidate_id, skill_name=skill_name)
        db.add(skill)

    # Add experience
    for idx, exp in enumerate(candidate_data.get('experience', [])):
        experience = CandidateExperience(
            candidate_id=candidate_id,
            title=exp['title'],
            company=exp['company'],
            location=exp.get('location'),
            start_date=exp.get('start_date'),
            end_date=exp.get('end_date'),
            responsibilities=exp.get('responsibilities', []),
            order_index=idx
        )
        db.add(experience)

    # Add education
    for idx, edu in enumerate(candidate_data.get('education', [])):
        education = CandidateEducation(
            candidate_id=candidate_id,
            degree=edu['degree'],
            field_of_study=edu.get('field_of_study'),
            institution=edu['institution'],
            start_date=edu.get('start_date'),
            end_date=edu.get('end_date'),
            status=edu.get('status'),
            order_index=idx
        )
        db.add(education)

    # Add certifications
    for cert in candidate_data.get('certifications', []):
        certification = CandidateCertification(
            candidate_id=candidate_id,
            name=cert['name'],
            issuer=cert['issuer'],
            year=cert.get('year')
        )
        db.add(certification)

    # Add languages
    for lang in candidate_data.get('languages', []):
        language = CandidateLanguage(
            candidate_id=candidate_id,
            language=lang['language'],
            proficiency=lang['proficiency']
        )
        db.add(language)

    db.commit()
    print(f"  ✅ Migrated candidate: {personal_info.get('firstName')} {personal_info.get('lastName')} ({candidate_id})")

def migrate_position(db, position_data):
    """Migrate a single position from JSON to database"""
    position_id = position_data['id']

    # Check if position already exists
    existing = db.query(Position).filter(Position.id == position_id).first()
    if existing:
        print(f"  ⚠️  Position {position_id} already exists, skipping...")
        return

    # Create position record
    contact = position_data.get('contact_person', {})
    position = Position(
        id=position_data['id'],
        status=position_data['status'],
        title=position_data['title'],
        company=position_data['company'],
        location=position_data.get('location'),
        work_arrangement=position_data.get('work_arrangement'),
        experience=position_data.get('experience'),
        description=position_data['description'],
        compensation=position_data.get('compensation'),
        timeline=position_data.get('timeline'),
        urgency=position_data.get('urgency'),
        contact_person_name=contact.get('name'),
        contact_person_title=contact.get('title'),
        contact_person_email=contact.get('email'),
        notes=position_data.get('notes')
    )
    db.add(position)

    # Add requirements (required)
    for idx, req in enumerate(position_data.get('requirements', [])):
        requirement = PositionRequirement(
            position_id=position_id,
            requirement=req,
            is_required=True,
            order_index=idx
        )
        db.add(requirement)

    # Add nice-to-have requirements
    for idx, req in enumerate(position_data.get('nice_to_have', [])):
        requirement = PositionRequirement(
            position_id=position_id,
            requirement=req,
            is_required=False,
            order_index=idx
        )
        db.add(requirement)

    # Add responsibilities
    for idx, resp in enumerate(position_data.get('responsibilities', [])):
        responsibility = PositionResponsibility(
            position_id=position_id,
            responsibility=resp,
            order_index=idx
        )
        db.add(responsibility)

    # Add skills
    for skill_name in position_data.get('skills', []):
        skill = PositionSkill(position_id=position_id, skill_name=skill_name)
        db.add(skill)

    db.commit()
    print(f"  ✅ Migrated position: {position_data['title']} at {position_data['company']} ({position_id})")

def main():
    """Main migration function"""
    print("\n🚀 Starting data migration...\n")

    # Initialize database (create tables)
    print("📊 Initializing database tables...")
    init_db()
    print("  ✅ Tables created\n")

    # Create database session
    db = SessionLocal()

    try:
        # Get data directory path (mounted at /app/data in Docker)
        data_dir = Path('/app/data')

        # Migrate candidates
        print("👥 Migrating candidates...")
        candidates_dir = data_dir / 'candidates'
        for json_file in sorted(candidates_dir.glob('candidate_*.json')):
            candidate_data = load_json_file(json_file)
            migrate_candidate(db, candidate_data)

        # Migrate positions
        print("\n💼 Migrating positions...")
        positions_dir = data_dir / 'positions'
        for json_file in sorted(positions_dir.glob('position_*.json')):
            position_data = load_json_file(json_file)
            migrate_position(db, position_data)

        print("\n✅ Migration completed successfully!\n")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}\n")
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    main()
