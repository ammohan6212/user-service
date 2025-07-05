# Use official Python image (more compatible than Alpine)
FROM python:3.13-rc-alpine3.20


# Install system dependencies
RUN apk update && apk add --no-cache \
    build-base \
    postgresql-dev \
    libffi-dev \
    gcc \
    cargo

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the application code
COPY src/ ./src

# Set working directory to src
WORKDIR /app/src

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
