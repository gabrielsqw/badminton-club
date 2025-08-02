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

# uv is imporatant
RUN pip install uv

# requirements
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# run the server
COPY badminton_club/ /app/badminton_club/
RUN uv pip install --system gunicorn
CMD ["gunicorn", "badminton_club.app:server", "--bind", "0.0.0.0:8000"]
