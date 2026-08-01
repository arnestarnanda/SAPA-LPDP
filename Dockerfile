FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt-lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and LPDP folder
COPY . .

# Expose port 8080 for Google Cloud Run
EXPOSE 8080

# Health check endpoint for container platform
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Launch Streamlit app on port 8080
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
