FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

# Conversión local DOCX -> PDF y tipografías compatibles.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libreoffice-writer fonts-crosextra-carlito fonts-liberation fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd --create-home --uid 10001 carta \
    && chown -R carta:carta /app
USER carta

EXPOSE 10000
CMD ["sh", "-c", "exec gunicorn interfaz:app --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 2 --timeout 180"]
