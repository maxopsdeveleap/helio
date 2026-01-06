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

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)
