# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (needed for psycopg2 database driver)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (to cache dependencies)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code into the container
# We copy it into /app/backend so imports work as expected
COPY backend/ ./backend/

# Set Python path so it can find the modules
ENV PYTHONPATH=/app/backend

# The 'command' in docker-compose.yml will override this, 
# but this is a good default.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]