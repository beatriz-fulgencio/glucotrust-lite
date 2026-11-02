FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/data/cache/huggingface

WORKDIR /app

# MiniLM runs on CPU. Install the CPU wheel before resolving the app dependencies.
RUN python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY pyproject.toml ./
COPY src/ ./src/
RUN python -m pip install . && python -m pip check

RUN useradd --create-home --uid 10001 glucotrust
COPY app.py ./
COPY assets/ ./assets/
COPY .streamlit/config.toml ./.streamlit/config.toml
COPY data/curated/ ./data/curated/
COPY scripts/__init__.py scripts/download_model.py ./scripts/
RUN mkdir -p data/cache runtime \
    && chown -R glucotrust:glucotrust data runtime

USER glucotrust
# Bake the pinned embedding model into the image; the cache volume is seeded on first use.
RUN python -m scripts.download_model

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
