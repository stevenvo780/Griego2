FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir aiohttp

# Copy all Griego2 content
COPY . /app/

WORKDIR /app/visor_markdown

# Expose single port (HTTP + WebSocket unified)
EXPOSE 8888

# Run server
CMD ["python3", "servidor.py"]
