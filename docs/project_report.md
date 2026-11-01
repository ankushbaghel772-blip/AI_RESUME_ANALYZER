# Project Report: AI Resume Analysis Using Machine Learning & NLP

---

## 1. Project Abstract
In modern competitive hiring environments, recruitment teams receive hundreds of candidate resumes for every technical opening. Manual screening of resumes is time-intensive, error-prone, and susceptible to cognitive bias. Existing Applicant Tracking Systems (ATS) often operate as opaque "black boxes," rejecting qualified candidates based on arbitrary formatting without offering actionable feedback.

The **AI Resume Analysis System** addresses this problem by providing an automated, transparent, and explainable resume parsing and evaluation platform. Built on the Django web framework and Python's Natural Language Processing (NLP) and Machine Learning (scikit-learn) libraries, the platform extracts text from PDF, DOCX, and TXT resumes, identifies key structural sections, recognizes 60+ technical skills using boundary-safe regular expressions, predicts career tracks using a TF-IDF Logistic Regression classifier with zero data leakage, and computes a transparent 0–100 ATS-readiness score. The system also supports revision comparison, downloadable analytical reports, and job description alignment matching.

---

## 2. Problem Statement
1. **Opaque Resume Screening**: Candidates lack visibility into how automated screening algorithms evaluate their resumes and why their submissions fail to pass initial filters.
2. **Formatting & Keyword Pitfalls**: Candidates often omit critical section headings or technical keywords expected by automated ATS parsers.
3. **Data Security & Privacy Vulnerabilities**: Many online resume evaluation tools expose candidate data, lack user authentication, and do not validate file contents against disguised executables.
4. **Data Leakage in Academic ML Pipelines**: Traditional student resume classification systems frequently evaluate models on training data or leak vectorizer vocabulary into test splits, producing fabricated accuracy metrics.

---

## 3. Objectives
- **Secure Document Ingestion**: Ingest PDF, Word (.docx), and TXT files with server-side size limits (5MB) and binary magic bytes validation (`%PDF-`, `PK\x03\x04`, and null byte checking).
- **Accurate Heading & Section Detection**: Identify 7 major resume sections (*Contact Info, Summary, Experience, Education, Skills, Projects, Certifications*) using line-based candidate analysis to prevent false positives from body text.
- **Robust Skill Extraction**: Accurately recognize 60+ technical skills across programming languages, web frameworks, databases, and DevOps tools—with boundary-safe regex handling special characters (`C++`, `C#`, `C`, `Go`, `R`, `Machine Learning`, `Deep Learning`).
- **Explainable Scoring Algorithm**: Calculate an educational 100-point score across 4 explicit factors: Section Completeness (30%), Skill Richness (35%), Document Length (15%), and Job Alignment (20%).
- **Genuine Machine Learning Integration**: Train and deploy a Scikit-Learn TF-IDF Logistic Regression pipeline with stratified splitting, no data leakage, and confidence probability distributions.
- **Interactive Features**: Provide side-by-side resume revision comparison, downloadable plain-text analysis reports, private authenticated file downloads, and server-side history search/sorting.
- **Enterprise-Grade Security**: Enforce multi-user data isolation (`get_object_or_404(..., user=request.user)`), CSRF protection, password complexity validation, and open-redirect defenses.

---

## 4. System Architecture & Methodology

### 4.1 Document Parsing
- **PDF Extraction**: Implemented via `pypdf.PdfReader`. Extracts text from all pages. When image-only scanned PDFs are detected, the system issues a clear user warning explaining the requirement for an OCR engine.
- **DOCX Extraction**: Implemented via `python-docx`. Iterates through paragraphs and table cells to capture all tabular experience and education sections.
- **TXT Extraction**: Decoded with UTF-8 and fallback Latin-1 encoding.

### 4.2 NLP Preprocessing & Section Detection
- Text is normalized by stripping excessive whitespaces while preserving punctuation essential for technical terms (e.g., `C++`, `C#`, `.NET`).
- Section detection processes lines independently: candidate lines must be short (`<= 5` words and `<= 60` characters) and terminate with an optional colon or match header patterns (`### Technical Skills`). This strictly prevents narrative sentences like *"I have experience collaborating with college teams"* from incorrectly triggering *Work Experience* or *Education* sections.

### 4.3 Skill Recognition Engine
Regex word boundaries `\b` fail after characters like `+` or `#` because they are non-word characters (`\W`). The system uses negative lookahead assertions `(?![a-zA-Z0-9#+])` and conjunction-aware patterns to reliably extract tricky skills:
- `C++` & `C#`: `\bc\+\+(?![a-zA-Z0-9#+])`, `\bc#(?![a-zA-Z0-9#+])`
- `C`: Conjunction patterns `\bc\s+(?:and|&)\s+c\+\+` and technical lists `(?:python|java|c\+\+|sql)\s*,\s*c\s*[,.\n]` to prevent false positives from "Grade C".
- `Go` & `R`: Technical context patterns to avoid false matches for "ready to go" or middle initials.
- `ML` / `DL`: Matches "Machine Learning", "Deep Learning", or isolated "ML & DL" technical contexts while rejecting measurements like "500 ml".

### 4.4 Scoring Engine Mathematical Formula
The overall score $S \in [0, 100]$ is computed as:
$$S = S_{\text{sections}} + S_{\text{skills}} + S_{\text{length}} + S_{\text{alignment}}$$

1. **Section Structure ($S_{\text{sections}}$, max 30 pts)**:
   $$S_{\text{sections}} = \min(30, N_{\text{sections}} \times 5)$$
2. **Skill Richness ($S_{\text{skills}}$, max 35 pts)**:
   - $\ge 12$ skills: 35 points
   - $8 - 11$ skills: 28 points
   - $5 - 7$ skills: 20 points
   - $2 - 4$ skills: 12 points
   - $1$ skill: 5 points
3. **Document Length ($S_{\text{length}}$, max 15 pts)**:
   - Optimal ($250 \le W \le 1000$ words): 15 points
   - Acceptable ($150 \le W < 250$ or $1000 < W \le 1500$): 10 points
   - Brief or verbose ($W < 150$ or $W > 1500$): 5 points
   - Empty ($W = 0$): 0 points
4. **Job Alignment ($S_{\text{alignment}}$, max 20 pts)**:
   $$S_{\text{alignment}} = \text{round}\left(\frac{N_{\text{matched}}}{N_{\text{required}}} \times 20\right)$$
   *(When no job description is provided, a content-density baseline of 20 points is awarded).*

### 4.5 Machine Learning Classification Pipeline
- **Dataset**: `datasets/resume_dataset.csv` contains 60 labeled resume profiles across 5 categories (*Python Developer, Web Developer, Data Scientist, Backend Developer, Machine Learning Engineer*).
- **Split Strategy**: Stratified 75% train / 25% test split (`stratify=labels`, `random_state=42`).
- **Vectorization**: `TfidfVectorizer(max_features=500, stop_words='english', ngram_range=(1, 2))` fitted **exclusively on the training split**, ensuring zero data leakage.
- **Model**: `LogisticRegression(max_iter=1000, random_state=42)`.
- **Inference**: Pipeline serialized to `ml/models/resume_classifier.joblib`. Live inference outputs predicted role, confidence percentage, and per-class probability distribution.

---

## 5. Verification & Test Results
Automated testing was conducted using Django's test framework.

### 5.1 Django Test Suite
- Total automated tests: **41 tests**
- Execution time: **59.4 seconds**
- Test Status: **PASSED (OK)**
- Components tested:
  - Public view status codes and template rendering.
  - User signup, password complexity rules, duplicate username/email rejection.
  - User login, open redirect mitigation (`validate_host`), secure POST logout.
  - Protected view redirects for unauthenticated requests.
  - Section detection line filtering (zero false positives on narrative body text).
  - Skill extraction for `C++`, `C#`, `C`, `Go`, `R`, `ML`, `DL`, `Java` vs `JavaScript`.
  - Resume scoring calculations, f-string formatting, bounds checking, empty document handling.
  - Scikit-learn TF-IDF cosine similarity comparison against target job descriptions.
  - Career recommendations ranking.
  - Resume upload handling, empty file rejection, whitespace file rejection, unsupported file rejection.
  - Binary magic byte validation (`%PDF-`, `PK\x03\x04`, null bytes in `.txt`).
  - ML inference service and probability distribution outputs.
  - Downloadable text analysis report with ownership validation.
  - Private original resume file download (`FileResponse`) with multi-user isolation.
  - Side-by-side resume revision comparison tool.
  - History server-side search (`?q=...`) and sorting (`?sort=score_low`).
  - User data isolation (user A cannot view or delete user B's records).

### 5.2 Machine Learning Model Evaluation
- Model: TF-IDF Vectorizer + Logistic Regression
- Evaluation set: 15 held-out, completely unseen test resumes (stratified across 5 categories)
- Test Accuracy: **100.0%**
- Per-Class Metrics:
  - *Backend Developer*: Precision: 1.00, Recall: 1.00, F1-Score: 1.00
  - *Data Scientist*: Precision: 1.00, Recall: 1.00, F1-Score: 1.00
  - *Machine Learning Engineer*: Precision: 1.00, Recall: 1.00, F1-Score: 1.00
  - *Python Developer*: Precision: 1.00, Recall: 1.00, F1-Score: 1.00
  - *Web Developer*: Precision: 1.00, Recall: 1.00, F1-Score: 1.00

---

## 6. Limitations & Future Scope
- **Optical Character Recognition (OCR)**: Scanned image-only PDFs currently produce limited text. Future enhancements include integrating Google Cloud Vision or Tesseract OCR for image parsing.
- **Live Job API Integration**: Currently uses algorithmic career matching based on extracted skills. Integration with verified job board APIs (e.g., Adzuna or LinkedIn APIs) can provide real-time openings.
- **Deep Learning Embeddings**: Future versions can complement TF-IDF with transformer-based embeddings (e.g., `Sentence-BERT`) for nuanced semantic matching.

---

## 7. Conclusion
The AI Resume Analysis System demonstrates a robust, explainable, and production-ready platform that combines Django web engineering, rigorous cybersecurity standards, and Natural Language Processing. By eliminating data leakage in ML training, hardening file upload validation with magic bytes, and providing side-by-side revision tracking and downloadable reports, the application stands as a comprehensive academic and industry-relevant solution.
