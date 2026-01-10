# CV Ingestion Setup Guide

## Prerequisites

1. **Get your Anthropic API Key**
   - Visit: https://console.anthropic.com/
   - Create an account or sign in
   - Navigate to API Keys section
   - Create a new API key

2. **Add API key to `.env` file**
   ```bash
   cd /home/develeap/hellio-hr-max
   echo "ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE" >> .env
   ```

## Installation

1. **Restart Docker containers** to install new dependencies:
   ```bash
   cd /home/develeap/hellio-hr-max
   docker compose down
   docker compose up -d --build
   ```

2. **Verify installation**:
   ```bash
   docker exec hellio_backend python -c "import PyPDF2; import docx; import anthropic; print('All packages installed!')"
   ```

## Usage

### Ingest a CV

```bash
# Auto-generate candidate ID
docker exec hellio_backend python /app/scripts/ingest_cv.py /app/data/cvs/new_candidate.pdf

# Specify custom candidate ID
docker exec hellio_backend python /app/scripts/ingest_cv.py /app/data/cvs/new_candidate.pdf --candidate-id candidate_004

# Enable debug logging
docker exec hellio_backend python /app/scripts/ingest_cv.py /app/data/cvs/new_candidate.pdf --debug
```

### What Happens During Ingestion

```
PDF/DOCX → Parse Text → Heuristics → LLM Extraction → Validation → Database
           (2000 chars)  (email,      (skills,        (check      (candidate
                          phone)       experience)     formats)     record)
```

**Step 1:** Parse document (PDF or DOCX) to extract plain text
**Step 2:** Run heuristic extractors (regex for email, phone, URLs)
**Step 3:** Run LLM extractors (AI extracts skills, experience, education, summary)
**Step 4:** Validate all extracted data (format checking, required fields)
**Step 5:** Store in database (insert into 12 normalized tables)

### Cost Tracking

Typical CV ingestion costs with Claude 3.5 Sonnet:
- Input: ~2000-3000 tokens (~$0.003-0.009)
- Output: ~1000-1500 tokens (~$0.015-0.022)
- **Total per CV: ~$0.018-0.031**

Processing 100 CVs ≈ $2-3

### Troubleshooting

**Error: "ANTHROPIC_API_KEY not found"**
- Make sure you added the API key to `.env` file
- Restart Docker containers after modifying `.env`

**Error: "PyPDF2 module not found"**
- Run `docker compose down && docker compose up -d --build` to rebuild containers

**Error: "Could not extract name from CV"**
- CV format may be unusual (images, scanned PDFs won't work)
- Try a different CV or manually create JSON

**Error: "Candidate already exists"**
- Use `--candidate-id` to specify a different ID
- Or delete existing candidate from database first

## Testing

### Test with a sample CV

1. Find or create a sample CV PDF
2. Place it in `/home/develeap/hellio-hr-max/data/cvs/test_cv.pdf`
3. Run ingestion:
   ```bash
   docker exec hellio_backend python /app/scripts/ingest_cv.py /app/data/cvs/test_cv.pdf
   ```
4. Check the UI: http://localhost:8000/public/index.html
5. Verify the candidate appears in the Candidates tab

### Compare with Manual JSON

To validate accuracy, you can:
1. Ingest a CV using the script
2. Compare extracted data with the original CV
3. Check for missing or incorrect fields
4. Adjust prompts in `llm_extractors.py` if needed

## Architecture

```
backend/
├── app/
│   └── services/
│       ├── document_parser.py      # PDF/DOCX → text
│       ├── heuristic_extractors.py # Regex-based extraction
│       ├── llm_client.py           # LLM abstraction (Claude API / Bedrock)
│       ├── llm_extractors.py       # AI-powered extraction
│       └── data_validator.py       # Validation layer
└── scripts/
    └── ingest_cv.py                # Main ingestion pipeline
```

## Next Steps

After completing Exercise 3:
- Exercise 4: Build SQL-based RAG to query candidates
- Exercise 5: Add semantic search with embeddings
- Exercise 6: Build intelligent agent with email monitoring

## Switching to AWS Bedrock (Optional)

To use AWS Bedrock instead of Claude API:

1. Uncomment Bedrock implementation in `llm_client.py`
2. Configure AWS credentials
3. Update `.env`:
   ```
   AWS_REGION=us-east-1
   LLM_PROVIDER=aws_bedrock
   LLM_MODEL=amazon.nova-lite-v1:0
   ```
4. Compare costs and quality with Claude API
