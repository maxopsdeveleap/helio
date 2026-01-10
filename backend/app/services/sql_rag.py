"""
SQL-RAG service: Natural language to SQL to grounded answers.
Two-step pipeline:
1. Generate SQL from question
2. Generate answer from SQL results
"""
import logging
from typing import Dict, Any, List
from sqlalchemy import text
from app.models.database import SessionLocal
from app.services.llm_client import get_llm_client
from app.services.schema_inspector import get_database_schema
from app.services.sql_validator import validate_sql, sanitize_sql

logger = logging.getLogger(__name__)


class SQLRAGService:
    """SQL-RAG service for natural language database queries"""

    def __init__(self):
        self.llm = get_llm_client()
        self.schema = get_database_schema()

    def generate_sql(self, question: str) -> str:
        """
        Generate SQL query from natural language question.

        Args:
            question: User's natural language question

        Returns:
            SQL query string
        """
        system_prompt = """You are a SQL expert for an HR recruitment database. Generate ONLY valid PostgreSQL SELECT queries.

CRITICAL SECURITY RULES:
- ONLY SELECT statements allowed - NEVER use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE
- NO semicolons (prevents SQL injection via statement chaining)
- NO EXEC, EXECUTE, or stored procedure calls
- Read-only queries ONLY

QUERY BEST PRACTICES:
- Always use LIMIT (default 100) to prevent huge result sets
- Use proper JOINs when querying multiple tables
- Use WHERE clauses for filtering
- Use aggregate functions (COUNT, SUM, AVG) for statistics
- Use ILIKE for case-insensitive text search
- Handle NULL values appropriately

OUTPUT FORMAT:
- Return ONLY the SQL query
- NO explanations, markdown, or code blocks
- NO comments in the SQL"""

        prompt = f"""Database Schema:
{self.schema}

Example queries:

Q: "List all candidates with Python skills"
A: SELECT c.id, c.first_name, c.last_name, c.email FROM candidates c JOIN candidate_skills cs ON c.id = cs.candidate_id WHERE cs.skill_name ILIKE '%Python%' LIMIT 100

Q: "How many open positions are there?"
A: SELECT COUNT(*) as open_positions FROM positions WHERE status = 'Open'

Q: "Which positions have no candidates?"
A: SELECT p.id, p.title, p.department FROM positions p LEFT JOIN applications a ON p.id = a.position_id WHERE a.id IS NULL LIMIT 100

User Question: {question}

Generate a PostgreSQL SELECT query to answer this question.
Return ONLY the SQL query, nothing else."""

        try:
            sql = self.llm.generate(prompt, system_prompt=system_prompt, max_tokens=500)
            sql = sanitize_sql(sql)
            logger.info(f"Generated SQL: {sql}")
            return sql
        except Exception as e:
            logger.error(f"Failed to generate SQL: {e}")
            raise ValueError(f"Failed to generate SQL query: {e}")

    def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.

        Args:
            sql: SQL query to execute

        Returns:
            List of rows as dictionaries

        Raises:
            ValueError: If SQL is invalid or execution fails
        """
        # Validate SQL safety
        is_valid, error_msg = validate_sql(sql)
        if not is_valid:
            logger.error(f"SQL validation failed: {error_msg}")
            raise ValueError(f"SQL validation failed: {error_msg}")

        # Execute query
        db = SessionLocal()
        try:
            result = db.execute(text(sql))
            rows = result.fetchall()

            # Convert to list of dicts
            if rows:
                columns = result.keys()
                results = [dict(zip(columns, row)) for row in rows]
            else:
                results = []

            logger.info(f"Query returned {len(results)} rows")
            return results

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise ValueError(f"SQL execution failed: {e}")

        finally:
            db.close()

    def generate_answer(self, question: str, sql: str, results: List[Dict[str, Any]]) -> str:
        """
        Generate natural language answer from SQL results.

        Args:
            question: Original question
            sql: SQL query that was executed
            results: Query results

        Returns:
            Natural language answer
        """
        system_prompt = """You are an HR assistant. Answer questions based ONLY on the provided query results.

CRITICAL GROUNDING RULES:
- Use ONLY data present in the query results - NO hallucinations or assumptions
- If results are empty, say "No matching records found" - do NOT invent data
- Do NOT add information not in the results (no job descriptions, skills, or details not shown)
- Do NOT make suggestions or recommendations beyond the data
- If asked for specifics not in results, say "This information is not available in the current data"

FORMATTING RULES:
- Be concise and direct
- For counts/statistics: state the number clearly
- For lists: format as bullet points if more than 3 items
- For single records: present key fields in a sentence
- Always cite the data: "The query found X records..." or "According to the database..."

TONE:
- Professional and factual
- No marketing language or enthusiasm
- Objective reporting only"""

        # Limit results to prevent token overflow
        results_preview = results[:50] if len(results) > 50 else results

        # Handle empty results
        if not results:
            return "No matching records found in the database."

        prompt = f"""Question: {question}

SQL Query Executed:
{sql}

Query Results ({len(results)} total rows):
{results_preview}

Provide a clear, factual answer based ONLY on these results. Do not add any information not present in the data."""

        try:
            answer = self.llm.generate(prompt, system_prompt=system_prompt, max_tokens=1000)
            logger.info(f"Generated answer ({len(answer)} chars)")
            return answer.strip()
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise ValueError(f"Failed to generate answer: {e}")

    def classify_question(self, question: str) -> tuple[str, str]:
        """
        Use LLM to classify if question is clear, vague, or conversational.

        Args:
            question: User's question

        Returns:
            Tuple of (category, suggested_response)
            category: 'clear', 'vague', or 'conversational'
        """
        system_prompt = """You are a question classifier for an HR database chatbot. Classify user questions into exactly one category:

CONVERSATIONAL: Greetings, small talk, questions about the bot itself
Examples: "hi", "how are you", "what can you do", "help", "who are you"

VAGUE: Questions missing key information needed to query the database
Examples: "give me a list", "show me", "tell me about", "what do you have", "provide information"

CLEAR: Specific questions that can be answered by querying candidates or positions
Examples: "list candidates with Python", "how many open positions", "show me engineers"

Respond with ONLY one word: CONVERSATIONAL, VAGUE, or CLEAR"""

        prompt = f'User question: "{question}"\n\nClassify this question:'

        try:
            classification = self.llm.generate(prompt, system_prompt=system_prompt, max_tokens=10).strip().upper()

            if "CONVERSATIONAL" in classification:
                return "conversational", "Hello! I can help you query the HR database. I can answer questions about candidates (their skills, experience, location) and positions (open roles, departments, requirements). Try asking something like 'List all candidates with Python skills' or 'How many open positions are there?'"

            elif "VAGUE" in classification:
                return "vague", "I'd be happy to help! Could you be more specific? For example, you can ask about:\n• Candidates (skills, experience, location)\n• Positions (open roles, departments, requirements)\n• Analytics (counts, statistics, comparisons)\n\nTry something like: 'Show me candidates with Python skills' or 'How many open positions are there?'"

            else:
                return "clear", ""

        except Exception as e:
            logger.error(f"Question classification failed: {e}")
            # If classification fails, assume question is clear and let it proceed
            return "clear", ""

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Answer a natural language question using SQL-RAG.

        Args:
            question: Natural language question

        Returns:
            Dict with answer, SQL, and trace information
        """
        logger.info(f"Processing question: {question}")

        # Classify the question using LLM
        category, clarification = self.classify_question(question)

        if category in ["conversational", "vague"]:
            logger.info(f"Question classified as {category}, returning clarification")
            return {
                "answer": clarification,
                "sql": None,
                "row_count": 0,
                "results": [],
                "trace": None
            }

        try:
            # Step 1: Generate SQL
            sql = self.generate_sql(question)

            # Step 2: Execute SQL
            results = self.execute_sql(sql)

            # Step 3: Generate answer
            answer = self.generate_answer(question, sql, results)

            return {
                "answer": answer,
                "sql": sql,
                "row_count": len(results),
                "results": results[:10],  # Return first 10 rows for transparency
                "trace": {
                    "question": question,
                    "sql": sql,
                    "row_count": len(results),
                    "columns": list(results[0].keys()) if results else []
                }
            }

        except ValueError as e:
            # Handle validation errors with user-friendly messages
            error_msg = str(e)
            if "must start with SELECT" in error_msg:
                return {
                    "answer": "I can only answer questions that retrieve information from the database. I cannot modify, delete, or create data. Please ask a question about existing candidates or positions.",
                    "sql": None,
                    "row_count": 0,
                    "results": [],
                    "trace": None
                }
            elif "validation failed" in error_msg.lower():
                return {
                    "answer": "I couldn't generate a valid database query for that question. Please try rephrasing it, or use one of the example questions below.",
                    "sql": None,
                    "row_count": 0,
                    "results": [],
                    "trace": None
                }
            else:
                return {
                    "answer": "I had trouble processing that question. Please try rephrasing it or ask something like: 'List candidates with Python skills' or 'How many open positions are there?'",
                    "sql": None,
                    "row_count": 0,
                    "results": [],
                    "trace": None
                }

        except Exception as e:
            logger.error(f"SQL-RAG failed: {e}")
            return {
                "answer": "I encountered an unexpected error processing your question. Please try rephrasing it or use one of the example questions.",
                "sql": None,
                "row_count": 0,
                "results": [],
                "trace": None
            }
