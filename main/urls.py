# backend/main/urls.py
from django.urls import path 
from .views import AnalyzeView, feedback_view, temp_create_superuser, AllQueryHistoryView, AllFeedbackView, change_admin_password, health_check,list_superusers, admin_check, temp_reset_superuser_password
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('', health_check, name='health_check'),
    path("analyze/", AnalyzeView.as_view()),
    path("feedback/", feedback_view),
    path("all-history/", AllQueryHistoryView.as_view()),
    path("all-feedback/", AllFeedbackView.as_view()),
    path("admin-token/", obtain_auth_token),  # This is for admin login
    path("change-password/", change_admin_password),
    path("admin-check/", admin_check),  
    path("temp-reset-superuser/", temp_reset_superuser_password),
    path("create-superuser/", temp_create_superuser),
    path("list-superusers/", list_superusers),
]