FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    build-essential cmake libboost-all-dev \
    libopenblas-dev liblapack-dev libx11-dev \
    libgtk-3-dev git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip

# ✅ Install prebuilt dlib binary package
RUN pip install dlib-bin==19.24.6

# ✅ Now install rest (do NOT include dlib in requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 10000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]
