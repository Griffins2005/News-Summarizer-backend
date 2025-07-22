#backend/main/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.generics import ListAPIView
from .utils import get_text_from_url, summarize_text, classify_fake_news_ensemble
from .models import QueryHistory, Feedback
from .serializers import QueryHistorySerializer
from django.contrib.auth.models import User
import sys
import time
from django.http import HttpResponse

def health_check(request):
    return HttpResponse(
        "<h2>📰 News Summarizer Backend</h2>"
        "<p>Status: <b>Running</b></p>"
        "<p>If you see this, the backend is deployed and online! For API usage, POST to <code>/api/...</code>.</p>",
        content_type="text/html"
    )

class AnalyzeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        start_time = time.time()
        url = request.data.get("url", "").strip()
        text = request.data.get("text", "").strip()
        if url:
            try:
                article = get_text_from_url(url)
            except Exception as e:
                print("AnalyzeView URL fetch error:", e, file=sys.stderr)
                return Response(
                    {"error": f"Failed to fetch article from the provided URL. This site may block bots, or the link is invalid. Error details: {str(e)}"},
                    status=400
                )
            text = article["text"]
            title = article.get("title", "")
            author = article.get("author", "")
            published_date = article.get("published_date", "")
            if not text:
                return Response(
                    {"error": "Could not extract article text from the provided URL. Please check the link or try another article."},
                    status=400
                )
        elif text:
            title = author = published_date = ""
            if len(text) < 5:
                return Response({"error": "Please provide more article text for analysis."}, status=400)
        else:
            return Response({"error": "No input provided. Paste a news article link or text."}, status=400)
        try:
            summary = summarize_text(text)
            verdict, confidence, details = classify_fake_news_ensemble(text)
        except Exception as e:
            print("AnalyzeView pipeline error:", e, file=sys.stderr)
            return Response({"error": f"AI failed: {str(e)}"}, status=500)
        duration_ms = int((time.time() - start_time) * 1000)
        QueryHistory.objects.create(
            input_type='url' if url else 'text',
            input_value=url or (text[:100] + "..."),
            summary=summary,
            fake_news_label=verdict,
            fake_news_confidence=confidence,
            article_title=title,
            duration_ms=duration_ms,
        )
        return Response({
            "title": title,
            "author": author,
            "published_date": published_date,
            "summary": summary,
            "fake_news_label": verdict,
            "fake_news_confidence": confidence,
            "details": details,
            "duration_ms": duration_ms,
        })

@api_view(["POST"])
@permission_classes([IsAdminUser])
def change_admin_password(request):
    new_password = request.data.get("new_password")
    if not new_password or len(new_password) < 4:
        return Response({"error": "Password too short."}, status=400)
    user = request.user
    user.set_password(new_password)
    user.save()
    return Response({"success": True})

@api_view(["POST"])
def feedback_view(request):
    data = request.data
    Feedback.objects.create(
        title=data.get("title", ""),
        fake_news_label=data.get("fake_news_label", ""),
        user_feedback=data.get("user_feedback", "")
    )
    return Response({"success": True})

class AllQueryHistoryView(ListAPIView):
    queryset = QueryHistory.objects.all().order_by('-created_at')
    serializer_class = QueryHistorySerializer
    permission_classes = [IsAdminUser]

class AllFeedbackView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        feedbacks = Feedback.objects.all().order_by('-created_at')
        data = [
            {
                "title": f.title,
                "fake_news_label": f.fake_news_label,
                "user_feedback": f.user_feedback,
                "created_at": f.created_at,
            }
            for f in feedbacks
        ]
        return Response(data)