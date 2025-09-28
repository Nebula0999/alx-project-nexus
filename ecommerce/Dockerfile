FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    # Pillow image libs
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    libtiff5-dev \
    libwebp-dev \
    libopenjp2-7-dev \
    # mysqlclient (only needed if you actually use MySQL; otherwise remove mysqlclient from requirements)
    default-libmysqlclient-dev \
    # cryptography / cffi extras
    libffi-dev \
    # Optional for better numpy/pandas performance (not strictly required; wheels usually cover) \
    libblas-dev \
    liblapack-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# Collect static in build stage (will run again runtime if needed)
RUN mkdir -p /app/staticfiles

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
