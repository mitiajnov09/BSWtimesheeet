FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home rotations
COPY app.py db.py domain.py service.py pdf_export.py backup.py ./
COPY migrations/ migrations/
COPY static/ static/
COPY fonts/ fonts/
RUN mkdir -p /app/data && chown -R rotations:rotations /app
USER rotations
ENV APP_HOST=0.0.0.0 APP_PORT=8080 APP_DB=/app/data/rotations.sqlite3
EXPOSE 8080
CMD ["python", "app.py"]
