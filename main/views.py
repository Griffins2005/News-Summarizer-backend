#backend/main/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from .utils import get_text_from_url, summarize_text, classify_fake_news_ensemble
from .models import QueryHistory, Feedback
from .serializers import QueryHistorySerializer
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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
        url = (request.data.get("url") or "").strip()
        text = (request.data.get("text") or "").strip()
        # Defensive: support only one being present
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
    
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def admin_check(request):
    if not request.user.is_superuser:
        return Response({"error": "Not a superuser."}, status=403)
    return Response({"success": True, "username": request.user.username})

@api_view(["POST"])
@csrf_exempt  # disables CSRF protection for this endpoint; fine for temporary admin use only!
def temp_reset_superuser_password(request):
    """
    Temporary endpoint to reset a superuser's password without shell access.
    POST with ?key=YOUR_SECRET_KEY
    Body: { "username": "admin", "new_password": "NEWPASSWORD" }
    """
    # Change this secret to something random before pushing!
    SECRET = "factCheck_123"
    if request.GET.get("key") != SECRET:
        return Response({"error": "Unauthorized"}, status=403)
    username = request.data.get("username")
    password = request.data.get("new_password")
    if not username or not password:
        return Response({"error": "Missing username or new_password"}, status=400)
    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        return Response({"success": True, "msg": f"Password for {username} updated."})
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["GET"])
def list_superusers(request):
    """Temporary endpoint to list all superuser usernames. Remove after use!"""
    usernames = list(User.objects.filter(is_superuser=True).values_list("username", flat=True))
    return Response({"superusers": usernames})