FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
# Install, then remove the installer itself: nothing installs packages at run time.
RUN pip install --no-cache-dir . && pip uninstall -y pip setuptools wheel
COPY src ./src
# Migrations ship in the image so a fresh deployment can migrate itself.
COPY alembic.ini .
COPY migrations ./migrations
ENV PYTHONPATH=/app/src
# Run as an unprivileged account; /data (problem-report and mail outbox) is its only writable place.
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app && mkdir -p /data && chown app:app /data
USER 10001
# Keep idle connections longer than the web proxy's client pool (Node ~4s), so the client
# always closes first and never reuses a socket the server is closing (ECONNRESET).
CMD ["uvicorn","flowforge.main:app","--host","0.0.0.0","--port","8000","--timeout-keep-alive","75"]
