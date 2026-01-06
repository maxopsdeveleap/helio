# Hellio HR - Database Schema Design

## Overview
This document defines the relational database schema for Hellio HR system. The schema normalizes candidate and position data while maintaining compatibility with the existing UI contract.

## Design Principles
1. **Normalize related data** - Separate repeating groups (skills, experience, education)
2. **Maintain JSON contract** - API responses should match Exercise 1 format
3. **Foreign key relationships** - Link candidates to positions
4. **Extensibility** - Design for future features (document versioning, candidate updates)

## Entity Relationship Diagram

```
candidates (1) ----< (N) candidate_skills
candidates (1) ----< (N) candidate_experience
candidates (1) ----< (N) candidate_education
candidates (1) ----< (N) candidate_certifications
candidates (1) ----< (N) candidate_languages
candidates (N) ----< (N) candidate_positions ----< (1) positions
candidates (1) ----< (N) cv_documents
```

## Tables

### 1. candidates
Primary table for candidate information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(50) | PRIMARY KEY | Unique identifier (candidate_001) |
| status | VARCHAR(20) | NOT NULL | Active, Inactive, etc. |
| first_name | VARCHAR(100) | NOT NULL | First name |
| last_name | VARCHAR(100) | NOT NULL | Last name |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email address |
| phone | VARCHAR(50) | | Phone number |
| location | VARCHAR(255) | | City, Country |
| linkedin | VARCHAR(255) | | LinkedIn profile URL |
| github | VARCHAR(255) | | GitHub profile URL |
| summary | TEXT | | Professional summary |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation time |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update time |

**Indexes:**
- email (unique)
- status
- (first_name, last_name)

---

### 2. candidate_skills
Many-to-many relationship for candidate skills.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| candidate_id | VARCHAR(50) | FOREIGN KEY | References candidates(id) |
| skill_name | VARCHAR(100) | NOT NULL | Skill name (Git, Python, etc.) |

**Indexes:**
- candidate_id
- skill_name

**Note:** We use a simple list approach rather than a separate skills table since skill names are straightforward.

---

### 3. candidate_experience
Work experience history.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| candidate_id | VARCHAR(50) | FOREIGN KEY | References candidates(id) |
| title | VARCHAR(255) | NOT NULL | Job title |
| company | VARCHAR(255) | NOT NULL | Company name |
| location | VARCHAR(255) | | Job location |
| start_date | VARCHAR(50) | | Start date (flexible format) |
| end_date | VARCHAR(50) | | End date or "Present" |
| responsibilities | TEXT[] | | Array of responsibility descriptions |
| order_index | INTEGER | DEFAULT 0 | Display order (0 = most recent) |

**Indexes:**
- candidate_id
- (candidate_id, order_index)

---

### 4. candidate_education
Educational background.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| candidate_id | VARCHAR(50) | FOREIGN KEY | References candidates(id) |
| degree | VARCHAR(255) | NOT NULL | Degree name |
| field_of_study | VARCHAR(255) | | Major/field |
| institution | VARCHAR(255) | NOT NULL | School/university name |
| start_date | VARCHAR(50) | | Start date |
| end_date | VARCHAR(50) | | End date or "Present" |
| status | VARCHAR(50) | | In Progress, Completed |
| order_index | INTEGER | DEFAULT 0 | Display order |

**Indexes:**
- candidate_id
- (candidate_id, order_index)

---

### 5. candidate_certifications
Professional certifications.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| candidate_id | VARCHAR(50) | FOREIGN KEY | References candidates(id) |
| name | VARCHAR(255) | NOT NULL | Certification name |
| issuer | VARCHAR(255) | NOT NULL | Issuing organization |
| year | INTEGER | | Year obtained |

**Indexes:**
- candidate_id

---

### 6. candidate_languages
Language proficiencies.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| candidate_id | VARCHAR(50) | FOREIGN KEY | References candidates(id) |
| language | VARCHAR(100) | NOT NULL | Language name |
| proficiency | VARCHAR(50) | NOT NULL | Native, Professional, Conversational |

**Indexes:**
- candidate_id

---

### 7. positions
Job position openings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(50) | PRIMARY KEY | Unique identifier (position_001) |
| status | VARCHAR(20) | NOT NULL | Open, Closed, On Hold |
| title | VARCHAR(255) | NOT NULL | Position title |
| company | VARCHAR(255) | NOT NULL | Company name |
| location | VARCHAR(255) | | Position location |
| work_arrangement | VARCHAR(100) | | Remote, Hybrid, Office |
| experience | VARCHAR(100) | | Required experience level |
| description | TEXT | NOT NULL | Position description |
| compensation | VARCHAR(255) | | Salary/compensation info |
| timeline | VARCHAR(100) | | Hiring timeline |
| urgency | VARCHAR(20) | | Critical, High, Medium, Low |
| contact_person_name | VARCHAR(255) | | Contact name |
| contact_person_title | VARCHAR(255) | | Contact title |
| contact_person_email | VARCHAR(255) | | Contact email |
| notes | TEXT | | Additional notes |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation time |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update time |

**Indexes:**
- status
- urgency
- company

---

### 8. position_requirements
Position requirements (many-to-many style).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| position_id | VARCHAR(50) | FOREIGN KEY | References positions(id) |
| requirement | TEXT | NOT NULL | Requirement description |
| is_required | BOOLEAN | DEFAULT true | Required vs Nice-to-have |
| order_index | INTEGER | DEFAULT 0 | Display order |

**Indexes:**
- position_id
- (position_id, is_required, order_index)

---

### 9. position_responsibilities
Position responsibilities.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| position_id | VARCHAR(50) | FOREIGN KEY | References positions(id) |
| responsibility | TEXT | NOT NULL | Responsibility description |
| order_index | INTEGER | DEFAULT 0 | Display order |

**Indexes:**
- position_id
- (position_id, order_index)

---

### 10. position_skills
Skills required for position.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| position_id | VARCHAR(50) | FOREIGN KEY | References positions(id) |
| skill_name | VARCHAR(100) | NOT NULL | Skill name |

**Indexes:**
- position_id
- skill_name

---

### 11. candidate_positions
Many-to-many relationship linking candidates to positions they've applied for.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| candidate_id | VARCHAR(50) | FOREIGN KEY | References candidates(id) |
| position_id | VARCHAR(50) | FOREIGN KEY | References positions(id) |
| application_status | VARCHAR(50) | | Applied, Screening, Interview, Offer, Rejected |
| applied_at | TIMESTAMP | DEFAULT NOW() | Application date |
| notes | TEXT | | Application notes |

**Indexes:**
- (candidate_id, position_id) UNIQUE
- candidate_id
- position_id

---

### 12. cv_documents
CV file storage and versioning.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| candidate_id | VARCHAR(50) | FOREIGN KEY | References candidates(id) |
| file_path | TEXT | NOT NULL | Path to CV file |
| file_name | VARCHAR(255) | NOT NULL | Original filename |
| file_type | VARCHAR(50) | | PDF, DOCX, etc. |
| version | INTEGER | DEFAULT 1 | Version number |
| is_current | BOOLEAN | DEFAULT true | Current version flag |
| uploaded_at | TIMESTAMP | DEFAULT NOW() | Upload timestamp |

**Indexes:**
- candidate_id
- (candidate_id, is_current)

---

## SQL Schema Creation Script

See `backend/migrations/001_initial_schema.sql` for the complete DDL.

---

## Data Migration Strategy

1. **Load existing JSON data** - Parse candidate_001.json, candidate_002.json, candidate_003.json
2. **Insert candidates** - Main candidate info into `candidates` table
3. **Insert related data** - Skills, experience, education, languages, certifications
4. **Load positions** - Position JSON files into `positions` and related tables
5. **Link CV files** - Insert records into `cv_documents` with file paths

---

## API Response Format

The backend API will reconstruct the JSON format from Exercise 1 by joining tables:

```sql
-- Example: Get candidate with all related data
SELECT
  c.*,
  array_agg(DISTINCT cs.skill_name) as skills,
  json_agg(DISTINCT ce.*) as experience,
  json_agg(DISTINCT ced.*) as education,
  -- etc.
FROM candidates c
LEFT JOIN candidate_skills cs ON c.id = cs.candidate_id
LEFT JOIN candidate_experience ce ON c.id = ce.candidate_id
LEFT JOIN candidate_education ced ON c.id = ced.candidate_id
WHERE c.id = 'candidate_001'
GROUP BY c.id;
```

This ensures the UI receives the same data structure as Exercise 1.

---

## Future Considerations

**For Exercise 3+:**
- Full-text search indexes on candidate summaries and position descriptions
- Candidate search history table
- Document parsing metadata (extracted text, entities)
- Audit log table for tracking changes

**Performance:**
- Add indexes as query patterns emerge
- Consider materialized views for complex aggregations
- Partition large tables by date if needed
