# backend/main/utils.py
import os
import requests
import logging
from newspaper import Article

# Set up logging for error tracing
logger = logging.getLogger(__name__)

def get_text_from_url(url):
    """Extract article text and metadata from the provided URL using newspaper3k."""
    article = Article(url)
    try:
        article.download()
        article.parse()
    except Exception as e:
        logger.exception("Failed to fetch article from URL: %s", url)
        raise RuntimeError(f"Could not fetch article. Error: {str(e)}")
    return {
        'text': article.text.strip(),
        'title': article.title or "",
        'author': ', '.join(article.authors) or "",
        'published_date': str(article.publish_date or ""),
    }

def summarize_text(text):
    """
    Calls HuggingFace summarization API and returns summary text or an error message.
    Handles missing API key, rate limits, model loading, and other common issues gracefully.
    """
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    api_key = os.getenv('HF_API_KEY')
    if not api_key:
        logger.error("HF_API_KEY not set in environment")
        return "Summary unavailable: HF_API_KEY not configured. Please contact the administrator."

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"inputs": text[:1024]}
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if response.status_code == 429:
            logger.warning("HuggingFace API rate limited: %s", response.text)
            return "Summary unavailable: Rate limit exceeded. Please wait and try again later."
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and "summary_text" in data[0]:
            return data[0]["summary_text"]
        if "error" in data:
            logger.error("HuggingFace API error: %s", data["error"])
            # Special case: model is loading on HuggingFace
            if "currently loading" in data["error"].lower() or "loading" in data["error"].lower():
                return "Summary model is loading. Please try again in a few moments."
            return f"Summary error: {data['error']}"
        if "estimated_time" in data:
            return "Summary model is loading. Please try again in a few moments."
        # Fallback for any unexpected API response
        return f"Summary unavailable: Unexpected API response. ({str(data)})"
    except requests.exceptions.HTTPError as http_err:
        logger.error("Summary API HTTP error: %s", http_err)
        return f"Summary API error: {str(http_err)}"
    except requests.exceptions.Timeout:
        logger.error("Summary API request timed out")
        return "Summary unavailable: The summarization service timed out. Please try again later."
    except Exception as e:
        logger.exception("Summarization error: %s", e)
        return f"Summary unavailable: {str(e)}"

def classify_fake_news_ensemble(text):
    """
    Calls HuggingFace zero-shot classification API and returns the verdict, confidence, and details.
    Handles API key, rate limit, loading, and error messages in a user-friendly way.
    """
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    api_key = os.getenv('HF_API_KEY')
    if not api_key:
        logger.error("HF_API_KEY not set in environment")
        return "UNSURE", 0, {"error": "HF_API_KEY not configured. Please contact the administrator."}
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": text[:512],
        "parameters": {
            "candidate_labels": ["real news", "fake news", "opinion", "satire"],
            "multi_label": False,
        },
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if response.status_code == 429:
            logger.warning("NLI API rate limited: %s", response.text)
            return "UNSURE", 0, {"error": "NLI service rate limited. Please wait and try again later."}
        response.raise_for_status()
        nli_result = response.json()
        if "error" in nli_result:
            logger.error("NLI API error: %s", nli_result["error"])
            if "currently loading" in nli_result["error"].lower() or "loading" in nli_result["error"].lower():
                return "UNSURE", 0, {"error": "The AI model is loading. Please try again in a few moments."}
            return "UNSURE", 0, {"error": nli_result["error"]}
        if "labels" not in nli_result or not nli_result["labels"]:
            logger.error("NLI API response missing labels: %s", nli_result)
            return "UNSURE", 0, {"error": "NLI API returned no labels."}
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
    except requests.exceptions.HTTPError as http_err:
        logger.error("NLI API HTTP error: %s", http_err)
        return "UNSURE", 0, {"error": str(http_err)}
    except requests.exceptions.Timeout:
        logger.error("NLI API request timed out")
        return "UNSURE", 0, {"error": "The fake news classification service timed out. Please try again later."}
    except Exception as e:
        logger.exception("NLI classification error: %s", e)
        return "UNSURE", 0, {"error": str(e)}