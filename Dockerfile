FROM python:3.10-slim

# Tesseractのインストール
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-jpn \
    libgl1

# 作業ディレクトリの設定
WORKDIR /app

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコピー
COPY . .

# ポート設定
EXPOSE 8501

# 起動コマンド
ENTRYPOINT ["streamlit", "run", "ocr_webapp.py", "--server.port=8501", "--server.address=0.0.0.0"]