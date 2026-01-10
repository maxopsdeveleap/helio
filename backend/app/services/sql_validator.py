"""
SQL validation and safety checks.
Ensures LLM-generated SQL is safe and read-only.
"""
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Dangerous SQL keywords that should never appear
FORBIDDEN_KEYWORDS = [
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
    'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE',
    'COMMIT', 'ROLLBACK', 'SAVEPOINT'
]


def validate_sql(sql: str) -> Tuple[bool, str]:
    """
    Validate that SQL is safe and read-only.

    Args:
        sql: SQL query to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if SQL is safe, False otherwise
        - error_message: Empty string if valid, error description if invalid
    """
    if not sql or not sql.strip():
        return False, "SQL query is empty"

    sql_upper = sql.upper().strip()

    # Check 1: Must start with SELECT
    if not sql_upper.startswith('SELECT'):
        return False, "Query must start with SELECT (read-only queries only)"

    # Check 2: No semicolons (prevents multiple statements)
    if ';' in sql.rstrip(';'):  # Allow trailing semicolon
        return False, "Multiple SQL statements not allowed (semicolon detected)"

    # Check 3: No forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        # Use word boundaries to avoid false positives (e.g., "UPDATE" in a column name)
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, sql_upper):
            return False, f"Forbidden keyword detected: {keyword}"

    # Check 4: Basic syntax check - must contain FROM (for most queries)
    # Note: Some valid queries like "SELECT 1" don't have FROM, so this is optional
    # if 'FROM' not in sql_upper:
    #     return False, "Query must contain FROM clause"

    logger.info(f"SQL validation passed: {sql[:100]}...")
    return True, ""


def sanitize_sql(sql: str) -> str:
    """
    Clean and normalize SQL query.

    Args:
        sql: Raw SQL query

    Returns:
        Cleaned SQL query
    """
    # Remove markdown code blocks if present
    sql = sql.strip()
    if sql.startswith('```'):
        lines = sql.split('\n')
        sql = '\n'.join(lines[1:-1]) if len(lines) > 2 else sql
        sql = sql.strip()

    # Remove 'sql' or 'SQL' prefix if present after code block removal
    if sql.lower().startswith('sql'):
        sql = sql[3:].strip()

    # Remove trailing semicolon
    sql = sql.rstrip(';')

    return sql
