FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATABASE_PATH=/data/db.sqlite3
COPY requirements.txt requirements.lock ./
RUN --mount=type=secret,id=custom_ca \
    if [ -f /run/secrets/custom_ca ]; then \
        PIP_CERT=/run/secrets/custom_ca pip install --no-cache-dir -r requirements.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi
COPY server ./server
EXPOSE 5000
CMD ["python", "server/app.py"]
