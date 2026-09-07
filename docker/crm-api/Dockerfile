FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY static/ ./static/

RUN mkdir -p /data

ENV PYTHONPATH=/app/src
ENV PORT=8000
ENV DB_PATH=/data/mock_salesforce.db
ENV STATIC_ASSETS_PATH=/app/static

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD python3 -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8000') + '/health', timeout=2)"

CMD ["sh", "-c", "uvicorn mock_salesforce.app:app --host 0.0.0.0 --port ${PORT}"]
