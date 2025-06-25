# Use official Python 3.9 base image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libboost-all-dev \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# ✅ Download and install prebuilt dlib wheel from a URL (or local path)
# Replace with your actual .whl URL or place it in your project directory
# Example from a GitHub raw link or S3/Render-compatible host
ADD https://your-bucket-url.com/dlib-19.24.0-cp39-cp39-manylinux2014_x86_64.whl /tmp/dlib.whl
RUN pip install /tmp/dlib.whl

# ✅ Now install remaining packages (excluding dlib in requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose port for Render
EXPOSE 10000

# Run app
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]
