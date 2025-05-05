# Dockerfile
FROM python:3.12-slim

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-distutils \
    netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .
COPY wait-for.sh /wait-for.sh
RUN chmod +x /wait-for.sh

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]