#!/usr/bin/env python3
"""
CV Ingestion Pipeline

Automatically extracts structured data from PDF/DOCX CVs and stores in database.

Usage:
    python ingest_cv.py /path/to/cv.pdf
    python ingest_cv.py /path/to/cv.pdf --candidate-id candidate_004
"""
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.candidate import (
    Candidate, CandidateSkill, CandidateExperience,
    CandidateEducation, CandidateCertification, CandidateLanguage, CVDocument
)
from app.services.document_parser import parse_document
from app.services.heuristic_extractors import (
    extract_email, extract_phone, extract_linkedin,
    extract_github, extract_name_heuristic
)
from app.services.llm_extractors import CVExtractor
from app.services.data_validator import (
    validate_email, validate_phone, validate_url,
    validate_personal_info, validate_experience, validate_education,
    validate_certifications, validate_languages, validate_skills
)
from app.services.embedding_service import generate_embedding, prepare_candidate_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_candidate_id(db) -> str:
    """Generate next candidate ID"""
    # Find highest existing ID
    from sqlalchemy import func
    result = db.query(func.max(Candidate.id)).scalar()

    if not result:
        return 'candidate_001'

    # Extract number and increment
    try:
        num = int(result.split('_')[1])
        return f'candidate_{num + 1:03d}'
    except:
        return 'candidate_001'


def ingest_cv(cv_path: Path, candidate_id: Optional[str] = None) -> str:
    """
    Ingest a CV and store structured data in database.

    Args:
        cv_path: Path to CV file (PDF or DOCX)
        candidate_id: Optional candidate ID (auto-generated if not provided)

    Returns:
        Candidate ID of ingested candidate

    Raises:
        Exception: If ingestion fails
    """
    logger.info(f"=" * 80)
    logger.info(f"Starting CV ingestion: {cv_path.name}")
    logger.info(f"=" * 80)

    # Step 1: Parse document to extract text
    logger.info("Step 1: Parsing document...")
    try:
        text = parse_document(cv_path)
        logger.info(f"Extracted {len(text)} characters of text")
    except Exception as e:
        logger.error(f"Failed to parse document: {e}")
        raise

    # Step 2: Heuristic extraction (fast, deterministic)
    logger.info("Step 2: Running heuristic extractors...")
    heuristic_data = {
        'email': extract_email(text),
        'phone': extract_phone(text),
        'linkedin': extract_linkedin(text),
        'github': extract_github(text),
        'name_hint': extract_name_heuristic(text),
    }
    logger.info(f"Heuristic extraction complete: {heuristic_data}")

    # Step 3: LLM extraction (intelligent, handles ambiguity)
    logger.info("Step 3: Running LLM extractors...")
    extractor = CVExtractor()
    llm_data = extractor.extract_all(text)
    logger.info("LLM extraction complete")

    # Step 4: Combine and validate data
    logger.info("Step 4: Validating extracted data...")

    # Personal info: prefer heuristics, fallback to LLM
    logger.debug(f"Validating personal_info: {llm_data['personal_info']}")
    personal_info = validate_personal_info(llm_data['personal_info'])

    logger.debug(f"Validating email from heuristics: {heuristic_data['email']}")
    email = validate_email(heuristic_data['email']) or validate_email(llm_data['personal_info'].get('email'))
    logger.debug(f"Validating phone from heuristics: {heuristic_data['phone']}")
    phone = validate_phone(heuristic_data['phone']) or validate_phone(llm_data['personal_info'].get('phone'))
    logger.debug(f"Validating linkedin: {heuristic_data['linkedin']}")
    linkedin = validate_url(heuristic_data['linkedin'])
    logger.debug(f"Validating github: {heuristic_data['github']}")
    github = validate_url(heuristic_data['github'])

    # Use heuristic name if available, otherwise LLM
    if heuristic_data['name_hint']:
        first_name = heuristic_data['name_hint'].get('first_name') or personal_info.get('first_name')
        last_name = heuristic_data['name_hint'].get('last_name') or personal_info.get('last_name')
    else:
        first_name = personal_info.get('first_name')
        last_name = personal_info.get('last_name')

    # Validate required fields
    if not first_name or not last_name:
        raise ValueError(f"Could not extract name from CV. Please check the document format.")

    if not email:
        logger.warning("No email found in CV")

    # Validate structured data
    logger.debug(f"Validating skills: {llm_data['skills']}")
    skills = validate_skills(llm_data['skills'])
    logger.debug(f"Validating experience: {llm_data['experience']}")
    experience = validate_experience(llm_data['experience'])
    logger.debug(f"Validating education: {llm_data['education']}")
    education = validate_education(llm_data['education'])
    logger.debug(f"Validating certifications: {llm_data['certifications']}")
    certifications = validate_certifications(llm_data['certifications'])
    logger.debug(f"Validating languages: {llm_data['languages']}")
    languages = validate_languages(llm_data['languages'])

    # Handle summary (ensure it's a string)
    summary_raw = llm_data.get('summary')
    if summary_raw and isinstance(summary_raw, str):
        summary = summary_raw.strip()
    else:
        summary = None

    logger.info(f"Validation complete: {first_name} {last_name}, {len(skills)} skills, "
                f"{len(experience)} experience entries, {len(education)} education entries")

    # Step 4.5: Generate embedding
    logger.info("Step 4.5: Generating embedding...")
    try:
        # Prepare candidate data for embedding
        candidate_data = {
            'summary': summary,
            'skills': skills,
            'experience': [
                {
                    'title': exp['title'],
                    'company': exp['company']
                }
                for exp in experience
            ],
            'education': [
                {
                    'degree': edu['degree'],
                    'field_of_study': edu.get('field_of_study')
                }
                for edu in education
            ]
        }

        # Generate embedding text
        embedding_text = prepare_candidate_text(candidate_data)
        logger.info(f"Embedding text prepared ({len(embedding_text)} chars)")

        # Generate embedding vector
        embedding_vector = generate_embedding(embedding_text)
        logger.info(f"Embedding generated ({len(embedding_vector)} dimensions)")

    except Exception as e:
        logger.warning(f"Failed to generate embedding: {e}. Continuing without embedding.")
        embedding_vector = None
        embedding_text = None

    # Step 5: Store in database
    logger.info("Step 5: Storing in database...")
    db = SessionLocal()

    try:
        # Generate ID if not provided
        if not candidate_id:
            candidate_id = generate_candidate_id(db)
            logger.info(f"Generated candidate ID: {candidate_id}")

        # Check if candidate already exists
        existing = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if existing:
            raise ValueError(f"Candidate {candidate_id} already exists. Use a different ID or delete existing.")

        # Create candidate record
        candidate = Candidate(
            id=candidate_id,
            status='New',  # Default status
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            location=personal_info.get('location'),
            linkedin=linkedin,
            github=github,
            summary=summary,
            embedding=embedding_vector,
            embedding_text=embedding_text
        )
        db.add(candidate)

        # Add skills
        for skill_name in skills:
            skill = CandidateSkill(candidate_id=candidate_id, skill_name=skill_name)
            db.add(skill)

        # Add experience
        for exp in experience:
            experience_entry = CandidateExperience(
                candidate_id=candidate_id,
                title=exp['title'],
                company=exp['company'],
                location=exp.get('location'),
                start_date=exp.get('start_date'),
                end_date=exp.get('end_date'),
                responsibilities=exp.get('responsibilities', [])
            )
            db.add(experience_entry)

        # Add education
        for edu in education:
            education_entry = CandidateEducation(
                candidate_id=candidate_id,
                degree=edu['degree'],
                institution=edu['institution'],
                start_date=edu.get('start_date'),
                end_date=edu.get('end_date'),
                status=edu.get('status')
            )
            db.add(education_entry)

        # Add certifications
        for cert in certifications:
            cert_entry = CandidateCertification(
                candidate_id=candidate_id,
                name=cert['name'],
                issuer=cert.get('issuer'),
                year=cert.get('year')
            )
            db.add(cert_entry)

        # Add languages
        for lang in languages:
            lang_entry = CandidateLanguage(
                candidate_id=candidate_id,
                language=lang['language'],
                proficiency=lang['proficiency']
            )
            db.add(lang_entry)

        # Add CV document reference
        cv_doc = CVDocument(
            candidate_id=candidate_id,
            file_path=str(cv_path),
            file_name=cv_path.name,
            file_type=cv_path.suffix.lower()
        )
        db.add(cv_doc)

        # Commit transaction
        db.commit()
        logger.info(f"✅ Successfully ingested candidate: {first_name} {last_name} ({candidate_id})")

        return candidate_id

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store in database: {e}")
        raise

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Ingest CV and extract structured data')
    parser.add_argument('cv_path', type=str, help='Path to CV file (PDF or DOCX)')
    parser.add_argument('--candidate-id', type=str, help='Optional candidate ID (auto-generated if not provided)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    cv_path = Path(args.cv_path)
    if not cv_path.exists():
        print(f"Error: File not found: {cv_path}")
        sys.exit(1)

    try:
        candidate_id = ingest_cv(cv_path, args.candidate_id)
        print(f"\n{'=' * 80}")
        print(f"✅ SUCCESS! Candidate ingested: {candidate_id}")
        print(f"{'=' * 80}")
        print(f"\nView in UI: http://localhost:8000/public/index.html")

    except Exception as e:
        print(f"\n{'=' * 80}")
        print(f"❌ FAILED: {e}")
        print(f"{'=' * 80}")
        sys.exit(1)


if __name__ == '__main__':
    main()
