# Hosted evaluator API (FastAPI). Data lives in a volume mounted at /app/data; masks are
# fetched on demand from the R2 store into /cache.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY lunar_eval ./lunar_eval
COPY api ./api
COPY web ./web
# Editable install keeps lunar_eval's REPO-relative data/ paths pointing at /app/data.
RUN pip install --no-cache-dir -e ".[sky]"

ENV LUNAR_CACHE=/cache \
    LUNAR_MASKS_URL=https://masks.pedrojon.com/cap_1km \
    PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
