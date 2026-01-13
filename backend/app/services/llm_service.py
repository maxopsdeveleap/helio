"""
LLM Service for parsing and extracting structured data
"""
from app.services.llm_client import get_llm_client
import json


def parse_position_details(title: str, description: str) -> dict:
    """
    Use LLM to parse job position details from email text.

    Args:
        title: Email subject or position title
        description: Email body with position details

    Returns:
        Structured position data
    """
    client = get_llm_client()

    prompt = f"""Parse the following job position information and extract structured data.

Position Title: {title}

Description:
{description}

Return ONLY a valid JSON object (not an array) with this exact structure:
{{
    "title": "Job title",
    "summary": "2-3 sentence summary of the role",
    "location": "City, Country",
    "work_arrangement": "Remote/Hybrid/On-site",
    "experience": "X-Y years",
    "urgency": "Low/Medium/High/Critical",
    "requirements": ["requirement 1", "requirement 2", ...],
    "responsibilities": ["responsibility 1", "responsibility 2", ...],
    "skills": ["skill 1", "skill 2", ...]
}}

IMPORTANT:
- Return ONLY the JSON object, no other text
- Requirements should be specific qualifications needed
- Responsibilities should be day-to-day tasks
- Skills should be technical skills or tools
- Do not wrap in markdown code blocks"""

    # Use generate() and manually parse JSON to avoid issues with extract_json finding arrays first
    try:
        response_text = client.generate(prompt, max_tokens=2048)
        print(f"LLM raw response: {response_text[:500]}")

        # Clean up the response
        response_text = response_text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()

        # Find the JSON object (starts with {, ends with })
        start_idx = response_text.find('{')
        if start_idx == -1:
            raise ValueError(f"No JSON object found in response: {response_text[:200]}")

        # Count braces to find the matching closing brace
        brace_count = 0
        in_string = False
        escape_next = False

        for i in range(start_idx, len(response_text)):
            char = response_text[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_text = response_text[start_idx:i+1]
                        parsed = json.loads(json_text)
                        print(f"LLM parsed result: {parsed}")

                        # Verify it's a dict
                        if not isinstance(parsed, dict):
                            raise ValueError(f"Parsed result is {type(parsed)}, not dict")

                        return parsed

        raise ValueError(f"Could not find complete JSON object in response")

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        raise ValueError(f"Failed to decode JSON: {e}")
    except Exception as e:
        print(f"LLM extraction error: {e}")
        raise ValueError(f"Failed to extract JSON from LLM: {e}")
