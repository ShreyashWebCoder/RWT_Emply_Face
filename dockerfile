# Use official Python 3.9 image
FROM python:3.9-slim

# Install system dependencies for face_recognition & OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libboost-all-dev \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# ✅ Install prebuilt dlib (don't put this in requirements.txt)
RUN pip install dlib-bin==19.24.6

# ✅ Install remaining packages (make sure dlib is removed from requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose Render-compatible port
EXPOSE 10000

# Run FastAPI app
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]
