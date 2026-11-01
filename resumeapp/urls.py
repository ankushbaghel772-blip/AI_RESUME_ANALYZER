"""
URL Patterns for resumeapp.
Maps all public, authentication, dashboard, analysis, and management views.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Public Pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),

    # User Authentication
    path('signup/', views.user_signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Dashboard & Resume Processing
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_resume, name='upload'),
    path('result/<int:analysis_id>/', views.result_detail, name='result'),
    path('result/<int:analysis_id>/report/', views.download_analysis_report, name='download_report'),
    path('result/<int:analysis_id>/download-file/', views.download_original_resume, name='download_original_resume'),

    # History & Record Management
    path('history/', views.history, name='history'),
    path('compare/', views.compare_resumes, name='compare_resumes'),
    path('delete/<int:analysis_id>/', views.delete_resume, name='delete_resume'),

    # Profile & Dedicated Career Recommendations
    path('profile/', views.profile_view, name='profile'),
    path('recommendations/', views.job_recommendations, name='job_recommendations'),
]
