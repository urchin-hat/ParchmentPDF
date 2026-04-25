# Nami-Seikyu (波請求) 🌊

Nami-Seikyu（波請求）は、ビジネスにおける「お金の流れ」を波のように淀みなく、スムーズに整えるための請求書発行システムです。

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

## 🛠 特徴
- **ライブプレビュー**: 入力内容をリアルタイムで確認可能。
- **日本語・印影対応**: Noto Sans JP フォントと電子印鑑の自動生成。
- **ステートレス**: 波のようにデータを残さず、高いセキュリティを実現。

## 📁 ディレクトリ構造
- `app/`: アプリケーションロジック（請求書生成、モデル、印影生成）
- `static/`: フォント、静的ファイル
- `templates/`: Jinja2 テンプレート
- `DESIGN.md`: 詳細な設計ドキュメント
