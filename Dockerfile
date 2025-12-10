# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (needed for psycopg2 database driver)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# We ADD 'netcat-openbsd' to check if the DB is ready
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (to cache dependencies)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy backend code
COPY backend/ ./backend/
# Copy src code (data loader)
COPY src/ ./src/
# Copy data (csv files)
COPY data/ ./data/

ENV PYTHONPATH=/app:/app/backend

# Set the ENTRYPOINT to our script
ENTRYPOINT ["./entrypoint.sh"]

# The CMD becomes the arguments passed to 'exec "$@"' at the end of the script
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]