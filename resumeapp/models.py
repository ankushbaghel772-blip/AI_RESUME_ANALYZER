from django.db import models
from django.contrib.auth.models import User
import os

class UserProfile(models.Model):
    """
    Extends Django's User model to store additional candidate details.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    target_role = models.CharField(max_length=100, blank=True, null=True, default='Software Engineer')
    experience_level = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        choices=[
            ('Entry Level', 'Entry Level (0-2 years)'),
            ('Mid Level', 'Mid Level (2-5 years)'),
            ('Senior Level', 'Senior Level (5+ years)')
        ],
        default='Entry Level'
    )
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class ResumeAnalysis(models.Model):
    """
    Stores uploaded resume metadata, extracted text, NLP extracted skills,
    score breakdown, and AI/NLP career recommendations.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    resume_file = models.FileField(upload_to='resumes/')
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Optional target job description provided by candidate/recruiter
    job_description = models.TextField(blank=True, null=True)
    
    # Extracted text from PDF/DOCX/TXT
    raw_text = models.TextField(blank=True)
    
    # NLP & Analysis Results (Stored as JSON structures)
    extracted_skills = models.JSONField(default=list, help_text="List of recognized skills")
    detected_sections = models.JSONField(default=list, help_text="Detected resume sections like Education, Experience, Skills")
    
    # Overall Resume Score (0-100) and transparent component breakdown
    score = models.IntegerField(default=0, help_text="Score between 0 and 100")
    score_breakdown = models.JSONField(default=dict, help_text="Detailed points for completeness, sections, skills")
    
    # When job description is matched:
    matched_skills = models.JSONField(default=list, help_text="Skills found in both resume and job description")
    missing_skills = models.JSONField(default=list, help_text="Job description skills absent in resume")
    
    # Career and job recommendation categories
    recommendations = models.JSONField(default=list, help_text="Recommended career paths based on skill profile")
    
    # Strengths and feedback
    strengths = models.JSONField(default=list)
    improvements = models.JSONField(default=list)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Resume Analysis'
        verbose_name_plural = 'Resume Analyses'

    def __str__(self):
        return f"{self.original_filename} - {self.user.username} ({self.score}/100)"

    def delete(self, *args, **kwargs):
        """Clean up actual uploaded resume file from disk when record is deleted."""
        if self.resume_file and os.path.isfile(self.resume_file.path):
            try:
                os.remove(self.resume_file.path)
            except OSError:
                pass
        super().delete(*args, **kwargs)
