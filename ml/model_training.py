"""
Machine Learning Model Training Pipeline for Resume Classification.
Trains a Multi-Class Resume Category Classifier using Scikit-Learn.
"""

import os
import csv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import joblib

# Fallback dataset if external CSV is missing
SAMPLE_TRAINING_DATA = [
    ("Experienced Python developer proficient in Django, Flask, PostgreSQL, Docker, Git, REST APIs, unit testing and microservices.", "Python Developer"),
    ("Backend software engineer specializing in Python, FastAPI, Celery, Redis caching, SQL queries, and CI/CD automation.", "Python Developer"),
    ("Python programmer with 3 years building automated data pipelines, web scrapers, Django dashboards, and Linux servers.", "Python Developer"),
    ("Frontend web developer skilled in HTML5, CSS3, JavaScript, React, Bootstrap, Tailwind, UI/UX design, and Figma.", "Web Developer"),
    ("Full stack web developer experienced with Node.js, Express, React, modern JavaScript, TypeScript, CSS, and responsive layouts.", "Web Developer"),
    ("Web application developer focused on user interfaces, single page applications, RESTful APIs, HTML, CSS, and JavaScript.", "Web Developer"),
    ("Data scientist with expertise in statistical modeling, machine learning, Pandas, NumPy, Scikit-Learn, data visualization, and Python.", "Data Scientist"),
    ("Machine learning researcher experienced with deep learning, PyTorch, TensorFlow, NLP text classification, data analysis, and Python.", "Data Scientist"),
    ("Data analyst and aspiring data scientist proficient in SQL, Python, Tableau, Power BI, predictive analytics, and statistical testing.", "Data Scientist"),
    ("Backend engineer with Java, Spring Boot, MySQL, REST APIs, microservices architecture, Docker, and Kafka.", "Backend Developer"),
    ("Senior backend developer specializing in system architecture, database schema design, PostgreSQL, Redis, and API scalability.", "Backend Developer"),
    ("Software engineer building robust server side architectures using Java, Python, SQL, REST APIs, and containerized Docker deployments.", "Backend Developer"),
]


def load_dataset():
    """
    Loads labeled resume corpus from datasets/resume_dataset.csv.
    Falls back to embedded SAMPLE_TRAINING_DATA if file is unavailable.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, 'datasets', 'resume_dataset.csv')
    
    texts = []
    labels = []
    
    if os.path.isfile(dataset_path):
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    text = row.get('text', '').strip()
                    label = row.get('role', '').strip()
                    if text and label:
                        texts.append(text)
                        labels.append(label)
        except Exception:
            pass
            
    if not texts:
        texts = [item[0] for item in SAMPLE_TRAINING_DATA]
        labels = [item[1] for item in SAMPLE_TRAINING_DATA]
        
    return texts, labels


def get_data_splits(test_size=0.25, random_state=42):
    """
    Returns reproducible, stratified train and test splits to prevent data leakage.
    """
    texts, labels = load_dataset()
    return train_test_split(
        texts, 
        labels, 
        test_size=test_size, 
        random_state=random_state, 
        stratify=labels if len(set(labels)) > 1 and len(texts) >= len(set(labels)) * 2 else None
    )


def train_resume_classifier(save_path=None):
    """
    Trains a TF-IDF + LogisticRegression classifier pipeline using strict featurization ordering.
    Preprocessing is fitted exclusively on the training split to eliminate data leakage.
    """
    X_train, X_test, y_train, y_test = get_data_splits()
    
    # Build scikit-learn pipeline (strictly fitted only on X_train)
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words='english', min_df=1, max_features=1500)),
        ('classifier', LogisticRegression(max_iter=300, random_state=42, C=1.0))
    ])
    
    pipeline.fit(X_train, y_train)
    train_acc = pipeline.score(X_train, y_train)
    test_acc = pipeline.score(X_test, y_test)
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        joblib.dump(pipeline, save_path)
        
    return {
        'pipeline': pipeline,
        'train_accuracy': train_acc,
        'test_accuracy': test_acc,
        'classes': list(pipeline.classes_),
        'X_test': X_test,
        'y_test': y_test
    }


if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_file = os.path.join(current_dir, 'models', 'resume_classifier.joblib')
    result = train_resume_classifier(save_path=model_file)
    print("=" * 50)
    print("ML Model Training Complete!")
    print(f"Detected Target Classes ({len(result['classes'])}):")
    for c in result['classes']:
        print(f"  - {c}")
    print(f"Training Split Accuracy: {result['train_accuracy'] * 100:.1f}%")
    print(f"Held-Out Test Accuracy: {result['test_accuracy'] * 100:.1f}%")
    print(f"Artifact Persisted To: {model_file}")
    print("=" * 50)
