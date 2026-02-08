# Expects build context = repo root (docker-compose: context: ., dockerfile: api/Dockerfile)
FROM python:3.12-slim

WORKDIR /app

# Install pricing-library
COPY pricing-library /app/pricing-library
RUN pip install --no-cache-dir /app/pricing-library

# Install API dependencies and code
RUN pip install --no-cache-dir fastapi "strawberry-graphql[fastapi]" "uvicorn[standard]"
COPY api/app /app/app

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
