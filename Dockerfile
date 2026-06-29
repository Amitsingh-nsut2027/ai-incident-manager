# Recipe to build the app image. Each line is a cached layer.
FROM python:3.13-slim

# Don't buffer stdout / don't write .pyc files — cleaner container logs.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install deps first (this layer is cached unless requirements.txt changes).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy the application code.
COPY app ./app

EXPOSE 8000

# Listen on $PORT if the host sets one (e.g. Render), else default to 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
