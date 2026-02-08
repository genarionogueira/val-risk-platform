# Expects build context = repo root (docker-compose: context: ., dockerfile: marketdata/Dockerfile)
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi "strawberry-graphql[fastapi]" "uvicorn[standard]" redis
COPY marketdata/app /app/app

ENV PYTHONPATH=/app
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
