# Use an official lightweight Python image
FROM python:3.13-slim

# Set working directory inside the container
WORKDIR /app

# Copy and install dependencies first (Docker caches this layer if requirements.txt hasn't changed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Run the Streamlit dashboard
CMD ["streamlit", "run", "app/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
