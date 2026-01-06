-- Hellio HR Database Schema
-- This file is for reference and manual initialization if needed
-- SQLAlchemy will auto-create tables from models

-- Enable UUID extension if needed in future
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create candidates table
CREATE TABLE IF NOT EXISTS candidates (
    id VARCHAR(50) PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    location VARCHAR(255),
    linkedin VARCHAR(255),
    github VARCHAR(255),
    summary TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(first_name, last_name);

-- Create candidate_skills table
CREATE TABLE IF NOT EXISTS candidate_skills (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    skill_name VARCHAR(100) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_candidate_skills_candidate ON candidate_skills(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_skills_skill ON candidate_skills(skill_name);

-- Create candidate_experience table
CREATE TABLE IF NOT EXISTS candidate_experience (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    start_date VARCHAR(50),
    end_date VARCHAR(50),
    responsibilities TEXT[],
    order_index INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_candidate_experience_candidate ON candidate_experience(candidate_id);

-- Create candidate_education table
CREATE TABLE IF NOT EXISTS candidate_education (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    degree VARCHAR(255) NOT NULL,
    field_of_study VARCHAR(255),
    institution VARCHAR(255) NOT NULL,
    start_date VARCHAR(50),
    end_date VARCHAR(50),
    status VARCHAR(50),
    order_index INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_candidate_education_candidate ON candidate_education(candidate_id);

-- Create candidate_certifications table
CREATE TABLE IF NOT EXISTS candidate_certifications (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    issuer VARCHAR(255) NOT NULL,
    year INTEGER
);

CREATE INDEX IF NOT EXISTS idx_candidate_certifications_candidate ON candidate_certifications(candidate_id);

-- Create candidate_languages table
CREATE TABLE IF NOT EXISTS candidate_languages (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    language VARCHAR(100) NOT NULL,
    proficiency VARCHAR(50) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_candidate_languages_candidate ON candidate_languages(candidate_id);

-- Create positions table
CREATE TABLE IF NOT EXISTS positions (
    id VARCHAR(50) PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    work_arrangement VARCHAR(100),
    experience VARCHAR(100),
    description TEXT NOT NULL,
    compensation VARCHAR(255),
    timeline VARCHAR(100),
    urgency VARCHAR(20),
    contact_person_name VARCHAR(255),
    contact_person_title VARCHAR(255),
    contact_person_email VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_urgency ON positions(urgency);
CREATE INDEX IF NOT EXISTS idx_positions_company ON positions(company);

-- Create position_requirements table
CREATE TABLE IF NOT EXISTS position_requirements (
    id SERIAL PRIMARY KEY,
    position_id VARCHAR(50) NOT NULL REFERENCES positions(id) ON DELETE CASCADE,
    requirement TEXT NOT NULL,
    is_required BOOLEAN DEFAULT true,
    order_index INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_position_requirements_position ON position_requirements(position_id);

-- Create position_responsibilities table
CREATE TABLE IF NOT EXISTS position_responsibilities (
    id SERIAL PRIMARY KEY,
    position_id VARCHAR(50) NOT NULL REFERENCES positions(id) ON DELETE CASCADE,
    responsibility TEXT NOT NULL,
    order_index INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_position_responsibilities_position ON position_responsibilities(position_id);

-- Create position_skills table
CREATE TABLE IF NOT EXISTS position_skills (
    id SERIAL PRIMARY KEY,
    position_id VARCHAR(50) NOT NULL REFERENCES positions(id) ON DELETE CASCADE,
    skill_name VARCHAR(100) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_position_skills_position ON position_skills(position_id);
CREATE INDEX IF NOT EXISTS idx_position_skills_skill ON position_skills(skill_name);

-- Create candidate_positions table (many-to-many)
CREATE TABLE IF NOT EXISTS candidate_positions (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    position_id VARCHAR(50) NOT NULL REFERENCES positions(id) ON DELETE CASCADE,
    application_status VARCHAR(50),
    applied_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    UNIQUE(candidate_id, position_id)
);

CREATE INDEX IF NOT EXISTS idx_candidate_positions_candidate ON candidate_positions(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_positions_position ON candidate_positions(position_id);

-- Create cv_documents table
CREATE TABLE IF NOT EXISTS cv_documents (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    version INTEGER DEFAULT 1,
    is_current BOOLEAN DEFAULT true,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cv_documents_candidate ON cv_documents(candidate_id);
CREATE INDEX IF NOT EXISTS idx_cv_documents_current ON cv_documents(candidate_id, is_current);
