FROM python:3.9-slim

# Install ghostscript and libgl1 (required by camelot and opencv)
RUN apt-get update && apt-get install -y \
    ghostscript \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
# Gunicorn is needed for production server
RUN pip install gunicorn

COPY . .

# Expose port
EXPOSE 5001

# Run with Gunicorn instead of Flask dev server
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "120", "app:app"]
