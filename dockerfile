FROM python:3.9-slim

# Install dependencies for OpenCV & face_recognition
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

RUN pip install --upgrade pip

# ✅ Pre-install prebuilt dlib binary so it doesn't try to build from source
RUN pip install dlib-bin==19.24.6

# ✅ Install remaining dependencies (excluding dlib)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]
