FROM python:3.9-slim

# Install system-level dependencies for dlib, OpenCV, face_recognition
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

WORKDIR /app

COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# ✅ Install prebuilt dlib from PyPI (avoids build errors)
RUN pip install dlib==19.24.0 --only-binary :all:

# ✅ Install remaining packages (make sure dlib is NOT in requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

# Start FastAPI server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]
