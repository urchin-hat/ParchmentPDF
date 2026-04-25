# ParchmentPDF 📜

ParchmentPDFは、固定されたPDFドキュメントを、Webフレンドリーで再利用可能なHTMLへと「再紡績（Re-spinning）」するサービスです。

## 🚀 開発環境での起動方法

### 1. uv を使用した直接起動 (推奨)
Python 3.12 と `uv` がインストールされている環境で、以下のコマンドを実行します。

```bash
# 依存関係のインストール
uv sync

# アプリケーションの起動
uv run uvicorn main:app --reload
```

起動後、 [http://localhost:8000](http://localhost:8000) にアクセスしてください。

### 2. Docker / Podman Compose を使用した起動
コンテナ環境を使用して、本番に近い構成で起動します。

```bash
docker-compose up --build
# または
podman-compose up --build
```

## 🛠 技術スタック
- **Backend**: Python 3.12 / FastAPI
- **Frontend**: htmx / Tailwind CSS
- **PDF Engine**: PyMuPDF (fitz)
- **Package Manager**: uv

## 📁 ディレクトリ構造
- `app/`: アプリケーションロジック（変換サービス、ユーティリティ）
- `static/`: 静的ファイル
- `templates/`: Jinja2 テンプレート
- `DESIGN.md`: 詳細な設計ドキュメント
