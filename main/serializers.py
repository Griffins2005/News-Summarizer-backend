# backend/main/serializers.py
from rest_framework import serializers
from .models import QueryHistory

class AnalyzeRequestSerializer(serializers.Serializer):
    url = serializers.URLField(required=False, allow_null=True)
    text = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if not data.get('url') and not data.get('text'):
            raise serializers.ValidationError("Please provide a URL or article text.")
        return data

class AnalyzeResponseSerializer(serializers.Serializer):
    summary = serializers.CharField()
    fake_news_label = serializers.CharField()
    fake_news_confidence = serializers.FloatField()
    article_title = serializers.CharField(allow_blank=True)
    article_author = serializers.CharField(allow_blank=True)
    published_date = serializers.CharField(allow_blank=True)
    error = serializers.CharField(allow_blank=True, required=False)

class QueryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryHistory
        fields = [
            'id', 'input_type', 'input_value', 'summary', 'fake_news_label',
            'fake_news_confidence', 'article_title', 'created_at', 'duration_ms'
        ]