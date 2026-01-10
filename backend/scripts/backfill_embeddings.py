#!/usr/bin/env python3
"""
Backfill Embeddings Script

Adds embeddings to existing candidates and positions that don't have them yet.
"""
import sys
import logging
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.candidate import Candidate
from app.models.position import Position
from app.services.embedding_service import generate_embedding, prepare_candidate_text, prepare_position_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_candidate_embeddings():
    """Add embeddings to candidates that don't have them."""
    db = SessionLocal()

    try:
        # Find candidates without embeddings
        candidates = db.query(Candidate).filter(Candidate.embedding == None).all()

        if not candidates:
            logger.info("No candidates need embeddings - all up to date!")
            return

        logger.info(f"Found {len(candidates)} candidates without embeddings")
        logger.info("=" * 80)

        success_count = 0
        error_count = 0

        for candidate in candidates:
            try:
                logger.info(f"Processing: {candidate.first_name} {candidate.last_name} ({candidate.id})")

                # Prepare candidate data
                candidate_data = {
                    'summary': candidate.summary,
                    'skills': [skill.skill_name for skill in candidate.skills],
                    'experience': [
                        {
                            'title': exp.title,
                            'company': exp.company
                        }
                        for exp in candidate.experience
                    ],
                    'education': [
                        {
                            'degree': edu.degree,
                            'field_of_study': edu.field_of_study
                        }
                        for edu in candidate.education
                    ]
                }

                # Generate embedding text
                embedding_text = prepare_candidate_text(candidate_data)
                logger.info(f"  Embedding text prepared ({len(embedding_text)} chars)")

                # Generate embedding vector
                embedding_vector = generate_embedding(embedding_text)
                logger.info(f"  Embedding generated ({len(embedding_vector)} dimensions)")

                # Update candidate
                candidate.embedding = embedding_vector
                candidate.embedding_text = embedding_text

                db.commit()
                success_count += 1
                logger.info(f"  ✅ Updated {candidate.id}")

            except Exception as e:
                logger.error(f"  ❌ Failed to process {candidate.id}: {e}")
                error_count += 1
                db.rollback()

        logger.info("=" * 80)
        logger.info(f"Backfill complete: {success_count} success, {error_count} errors")

    finally:
        db.close()


def backfill_position_embeddings():
    """Add embeddings to positions that don't have them."""
    db = SessionLocal()

    try:
        # Find positions without embeddings
        positions = db.query(Position).filter(Position.embedding == None).all()

        if not positions:
            logger.info("No positions need embeddings - all up to date!")
            return

        logger.info(f"Found {len(positions)} positions without embeddings")
        logger.info("=" * 80)

        success_count = 0
        error_count = 0

        for position in positions:
            try:
                logger.info(f"Processing: {position.title} at {position.company} ({position.id})")

                # Prepare position data
                position_data = {
                    'title': position.title,
                    'description': position.description,
                    'requirements': [
                        {'requirement': req.requirement}
                        for req in position.requirements
                    ],
                    'skills': [skill.skill_name for skill in position.skills],
                    'experience': position.experience
                }

                # Generate embedding text
                embedding_text = prepare_position_text(position_data)
                logger.info(f"  Embedding text prepared ({len(embedding_text)} chars)")

                # Generate embedding vector
                embedding_vector = generate_embedding(embedding_text)
                logger.info(f"  Embedding generated ({len(embedding_vector)} dimensions)")

                # Update position
                position.embedding = embedding_vector
                position.embedding_text = embedding_text

                db.commit()
                success_count += 1
                logger.info(f"  ✅ Updated {position.id}")

            except Exception as e:
                logger.error(f"  ❌ Failed to process {position.id}: {e}")
                error_count += 1
                db.rollback()

        logger.info("=" * 80)
        logger.info(f"Backfill complete: {success_count} success, {error_count} errors")

    finally:
        db.close()


def main():
    logger.info("=" * 80)
    logger.info("Starting Embedding Backfill")
    logger.info("=" * 80)

    # Backfill candidates
    logger.info("\n📋 Backfilling candidate embeddings...")
    backfill_candidate_embeddings()

    # Backfill positions
    logger.info("\n📋 Backfilling position embeddings...")
    backfill_position_embeddings()

    logger.info("\n" + "=" * 80)
    logger.info("✅ Backfill complete!")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
