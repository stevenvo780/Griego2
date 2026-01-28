FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir websockets

# Copy all Griego2 content
COPY . /app/

WORKDIR /app/visor_markdown

# Expose both HTTP and WebSocket ports
EXPOSE 8888
EXPOSE 8889

# Run server
CMD ["python3", "servidor.py"]
