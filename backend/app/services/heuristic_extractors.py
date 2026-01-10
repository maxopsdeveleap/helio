"""
Heuristic extraction utilities using regex patterns.
These are deterministic, fast, and don't require LLM calls.
"""
import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def extract_email(text: str) -> Optional[str]:
    """
    Extract email address from text using regex.

    Args:
        text: Input text

    Returns:
        First email address found, or None
    """
    # Simple email regex pattern
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(pattern, text)

    if matches:
        email = matches[0]
        logger.debug(f"Extracted email: {email}")
        return email

    logger.debug("No email found in text")
    return None


def extract_phone(text: str) -> Optional[str]:
    """
    Extract phone number from text using regex.
    Handles various formats: +1-234-567-8900, (123) 456-7890, 123.456.7890, etc.

    Args:
        text: Input text

    Returns:
        First phone number found, or None
    """
    # Pattern for phone numbers with various separators
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-234-567-8900
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            phone = matches[0]
            logger.debug(f"Extracted phone: {phone}")
            return phone

    logger.debug("No phone found in text")
    return None


def extract_linkedin(text: str) -> Optional[str]:
    """
    Extract LinkedIn profile URL from text.

    Args:
        text: Input text

    Returns:
        LinkedIn profile URL, or None
    """
    # Pattern for LinkedIn URLs
    pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
    matches = re.findall(pattern, text, re.IGNORECASE)

    if matches:
        linkedin = matches[0]
        # Remove protocol if present to match our schema format
        linkedin = re.sub(r'^https?://', '', linkedin)
        linkedin = re.sub(r'^www\.', '', linkedin)
        logger.debug(f"Extracted LinkedIn: {linkedin}")
        return linkedin

    logger.debug("No LinkedIn URL found in text")
    return None


def extract_github(text: str) -> Optional[str]:
    """
    Extract GitHub profile URL from text.

    Args:
        text: Input text

    Returns:
        GitHub profile URL, or None
    """
    # Pattern for GitHub URLs
    pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+'
    matches = re.findall(pattern, text, re.IGNORECASE)

    if matches:
        github = matches[0]
        # Remove protocol if present to match our schema format
        github = re.sub(r'^https?://', '', github)
        github = re.sub(r'^www\.', '', github)
        logger.debug(f"Extracted GitHub: {github}")
        return github

    logger.debug("No GitHub URL found in text")
    return None


def extract_name_heuristic(text: str) -> Optional[dict]:
    """
    Attempt to extract name from the first few lines of text.
    This is a simple heuristic - looks for capitalized words in the first line.

    Args:
        text: Input text

    Returns:
        Dict with 'first_name' and 'last_name', or None
    """
    # Take first 3 lines
    lines = [line.strip() for line in text.split('\n') if line.strip()][:3]

    for line in lines:
        # Look for 2-3 capitalized words (likely a name)
        words = line.split()
        if len(words) >= 2 and all(w[0].isupper() for w in words[:3] if w):
            # Assume first word is first name, last word is last name
            if len(words) == 2:
                return {'first_name': words[0], 'last_name': words[1]}
            elif len(words) >= 3:
                # If 3+ words, take first as first_name and last as last_name
                return {'first_name': words[0], 'last_name': words[-1]}

    logger.debug("Could not extract name heuristically")
    return None


def extract_years_of_experience(text: str) -> Optional[int]:
    """
    Extract years of experience from phrases like:
    - "5+ years of experience"
    - "10 years experience"
    - "3-5 years"

    Args:
        text: Input text

    Returns:
        Number of years, or None
    """
    patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'(\d+)\s*years?\s+experience',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            years = int(matches[0])
            logger.debug(f"Extracted years of experience: {years}")
            return years

    logger.debug("No years of experience found")
    return None


def extract_dates(text: str) -> List[str]:
    """
    Extract date-like strings from text.
    Matches formats like: 2020-2023, Jan 2020, 2020-Present, etc.

    Args:
        text: Input text

    Returns:
        List of date strings found
    """
    patterns = [
        r'\b\d{4}\s*[-–—]\s*\d{4}\b',  # 2020-2023
        r'\b\d{4}\s*[-–—]\s*(?:Present|Current)\b',  # 2020-Present
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',  # Jan 2020
    ]

    dates = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)

    if dates:
        logger.debug(f"Extracted {len(dates)} date strings")

    return dates
