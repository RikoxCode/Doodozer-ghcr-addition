# Multi-Stage Dockerfile für Doodozer CLI
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Installiere Build-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements und installiere Abhängigkeiten
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Metadata Labels (OCI Standard)
LABEL org.opencontainers.image.title="Doodozer CLI" \
      org.opencontainers.image.description="Fast DoodStream video downloader for command-line" \
      org.opencontainers.image.url="https://github.com/RikoxCode/Doodozer" \
      org.opencontainers.image.source="https://github.com/RikoxCode/Doodozer" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="RikoxCode"

# Build Arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}"

# Erstelle non-root User
RUN groupadd -g 1000 doodozer && \
    useradd -r -u 1000 -g doodozer doodozer

WORKDIR /app

# Installiere Runtime-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Kopiere wheels vom Builder und installiere
COPY --from=builder /build/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Kopiere Application Code
COPY --chown=doodozer:doodozer . .

# Erstelle Download-Verzeichnis mit korrekten Berechtigungen
RUN mkdir -p /downloads && \
    chown -R doodozer:doodozer /downloads /app

# Umgebungsvariablen
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OUTPUT_PATH=/downloads \
    PIP_NO_CACHE_DIR=1

# Volume für Downloads
VOLUME ["/downloads"]

# Wechsel zu non-root User
USER doodozer

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Einstiegspunkt
ENTRYPOINT ["python", "main.py"]

# Standard-Argumente
CMD ["--help"]