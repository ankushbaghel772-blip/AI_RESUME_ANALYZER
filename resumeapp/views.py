"""
Views for AI Resume Analysis:
Handles home, about, authentication, dashboard, upload & processing pipeline,
result display, history, profile, and career recommendations.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.http import HttpResponse, FileResponse, Http404
import os

from .models import ResumeAnalysis, UserProfile
from .forms import ResumeUploadForm, UserRegisterForm, UserProfileForm
from .services.text_extractor import extract_resume_text
from .services.text_preprocessor import clean_and_normalize_text, detect_sections
from .services.skill_extractor import extract_skills_from_text, compare_with_job_description
from .services.resume_scorer import compute_resume_score
from .services.job_recommender import recommend_career_paths
from .services.bert_matcher import score_resume_job
from ml.classifier import classify_resume_text


# ---------------------------------------------------------
# Public Views: Home & About
# ---------------------------------------------------------

def home(request):
    """Landing page featuring system capabilities, process workflow, and CTAs."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'resumeapp/home.html')


def about(request):
    """About page explaining project architecture, NLP methodology, and scoring."""
    return render(request, 'resumeapp/about.html')


# ---------------------------------------------------------
# Authentication Views: Register, Login, Logout
# ---------------------------------------------------------

def user_signup(request):
    """Handles new user account registration with secure password hashing."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create associated UserProfile
            UserProfile.objects.create(user=user)
            
            # Log the user in directly after signup
            login(request, user)
            messages.success(request, f"Welcome to AI Resume Analysis, {user.username}! Your account has been created.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, 'resumeapp/signup.html', {'form': form})


from django.utils.http import url_has_allowed_host_and_scheme

def user_login(request):
    """
    Handles user login authentication and session initialization.
    Validates redirect destinations to prevent Open Redirect attacks.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                
                # Check next parameter safely (CWE-601 Open Redirect mitigation)
                next_url = request.POST.get('next') or request.GET.get('next')
                if not next_url or not url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                ):
                    next_url = 'dashboard'
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'resumeapp/login.html', {'form': form})


def user_logout(request):
    """
    Logs out the user securely via POST request and clears the session.
    Protects against accidental prefetch logouts and CSRF attacks.
    """
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been successfully logged out.")
        return redirect('home')
    
    # If accessed via GET, safely redirect back to dashboard or home
    return redirect('dashboard' if request.user.is_authenticated else 'home')


# ---------------------------------------------------------
# Dashboard View
# ---------------------------------------------------------

@login_required
def dashboard(request):
    """User dashboard showing summary statistics, recent analyses, and quick actions."""
    user_resumes = ResumeAnalysis.objects.filter(user=request.user)
    total_count = user_resumes.count()
    recent_analyses = user_resumes[:5]
    
    latest_resume = user_resumes.first()
    latest_score = latest_resume.score if latest_resume else None
    
    # Collect all unique skills extracted across user's resumes
    all_skills = set()
    for r in user_resumes[:10]:
        for s in r.extracted_skills:
            all_skills.add(s)
            
    # Calculate average score
    avg_score = user_resumes.aggregate(Avg('score'))['score__avg']
    avg_score = round(avg_score, 1) if avg_score else 0.0

    context = {
        'total_count': total_count,
        'recent_analyses': recent_analyses,
        'latest_resume': latest_resume,
        'latest_score': latest_score,
        'avg_score': avg_score,
        'skills_count': len(all_skills),
        'top_skills': sorted(list(all_skills))[:8],
    }
    return render(request, 'resumeapp/dashboard.html', context)


# ---------------------------------------------------------
# Resume Upload & NLP Analysis Pipeline View
# ---------------------------------------------------------

@login_required
def upload_resume(request):
    """
    Accepts PDF, DOCX, and TXT resume files with optional job description.
    Runs text extraction, cleaning, section detection, skill matching,
    resume scoring, and career recommendations.
    """
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['resume_file']
            job_description = form.cleaned_data.get('job_description', '')
            
            # Step 1: Text Extraction
            raw_text, extract_error = extract_resume_text(uploaded_file)
            
            if not raw_text.strip():
                error_msg = extract_error or "Could not extract text from the file. Please ensure the file is not empty or password protected."
                messages.error(request, error_msg)
                return render(request, 'resumeapp/upload.html', {'form': form})
                
            # Step 2: Text Preprocessing & Cleaning
            cleaned_text = clean_and_normalize_text(raw_text)
            
            # Step 3: Section Detection
            detected_sections = detect_sections(cleaned_text)
            
            # Step 4: Skill Extraction
            skill_result = extract_skills_from_text(cleaned_text)
            extracted_skills = skill_result['skills']
            
            # Step 5: Optional Job Description Comparison
            jd_comparison = None
            matched_skills = []
            missing_skills = []
            if job_description.strip():
                jd_comparison = compare_with_job_description(
                    extracted_skills, job_description, resume_text=cleaned_text
                )
                matched_skills = jd_comparison['matched_skills']
                missing_skills = jd_comparison['missing_skills']
                
            # Step 6: Transparent Scoring Engine
            # Step 6: Transparent Scoring Engine
            scoring_result = compute_resume_score(
                raw_text=cleaned_text,
                detected_sections=detected_sections,
                extracted_skills=extracted_skills,
                jd_comparison=jd_comparison
            )

            # Keep the Sentence Transformer signal separate from the transparent ATS score.
            if job_description.strip():
                scoring_result['breakdown']['bert_matching'] = score_resume_job(
                    cleaned_text, job_description
                )
            
            # Step 7: Machine Learning Career Track Classification
            ml_classification = classify_resume_text(cleaned_text)
            if ml_classification:
                scoring_result['breakdown']['ml_classification'] = ml_classification
            
            # Step 8: Career Track Recommendations
            recommendations = recommend_career_paths(extracted_skills)
            
            # Step 9: Save to Database linked to current user
            analysis = ResumeAnalysis.objects.create(
                user=request.user,
                resume_file=uploaded_file,
                original_filename=uploaded_file.name,
                job_description=job_description,
                raw_text=cleaned_text,
                extracted_skills=extracted_skills,
                detected_sections=detected_sections,
                score=scoring_result['total_score'],
                score_breakdown=scoring_result['breakdown'],
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                recommendations=recommendations,
                strengths=scoring_result['strengths'],
                improvements=scoring_result['improvements'],
            )
            
            messages.success(request, f"Resume '{uploaded_file.name}' analyzed successfully!")
            return redirect('result', analysis_id=analysis.id)
        else:
            messages.error(request, "Upload failed. Please check the file requirements below.")
    else:
        form = ResumeUploadForm()

    return render(request, 'resumeapp/upload.html', {'form': form})


# ---------------------------------------------------------
# Analysis Result View
# ---------------------------------------------------------

@login_required
def result_detail(request, analysis_id):
    """Displays comprehensive analysis findings strictly for the owning user."""
    analysis = get_object_or_404(ResumeAnalysis, id=analysis_id, user=request.user)
    
    # Categorize skills for clean presentation
    categorized_skills = extract_skills_from_text(analysis.raw_text)['categorized']
    
    # Retrieve ML classification details if saved, or compute on-the-fly
    ml_classification = analysis.score_breakdown.get('ml_classification')
    if not ml_classification and analysis.raw_text:
        ml_classification = classify_resume_text(analysis.raw_text)
    
    context = {
        'analysis': analysis,
        'breakdown': analysis.score_breakdown,
        'categorized_skills': categorized_skills,
        'ml_classification': ml_classification,
    }
    return render(request, 'resumeapp/result.html', context)


# ---------------------------------------------------------
# History & Management Views
# ---------------------------------------------------------

@login_required
def history(request):
    """
    Lists past uploaded resumes with search, sorting, pagination,
    and access strictly restricted to the owning user.
    """
    resumes_list = ResumeAnalysis.objects.filter(user=request.user)
    
    # Search filter (filename or raw text keywords)
    query = request.GET.get('q', '').strip()
    if query:
        resumes_list = resumes_list.filter(
            Q(original_filename__icontains=query) | Q(raw_text__icontains=query)
        )
        
    # Sorting filter
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        resumes_list = resumes_list.order_by('uploaded_at')
    elif sort_by == 'score_high':
        resumes_list = resumes_list.order_by('-score', '-uploaded_at')
    elif sort_by == 'score_low':
        resumes_list = resumes_list.order_by('score', '-uploaded_at')
    else:
        resumes_list = resumes_list.order_by('-uploaded_at')
        
    paginator = Paginator(resumes_list, 8)  # 8 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
        'total_results': resumes_list.count()
    }
    return render(request, 'resumeapp/history.html', context)


@login_required
def delete_resume(request, analysis_id):
    """Safely deletes an analysis record and file belonging strictly to current user."""
    analysis = get_object_or_404(ResumeAnalysis, id=analysis_id, user=request.user)
    if request.method == 'POST':
        filename = analysis.original_filename
        analysis.delete()
        messages.success(request, f"Record for '{filename}' was permanently deleted.")
        return redirect('history')
    return redirect('history')


# ---------------------------------------------------------
# Download Reports & Files (Ownership Validated)
# ---------------------------------------------------------

@login_required
def download_analysis_report(request, analysis_id):
    """
    Generates and downloads a clean, professional text summary report
    of the resume analysis results. Strictly enforces user ownership.
    """
    analysis = get_object_or_404(ResumeAnalysis, id=analysis_id, user=request.user)
    
    report_lines = [
        "=" * 70,
        "AI RESUME ANALYSIS REPORT",
        "=" * 70,
        f"Document Name       : {analysis.original_filename}",
        f"Analysis Date       : {analysis.uploaded_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Candidate Username  : {request.user.username}",
        f"Overall ATS Score   : {analysis.score} / 100",
        "-" * 70,
        "SCORE BREAKDOWN:",
        f"  * Section Structure          : {analysis.score_breakdown.get('sections_score', 'N/A')} / {analysis.score_breakdown.get('sections_max', 30)} pts",
        f"  * Technical Skill Richness   : {analysis.score_breakdown.get('skills_score', 'N/A')} / {analysis.score_breakdown.get('skills_max', 35)} pts",
        f"  * Word Count & Length        : {analysis.score_breakdown.get('length_score', 'N/A')} / {analysis.score_breakdown.get('length_max', 15)} pts ({analysis.score_breakdown.get('word_count', 0)} words)",
        f"  * Alignment / Completeness   : {analysis.score_breakdown.get('alignment_score', 'N/A')} / {analysis.score_breakdown.get('alignment_max', 20)} pts",
    ]
    
    ml_cls = analysis.score_breakdown.get('ml_classification')
    if not ml_cls and analysis.raw_text:
        ml_cls = classify_resume_text(analysis.raw_text)
        
    if ml_cls:
        report_lines.extend([
            "-" * 70,
            "MACHINE LEARNING CLASSIFICATION:",
            f"  * Predicted Career Track : {ml_cls.get('predicted_role', 'N/A')}",
            f"  * Model Confidence       : {ml_cls.get('confidence', 'N/A')}%",
            f"  * Classifier Model       : {ml_cls.get('model_name', 'Scikit-Learn')}",
        ])
        
    report_lines.extend([
        "-" * 70,
        f"DETECTED RESUME SECTIONS ({len(analysis.detected_sections)}):",
        "  " + (", ".join(analysis.detected_sections) if analysis.detected_sections else "None detected"),
        "-" * 70,
        f"RECOGNIZED TECHNICAL SKILLS ({len(analysis.extracted_skills)}):",
        "  " + (", ".join(analysis.extracted_skills) if analysis.extracted_skills else "None recognized"),
    ])
    
    if analysis.job_description:
        report_lines.extend([
            "-" * 70,
            "JOB DESCRIPTION MATCHING:",
            f"  * Matched Skills ({len(analysis.matched_skills)}): " + (", ".join(analysis.matched_skills) if analysis.matched_skills else "None"),
            f"  * Missing In-Demand Skills ({len(analysis.missing_skills)}): " + (", ".join(analysis.missing_skills) if analysis.missing_skills else "None"),
        ])
        bert_match = analysis.score_breakdown.get('bert_matching')
        if bert_match:
            report_lines.extend(["", "SENTENCE TRANSFORMER SEMANTIC SIMILARITY:"])
            if bert_match.get('available'):
                report_lines.append(f"  * Cosine Similarity   : {bert_match.get('cosine_similarity')}")
                report_lines.append(f"  * Model               : {bert_match.get('model_name', 'Sentence Transformer')}")
                report_lines.append("  * Note                : Uncalibrated signal; not a probability, percentage, or hiring decision.")
            else:
                report_lines.append("  * Status              : Unavailable; the existing ATS score and classifier are unaffected.")
        
    report_lines.extend([
        "-" * 70,
        "KEY STRENGTHS:",
    ])
    for s in analysis.strengths:
        report_lines.append(f"  [+] {s}")
        
    report_lines.extend([
        "-" * 70,
        "RECOMMENDED IMPROVEMENTS:",
    ])
    for imp in analysis.improvements:
        report_lines.append(f"  [-] {imp}")
        
    report_lines.extend([
        "-" * 70,
        "CAREER PATH RECOMMENDATIONS:",
    ])
    for rec in analysis.recommendations[:4]:
        report_lines.append(f"  * {rec.get('role_title')} ({rec.get('match_percentage')}% Match): {rec.get('rationale')}")
        
    report_lines.extend([
        "=" * 70,
        "DISCLAIMER: This report is an analytical evaluation generated by AI Resume Analysis.",
        "It evaluates keyword presence and formatting structure for educational purposes.",
        "=" * 70
    ])
    
    report_content = "\n".join(report_lines)
    response = HttpResponse(report_content, content_type='text/plain; charset=utf-8')
    filename = f"analysis_report_{analysis.id}.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def download_original_resume(request, analysis_id):
    """
    Allows authenticated users to download their own uploaded resume file.
    Validates user ownership strictly before serving the file.
    """
    analysis = get_object_or_404(ResumeAnalysis, id=analysis_id, user=request.user)
    if not analysis.resume_file or not os.path.isfile(analysis.resume_file.path):
        messages.error(request, "Resume file not found on disk.")
        return redirect('result', analysis_id=analysis.id)
        
    response = FileResponse(open(analysis.resume_file.path, 'rb'), as_attachment=True, filename=analysis.original_filename)
    return response


# ---------------------------------------------------------
# Resume Comparison View
# ---------------------------------------------------------

@login_required
def compare_resumes(request):
    """
    Compares two saved resumes side-by-side for the current user.
    Helps candidates track improvement and skill additions across revisions.
    """
    id1 = request.GET.get('id1')
    id2 = request.GET.get('id2')
    user_resumes = ResumeAnalysis.objects.filter(user=request.user)
    
    resume1 = None
    resume2 = None
    comparison_data = None
    
    if id1 and id2:
        resume1 = get_object_or_404(ResumeAnalysis, id=id1, user=request.user)
        resume2 = get_object_or_404(ResumeAnalysis, id=id2, user=request.user)
        
        skills1 = set(resume1.extracted_skills)
        skills2 = set(resume2.extracted_skills)
        
        common_skills = sorted(list(skills1.intersection(skills2)))
        new_in_resume2 = sorted(list(skills2.difference(skills1)))
        removed_in_resume2 = sorted(list(skills1.difference(skills2)))
        
        score_diff = resume2.score - resume1.score
        
        comparison_data = {
            'common_skills': common_skills,
            'new_in_resume2': new_in_resume2,
            'removed_in_resume2': removed_in_resume2,
            'score_diff': score_diff,
        }
        
    context = {
        'user_resumes': user_resumes,
        'resume1': resume1,
        'resume2': resume2,
        'comparison': comparison_data,
        'selected_id1': int(id1) if id1 and id1.isdigit() else None,
        'selected_id2': int(id2) if id2 and id2.isdigit() else None,
    }
    return render(request, 'resumeapp/compare.html', context)


# ---------------------------------------------------------
# Profile View
# ---------------------------------------------------------

@login_required
def profile_view(request):
    """View and update candidate profile and target career preferences."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been updated.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
        
    user_resumes = ResumeAnalysis.objects.filter(user=request.user)
    total_resumes = user_resumes.count()
    avg_score = user_resumes.aggregate(Avg('score'))['score__avg']
    avg_score = round(avg_score, 1) if avg_score else 0.0

    context = {
        'profile': profile,
        'form': form,
        'total_resumes': total_resumes,
        'avg_score': avg_score,
    }
    return render(request, 'resumeapp/profile.html', context)


# ---------------------------------------------------------
# Career Recommendations View
# ---------------------------------------------------------

@login_required
def job_recommendations(request):
    """Dedicated career recommendations page based on user's latest analyzed resume."""
    latest_resume = ResumeAnalysis.objects.filter(user=request.user).first()
    
    recommendations = []
    ml_prediction = None
    
    if latest_resume:
        recommendations = latest_resume.recommendations
        ml_prediction = latest_resume.score_breakdown.get('ml_classification')
        if not ml_prediction and latest_resume.raw_text:
            ml_prediction = classify_resume_text(latest_resume.raw_text)
    else:
        # Default starter tracks if no resume uploaded yet
        recommendations = recommend_career_paths([])

    context = {
        'latest_resume': latest_resume,
        'recommendations': recommendations,
        'ml_prediction': ml_prediction,
    }
    return render(request, 'resumeapp/job_recommendations.html', context)
