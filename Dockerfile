FROM python:3.10-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY *.py ./
COPY hooks/ ./hooks/

# Install dependencies
RUN uv sync

# Expose port
EXPOSE 8000

# Run the server
CMD ["uv", "run", "python", "main.py"]

