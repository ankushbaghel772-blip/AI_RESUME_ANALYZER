"""
Machine Learning Feature Extractor for AI Resume Analysis.
Uses scikit-learn's TfidfVectorizer to convert resume texts and job descriptions
into numerical feature vectors and compute cosine similarity scores.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ResumeFeatureExtractor:
    """
    Extracts TF-IDF features and measures semantic keyword similarity
    between resumes and job descriptions using scikit-learn.
    """
    def __init__(self, max_features=1000, stop_words='english'):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words=stop_words,
            ngram_range=(1, 2)
        )
        self.is_fitted = False

    def fit_transform(self, text_corpus):
        """Fits vectorizer to a corpus of resumes and transforms it to TF-IDF matrix."""
        self.is_fitted = True
        return self.vectorizer.fit_transform(text_corpus)

    def compute_similarity(self, resume_text, job_description_text):
        """
        Calculates cosine similarity between a resume and job description.
        Returns: float between 0.0 and 1.0 (or percentage 0 - 100).
        """
        if not resume_text or not job_description_text:
            return 0.0

        try:
            tfidf_matrix = self.vectorizer.fit_transform([resume_text, job_description_text])
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(round(max(0.0, min(1.0, sim)) * 100, 1))
        except Exception:
            return 0.0
