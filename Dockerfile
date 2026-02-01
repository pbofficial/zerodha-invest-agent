# Use the official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install essential system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project code
COPY . .

# Cloud Run uses the $PORT env var (default 8080)
ENV PORT=8080

# Expose the port
EXPOSE 8080

# Run Streamlit on the specified port
CMD streamlit run src/dashboard/app.py --server.port=${PORT} --server.address=0.0.0.0
