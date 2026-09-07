FROM python:3.12-slim

WORKDIR /app

COPY mcp_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server/ ./mcp_server/

ENV HOST=0.0.0.0
ENV PORT=8001
ENV API_BASE_URL=http://crm-api:8000

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD python3 -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8001') + '/health', timeout=2)"

CMD ["python3", "-m", "mcp_server.app"]
