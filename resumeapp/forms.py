"""
Forms for AI Resume Analysis
----------------------------
- User Registration and Authentication
- Resume Upload with server-side validation
- User Profile Management
"""

import os
import zipfile
from io import BytesIO

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import ResumeAnalysis, UserProfile


# =========================================================
# RESUME UPLOAD SETTINGS
# =========================================================

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# =========================================================
# RESUME UPLOAD FORM
# =========================================================

class ResumeUploadForm(forms.ModelForm):
    """
    Form for uploading PDF, DOCX, or TXT resumes.

    Features:
    - File extension validation
    - File size validation
    - Basic file signature validation
    - DOCX container validation
    - Optional job description
    """

    job_description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": (
                    "Paste the job description here (optional). "
                    "The AI will compare your resume against these "
                    "requirements to identify matching and missing skills."
                ),
            }
        ),
        label="Target Job Description (Optional)",
    )

    class Meta:
        model = ResumeAnalysis
        fields = ["resume_file", "job_description"]

        widgets = {
            "resume_file": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "id": "resumeFileInput",
                    "accept": ".pdf,.docx,.txt",
                }
            )
        }

    def clean_resume_file(self):
        uploaded_file = self.cleaned_data.get("resume_file")

        # 1. Check whether a file was selected.
        if not uploaded_file:
            raise ValidationError(
                "Please select a resume file to upload."
            )

        # 2. Reject empty files.
        if uploaded_file.size == 0:
            raise ValidationError(
                "The submitted file is empty. Please upload a valid document."
            )

        # 3. Validate extension.
        extension = os.path.splitext(uploaded_file.name)[1].lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Unsupported file type '{extension}'. "
                "Please upload a PDF (.pdf), Word (.docx), "
                "or Text (.txt) file."
            )

        # 4. Validate file size.
        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            actual_size_mb = uploaded_file.size / (1024 * 1024)

            raise ValidationError(
                f"File size exceeds the {MAX_FILE_SIZE_MB} MB limit. "
                f"Your file is {actual_size_mb:.1f} MB."
            )

        try:
            # Read a small header and restore the pointer afterwards.
            header = uploaded_file.read(2048)
            uploaded_file.seek(0)

            # -------------------------------------------------
            # PDF VALIDATION
            # -------------------------------------------------
            if extension == ".pdf":

                # PDF headers are normally at the beginning, but
                # some valid files have leading bytes.
                if b"%PDF-" not in header[:1024]:
                    raise ValidationError(
                        "Invalid PDF file. The uploaded file does not appear to be "
                        "a valid PDF. Please select a genuine PDF file."
                    )

            # -------------------------------------------------
            # DOCX VALIDATION
            # -------------------------------------------------
            elif extension == ".docx":

                # DOCX is a ZIP-based Office Open XML document.
                if not header.startswith(b"PK"):
                    raise ValidationError(
                        "Invalid Word document. Please upload a valid "
                        ".docx file instead of renaming another file."
                    )

                # Validate the ZIP container and essential DOCX parts.
                try:
                    uploaded_file.seek(0)

                    with zipfile.ZipFile(uploaded_file) as document:
                        names = set(document.namelist())

                        required_parts = {
                            "[Content_Types].xml",
                            "word/document.xml",
                        }

                        if not required_parts.issubset(names):
                            raise ValidationError(
                                "The uploaded file is not a valid DOCX "
                                "document. Please save it as a Word "
                                "Document (.docx) and try again."
                            )

                        # Check that the ZIP archive can be read.
                        bad_file = document.testzip()

                        if bad_file is not None:
                            raise ValidationError(
                                "The Word document appears to be "
                                "corrupted. Please upload another copy."
                            )

                except ValidationError:
                    raise

                except (zipfile.BadZipFile, OSError, EOFError):
                    raise ValidationError(
                        "The Word document is corrupted or invalid. "
                        "Please upload a valid .docx file."
                    )

            # -------------------------------------------------
            # TXT VALIDATION
            # -------------------------------------------------
            elif extension == ".txt":

                # Reject files that appear to contain binary data.
                if b"\x00" in header:
                    raise ValidationError(
                        "Invalid text file. File contains binary null characters. "
                        "Please upload a plain-text .txt file."
                    )

                # Check whether the content can be decoded as text.
                uploaded_file.seek(0)
                content = uploaded_file.read()

                try:
                    content.decode("utf-8-sig")
                except UnicodeDecodeError:
                    try:
                        content.decode("cp1252")
                    except UnicodeDecodeError:
                        raise ValidationError(
                            "The text file encoding is not supported. "
                            "Please save the file as UTF-8 text and retry."
                        )

        except ValidationError:
            raise

        except Exception:
            raise ValidationError(
                "An error occurred while validating the uploaded file. "
                "Please check the document and try again."
            )

        finally:
            # Ensure the file pointer is reset for subsequent processing.
            try:
                uploaded_file.seek(0)
            except (AttributeError, OSError):
                pass

        return uploaded_file


# =========================================================
# USER REGISTRATION FORM
# =========================================================

class UserRegisterForm(forms.ModelForm):
    """
    Registration form with:
    - Unique username validation
    - Unique email validation
    - Password strength validation
    - Password confirmation
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "name@example.com",
            }
        ),
    )

    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "First Name",
            }
        ),
    )

    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last Name",
            }
        ),
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter Password",
            }
        ),
        label="Password",
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm Password",
            }
        ),
        label="Confirm Password",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
        ]

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Choose a username",
                }
            )
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if username and User.objects.filter(
            username__iexact=username
        ).exists():
            raise ValidationError(
                "This username is already taken. Please choose another."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if email and User.objects.filter(
            email__iexact=email
        ).exists():
            raise ValidationError(
                "An account with this email address already exists."
            )

        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")

        if password:
            username = self.cleaned_data.get("username")

            user = User(
                username=username or "",
                email=self.cleaned_data.get("email", ""),
                first_name=self.cleaned_data.get("first_name", ""),
                last_name=self.cleaned_data.get("last_name", ""),
            )

            validate_password(password, user=user)

        return password

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error(
                "confirm_password",
                "Passwords do not match.",
            )

        return cleaned_data


# =========================================================
# USER PROFILE FORM
# =========================================================

class UserProfileForm(forms.ModelForm):
    """
    Form for updating user profile information and career preferences.
    """

    class Meta:
        model = UserProfile

        fields = [
            "phone",
            "target_role",
            "experience_level",
            "bio",
        ]

        widgets = {
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+91 9876543210",
                }
            ),

            "target_role": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Python Developer",
                }
            ),

            "experience_level": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Brief summary about yourself",
                }
            ),
        }