"""
Matching Service - Provides LLM-powered explanations for candidate-position matches.

Uses Claude to analyze semantic similarity matches and generate human-readable
explanations of why a candidate is a good fit for a position.
"""

import os
from typing import List, Dict, Any
from anthropic import Anthropic

# Initialize Claude client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def explain_position_match(
    candidate: Dict[str, Any],
    position: Dict[str, Any],
    similarity_score: float
) -> str:
    """
    Generate an explanation for why a position matches a candidate.

    Args:
        candidate: Candidate data dictionary
        position: Position data dictionary
        similarity_score: Similarity score (0-1)

    Returns:
        Human-readable explanation of the match
    """
    # Build candidate summary
    candidate_summary = f"""
Candidate: {candidate.get('first_name')} {candidate.get('last_name')}
Summary: {candidate.get('summary', 'N/A')}
Skills: {', '.join(candidate.get('skills', []))}
"""

    # Add recent experience
    experience = candidate.get('experience', [])
    if experience:
        exp = experience[0]  # Most recent
        candidate_summary += f"Current/Recent Role: {exp.get('title')} at {exp.get('company')}\n"

    # Add education
    education = candidate.get('education', [])
    if education:
        edu = education[0]
        candidate_summary += f"Education: {edu.get('degree')} in {edu.get('field_of_study', 'N/A')}\n"

    # Build position summary
    position_summary = f"""
Position: {position.get('title')} at {position.get('company')}
Description: {position.get('description', 'N/A')}
Required Skills: {', '.join(position.get('skills', []))}
Experience Level: {position.get('experience', 'N/A')}
"""

    # Create prompt for Claude
    prompt = f"""You are analyzing a job match between a candidate and a position.

{candidate_summary}

{position_summary}

Similarity Score: {similarity_score:.1%}

Task: Write a concise 2-3 sentence explanation of why this position is a good match for this candidate. Focus on:
1. Skills alignment
2. Experience relevance
3. Career progression fit

Keep it professional and specific. Don't mention the similarity score."""

    # Call Claude API
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=200,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract explanation from response
    explanation = message.content[0].text.strip()

    return explanation


def explain_multiple_matches(
    candidate: Dict[str, Any],
    positions_with_scores: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate explanations for multiple position matches.

    Args:
        candidate: Candidate data dictionary
        positions_with_scores: List of positions with similarity_score field

    Returns:
        List of positions with added 'match_explanation' field
    """
    results = []

    for position in positions_with_scores:
        try:
            explanation = explain_position_match(
                candidate=candidate,
                position=position,
                similarity_score=position['similarity_score']
            )

            result = {**position, "match_explanation": explanation}
            results.append(result)

        except Exception as e:
            # If explanation fails, still return position without explanation
            result = {
                **position,
                "match_explanation": f"Match score: {position['similarity_score']:.1%}"
            }
            results.append(result)

    return results
