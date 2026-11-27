FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY src ./src
# Migrations ship in the image so a fresh deployment can migrate itself.
COPY alembic.ini .
COPY migrations ./migrations
ENV PYTHONPATH=/app/src
CMD ["uvicorn","flowforge.main:app","--host","0.0.0.0","--port","8000"]
