FROM python:3.11-slim

WORKDIR /app

# aiohttp のビルドに必要なパッケージを追加
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# pip を最新化
RUN pip install --upgrade pip setuptools wheel

# 依存関係インストール
COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコピー
COPY app /app

ENV PORT=8000
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["python", "main.py"]
