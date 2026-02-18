# Builder Stage
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10

RUN apt-get update && apt-get install -y --no-install-recommends \
    git gcc build-essential openssh-client \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh && \
    ssh-keyscan github.com ssh.github.com >> /root/.ssh/known_hosts

COPY requirements.txt .

RUN --mount=type=ssh \
    pip wheel --wheel-dir /wheels -r requirements.txt

# Runtime Stage
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    TZ=Asia/Tehran

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    unixodbc \
    libmariadb3 \
    ca-certificates \
    curl \
    gnupg \
 && ln -fs /usr/share/zoneinfo/Asia/Tehran /etc/localtime \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

# MSSQL ODBC Driver (runtime)
RUN curl https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg \
 && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
    https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN python -m pip install --upgrade pip setuptools \
 && pip install --no-cache-dir /wheels/* \
 && rm -rf /wheels

COPY . .

RUN mkdir -p /var/log \
 && touch /var/log/log_etl.log /var/log/log_etl_scheduler.log \
 && chmod 0666 /var/log/log_etl.log /var/log/log_etl_scheduler.log

CMD ["python", "/app/run_scheduler.py"]
