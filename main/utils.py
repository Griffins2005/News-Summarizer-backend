# backend/main/utils.py
import os
import requests
from newspaper import Article

def get_text_from_url(url):
    article = Article(url)
    try:
        article.download()
        article.parse()
    except Exception as e:
        raise RuntimeError(f"Could not fetch article. Error: {str(e)}")
    return {
        'text': article.text.strip(),
        'title': article.title or "",
        'author': ', '.join(article.authors) or "",
        'published_date': str(article.publish_date or ""),
    }

def summarize_text(text):
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
    payload = {"inputs": text[:1024]}
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and "summary_text" in data[0]:
            return data[0]["summary_text"]
        # Handle API error messages
        if "error" in data:
            return f"Summary error: {data['error']}"
        return str(data)
    except requests.exceptions.HTTPError as http_err:
        return f"Summary API error: {str(http_err)}"
    except Exception as e:
        return f"Summary unavailable: {str(e)}"

def classify_fake_news_ensemble(text):
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
    payload = {
        "inputs": text[:512],
        "parameters": {
            "candidate_labels": ["real news", "fake news", "opinion", "satire"],
            "multi_label": False,
        },
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        nli_result = response.json()
        label = nli_result["labels"][0]
        confidence = round(nli_result["scores"][0] * 100, 1)
        if label in ["fake news", "opinion", "satire"] and confidence > 60:
            verdict = label.upper()
        elif label == "real news" and confidence > 60:
            verdict = "REAL NEWS"
        else:
            verdict = "UNSURE"
        return verdict, confidence, {
            "nli_label": label,
            "nli_confidence": confidence,
        }
    except Exception as e:
        return "UNSURE", 0, {"error": str(e)}