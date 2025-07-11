import requests

# NewsAPIキーをここに記入（例: "api_key_here"）
NEWS_API_KEY = "api_key_here"

# 必要な翻訳ライブラリのインポートとインストール
try:
    from googletrans import Translator
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "googletrans==4.0.0-rc1"])
    from googletrans import Translator

translator = Translator()

def get_company_news(company_name, language="en", max_results=5):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": company_name,
        "language": language,
        "sortBy": "publishedAt",
        "pageSize": max_results,
        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        return [(a["title"], a["url"]) for a in articles]
    except Exception as e:
        print(f"[NewsAPI Error] {e}")
        return []

def translate_text(text):
    try:
        result = translator.translate(text, dest="ja")
        return result.text
    except Exception as e:
        print(f"[Translation Error] {e}")
        return text
