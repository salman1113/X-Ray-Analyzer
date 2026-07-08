FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps: build tools + dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
# PyTorch CPU wheels are large — install from the official index first
COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir \
    torch==2.3.0 torchvision==0.18.0 \
    --index-url https://download.pytorch.org/whl/cpu \
 && pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

COPY . .

# Ensure upload and model directories exist inside the container
RUN mkdir -p uploads/gradcam routes/ai/models

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
