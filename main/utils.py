# backend/main/utils.py
from transformers import pipeline
from newspaper import Article

# Use only summarizer and NLI models with safetensors support
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
nli_clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")  # BART-MNLI uses safetensors

def get_text_from_url(url):
    article = Article(url)
    try:
        article.download()
        article.parse()
    except Exception as e:
        # Return None or a specific error for the view to handle
        raise RuntimeError(f"Could not fetch article. Error: {str(e)}")
    return {
        'text': article.text.strip(),
        'title': article.title or "",
        'author': ', '.join(article.authors) or "",
        'published_date': str(article.publish_date or ""),
    }

def summarize_text(text):
    text = text[:1024]
    try:
        summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
        return summary[0]['summary_text']
    except Exception:
        return "Summary unavailable. Please try again."

def classify_fake_news_ensemble(text):
    # Only use Zero-Shot NLI (MNLI) for now
    nli_result = nli_clf(
        text[:512],
        candidate_labels=["real news", "fake news", "opinion", "satire"],
        multi_label=False
    )
    label = nli_result['labels'][0]
    confidence = round(nli_result['scores'][0] * 100, 1)

    # Simple verdict logic for demo
    if label in ["fake news", "opinion", "satire"] and confidence > 60:
        verdict = label.upper()
    elif label == "real news" and confidence > 60:
        verdict = "REAL NEWS"
    else:
        verdict = "UNSURE"

    return verdict, confidence, {
        "nli_label": label,
        "nli_confidence": confidence
    }