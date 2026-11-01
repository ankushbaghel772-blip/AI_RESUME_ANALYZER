# AI Resume Analysis Using Machine Learning & NLP
## (Complete English & हिंदी Documentation & Viva Guide)

---

## 1. Project Overview (प्रोजेक्ट क्या है?)

**English**:  
The **AI Resume Analysis System** is an end-to-end web application developed using **Python, Django, and Scikit-Learn**. It allows candidates to upload resumes in **PDF, DOCX, or TXT** formats. The system uses Natural Language Processing (NLP) to extract structural sections and technical skills, evaluates the resume against a transparent **0–100 ATS readiness score**, predicts career categories using a trained **Machine Learning classifier**, performs side-by-side revision comparisons, and generates downloadable analytical reports.

**हिंदी**:  
**AI Resume Analysis System** ek modern web application hai jo candidate ke resume (PDF, DOCX, TXT) ko analyze karta hai. Natural Language Processing (NLP) ki madad se yeh technical skills aur resume ke sections detect karta hai, ek transparent **0 se 100 ATS readiness score** calculate karta hai, trained **Machine Learning Model** ke zariye suitable career track predict karta hai, do alag-alag resume versions ko side-by-side compare karta hai, aur candidate ko ek detailed downloadable text report provide karta hai.

---

## 2. Key Features (प्रमुख विशेषताएं)

1. **Multi-Format Secure Document Upload**:
   - Supports **PDF (.pdf)**, **Word (.docx)**, and **Text (.txt)** up to 5MB.
   - **Binary Magic Bytes Validation**: Inspects real file headers (`%PDF-` for PDFs, `PK\x03\x04` for Word DOCX, and null-byte check for TXT) to reject disguised executables or corrupt files.
2. **Accurate Section Detection**:
   - Uses line-based candidate filtering (short headings $\le$ 5 words, $\le$ 60 characters) to identify 7 standard sections (*Contact Info, Summary, Experience, Education, Skills, Projects, Certifications*).
   - Zero false positives on narrative body sentences.
3. **Advanced Skill Extraction (60+ Skills)**:
   - Boundary-safe regular expressions (`(?![a-zA-Z0-9#+])`) for special-character languages: `C++`, `C#`, `C`, `Go`, `R`, `Machine Learning`, `Deep Learning`, `Python`, `Java`, `JavaScript`, etc.
   - Conjunction-aware logic handles "C and C++", "ML & DL", and technical comma-separated lists.
4. **Transparent 100-Point Resume Scoring**:
   - Section Completeness (Max 30 pts)
   - Technical Skill Richness (Max 35 pts)
   - Word Count & Readability (Max 15 pts)
   - Job Alignment / Completeness (Max 20 pts)
5. **Supervised Machine Learning Career Classifier**:
   - Trained Scikit-Learn **TF-IDF + Logistic Regression** pipeline on 60 categorized technical resumes.
   - **Zero Data Leakage**: Stratified 75/25 train-test split, vectorizer fitted strictly on training data.
   - Evaluated on held-out test data with **100% test accuracy**.
   - Live inference displays predicted role, confidence percentage, and per-class probability distribution.
6. **Side-by-Side Resume Revision Comparison**:
   - Compare two revisions of a candidate's resume (`alice_v1` vs `alice_v2`).
   - Automatically computes score delta (+/- points), newly added skills, retained skills, and omitted skills.
7. **Downloadable Analysis Report**:
   - Generates a formatted text summary report (`.txt`) for offline review, detailing score breakdown, ML predictions, detected sections, strengths, and recommended improvements.
8. **Secure Original File Download**:
   - Protected `FileResponse` view serving user files only to authenticated owners.
9. **Advanced History Search, Sorting & Pagination**:
   - Server-side search by filename (`?q=...`), sorting by highest score, lowest score, newest, or oldest, with preserved query parameters across pagination.
10. **Enterprise-Grade Security & Isolation**:
    - Multi-tenant data isolation: User A cannot view, download, or delete User B's resumes (returns HTTP 404).
    - CSRF protection on all forms, POST-only logout, password complexity rules, and open-redirect defenses.

---

## 3. Technology Stack (तकनीकी स्टैक)

| Component | Technology / Library | Role |
|---|---|---|
| **Backend Framework** | Python 3.14 / Django 6.1 | MVC/MVT architecture, ORM, routing, authentication |
| **Frontend UI** | HTML5, CSS3, JavaScript | Custom dark navy theme (`#0B0F19`), glassmorphism, responsive cards |
| **UI Component Library**| Bootstrap 5.3 (CDN), Bootstrap Icons | Responsive grid, modal dialogs, icons |
| **Document Parsing** | `pypdf`, `python-docx` | PDF page text parsing, Word paragraph & table extraction |
| **NLP & Matching** | Regular Expressions (`re`) | Line-based section detection, boundary-safe skill extraction |
| **Machine Learning** | `scikit-learn`, `joblib` | TF-IDF feature extraction, cosine similarity, Logistic Regression |
| **Database** | SQLite (Default) / MySQL / PostgreSQL | Multi-tenant relational persistence layer |

---

## 4. Project Directory Structure (प्रोजेक्ट फोल्डर संरचना)

```text
AI Resume/
│
├── ai/                                    # Python Virtual Environment
│
└── AI_RESUME_ANALYSIS/                    # Main Django Project Root
    ├── manage.py                          # Django CLI utility
    ├── requirements.txt                   # Dependency manifest
    ├── README.md                          # Complete bilingual documentation
    ├── .env                               # Environment configurations
    ├── .env.example                       # Example config template
    ├── .gitignore                         # Git exclusion rules
    │
    ├── AI/                                # Django Configuration Package
    │   ├── __init__.py
    │   ├── settings.py                    # Hardened settings (DB, auth, media, static)
    │   ├── urls.py                        # Master routing
    │   ├── asgi.py
    │   └── wsgi.py
    │
    ├── resumeapp/                         # Main Resume Application
    │   ├── __init__.py
    │   ├── admin.py                       # Django admin model registrations
    │   ├── apps.py
    │   ├── models.py                      # ResumeAnalysis & UserProfile models
    │   ├── views.py                       # All view controllers & pipelines
    │   ├── forms.py                       # Upload & auth forms with magic-byte validation
    │   ├── urls.py                        # Route definitions
    │   ├── tests.py                       # 41 automated unit & integration tests
    │   ├── migrations/                    # Database schema migrations
    │   │
    │   ├── services/                      # Resume Processing Services
    │   │   ├── __init__.py
    │   │   ├── text_extractor.py          # PDF, DOCX, TXT parser with OCR notice
    │   │   ├── text_preprocessor.py       # Text cleaning & line-based section detector
    │   │   ├── skill_extractor.py         # 60+ technical skills regex matcher
    │   │   ├── resume_scorer.py           # Transparent 100-point scoring engine
    │   │   └── job_recommender.py         # Career tracks matching logic
    │   │
    │   ├── templates/resumeapp/           # User Interface Templates
    │   │   ├── base.html                  # Base layout with navbar, footer, & compare link
    │   │   ├── home.html                  # Landing page
    │   │   ├── about.html                 # Architecture & NLP explanation
    │   │   ├── signup.html                # User registration
    │   │   ├── login.html                 # Authentication login
    │   │   ├── dashboard.html             # Candidate dashboard & quick statistics
    │   │   ├── upload.html                # Drag-and-drop resume upload & job target input
    │   │   ├── result.html                # Score breakdown, ML career prediction card, actions
    │   │   ├── compare.html               # Side-by-side resume revision comparison tool
    │   │   ├── history.html               # User history table with search, sort & pagination
    │   │   ├── profile.html               # Profile & career track preferences
    │   │   └── job_recommendations.html   # Curated career tracks with ML prediction banner
    │   │
    │   └── static/resumeapp/              # Static Assets
    │       ├── css/
    │       │   ├── style.css              # Dark navy design system & glassmorphism
    │       │   ├── auth.css               # Login & signup styling
    │       │   ├── dashboard.css          # Metric cards & tables
    │       │   └── analysis.css           # Dropzone, meters, feedback lists
    │       ├── js/
    │       │   ├── main.js                # Auto-dismiss alerts, counters
    │       │   ├── upload.js              # Drag-drop & size validation
    │       │   └── dashboard.js           # Client-side table filter helper
    │       └── images/
    │           ├── logo.png
    │           └── hero.png
    │
    ├── ml/                                # Machine Learning Components
    │   ├── __init__.py
    │   ├── classifier.py                  # Live ML inference service (predict + probabilities)
    │   ├── feature_extractor.py           # TF-IDF & Cosine Similarity
    │   ├── model_training.py              # Zero-leakage training script (stratified split)
    │   ├── model_evaluation.py            # Evaluation script on held-out test split
    │   └── models/
    │       └── resume_classifier.joblib   # Trained Scikit-Learn pipeline artifact
    │
    ├── datasets/                          # Datasets Folder
    │   ├── README.md
    │   └── resume_dataset.csv             # 60 categorized resume training records
    │
    ├── media/                             # Uploaded resume files (authenticated download)
    │   └── resumes/
    │
    └── docs/                              # Project Documentation
        ├── project_report.md              # Academic project report
        ├── system_architecture.md         # Flowcharts and component layers
        └── database_design.md             # Schema tables and ER diagrams
```

---

## 5. Step-by-Step Installation & Running Guide (सेटअप कैसे करें)

### Step 1: Open Windows PowerShell
Navigate to the project root directory:
```powershell
cd "C:\Users\krish\Desktop\l2\AI Resume\AI_RESUME_ANALYSIS"
```

### Step 2: Activate the Virtual Environment
```powershell
& "..\ai\Scripts\Activate.ps1"
```

### Step 3: Verify Installed Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run Database Migrations
```powershell
python manage.py migrate
```

### Step 5: Run Django System Health Check
```powershell
python manage.py check
```

### Step 6: Run All 41 Automated Tests
```powershell
python manage.py test
```
*(All 41 tests will execute and report `OK`)*

### Step 7: (Optional) Re-Train the ML Classifier
```powershell
python ml/model_training.py
python ml/model_evaluation.py
```

### Step 8: Start the Local Development Server
```powershell
python manage.py runserver
```

Open your browser and navigate to:
👉 **http://127.0.0.1:8000/**

---

## 6. Application URL Directory (सभी पेजेस के लिंक्स)

| Endpoint | View Function | Description |
|---|---|---|
| `/` | `home` | Landing page with feature showcases |
| `/about/` | `about` | NLP pipeline and scoring architecture explanation |
| `/signup/` | `user_signup` | User registration with password validation |
| `/login/` | `user_login` | Secure login with open-redirect protection |
| `/logout/` | `user_logout` | Secure POST-only logout |
| `/dashboard/` | `dashboard` | Candidate statistics, recent resumes, top skills |
| `/upload/` | `upload_resume` | Drag-and-drop resume upload & job description matcher |
| `/result/<id>/` | `result_detail` | Detailed ATS score, ML career prediction, recommendations |
| `/result/<id>/report/` | `download_analysis_report`| Downloadable text report (`.txt`) for offline review |
| `/result/<id>/download-file/`| `download_original_resume`| Authenticated download of original uploaded resume file |
| `/compare/` | `compare_resumes` | Side-by-side comparison of 2 resume revisions |
| `/history/` | `history` | History table with search, sorting, and pagination |
| `/delete/<id>/` | `delete_resume` | Secure deletion of resume and associated analysis |
| `/profile/` | `profile_view` | User profile, contact details, and target role preference |
| `/recommendations/` | `job_recommendations` | Curated career paths based on extracted skills |
| `/admin/` | `admin.site.urls` | Django admin back-office |

---

## 7. College Viva Questions & Answers (वाइवा के लिए महत्वपूर्ण प्रश्न)

### Q1: What is the architecture of this project? (प्रोजेक्ट का आर्किटेक्चर क्या है?)
**Answer (English)**:  
The project follows Django's **MVT (Model-View-Template)** architecture:
- **Model**: `ResumeAnalysis` and `UserProfile` in `models.py` define the database structure and cascade relationships.
- **View**: `views.py` coordinates HTTP requests, text extraction, NLP preprocessing, scoring, and ML inference.
- **Template**: HTML5 templates styled with modern CSS, glassmorphism, and Bootstrap 5 render responsive dynamic pages.

**उत्तर (हिंदी)**:  
Yeh project Django ke **MVT (Model-View-Template)** architecture par kaam karta hai:
- **Model (`models.py`)**: Database structure define karta hai (`ResumeAnalysis` aur `UserProfile`).
- **View (`views.py`)**: Business logic, file extraction, NLP parsing aur ML inference ko handle karta hai.
- **Template**: HTML5 aur Bootstrap 5 templates jo browser me user ko dynamic responsive interface dikhate hain.

---

### Q2: How does skill extraction work and how do you handle special characters like C++ or C#?
**Answer (English)**:  
Skill extraction is implemented in `resumeapp/services/skill_extractor.py`. Traditional `\b` word boundaries fail after symbols like `+` or `#` because they are treated as non-word characters (`\W`). We solve this using negative lookahead assertions: `\bc\+\+(?![a-zA-Z0-9#+])` and `\bc#(?![a-zA-Z0-9#+])`. Furthermore, short skill names like `C`, `Go`, and `R` use conjunction and list-context patterns to eliminate false positives from everyday English words like "Grade C", "ready to go", or middle initials.

**उत्तर (हिंदी)**:  
Skill extraction `resumeapp/services/skill_extractor.py` me regular expressions ke zariye ki gayi hai. Normal `\b` boundary `+` aur `#` ke baad fail ho jati hai kyunki regex me yeh non-word characters hote hain. Humne negative lookahead `(?![a-zA-Z0-9#+])` use kiya hai. Saath hi chote words jaise `C`, `Go`, `R` ke liye technical context (jaise `C and C++`, `Python, C, Java`) check kiya jata hai taaki "Grade C" ya "ready to go" jaise aam sentences galat skill na detect hon.

---

### Q3: How is section detection implemented without false positives?
**Answer (English)**:  
Instead of searching across the entire narrative text with broad regex, `resumeapp/services/text_preprocessor.py` analyzes the text line-by-line. Candidate lines must be short ($\le 5$ words and $\le 60$ characters) and terminate with an optional colon or match heading patterns (e.g., `### Technical Skills` or `Work Experience:`). This strictly prevents narrative sentences like *"I have experience working with college teams"* from falsely triggering sections.

**उत्तर (हिंदी)**:  
Pehle code poore text me 'experience' ya 'college' dhoondh raha tha jisse paragraph ke aam shabd bhi section ban jaate the. Humne isse line-by-line candidate filtering me convert kiya hai. Sirf wahi lines check hoti hain jo 5 words se kam aur 60 characters se chhoti hon aur heading format me hon. Isse narrative sentences kabhi false section trigger nahi karte.

---

### Q4: How is Machine Learning implemented and how did you prevent Data Leakage?
**Answer (English)**:  
In `ml/model_training.py`, we train a Scikit-Learn pipeline consisting of a `TfidfVectorizer` and a `LogisticRegression` classifier on `datasets/resume_dataset.csv`.  
**Preventing Data Leakage**: We perform a stratified train/test split (75% train / 25% test) using `stratify=labels`. The TF-IDF vectorizer is fitted **exclusively on the training split (`X_train`)**, and `X_test` is only transformed. In `ml/model_evaluation.py`, the model is evaluated strictly on the held-out test split, achieving 100% test accuracy across all 5 categories.

**उत्तर (हिंदी)**:  
Machine Learning classifier `ml/model_training.py` me `TfidfVectorizer` aur `LogisticRegression` use karke train kiya gaya hai.  
**Data Leakage Rokna**: Pehle evaluation poore dataset par ho rahi thi jo ki data leakage thi. Humne `train_test_split(..., stratify=labels, test_size=0.25)` use kiya. TF-IDF Vectorizer ko **sirf training data (`X_train`)** par `fit` kiya gaya aur test data ko bilkul alag rakha gaya. Model ko held-out test set par evaluate karke 100% genuine accuracy prapt hui.

---

### Q5: How is user privacy and data security enforced?
**Answer (English)**:  
1. **Multi-Tenant Data Isolation**: Every resume analysis is tied via a foreign key to the logged-in user. Views query strictly using `ResumeAnalysis.objects.filter(user=request.user)` and `get_object_or_404(ResumeAnalysis, id=analysis_id, user=request.user)`. If User B attempts to access User A's ID, Django returns a strict `404 Not Found`.
2. **File Content Validation**: Uploads are inspected for binary magic bytes (`%PDF-`, `PK\x03\x04`, null bytes in TXT) to prevent malicious executable files from being uploaded.
3. **Protected File Downloads**: Uploaded resumes are served through an authenticated view (`download_original_resume`) rather than direct public media URLs.
4. **CSRF & Auth Security**: All forms enforce CSRF tokens, logout requires POST requests, and login redirects are validated against safe local hosts.

**उत्तर (हिंदी)**:  
1. Har record user se linked hota hai. Views me `get_object_or_404(..., user=request.user)` lagaya gaya hai, jisse doosra user kisi aur ka resume ya report na dekh sake (404 error aata hai).
2. Upload hone wali files ke binary magic bytes check kiye jaate hain taaki koi renamed executable virus na daal sake.
3. Logout strictly POST request se hota hai (CSRF protected).
4. Login redirect me open redirect attack rokne ke liye host validation lagayi gayi hai.

---

### Q6: How is the 0–100 Resume Score calculated? Is it an official ATS score?
**Answer (English)**:  
The score is a transparent 100-point educational metric:
1. **Section Structure**: Max 30 points (5 points per key section found).
2. **Technical Skill Richness**: Max 35 points (tiered based on number of recognized skills).
3. **Document Length & Readability**: Max 15 points (optimal 250–1000 words).
4. **Job Alignment / Content Density**: Max 20 points (based on keyword match with target job description).  
*Disclaimer*: It is an educational evaluation metric, not a proprietary commercial ATS algorithm, and does not claim to predict employment decisions.

**उत्तर (हिंदी)**:  
Score 0 se 100 ke beech 4 factors par transparently calculate hota hai:
1. Section Structure (Max 30 pts)
2. Technical Skills (Max 35 pts)
3. Word Count / Length (Max 15 pts)
4. Job Alignment / Completeness (Max 20 pts)  
Yeh ek analytical aur educational tool hai jo candidate ko resume formatting aur keywords behtar banane me madad karta hai.

## BERT / Sentence Transformer semantic matching

The existing 0–100 rule-based resume score and TF-IDF + Logistic Regression career classifier remain unchanged. When an upload includes a job description, the application also reports a separate raw cosine-similarity signal from the bundled pretrained `sentence-transformers/all-MiniLM-L6-v2` model. It is not a percentage, probability, or hiring decision. Long documents are encoded in chunks. The model is loaded locally; web requests do not download weights.

### Install the matching dependencies

Use Python 3.14 on Windows for the verified project environment, create a virtual environment, install the existing application requirements, then install the CPU inference pins:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-bert.txt
```

The final ZIP includes model weights under `ml/models/bert_resume_matcher/`. It does not include a virtual environment or active `.env` file. Copy `.env.example` to `.env` and set local values as appropriate.

### Reproduce the controlled synthetic-data experiment

Install notebook and data support, start Jupyter from the project directory, then run the three notebooks in order:

```powershell
python -m pip install -r requirements-notebooks.txt
jupyter lab
```

1. `notebooks/01_EDA_and_DATA_prep.ipynb` verifies the Hugging Face dataset’s public/ungated status and MIT declaration, downloads the three Parquet tables, checks their schemas and references, and writes `data/processed/resume_job_positive_pairs.csv`.
2. `notebooks/02_BERT_EMBEDDINGS.ipynb` loads that canonical file, embeds a deterministic sample, and reports descriptive similarity values for explicitly relevant pairs only.
3. `notebooks/03_BERT_FINETUNEipynb.ipynb` checks whether the available labels support supervised training and held-out evaluation. For this dataset it reports the exact blocker and does not train or emit performance metrics.

The dataset is synthetic and its match list contains only explicitly relevant resume IDs, capped at 30 per job. Unlisted pairs are unlabeled. No negative or graded matching labels are inferred. The pretrained model remains the application’s semantic baseline until a dataset with reuse rights and verified negative or graded labels is available. Results from this controlled experiment are not human-validated matching performance or real-world hiring accuracy.
