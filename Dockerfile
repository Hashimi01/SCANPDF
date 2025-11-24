FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    I2PDF_TMPDIR=/tmp/i2pdf \
    TMPDIR=/tmp/i2pdf

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    ghostscript \
    qpdf \
    unpaper \
    pngquant \
    poppler-utils \
    icc-profiles-free \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/i2pdf

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN chmod +x scripts/cleanup_temp.sh

ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["service:app", "--host", "0.0.0.0", "--port", "8080"]

