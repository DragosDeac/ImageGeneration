# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy the requirements file
COPY requirements.txt .

# Install dependencies with verbose output and error handling
RUN pip install --no-cache-dir -r requirements.txt || (echo "Installation failed" && cat /root/.pip/pip.log)

# Copy the rest of the project files
COPY . .

# Set additional environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Create a non-root user
RUN addgroup --system flask && adduser --system --group flask
USER flask

# Expose the port the app runs on
EXPOSE 5000

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]