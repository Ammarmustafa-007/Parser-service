FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port
EXPOSE 5001

# Keep one parser worker on small Render instances; pdfplumber parsing is CPU-bound,
# so multiple workers can fight for the same limited CPU and memory.
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "1", "--threads", "2", "--preload", "--timeout", "120", "app:app"]
