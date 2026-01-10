"""
Similarity Search Service - Finds similar candidates and positions using vector embeddings.

Uses pgvector's cosine distance operator (<->) to find semantically similar items.
Lower distance = more similar (0 = identical, 2 = opposite)
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import re

from app.models.candidate import Candidate
from app.models.position import Position, CandidatePosition
from app.services.embedding_service import generate_embedding, prepare_position_text


def parse_experience_years(experience_str: str) -> int:
    """
    Parse experience requirement string to extract minimum years.

    Examples:
        "5+ years" -> 5
        "0-2 years" -> 0
        "3-5 years" -> 3
        "Senior (8+ years)" -> 8

    Returns:
        Minimum years of experience required (default 0 if unparseable)
    """
    if not experience_str:
        return 0

    # Look for patterns like "5+", "5-7", "8+ years"
    match = re.search(r'(\d+)', experience_str)
    if match:
        return int(match.group(1))

    return 0


def calculate_candidate_experience(candidate: Candidate) -> int:
    """
    Calculate total years of experience from candidate's work history.

    First tries to extract years from summary, then falls back to counting entries.

    Returns:
        Approximate years of experience
    """
    # First, try to extract years from summary
    if candidate.summary:
        # Look for patterns like "2 years", "5+ years", "1.5 years"
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience', candidate.summary, re.IGNORECASE)
        if match:
            return int(float(match.group(1)))

    # Fallback: count experience entries (each roughly = 2 years)
    return len(candidate.experience) * 2 if candidate.experience else 0


def check_experience_match(candidate_years: int, required_str: str) -> bool:
    """
    Check if candidate's experience matches position requirements.

    Args:
        candidate_years: Candidate's years of experience
        required_str: Position's experience requirement string

    Returns:
        True if candidate meets minimum requirement with some flexibility
    """
    required_years = parse_experience_years(required_str)

    # Allow 1-2 years flexibility for borderline cases
    # e.g., 3-4 years experience can apply to "5+ years" positions
    flexibility = 2

    return candidate_years >= (required_years - flexibility)


def find_similar_candidates(
    position_id: str,
    db: Session,
    limit: int = 3,
    min_similarity: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Find candidates most similar to a given position.

    Args:
        position_id: ID of the position to match
        db: Database session
        limit: Maximum number of candidates to return (default 3)
        min_similarity: Minimum similarity score (0-1, default 0.7)
                       Note: cosine distance is converted to similarity (1 - distance/2)

    Returns:
        List of candidate dictionaries with similarity scores
    """
    # Get position
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise ValueError(f"Position {position_id} not found")

    if position.embedding is None:
        raise ValueError(f"Position {position_id} has no embedding. Run backfill script first.")

    # Query for similar candidates using cosine distance
    # Use raw SQL with position binding to avoid issues with array comparison
    # Fetch more candidates initially so we can filter by experience
    query = text("""
        SELECT
            c.id,
            c.first_name,
            c.last_name,
            c.email,
            c.location,
            c.summary,
            (1 - (c.embedding <=> p.embedding) / 2) as similarity_score
        FROM candidates c, positions p
        WHERE c.embedding IS NOT NULL
          AND p.id = :position_id
        ORDER BY c.embedding <=> p.embedding
        LIMIT :fetch_limit
    """)

    # Fetch more than needed to account for experience filtering
    result = db.execute(
        query,
        {"position_id": position_id, "fetch_limit": limit * 3}
    )

    # Get list of candidates already added to this position
    already_added_ids = {
        cp.candidate_id
        for cp in db.query(CandidatePosition).filter(
            CandidatePosition.position_id == position_id
        ).all()
    }

    # Format and filter results
    candidates = []
    for row in result:
        similarity_score = float(row.similarity_score)

        # Filter by minimum similarity
        if similarity_score < min_similarity:
            continue

        # Skip candidates already added to this position
        if row.id in already_added_ids:
            continue

        # Get full candidate object to check experience
        candidate = db.query(Candidate).filter(Candidate.id == row.id).first()
        if not candidate:
            continue

        # Check experience match
        candidate_years = calculate_candidate_experience(candidate)
        if not check_experience_match(candidate_years, position.experience):
            continue  # Skip candidates with insufficient experience

        candidates.append({
            "id": row.id,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email": row.email,
            "location": row.location,
            "summary": row.summary,
            "similarity_score": round(similarity_score, 3),
            "years_experience": candidate_years  # Add for transparency
        })

        # Stop once we have enough matching candidates
        if len(candidates) >= limit:
            break

    return candidates


def find_similar_positions(
    candidate_id: str,
    db: Session,
    limit: int = 3,
    min_similarity: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Find positions most similar to a given candidate.

    Args:
        candidate_id: ID of the candidate to match
        db: Database session
        limit: Maximum number of positions to return (default 3)
        min_similarity: Minimum similarity score (0-1, default 0.7)

    Returns:
        List of position dictionaries with similarity scores
    """
    # Get candidate
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found")

    if candidate.embedding is None:
        raise ValueError(f"Candidate {candidate_id} has no embedding. Run backfill script first.")

    # Calculate candidate's experience
    candidate_years = calculate_candidate_experience(candidate)

    # Query for similar positions using cosine distance
    # Fetch more positions to account for experience filtering
    query = text("""
        SELECT
            p.id,
            p.title,
            p.company,
            p.location,
            p.description,
            p.experience,
            (1 - (p.embedding <=> c.embedding) / 2) as similarity_score
        FROM positions p, candidates c
        WHERE p.embedding IS NOT NULL
          AND c.id = :candidate_id
        ORDER BY p.embedding <=> c.embedding
        LIMIT :fetch_limit
    """)

    result = db.execute(
        query,
        {"candidate_id": candidate_id, "fetch_limit": limit * 3}
    )

    # Format and filter results
    positions = []
    for row in result:
        similarity_score = float(row.similarity_score)

        # Filter by minimum similarity
        if similarity_score < min_similarity:
            continue

        # Check if candidate meets experience requirements
        if not check_experience_match(candidate_years, row.experience):
            continue  # Skip positions requiring too much experience

        positions.append({
            "id": row.id,
            "title": row.title,
            "company": row.company,
            "location": row.location,
            "description": row.description,
            "experience": row.experience,
            "similarity_score": round(similarity_score, 3),
            "candidate_experience": candidate_years  # Add for transparency
        })

        # Stop once we have enough matching positions
        if len(positions) >= limit:
            break

    return positions


def search_candidates_by_query(
    query_text: str,
    db: Session,
    limit: int = 10,
    min_similarity: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Search candidates using natural language query.

    Args:
        query_text: Natural language search query (e.g., "Python developer with AWS experience")
        db: Database session
        limit: Maximum number of candidates to return
        min_similarity: Minimum similarity score (0-1)

    Returns:
        List of candidate dictionaries with similarity scores
    """
    # Generate embedding for query
    query_embedding = generate_embedding(query_text)
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

    # Query for similar candidates
    query = text("""
        SELECT
            c.id,
            c.first_name,
            c.last_name,
            c.email,
            c.location,
            c.summary,
            (1 - (c.embedding <=> :embedding::vector) / 2) as similarity_score
        FROM candidates c
        WHERE c.embedding IS NOT NULL
        ORDER BY c.embedding <=> :embedding::vector
        LIMIT :limit
    """)

    result = db.execute(
        query,
        {"embedding": embedding_str, "limit": limit}
    )

    # Format results
    candidates = []
    for row in result:
        similarity_score = float(row.similarity_score)

        if similarity_score < min_similarity:
            continue

        candidates.append({
            "id": row.id,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email": row.email,
            "location": row.location,
            "summary": row.summary,
            "similarity_score": round(similarity_score, 3)
        })

    return candidates
