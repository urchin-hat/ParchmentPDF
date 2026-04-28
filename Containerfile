FROM python:3.12-slim-bookworm

# uvバイナリを公式イメージからコピー
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# バイトコード生成抑制 & 標準出力即時出し
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 依存関係ファイルをコピー
COPY uv.lock pyproject.toml ./

# 【重要】システム環境に直接インストール
# pyproject.toml を読み取って、仮想環境を作らずにインストールします
RUN uv pip install --system --requirement pyproject.toml

# アプリケーションコードをコピー
COPY . .

EXPOSE 8000
# システムにインストールしたので、直接 uvicorn を実行可能
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
