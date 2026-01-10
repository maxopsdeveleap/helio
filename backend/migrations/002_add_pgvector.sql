-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to candidates table
-- Using vector(1024) to match Voyage AI embedding dimensions
ALTER TABLE candidates
ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- Add embedding column to positions table
ALTER TABLE positions
ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- Create index for fast similarity search on candidates
-- Using ivfflat index with cosine distance operator
CREATE INDEX IF NOT EXISTS idx_candidates_embedding
ON candidates
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for fast similarity search on positions
CREATE INDEX IF NOT EXISTS idx_positions_embedding
ON positions
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Add embedding_text column to store what was embedded (for debugging)
ALTER TABLE candidates
ADD COLUMN IF NOT EXISTS embedding_text TEXT;

ALTER TABLE positions
ADD COLUMN IF NOT EXISTS embedding_text TEXT;
