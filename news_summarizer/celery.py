# backend/news_summarizer/celery.py

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_summarizer.settings')
app = Celery('news_summarizer')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
