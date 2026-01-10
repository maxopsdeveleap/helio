"""
Database schema inspection for SQL-RAG.
Extracts table and column information to provide context to LLM.
"""
import logging
from typing import Dict, List
from sqlalchemy import inspect, text
from app.models.database import engine

logger = logging.getLogger(__name__)


def get_database_schema() -> str:
    """
    Get formatted database schema for LLM context.

    Returns:
        String representation of database schema with tables and columns
    """
    inspector = inspect(engine)
    schema_parts = []

    # Get all table names
    tables = inspector.get_table_names()
    logger.info(f"Found {len(tables)} tables in database")

    for table_name in tables:
        # Get columns for this table
        columns = inspector.get_columns(table_name)

        # Format table schema
        table_schema = f"\nTable: {table_name}\n"
        table_schema += "Columns:\n"

        for col in columns:
            col_type = str(col['type'])
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            table_schema += f"  - {col['name']} ({col_type}) {nullable}\n"

        schema_parts.append(table_schema)

    schema_text = "".join(schema_parts)
    logger.debug(f"Generated schema:\n{schema_text}")

    return schema_text


def get_relevant_tables() -> List[str]:
    """
    Get list of relevant tables for HR queries.

    Returns:
        List of table names
    """
    # For now, return all tables. Later we can filter based on query intent.
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return tables
