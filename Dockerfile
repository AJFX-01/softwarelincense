# LicenseWise: one image with the web UI and the API (FastAPI serves ui/dist).
# The fine-tuned verifier (models/, gitignored) is copied in, so build from a
# checkout that has it. Azure Container Apps runs linux/amd64:
#   docker buildx build --platform linux/amd64 -t ghcr.io/<owner>/licensewise:latest --push .
# GROQ_API_KEY is passed at run time, never baked into the image.

# --- 1. Build the UI ---
FROM node:24-slim AS ui
WORKDIR /ui
RUN corepack enable
COPY ui/package.json ui/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY ui/ ./
RUN pnpm build

# --- 2. API + verifier ---
FROM python:3.14-slim
# Links the GHCR package to the repo, so the deploy workflow may push to it
LABEL org.opencontainers.image.source=https://github.com/AJFX-01/softwarelincense
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HUB_OFFLINE=1
WORKDIR /app
COPY requirements.txt .
# CPU-only torch (the CUDA build is several GB larger and there is no GPU)
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1 \
 && pip install -r requirements.txt
RUN useradd --create-home app && mkdir -p data/runs && chown app data/runs
COPY licensewise/ licensewise/
COPY data/processed/licenses.json data/processed/spdx_ids.json data/processed/
COPY examples/samples/ examples/samples/
# --chown: the weights file is owner-only (600) on the build machine
COPY --chown=app models/deberta-v3-large-license-nli/ models/deberta-v3-large-license-nli/
COPY --from=ui /ui/dist ui/dist
USER app
EXPOSE 8000
CMD ["uvicorn", "licensewise.api:app", "--host", "0.0.0.0", "--port", "8000"]
