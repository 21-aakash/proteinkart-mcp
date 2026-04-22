# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY . .

# Cloud Run uses the PORT env var
ENV PORT=3000
EXPOSE 3000

# Run the MCP server
CMD ["python", "mcp_server.py"]
