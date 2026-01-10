#!/bin/bash
# Test CV ingestion with a new candidate ID

echo "Testing CV ingestion pipeline..."
docker exec hellio_backend python /app/scripts/ingest_cv.py /app/data/test_cv.pdf --candidate-id candidate_006

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Ingestion successful!"
    echo "View the candidate at: http://localhost:8000/public/index.html"
else
    echo ""
    echo "❌ Ingestion failed. Check logs above."
fi
