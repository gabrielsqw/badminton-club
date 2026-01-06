FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies, including git
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# uv is important
RUN pip install uv

# requirements
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Install gunicorn
RUN uv pip install --system gunicorn

# Copy alembic configuration and migrations
COPY alembic.ini .
COPY alembic/ /app/alembic/

# Copy application code
COPY badminton_club/ /app/badminton_club/

# Copy and set up entrypoint (convert Windows line endings to Unix)
COPY entrypoint.sh .
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Use entrypoint to run migrations before starting
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "badminton_club.app:server", "--bind", "0.0.0.0:8000"]
