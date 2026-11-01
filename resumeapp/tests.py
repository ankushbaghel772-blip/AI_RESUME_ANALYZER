"""
Comprehensive Test Suite for AI Resume Analysis System.
Covers:
- Public and Protected View Access
- User Authentication (Signup, Login, POST Logout, Open Redirect Defense)
- Password Validation Enforcement & Duplicate Data Handling
- NLP and Text Processing Services
- Skill Extraction, Tricky Characters (C++, C#, Go, R, C), and Anti-False-Positive Rules
- Resume Scoring Engine (f-string formatting, empty text handling, bounds)
- Scikit-Learn TF-IDF Semantic Job Description Comparison
- Career Recommendations
- Upload Validation (PDF, DOCX, TXT, Empty/Corrupted Files) & Database Persistence
- Multi-User Data Isolation & Security
"""

import os
from unittest.mock import patch
from django.test import TestCase, Client, SimpleTestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import ResumeAnalysis, UserProfile
from .services.text_extractor import extract_text_from_txt, extract_resume_text
from .services.text_preprocessor import clean_and_normalize_text, detect_sections
from .services.skill_extractor import extract_skills_from_text, compare_with_job_description
from .services.resume_scorer import compute_resume_score
from .services.job_recommender import recommend_career_paths
from .services.bert_matcher import score_resume_job
from ml.classifier import classify_resume_text


class BertMatcherServiceTests(SimpleTestCase):
    def test_sentence_transformer_returns_raw_cosine_signal(self):
        class FakeTokenizer:
            def encode(self, text, add_special_tokens=False):
                return [1, 2, 3]

            def decode(self, tokens, **kwargs):
                return "test text"

        class FakeModel:
            tokenizer = FakeTokenizer()
            max_seq_length = 256

            def __init__(self):
                self.vectors = iter([[[1.0, 0.0]], [[0.8, 0.6]]])

            def encode(self, texts, **kwargs):
                return next(self.vectors)

        with patch('resumeapp.services.bert_matcher._load_model', return_value=FakeModel()):
            result = score_resume_job('resume text', 'job description')

        self.assertTrue(result['available'])
        self.assertEqual(result['cosine_similarity'], 0.8)
        self.assertFalse(result['fine_tuned'])
        self.assertIn('not a probability', result['interpretation'])

    def test_empty_pair_does_not_load_model(self):
        with patch('resumeapp.services.bert_matcher._load_model') as load_model:
            result = score_resume_job('', 'job description')
        self.assertFalse(result['available'])
        load_model.assert_not_called()

    def test_missing_model_returns_unavailable_without_raising(self):
        with patch('resumeapp.services.bert_matcher._load_model', side_effect=FileNotFoundError):
            result = score_resume_job('resume text', 'job description')
        self.assertFalse(result['available'])
        self.assertIn('unavailable', result['message'].lower())


class PublicViewsTests(TestCase):
    """Tests for public endpoints: Home and About pages."""
    def setUp(self):
        self.client = Client()

    def test_homepage_status(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Resume Analysis")

    def test_about_page_status(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About AI Resume Analysis System")


class AuthenticationTests(TestCase):
    """Tests for Signup, Login, Password Validation, and Logout flows."""
    def setUp(self):
        self.client = Client()
        self.username = "testuser"
        self.email = "testuser@example.com"
        self.password = "SecurePass123!"

    def test_user_signup_success(self):
        response = self.client.post(reverse('signup'), {
            'username': self.username,
            'email': self.email,
            'first_name': 'Test',
            'last_name': 'User',
            'password': self.password,
            'confirm_password': self.password
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username=self.username).exists())
        user = User.objects.get(username=self.username)
        self.assertTrue(user.check_password(self.password))
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_user_signup_weak_password_rejected(self):
        """Ensures Django password validation rejects short or purely numeric passwords."""
        response = self.client.post(reverse('signup'), {
            'username': 'weakuser',
            'email': 'weakuser@example.com',
            'password': '123',
            'confirm_password': '123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='weakuser').exists())
        self.assertContains(response, "This password is too short")

    def test_user_signup_password_mismatch(self):
        response = self.client.post(reverse('signup'), {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': self.password,
            'confirm_password': 'DifferentPassword123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatchuser').exists())
        self.assertContains(response, "Passwords do not match")

    def test_user_signup_duplicate_username(self):
        User.objects.create_user(username=self.username, email="another@example.com", password=self.password)
        response = self.client.post(reverse('signup'), {
            'username': self.username,
            'email': 'newunique@example.com',
            'password': self.password,
            'confirm_password': self.password
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This username is already taken")

    def test_user_signup_duplicate_email(self):
        User.objects.create_user(username="originaluser", email=self.email, password=self.password)
        response = self.client.post(reverse('signup'), {
            'username': 'brandnewuser',
            'email': self.email,
            'password': self.password,
            'confirm_password': self.password
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email address already exists")

    def test_user_login_and_post_logout(self):
        User.objects.create_user(username=self.username, email=self.email, password=self.password)
        login_resp = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(login_resp.status_code, 302)
        self.assertRedirects(login_resp, reverse('dashboard'))

        # Secure POST Logout
        logout_resp = self.client.post(reverse('logout'))
        self.assertEqual(logout_resp.status_code, 302)
        self.assertRedirects(logout_resp, reverse('home'))

    def test_user_get_logout_redirects_safely(self):
        """GET requests to logout must not perform logout and must redirect safely."""
        user = User.objects.create_user(username=self.username, email=self.email, password=self.password)
        self.client.login(username=self.username, password=self.password)
        
        get_logout_resp = self.client.get(reverse('logout'))
        self.assertEqual(get_logout_resp.status_code, 302)
        self.assertRedirects(get_logout_resp, reverse('dashboard'))
        # User must still be authenticated
        dash_resp = self.client.get(reverse('dashboard'))
        self.assertEqual(dash_resp.status_code, 200)

    def test_user_login_with_valid_internal_next_url(self):
        User.objects.create_user(username=self.username, email=self.email, password=self.password)
        response = self.client.post(f"{reverse('login')}?next=/history/", {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/history/')

    def test_user_login_with_malicious_external_next_url(self):
        """Open redirect defense: external domains must be rejected in favor of dashboard."""
        User.objects.create_user(username=self.username, email=self.email, password=self.password)
        response = self.client.post(f"{reverse('login')}?next=https://malicious-phishing-site.com", {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))


class ProtectedPagesAccessTests(TestCase):
    """Ensures unauthorized anonymous requests are safely redirected to login."""
    def setUp(self):
        self.client = Client()

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_upload_requires_login(self):
        response = self.client.get(reverse('upload'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_history_requires_login(self):
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_job_recommendations_requires_login(self):
        response = self.client.get(reverse('job_recommendations'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)


class NLPServicesUnitTests(TestCase):
    """Unit tests for Text Preprocessing, Skill Extraction, Scoring, and Recommendations."""
    def setUp(self):
        self.sample_text = """
        John Doe | Contact: john@example.com | 123-456-7890
        Professional Summary:
        Experienced software engineer with 3 years building web applications and ML systems.
        Technical Skills:
        Python, Django, PostgreSQL, Docker, Git, Machine Learning, Pandas, Scikit-Learn, HTML, CSS.
        Work Experience:
        Software Developer at TechCorp. Built scalable REST APIs using Django and Docker.
        Education:
        B.S. in Computer Science, University of Technology.
        Projects:
        AI Resume Analysis Platform with NLP skill extraction.
        """

    def test_text_cleaning_and_normalization(self):
        raw = "  Python  \t  Developer   \n\n\n\n Django   "
        cleaned = clean_and_normalize_text(raw)
        self.assertEqual(cleaned, "Python Developer\n\nDjango")

    def test_section_detection(self):
        sections = detect_sections(self.sample_text)
        self.assertIn('Technical Skills', sections)
        self.assertIn('Work Experience', sections)
        self.assertIn('Education', sections)
        self.assertIn('Projects', sections)

    def test_skill_extraction_accuracy(self):
        skills_data = extract_skills_from_text(self.sample_text)
        skills = skills_data['skills']
        self.assertIn('Python', skills)
        self.assertIn('Django', skills)
        self.assertIn('Machine Learning', skills)
        self.assertIn('Docker', skills)
        self.assertIn('PostgreSQL', skills)
        # Verify no false positive for Java inside JavaScript
        self.assertNotIn('Java', skills)

    def test_skill_extraction_special_characters_and_edge_cases(self):
        """Verifies special-character languages (C++, C#) and short skills (Go, R, C)."""
        # C++ and C#
        text_cpp_cs = "Proficient in C++ and C# with .NET framework development."
        res_cpp_cs = extract_skills_from_text(text_cpp_cs)['skills']
        self.assertIn('C++', res_cpp_cs)
        self.assertIn('C#', res_cpp_cs)

        # Go and R in valid technical contexts
        text_go_r = "Skills: Python, Go, Rust. Data analysis using Python, R, SQL."
        res_go_r = extract_skills_from_text(text_go_r)['skills']
        self.assertIn('Go', res_go_r)
        self.assertIn('R', res_go_r)

        # C language in valid technical contexts
        text_c = "Languages: Python, C, Java, C++."
        res_c = extract_skills_from_text(text_c)['skills']
        self.assertIn('C', res_c)
        self.assertIn('C++', res_c)
        self.assertIn('Java', res_c)

        # Anti-False-Positive tests
        text_false_pos = "John R. Smith received Grade C in school. He is ready to go to the company with 500 ml water."
        res_false_pos = extract_skills_from_text(text_false_pos)['skills']
        self.assertNotIn('R', res_false_pos)
        self.assertNotIn('C', res_false_pos)
        self.assertNotIn('Go', res_false_pos)
        self.assertNotIn('Machine Learning', res_false_pos)

    def test_job_description_comparison(self):
        resume_skills = ['Python', 'Django', 'PostgreSQL', 'Docker']
        job_desc = "Looking for a Python Developer proficient in Python, Django, AWS, and Kubernetes."
        resume_sample = "Experienced Python and Django developer with PostgreSQL and Docker microservices."
        comparison = compare_with_job_description(resume_skills, job_desc, resume_text=resume_sample)
        self.assertIn('Python', comparison['matched_skills'])
        self.assertIn('Django', comparison['matched_skills'])
        self.assertIn('AWS', comparison['missing_skills'])
        self.assertIn('Kubernetes', comparison['missing_skills'])
        self.assertGreaterEqual(comparison['match_percentage'], 50.0)
        # Check TF-IDF semantic similarity was computed
        self.assertIn('semantic_similarity', comparison)
        self.assertGreaterEqual(comparison['semantic_similarity'], 0.0)

    def test_resume_scoring_calculation(self):
        detected_sections = ['Technical Skills', 'Work Experience', 'Education', 'Projects']
        extracted_skills = ['Python', 'Django', 'Docker', 'PostgreSQL', 'Git', 'Pandas']
        score_res = compute_resume_score(self.sample_text, detected_sections, extracted_skills)
        self.assertGreaterEqual(score_res['total_score'], 0)
        self.assertLessEqual(score_res['total_score'], 100)
        self.assertIn('breakdown', score_res)
        self.assertTrue(len(score_res['strengths']) > 0)

    def test_resume_scoring_string_formatting_no_literal_bracket(self):
        """Verifies that {word_count} is never output literally in score improvements."""
        short_text = "Brief resume text with Python and Django."
        score_res = compute_resume_score(short_text, ['Technical Skills'], ['Python', 'Django'])
        for imp in score_res['improvements']:
            self.assertNotIn("{word_count}", imp)
        # Verify word count is present as real number
        improvements_text = " ".join(score_res['improvements'])
        self.assertIn(f"({len(short_text.split())} words)", improvements_text)

    def test_resume_scoring_empty_text(self):
        score_res = compute_resume_score("", [], [])
        self.assertEqual(score_res['total_score'], 0)
        self.assertEqual(score_res['breakdown']['word_count'], 0)
        self.assertTrue(any("no readable text" in imp.lower() for imp in score_res['improvements']))

    def test_career_recommendations(self):
        extracted_skills = ['Python', 'Django', 'SQL', 'PostgreSQL', 'Git', 'Docker']
        recs = recommend_career_paths(extracted_skills)
        self.assertTrue(len(recs) > 0)
        top_role = recs[0]
        self.assertIn(top_role['role_title'], ['Python Developer', 'Backend Developer'])
        self.assertGreater(top_role['match_percentage'], 0)


class ResumeUploadAndDataIsolationTests(TestCase):
    """Tests file upload processing and multi-user data isolation."""
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="alice", password="Password123!")
        self.user2 = User.objects.create_user(username="bob", password="Password123!")

        # Create sample analysis for Alice
        self.alice_analysis = ResumeAnalysis.objects.create(
            user=self.user1,
            original_filename="alice_resume.txt",
            raw_text="Alice Resume Python Django SQL",
            extracted_skills=['Python', 'Django', 'SQL'],
            detected_sections=['Technical Skills'],
            score=70,
            score_breakdown={'sections_score': 15, 'skills_score': 25, 'length_score': 10, 'alignment_score': 20}
        )

    def test_user_upload_txt_resume(self):
        self.client.login(username="alice", password="Password123!")
        txt_content = b"Candidate Resume with Python, Django, Git, and Education."
        upload_file = SimpleUploadedFile("my_resume.txt", txt_content, content_type="text/plain")

        response = self.client.post(reverse('upload'), {
            'resume_file': upload_file,
            'job_description': 'Python Developer'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ResumeAnalysis.objects.filter(user=self.user1, original_filename="my_resume.txt").exists())

    @patch('resumeapp.views.score_resume_job', return_value={
        'available': True,
        'cosine_similarity': 0.7132,
        'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
        'fine_tuned': False,
        'interpretation': 'Uncalibrated semantic similarity; not a probability, percentage, or hiring decision.',
    })
    def test_upload_persists_separate_semantic_signal(self, score_resume_job_mock):
        self.client.login(username="alice", password="Password123!")
        upload_file = SimpleUploadedFile(
            "bert_resume.txt",
            b"Technical Skills:\nPython Django SQL\n\nExperience:\nBuilt web applications and REST APIs.",
            content_type="text/plain",
        )
        response = self.client.post(reverse('upload'), {
            'resume_file': upload_file,
            'job_description': 'Python developer with Django and REST API experience',
        })
        self.assertEqual(response.status_code, 302)
        analysis = ResumeAnalysis.objects.get(user=self.user1, original_filename="bert_resume.txt")
        self.assertEqual(analysis.score_breakdown['bert_matching']['cosine_similarity'], 0.7132)
        self.assertGreaterEqual(analysis.score, 0)
        self.assertLessEqual(analysis.score, 100)
        score_resume_job_mock.assert_called_once()

        result_response = self.client.get(response.url)
        self.assertEqual(result_response.status_code, 200)
        self.assertContains(result_response, "Sentence Transformer semantic signal")
        self.assertContains(result_response, "0.7132")

        report_response = self.client.get(reverse('download_report', kwargs={'analysis_id': analysis.id}))
        self.assertEqual(report_response.status_code, 200)
        self.assertIn("SENTENCE TRANSFORMER SEMANTIC SIMILARITY", report_response.content.decode('utf-8'))

    def test_user_upload_empty_file_rejected(self):
        self.client.login(username="alice", password="Password123!")
        empty_file = SimpleUploadedFile("empty_resume.txt", b"", content_type="text/plain")

        response = self.client.post(reverse('upload'), {
            'resume_file': empty_file,
            'job_description': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ResumeAnalysis.objects.filter(original_filename="empty_resume.txt").exists())
        self.assertContains(response, "The submitted file is empty")

    def test_user_upload_whitespace_file_rejected(self):
        """A file with only whitespace or no readable characters must fail text extraction."""
        self.client.login(username="alice", password="Password123!")
        blank_file = SimpleUploadedFile("blank.txt", b"   \n   \t  \n  ", content_type="text/plain")

        response = self.client.post(reverse('upload'), {
            'resume_file': blank_file,
            'job_description': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ResumeAnalysis.objects.filter(original_filename="blank.txt").exists())
        self.assertContains(response, "Could not extract text from the file")

    def test_user_upload_unsupported_file_rejected(self):
        self.client.login(username="alice", password="Password123!")
        unsupported_file = SimpleUploadedFile("script.exe", b"binary content", content_type="application/octet-stream")

        response = self.client.post(reverse('upload'), {
            'resume_file': unsupported_file,
            'job_description': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ResumeAnalysis.objects.filter(original_filename="script.exe").exists())
        self.assertContains(response, "Unsupported file type")

    def test_user_cannot_view_another_users_result(self):
        # Bob logs in and tries to access Alice's analysis ID
        self.client.login(username="bob", password="Password123!")
        response = self.client.get(reverse('result', kwargs={'analysis_id': self.alice_analysis.id}))
        # Should return 404 Not Found to prevent data leakage
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_another_users_record(self):
        # Bob tries to delete Alice's analysis
        self.client.login(username="bob", password="Password123!")
        response = self.client.post(reverse('delete_resume', kwargs={'analysis_id': self.alice_analysis.id}))
        self.assertEqual(response.status_code, 404)
        # Alice's record must still exist
        self.assertTrue(ResumeAnalysis.objects.filter(id=self.alice_analysis.id).exists())

    def test_history_shows_only_current_user_records(self):
        self.client.login(username="bob", password="Password123!")
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 200)
        # Alice's resume must not appear in Bob's history view
        self.assertNotContains(response, "alice_resume.txt")

    def test_profile_view_and_update(self):
        self.client.login(username="alice", password="Password123!")
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)

        update_resp = self.client.post(reverse('profile'), {
            'phone': '+1 555 123 4567',
            'target_role': 'Python Developer',
            'experience_level': 'Mid Level',
            'bio': 'Passionate Python developer building AI applications.'
        })
        self.assertEqual(update_resp.status_code, 302)
        profile = UserProfile.objects.get(user=self.user1)
        self.assertEqual(profile.target_role, 'Python Developer')
        self.assertEqual(profile.experience_level, 'Mid Level')


class NewFeaturesAndSecurityTests(TestCase):
    """Tests for Magic Bytes Validation, ML Classification, Report Generation, File Download, Comparison, and History Search."""
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="alice", password="Password123!")
        self.user2 = User.objects.create_user(username="bob", password="Password123!")

        # Create sample analysis for Alice
        sample_file = SimpleUploadedFile("alice_v1.txt", b"Technical Skills:\nPython, Django, SQL\n\nExperience:\nBuilt APIs.", content_type="text/plain")
        self.analysis1 = ResumeAnalysis.objects.create(
            user=self.user1,
            original_filename="alice_v1.txt",
            resume_file=sample_file,
            raw_text="Alice Resume Python Django SQL",
            extracted_skills=['Python', 'Django', 'SQL'],
            detected_sections=['Technical Skills', 'Experience'],
            score=70,
            score_breakdown={'sections_score': 15, 'skills_score': 25, 'length_score': 10, 'alignment_score': 20}
        )
        self.analysis2 = ResumeAnalysis.objects.create(
            user=self.user1,
            original_filename="alice_v2.txt",
            raw_text="Alice Resume Python Django SQL Docker Kubernetes Machine Learning",
            extracted_skills=['Python', 'Django', 'SQL', 'Docker', 'Kubernetes', 'Machine Learning'],
            detected_sections=['Technical Skills', 'Experience', 'Projects'],
            score=88,
            score_breakdown={'sections_score': 20, 'skills_score': 35, 'length_score': 13, 'alignment_score': 20}
        )

    def test_section_detection_no_false_positives_on_narrative_text(self):
        """Verifies that words like 'experience' and 'college' inside ordinary sentences do not falsely trigger sections."""
        narrative = "I have extensive experience collaborating with different college clubs and school sports teams."
        detected = detect_sections(narrative)
        self.assertNotIn("Work Experience", detected)
        self.assertNotIn("Education", detected)

    def test_magic_bytes_rejects_disguised_pdf(self):
        """A file with .pdf extension but binary executable / plain invalid header must be rejected."""
        self.client.login(username="alice", password="Password123!")
        fake_pdf = SimpleUploadedFile("fake.pdf", b"MZ\x90\x00NotARealPdfHeaderAtAll", content_type="application/pdf")
        response = self.client.post(reverse('upload'), {
            'resume_file': fake_pdf,
            'job_description': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid PDF file")

    def test_magic_bytes_rejects_txt_with_null_bytes(self):
        """A .txt file containing embedded null bytes (indicative of compiled binaries) must be rejected."""
        self.client.login(username="alice", password="Password123!")
        binary_txt = SimpleUploadedFile("binary.txt", b"Hello\x00World\x00Disguised", content_type="text/plain")
        response = self.client.post(reverse('upload'), {
            'resume_file': binary_txt,
            'job_description': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "File contains binary null characters")

    def test_ml_classifier_inference(self):
        """Verifies the trained TF-IDF classifier predicts technical roles with probability distributions."""
        resume_text = "Expert Python Developer with Django, Flask, PostgreSQL, Docker, Git, REST APIs, Microservices, and Celery."
        pred = classify_resume_text(resume_text)
        self.assertIsNotNone(pred)
        self.assertIn(pred['predicted_role'], ['Python Developer', 'Backend Developer', 'Web Developer', 'Data Scientist', 'Machine Learning Engineer'])
        self.assertGreater(pred['confidence'], 0.0)
        self.assertTrue(len(pred['class_probabilities']) > 0)

    def test_download_analysis_report_authorized_and_isolated(self):
        """Alice can download her report; Bob receives 404 trying to access Alice's report."""
        self.client.login(username="alice", password="Password123!")
        res = self.client.get(reverse('download_report', kwargs={'analysis_id': self.analysis1.id}))
        self.assertEqual(res.status_code, 200)
        self.assertIn("attachment; filename=", res['Content-Disposition'])
        self.assertIn("RESUME ANALYSIS REPORT", res.content.decode('utf-8'))
        self.assertIn("Overall ATS Score   : 70 / 100", res.content.decode('utf-8'))

        # Bob attempt
        self.client.login(username="bob", password="Password123!")
        res_bob = self.client.get(reverse('download_report', kwargs={'analysis_id': self.analysis1.id}))
        self.assertEqual(res_bob.status_code, 404)

    def test_download_original_resume_authorized_and_isolated(self):
        """Alice can download her uploaded resume file; Bob receives 404."""
        self.client.login(username="alice", password="Password123!")
        res = self.client.get(reverse('download_original_resume', kwargs={'analysis_id': self.analysis1.id}))
        self.assertEqual(res.status_code, 200)

        # Bob attempt
        self.client.login(username="bob", password="Password123!")
        res_bob = self.client.get(reverse('download_original_resume', kwargs={'analysis_id': self.analysis1.id}))
        self.assertEqual(res_bob.status_code, 404)

    def test_compare_resumes_view(self):
        """Alice compares her two resumes side-by-side."""
        self.client.login(username="alice", password="Password123!")
        # GET selection page
        res = self.client.get(reverse('compare_resumes'))
        self.assertEqual(res.status_code, 200)

        # GET comparison with IDs
        res_compare = self.client.get(f"{reverse('compare_resumes')}?id1={self.analysis1.id}&id2={self.analysis2.id}")
        self.assertEqual(res_compare.status_code, 200)
        self.assertContains(res_compare, "Performance Delta")
        self.assertContains(res_compare, "+18 pts Improvement")

        # Bob cannot compare Alice's resumes
        self.client.login(username="bob", password="Password123!")
        res_bob = self.client.get(f"{reverse('compare_resumes')}?id1={self.analysis1.id}&id2={self.analysis2.id}")
        self.assertEqual(res_bob.status_code, 404)

    def test_history_search_and_sorting(self):
        """Search query 'v2' returns only alice_v2.txt; sorting reorders appropriately."""
        self.client.login(username="alice", password="Password123!")

        # Search
        res_search = self.client.get(f"{reverse('history')}?q=v2")
        self.assertEqual(res_search.status_code, 200)
        self.assertContains(res_search, "alice_v2.txt")
        self.assertNotContains(res_search, "alice_v1.txt")

        # Sorting score ascending (alice_v1: 70 comes before alice_v2: 88)
        res_sort = self.client.get(f"{reverse('history')}?sort=score_low")
        self.assertEqual(res_sort.status_code, 200)
        content = res_sort.content.decode('utf-8')
        idx1 = content.find("alice_v1.txt")
        idx2 = content.find("alice_v2.txt")
        self.assertTrue(idx1 < idx2)

