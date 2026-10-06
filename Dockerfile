FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATABASE_PATH=/data/db.sqlite3
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server ./server
EXPOSE 5000
CMD ["python", "server/app.py"]
