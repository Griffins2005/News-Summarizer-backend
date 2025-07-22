# backend/main/models.py
from django.db import models

class QueryHistory(models.Model):
    input_type = models.CharField(max_length=10, choices=[('url', 'URL'), ('text', 'Text')])
    input_value = models.TextField()
    summary = models.TextField()
    fake_news_label = models.CharField(max_length=16)
    fake_news_confidence = models.FloatField()
    article_title = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    duration_ms = models.IntegerField(default=0)

    def __str__(self):
        return f'Query: {self.article_title or self.input_value[:32]}...'
    
class Feedback(models.Model):
    title = models.CharField(max_length=512, blank=True)
    fake_news_label = models.CharField(max_length=16)
    user_feedback = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'Feedback: {self.title[:32]}... - {self.user_feedback}'
