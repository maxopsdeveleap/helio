"""
LLM-based extraction functions for candidate data.
Uses AI to extract structured information from unstructured CV text.
"""
import logging
from typing import Dict, List, Any, Optional
from .llm_client import get_llm_client, LLMClient

logger = logging.getLogger(__name__)


class CVExtractor:
    """Extract structured candidate data from CV text using LLMs"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize CV extractor.

        Args:
            llm_client: LLM client to use (defaults to auto-configured client)
        """
        self.llm = llm_client or get_llm_client()

    def extract_personal_info(self, text: str) -> Dict[str, Any]:
        """
        Extract personal information (name, location) from CV text.

        Args:
            text: CV text

        Returns:
            Dict with personal info fields
        """
        prompt = f"""Extract the following personal information from this CV text:
- first_name
- last_name
- location (city, country)

CV Text:
{text[:2000]}

Return valid JSON with these fields. If a field cannot be determined, use null."""

        try:
            data = self.llm.extract_json(prompt)
            logger.info(f"Extracted personal info: {data.get('first_name')} {data.get('last_name')}")
            return data
        except Exception as e:
            logger.error(f"Failed to extract personal info: {e}")
            return {}

    def extract_skills(self, text: str) -> List[str]:
        """
        Extract technical skills from CV text.

        Args:
            text: CV text

        Returns:
            List of skill names
        """
        prompt = f"""Extract all technical skills from this CV. Include:
- Programming languages
- Frameworks and libraries
- Tools and technologies
- Cloud platforms
- Methodologies (Agile, DevOps, etc.)

CV Text:
{text}

Return JSON array of skill names only. Example: ["Python", "Docker", "AWS"]"""

        try:
            data = self.llm.extract_json(prompt)

            # Handle different response formats
            if isinstance(data, list):
                skills = data
            elif isinstance(data, dict):
                # If dict has a 'skills' key, use that
                if 'skills' in data:
                    skills = data['skills']
                else:
                    # Flatten nested dict structure (e.g., {'programming_languages': [...], 'frameworks': [...]})
                    skills = []
                    for key, value in data.items():
                        if isinstance(value, list):
                            skills.extend(value)
                        elif isinstance(value, str):
                            skills.append(value)
                    logger.info(f"Flattened nested skills dict with keys: {list(data.keys())}")
            else:
                logger.warning(f"Unexpected skills format: {data}")
                skills = []

            logger.info(f"Extracted {len(skills)} skills")
            return skills

        except Exception as e:
            logger.error(f"Failed to extract skills: {e}")
            return []

    def extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract work experience from CV text.

        Args:
            text: CV text

        Returns:
            List of experience entries
        """
        prompt = f"""Extract work experience from this CV. For each position, extract:
- title (job title)
- company (company name)
- location (city, country if available)
- start_date (format: YYYY-MM or YYYY)
- end_date (format: YYYY-MM or YYYY, or "Present")
- responsibilities (list of 3-5 key responsibilities/achievements)

CV Text:
{text}

Return JSON array of experience objects. Order by most recent first."""

        try:
            data = self.llm.extract_json(prompt)

            # Handle both direct array and {"experience": [...]} format
            if isinstance(data, list):
                experience = data
            elif isinstance(data, dict) and 'experience' in data:
                experience = data['experience']
            else:
                logger.warning(f"Unexpected experience format: {data}")
                experience = []

            logger.info(f"Extracted {len(experience)} experience entries")
            return experience

        except Exception as e:
            logger.error(f"Failed to extract experience: {e}")
            return []

    def extract_education(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract education from CV text.

        Args:
            text: CV text

        Returns:
            List of education entries
        """
        prompt = f"""Extract education from this CV. For each degree, extract:
- degree (e.g., "Bachelor of Science in Computer Science")
- institution (university/school name)
- location (city, country if available)
- start_date (format: YYYY)
- end_date (format: YYYY)
- status ("Completed", "In Progress", "Expected YYYY")

CV Text:
{text}

Return JSON array of education objects. Order by most recent first."""

        try:
            data = self.llm.extract_json(prompt)

            # Handle both direct array and {"education": [...]} format
            if isinstance(data, list):
                education = data
            elif isinstance(data, dict) and 'education' in data:
                education = data['education']
            else:
                logger.warning(f"Unexpected education format: {data}")
                education = []

            logger.info(f"Extracted {len(education)} education entries")
            return education

        except Exception as e:
            logger.error(f"Failed to extract education: {e}")
            return []

    def extract_certifications(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract certifications from CV text.

        Args:
            text: CV text

        Returns:
            List of certification entries
        """
        prompt = f"""Extract certifications from this CV. For each certification, extract:
- name (certification name)
- issuer (issuing organization)
- year (year obtained, if available)

CV Text:
{text}

Return JSON array of certification objects. If no certifications found, return empty array []."""

        try:
            data = self.llm.extract_json(prompt)

            # Handle both direct array and {"certifications": [...]} format
            if isinstance(data, list):
                certifications = data
            elif isinstance(data, dict) and 'certifications' in data:
                certifications = data['certifications']
            else:
                logger.warning(f"Unexpected certifications format: {data}")
                certifications = []

            logger.info(f"Extracted {len(certifications)} certifications")
            return certifications

        except Exception as e:
            logger.error(f"Failed to extract certifications: {e}")
            return []

    def extract_languages(self, text: str) -> List[Dict[str, str]]:
        """
        Extract languages from CV text.

        Args:
            text: CV text

        Returns:
            List of language entries with proficiency
        """
        prompt = f"""Extract languages and proficiency levels from this CV. For each language, extract:
- language (language name)
- proficiency ("Native", "Fluent", "Professional", "Intermediate", "Basic")

CV Text:
{text}

Return JSON array of language objects. If no languages found, return empty array []."""

        try:
            data = self.llm.extract_json(prompt)

            # Handle both direct array and {"languages": [...]} format
            if isinstance(data, list):
                languages = data
            elif isinstance(data, dict) and 'languages' in data:
                languages = data['languages']
            else:
                logger.warning(f"Unexpected languages format: {data}")
                languages = []

            logger.info(f"Extracted {len(languages)} languages")
            return languages

        except Exception as e:
            logger.error(f"Failed to extract languages: {e}")
            return []

    def generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate a concise summary of the candidate profile.

        Args:
            text: CV text
            max_sentences: Maximum number of sentences in summary

        Returns:
            Summary text
        """
        prompt = f"""Write a concise {max_sentences}-sentence professional summary for this candidate suitable for a recruiter.
Focus on:
- Current role and years of experience
- Key technical skills and expertise
- Notable achievements or specializations

CV Text:
{text[:3000]}

Write the summary as plain text, not JSON."""

        try:
            summary = self.llm.generate(prompt, max_tokens=200)
            summary = summary.strip()
            logger.info(f"Generated summary ({len(summary)} chars)")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return ""

    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        Extract all candidate data from CV text.

        Args:
            text: CV text

        Returns:
            Dict with all extracted fields
        """
        logger.info("Starting full CV extraction...")

        result = {
            'personal_info': self.extract_personal_info(text),
            'skills': self.extract_skills(text),
            'experience': self.extract_experience(text),
            'education': self.extract_education(text),
            'certifications': self.extract_certifications(text),
            'languages': self.extract_languages(text),
            'summary': self.generate_summary(text),
        }

        logger.info("Completed full CV extraction")
        return result
