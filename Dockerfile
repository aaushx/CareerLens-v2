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

# Install CPU-only PyTorch to reduce image size and memory usage
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Model will be lazy-loaded on first use to save memory during startup
# Includes fallback to keyword-based matching if model loading fails
# (This allows the app to work on Render free tier: 512MB RAM limit)

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

# Start application using Gunicorn with memory optimization
# --workers 1: Single worker for minimal memory usage (free tier constraint)
# --timeout 180: Allow up to 3min for model loading on first request
# --max-requests 100: Restart worker periodically to avoid memory creep
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --workers 1 --worker-class sync --timeout 180 --max-requests 100 app:app"]
