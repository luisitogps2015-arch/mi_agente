FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt constraints.txt ./

RUN pip install --no-cache-dir --upgrade pip -c constraints.txt && \
    pip install --no-cache-dir -r requirements.txt -c constraints.txt

COPY . .

RUN mkdir -p /app/plugins && chmod -R 777 /app/plugins

EXPOSE 5000

CMD ["python3", "app.py"]
