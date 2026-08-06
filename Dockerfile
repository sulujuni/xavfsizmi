FROM python:3.11-slim

# Logs must stream unbuffered or the platform's log view stays empty until a
# crash flushes the buffer.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# opencv-python-headless drops the GUI stack but still links libgthread/libglib.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The SQLite database lives on a volume mounted at /data. Create the mount point
# and hand it to the app user so the first write succeeds on a fresh volume.
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /data \
    && chown -R app:app /app /data
USER app

CMD ["python3", "main.py"]
