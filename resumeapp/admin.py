from django.contrib import admin
from .models import ResumeAnalysis, UserProfile

@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'user', 'score', 'uploaded_at')
    list_filter = ('uploaded_at', 'score')
    search_fields = ('original_filename', 'user__username', 'raw_text')
    readonly_fields = ('uploaded_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_role', 'experience_level', 'phone')
    search_fields = ('user__username', 'user__email', 'target_role')
