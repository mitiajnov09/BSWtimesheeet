FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home rotations
COPY app.py db.py domain.py service.py feedback.py photos.py pdf_export.py backup.py restore.py ./
COPY VERSION ./
COPY migrations/ migrations/
COPY static/ static/
COPY fonts/ fonts/
RUN mkdir -p /app/data && chown -R rotations:rotations /app
USER rotations
ENV APP_HOST=0.0.0.0 APP_PORT=8080 APP_DB=/app/data/rotations.sqlite3
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/', timeout=3).close()"
CMD ["python", "app.py"]
