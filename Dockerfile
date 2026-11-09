FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOST=0.0.0.0 \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

WORKDIR /app

# Tesseract is local-only; the Korean traineddata package is included in the image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-kor \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app.py recognition_engine.py recommendation_engine.py README.md ./
COPY static ./static

# Fail the image build if the OCR engine or Korean model is unavailable.
RUN python -c "import PIL, pytesseract; print('Pillow', PIL.__version__); print('pytesseract', pytesseract.__version__)" \
    && tesseract --version \
    && tesseract --list-langs 2>&1 | grep -qx 'kor'

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3)"

CMD ["python", "app.py"]
