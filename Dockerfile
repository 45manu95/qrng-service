# Use the official lightweight Python image (slim)
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Optimization: copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install classical and quantum dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our project code into the container
COPY . .

# No fixed CMD is specified here, as Docker Compose will decide
# based on whether the container acts as API, Worker, or Orchestrator.