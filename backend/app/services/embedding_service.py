"""
Embedding Service - Converts text to vector embeddings using Voyage AI.

This service abstracts the embedding provider, making it easy to switch
between Voyage AI, OpenAI, AWS Titan, or other providers later.
"""

import os
from typing import List, Optional
import voyageai

# Initialize Voyage AI client
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
if not VOYAGE_API_KEY:
    raise ValueError("VOYAGE_API_KEY environment variable not set")

voyage_client = voyageai.Client(api_key=VOYAGE_API_KEY)

# Model configuration
EMBEDDING_MODEL = "voyage-2"  # Optimized for retrieval/search
EMBEDDING_DIMENSIONS = 1024  # Voyage-2 outputs 1024-dimensional vectors


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text string.

    Args:
        text: The text to embed

    Returns:
        List of floats representing the embedding vector (1024 dimensions)
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")

    # Call Voyage AI API
    result = voyage_client.embed(
        texts=[text],
        model=EMBEDDING_MODEL,
        input_type="document"  # "document" for indexing, "query" for search
    )

    # Return first (and only) embedding
    return result.embeddings[0]


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in one API call.
    More efficient than calling generate_embedding multiple times.

    Args:
        texts: List of texts to embed

    Returns:
        List of embedding vectors
    """
    if not texts:
        return []

    # Filter out empty strings
    valid_texts = [t for t in texts if t and t.strip()]
    if not valid_texts:
        raise ValueError("No valid texts to embed")

    # Call Voyage AI API with batch
    result = voyage_client.embed(
        texts=valid_texts,
        model=EMBEDDING_MODEL,
        input_type="document"
    )

    return result.embeddings


def prepare_candidate_text(candidate_data: dict) -> str:
    """
    Prepare candidate data for embedding.

    Creates a standardized text representation focusing on:
    - Summary
    - Skills
    - Experience titles and companies

    Args:
        candidate_data: Dictionary with candidate fields

    Returns:
        Formatted text ready for embedding
    """
    parts = []

    # Add summary
    if candidate_data.get("summary"):
        parts.append(f"Summary: {candidate_data['summary']}")

    # Add skills
    if candidate_data.get("skills"):
        skills_text = ", ".join(candidate_data["skills"])
        parts.append(f"Skills: {skills_text}")

    # Add experience
    if candidate_data.get("experience"):
        exp_items = []
        for exp in candidate_data["experience"]:
            title = exp.get("title", "")
            company = exp.get("company", "")
            if title and company:
                exp_items.append(f"{title} at {company}")
        if exp_items:
            parts.append(f"Experience: {'; '.join(exp_items)}")

    # Add education
    if candidate_data.get("education"):
        edu_items = []
        for edu in candidate_data["education"]:
            degree = edu.get("degree", "")
            field = edu.get("field_of_study", "")
            if degree:
                edu_items.append(f"{degree} in {field}" if field else degree)
        if edu_items:
            parts.append(f"Education: {'; '.join(edu_items)}")

    result = "\n".join(parts)

    # Ensure we have something to embed
    if not result.strip():
        raise ValueError("Cannot create embedding text: candidate has no meaningful data")

    return result


def prepare_position_text(position_data: dict) -> str:
    """
    Prepare position data for embedding.

    Creates a standardized text representation focusing on:
    - Title
    - Description
    - Requirements
    - Skills

    Args:
        position_data: Dictionary with position fields

    Returns:
        Formatted text ready for embedding
    """
    parts = []

    # Add title
    if position_data.get("title"):
        parts.append(f"Position: {position_data['title']}")

    # Add description
    if position_data.get("description"):
        parts.append(f"Description: {position_data['description']}")

    # Add requirements
    if position_data.get("requirements"):
        req_text = "; ".join([r.get("requirement", "") for r in position_data["requirements"] if r.get("requirement")])
        if req_text:
            parts.append(f"Requirements: {req_text}")

    # Add skills
    if position_data.get("skills"):
        skills_text = ", ".join(position_data["skills"])
        parts.append(f"Skills: {skills_text}")

    # Add experience level
    if position_data.get("experience"):
        parts.append(f"Experience Level: {position_data['experience']}")

    result = "\n".join(parts)

    # Ensure we have something to embed
    if not result.strip():
        raise ValueError("Cannot create embedding text: position has no meaningful data")

    return result
