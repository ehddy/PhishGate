FROM python:3.11.0-slim@sha256:b5ee5360b357dcd0ab2e1cc5e22fa589b6734bbd55776df6b1700994febf1527 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.lock.txt ./requirements.lock.txt
RUN pip install --no-cache-dir --require-hashes --requirement requirements.lock.txt

COPY backend/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
