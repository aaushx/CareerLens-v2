FROM python:3.12-slim

# Install system dependencies (including Tesseract OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create uploads directory, setup group/user, and assign ownerships
RUN mkdir -p uploads && \
    groupadd -g 10001 careerlens && \
    useradd -u 10001 -g careerlens -m -s /bin/bash careerlens && \
    chown -R careerlens:careerlens /app

# Switch to restricted non-root user
USER careerlens

# Expose port 5000 for Flask
EXPOSE 5000

# Set environment variables for production
ENV PORT=5000
ENV FLASK_ENV=production
ENV TESSERACT_CMD=/usr/bin/tesseract

# Start application using Gunicorn with optimal settings
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --workers 1 --worker-class sync --timeout 120 app:app"]
