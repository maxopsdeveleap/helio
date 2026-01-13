from .database import Base, engine, get_db, SessionLocal
from .candidate import (
    Candidate,
    CandidateSkill,
    CandidateExperience,
    CandidateEducation,
    CandidateCertification,
    CandidateLanguage,
    CVDocument
)
from .position import (
    Position,
    PositionRequirement,
    PositionResponsibility,
    PositionSkill,
    CandidatePosition
)

# Create all tables and run migrations
def init_db():
    import os
    from pathlib import Path
    from sqlalchemy import text

    # Create tables from models
    Base.metadata.create_all(bind=engine)

    # Run SQL migrations
    migrations_dir = Path(__file__).parent.parent.parent / "migrations"
    if migrations_dir.exists():
        migration_files = sorted(migrations_dir.glob("*.sql"))

        with SessionLocal() as db:
            for migration_file in migration_files:
                try:
                    print(f"Running migration: {migration_file.name}")
                    with open(migration_file, 'r') as f:
                        sql = f.read()
                        # Split by semicolon and execute each statement
                        statements = [s.strip() for s in sql.split(';') if s.strip()]
                        for statement in statements:
                            db.execute(text(statement))
                        db.commit()
                    print(f"✅ Migration {migration_file.name} completed")
                except Exception as e:
                    print(f"⚠️  Migration {migration_file.name} failed or already applied: {e}")
                    db.rollback()
