FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev --no-install-project

RUN useradd --create-home --uid 10001 appuser

COPY --chown=appuser:appuser main.py ./
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser app/ ./app/

USER appuser

EXPOSE 8501

CMD ["python", "main.py"]
