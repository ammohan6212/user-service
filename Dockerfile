# Use official Python image
FROM python:3.11-alpine
RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    build-base \
    cargo

# Set base working directory
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the entire src folder into the container
COPY src/ ./src

# Set working directory to src where main.py is located
WORKDIR /app/src

# Expose FastAPI default port
EXPOSE 8000

# Run FastAPI app inside src folder
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
