# Use an Alpine-based Python image
FROM python:3.13-alpine3.21

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /toolset

# Install system dependencies (if needed, include build tools for compiling Python packages)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    && pip install --upgrade pip

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY toolset /toolset

# Command to run the main.py script
CMD ["python", "/toolset/main.py"]