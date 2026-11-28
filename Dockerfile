FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY src ./src
# Migrations ship in the image so a fresh deployment can migrate itself.
COPY alembic.ini .
COPY migrations ./migrations
ENV PYTHONPATH=/app/src
# Keep idle connections longer than the web proxy's client pool (Node ~4s), so the client
# always closes first and never reuses a socket the server is closing (ECONNRESET).
CMD ["uvicorn","flowforge.main:app","--host","0.0.0.0","--port","8000","--timeout-keep-alive","75"]
