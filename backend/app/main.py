from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import init_db

# Create FastAPI app
app = FastAPI(
    title="Hellio HR API",
    description="Intelligent Hiring Operations Assistant API",
    version="1.0.0"
)

# Configure CORS (allow frontend to call backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Database tables created successfully")

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Hellio HR API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Import and include routers (we'll create these next)
from app.api import candidates, positions

app.include_router(candidates.router, prefix="/api/candidates", tags=["Candidates"])
app.include_router(positions.router, prefix="/api/positions", tags=["Positions"])
