FROM python:3.11-slim

# Install system dependencies (including Tesseract OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies (lightweight - no heavy ML libraries)
RUN pip install --no-cache-dir -r requirements.txt

# Using TF-IDF for semantic matching (lightweight alternative to Sentence Transformer)
# This saves ~400MB of RAM compared to heavy ML models
# App is now optimized for minimal memory usage and works on any free tier

# Copy the rest of the application files
COPY . .

# Create uploads directory for file uploads
RUN mkdir -p uploads

# Expose port 5000 for Flask
EXPOSE 5000

# Set environment variables for production
ENV PORT=5000
ENV FLASK_ENV=production
ENV TESSERACT_CMD=/usr/bin/tesseract

# Start application using Gunicorn with optimal settings
# --workers 1: Single worker to minimize memory on free tier
# --timeout 120: Extra time for first-request lazy imports (sklearn, reportlab)
# --preload: NOT used, so lazy imports stay deferred until first request
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --workers 1 --worker-class sync --timeout 120 app:app"]
