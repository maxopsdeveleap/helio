FROM python:3.11-alpine

WORKDIR /app

# Install PostgreSQL dependencies
RUN apk add --no-cache postgresql-dev gcc python3-dev musl-dev

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
