"""
Data validation utilities for extracted candidate information.
Treats LLM output as untrusted and validates before storing in database.
"""
import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def validate_email(email: Optional[str]) -> Optional[str]:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        Validated email or None if invalid
    """
    if not email:
        return None

    # Basic email validation
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
    if re.match(pattern, email):
        return email.lower()

    logger.warning(f"Invalid email format: {email}")
    return None


def validate_phone(phone: Optional[str]) -> Optional[str]:
    """
    Validate and clean phone number.

    Args:
        phone: Phone number to validate

    Returns:
        Cleaned phone or None if invalid
    """
    if not phone:
        return None

    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)

    # Must have at least 10 digits
    if len(re.sub(r'[^\d]', '', cleaned)) >= 10:
        return phone  # Return original format (with separators)

    logger.warning(f"Invalid phone number: {phone}")
    return None


def validate_url(url: Optional[str]) -> Optional[str]:
    """
    Validate URL format (for LinkedIn, GitHub, etc.).

    Args:
        url: URL to validate

    Returns:
        Cleaned URL or None if invalid
    """
    if not url:
        return None

    # Remove protocol and www if present
    cleaned = re.sub(r'^https?://', '', url)
    cleaned = re.sub(r'^www\.', '', cleaned)

    # Basic validation: should have domain.tld/path format
    if '.' in cleaned and '/' in cleaned:
        return cleaned

    logger.warning(f"Invalid URL format: {url}")
    return None


def validate_year(year: Any) -> Optional[int]:
    """
    Validate year is in reasonable range.

    Args:
        year: Year to validate (int or string)

    Returns:
        Validated year or None if invalid
    """
    if year is None:
        return None

    try:
        year_int = int(year)
        # Reasonable range: 1950-2030
        if 1950 <= year_int <= 2030:
            return year_int
    except (ValueError, TypeError):
        pass

    logger.warning(f"Invalid year: {year}")
    return None


def validate_date(date_str: Optional[str]) -> Optional[str]:
    """
    Validate and normalize date string.

    Args:
        date_str: Date string (e.g., "2020-01", "2020", "Present")

    Returns:
        Validated date or None if invalid
    """
    if not date_str:
        return None

    date_str = str(date_str).strip()

    # Allow "Present", "Current", etc.
    if date_str.lower() in ['present', 'current', 'now']:
        return 'Present'

    # Validate YYYY or YYYY-MM format
    if re.match(r'^\d{4}$', date_str):
        year = validate_year(date_str)
        return date_str if year else None

    if re.match(r'^\d{4}-\d{2}$', date_str):
        year = validate_year(date_str[:4])
        month = int(date_str[5:7])
        if year and 1 <= month <= 12:
            return date_str

    logger.warning(f"Invalid date format: {date_str}")
    return None


def validate_personal_info(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate personal information fields.

    Args:
        data: Personal info dict from LLM

    Returns:
        Validated personal info dict
    """
    validated = {}

    # Name fields (required)
    first_name = data.get('first_name', '').strip() if isinstance(data.get('first_name'), str) and data.get('first_name') else None
    last_name = data.get('last_name', '').strip() if isinstance(data.get('last_name'), str) and data.get('last_name') else None

    if first_name:
        validated['first_name'] = first_name
    if last_name:
        validated['last_name'] = last_name

    # Location (optional) - handle both string and dict formats
    location_raw = data.get('location')
    if location_raw:
        if isinstance(location_raw, str):
            validated['location'] = location_raw.strip()
        elif isinstance(location_raw, dict):
            # Convert dict to string format "City, Country"
            city = location_raw.get('city', '')
            country = location_raw.get('country', '')
            if city and country:
                validated['location'] = f"{city}, {country}"
            elif city:
                validated['location'] = city
            elif country:
                validated['location'] = country

    return validated


def validate_experience(experience_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate experience entries.

    Args:
        experience_list: List of experience dicts from LLM

    Returns:
        List of validated experience dicts
    """
    validated = []

    for exp in experience_list:
        if not isinstance(exp, dict):
            continue

        validated_exp = {}

        # Required fields
        title = exp.get('title', '').strip() if exp.get('title') else None
        company = exp.get('company', '').strip() if exp.get('company') else None

        if not title or not company:
            logger.warning(f"Skipping experience entry missing title or company: {exp}")
            continue

        validated_exp['title'] = title
        validated_exp['company'] = company

        # Optional fields
        if exp.get('location') and isinstance(exp.get('location'), str):
            validated_exp['location'] = exp['location'].strip()

        # Dates
        start_date = validate_date(exp.get('start_date'))
        end_date = validate_date(exp.get('end_date'))

        if start_date:
            validated_exp['start_date'] = start_date
        if end_date:
            validated_exp['end_date'] = end_date

        # Responsibilities
        responsibilities = exp.get('responsibilities', [])
        if isinstance(responsibilities, list) and responsibilities:
            validated_exp['responsibilities'] = [r.strip() for r in responsibilities if r and isinstance(r, str)]

        validated.append(validated_exp)

    logger.info(f"Validated {len(validated)}/{len(experience_list)} experience entries")
    return validated


def validate_education(education_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate education entries.

    Args:
        education_list: List of education dicts from LLM

    Returns:
        List of validated education dicts
    """
    validated = []

    for edu in education_list:
        if not isinstance(edu, dict):
            continue

        validated_edu = {}

        # Required fields
        degree = edu.get('degree', '').strip() if edu.get('degree') else None
        institution = edu.get('institution', '').strip() if edu.get('institution') else None

        if not degree or not institution:
            logger.warning(f"Skipping education entry missing degree or institution: {edu}")
            continue

        validated_edu['degree'] = degree
        validated_edu['institution'] = institution

        # Optional fields
        if edu.get('location') and isinstance(edu.get('location'), str):
            validated_edu['location'] = edu['location'].strip()

        # Dates
        start_date = validate_date(edu.get('start_date'))
        end_date = validate_date(edu.get('end_date'))

        if start_date:
            validated_edu['start_date'] = start_date
        if end_date:
            validated_edu['end_date'] = end_date

        # Status
        if edu.get('status') and isinstance(edu.get('status'), str):
            validated_edu['status'] = edu['status'].strip()

        validated.append(validated_edu)

    logger.info(f"Validated {len(validated)}/{len(education_list)} education entries")
    return validated


def validate_certifications(cert_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate certification entries.

    Args:
        cert_list: List of certification dicts from LLM

    Returns:
        List of validated certification dicts
    """
    validated = []

    for cert in cert_list:
        if not isinstance(cert, dict):
            continue

        name = cert.get('name', '').strip() if cert.get('name') else None
        if not name:
            continue

        validated_cert = {'name': name}

        if cert.get('issuer') and isinstance(cert.get('issuer'), str):
            validated_cert['issuer'] = cert['issuer'].strip()

        year = validate_year(cert.get('year'))
        if year:
            validated_cert['year'] = year

        validated.append(validated_cert)

    logger.info(f"Validated {len(validated)}/{len(cert_list)} certifications")
    return validated


def validate_languages(lang_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Validate language entries.

    Args:
        lang_list: List of language dicts from LLM

    Returns:
        List of validated language dicts
    """
    validated = []
    valid_proficiencies = ['native', 'fluent', 'professional', 'intermediate', 'basic']

    for lang in lang_list:
        if not isinstance(lang, dict):
            continue

        language = lang.get('language', '').strip() if lang.get('language') else None
        if not language:
            continue

        validated_lang = {'language': language}

        proficiency = lang.get('proficiency', '').strip().lower() if lang.get('proficiency') else None
        if proficiency and proficiency in valid_proficiencies:
            validated_lang['proficiency'] = proficiency.capitalize()
        else:
            validated_lang['proficiency'] = 'Professional'  # Default

        validated.append(validated_lang)

    logger.info(f"Validated {len(validated)}/{len(lang_list)} languages")
    return validated


def validate_skills(skills: List[str]) -> List[str]:
    """
    Validate and clean skills list.

    Args:
        skills: List of skill names from LLM

    Returns:
        List of validated skill names
    """
    if not isinstance(skills, list):
        logger.warning(f"Skills is not a list: {type(skills)}")
        return []

    validated = []
    for skill in skills:
        # Convert to string if needed (handles both str and non-str items)
        if not isinstance(skill, str):
            logger.warning(f"Skipping non-string skill: {skill} (type: {type(skill)})")
            continue

        skill_str = skill.strip()
        if skill_str:
            # Remove duplicates (case-insensitive)
            if skill_str.lower() not in [s.lower() for s in validated]:
                validated.append(skill_str)

    logger.info(f"Validated {len(validated)}/{len(skills)} skills")
    return validated
