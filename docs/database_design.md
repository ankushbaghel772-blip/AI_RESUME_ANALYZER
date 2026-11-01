# Database Architecture & Entity Design

## 1. Overview
The database layer is implemented using Django's Object-Relational Mapping (ORM) system. It connects seamlessly to **SQLite** (for zero-configuration local development) or **MySQL / PostgreSQL** (for production environments).

Every record in the system is tied to an authenticated user, enforcing strict multi-tenant isolation so no candidate can view, edit, or delete another candidate's uploaded resumes or analytical evaluations.

---

## 2. Entity-Relationship Overview

```
      ┌────────────────────────┐
      │   django.contrib.auth  │
      │        User            │
      └───────────┬────────────┘
                  │ 1
                  │
        ┌─────────┴─────────┐
        │ 1                 │ *
┌───────▼──────────┐ ┌──────▼──────────────┐
│   UserProfile    │ │   ResumeAnalysis    │
└──────────────────┘ └─────────────────────┘
```

---

## 3. Schema Specifications

### Model: `UserProfile` (`resumeapp_userprofile`)
Extends the core Django `User` model using a 1-to-1 relationship. Stores candidate career aspirations, experience level, and profile details.

| Field Name | Type | Constraints / Attributes | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key, Auto-increment | Unique profile ID |
| `user` | OneToOneField | `to=User`, `on_delete=models.CASCADE`, `related_name='profile'` | Associated user account |
| `phone` | CharField | `max_length=20`, `blank=True` | Contact phone number |
| `target_role` | CharField | `max_length=100`, `blank=True` | Aspired career role (e.g. Python Developer) |
| `experience_level`| CharField | `max_length=20`, `choices=EXPERIENCE_CHOICES`, `default='Fresher'` | Level: Fresher, Junior, Mid Level, Senior, Lead |
| `bio` | TextField | `blank=True` | Candidate summary or biography |
| `created_at` | DateTimeField | `auto_now_add=True` | Profile creation timestamp |
| `updated_at` | DateTimeField | `auto_now=True` | Last modification timestamp |

---

### Model: `ResumeAnalysis` (`resumeapp_resumeanalysis`)
Stores the parsed resume text, uploaded file reference, extracted skills, detected sections, computed scores, and optional job description comparison.

| Field Name | Type | Constraints / Attributes | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key, Auto-increment | Unique analysis ID |
| `user` | ForeignKey | `to=User`, `on_delete=models.CASCADE`, `related_name='analyses'` | Uploading candidate |
| `original_filename`| CharField | `max_length=255` | Sanitized original filename |
| `resume_file` | FileField | `upload_to='resumes/%Y/%m/'`, `blank=True`, `null=True` | File system storage path for original resume |
| `uploaded_at` | DateTimeField | `auto_now_add=True`, `db_index=True` | Upload date and time |
| `raw_text` | TextField | Required | Cleaned extracted plain text |
| `job_description` | TextField | `blank=True` | Optional target job description |
| `extracted_skills` | JSONField | `default=list` | Array of extracted skill strings (e.g. `["Python", "Django"]`) |
| `detected_sections`| JSONField | `default=list` | Array of detected resume headings (e.g. `["Experience", "Skills"]`) |
| `score` | IntegerField | `default=0`, `db_index=True` | Final calculated ATS readiness score (0–100) |
| `score_breakdown` | JSONField | `default=dict` | Breakdown dict: `sections_score`, `skills_score`, `length_score`, etc. |
| `analysis_metadata`| JSONField | `default=dict` | Storage for strengths, suggestions, ML prediction, match percent |

---

## 4. Integrity and Security Controls
1. **Cascade Deletions (`on_delete=models.CASCADE`)**:
   Deleting a user automatically purges their `UserProfile` and all associated `ResumeAnalysis` records, preventing orphaned data.
2. **Database Indices**:
   - `uploaded_at` is indexed for fast reverse-chronological sorting in the user's dashboard and history.
   - `score` is indexed for fast ascending/descending filtering.
3. **Data Isolation (Multi-Tenancy)**:
   All queries inside views use `ResumeAnalysis.objects.filter(user=request.user)`. Attempting to access an analysis belonging to another user returns a strict `404 Not Found`.
