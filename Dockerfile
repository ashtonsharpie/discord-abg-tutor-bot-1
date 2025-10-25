FROM python:3.13.4-slim

# Install system dependencies (tesseract-ocr for image text extraction + build tools)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Expose the port (Render will set PORT environment variable)
EXPOSE 10000

# Run the Discord bot
CMD ["python", "main.py"]
