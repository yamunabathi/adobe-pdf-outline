FROM python:3.10-slim

WORKDIR /app

# Install OCR and image dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Add project files
COPY src/ ./src/
COPY input/ ./input/
COPY output/ ./output/

CMD ["python", "src/extractor.py"]
