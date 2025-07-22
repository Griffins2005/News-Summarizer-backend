# backend/main/tasks.py

from celery import shared_task
from .utils import summarize_text, classify_fake_news

@shared_task
def analyze_article_task(text, title, author, published_date):
    summary = summarize_text(text)
    label, confidence = classify_fake_news(text)
    return {
        'summary': summary,
        'fake_news_label': label,
        'fake_news_confidence': confidence,
        'article_title': title,
        'article_author': author,
        'published_date': published_date,
    }
