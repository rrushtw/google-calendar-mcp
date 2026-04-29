FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gcal_mcp/ ./gcal_mcp/

ENV GCAL_MCP_CONFIG_DIR=/config
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-m", "gcal_mcp"]
