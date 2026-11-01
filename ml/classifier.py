"""
Machine Learning Classifier Inference Service for AI Resume Analysis.
Loads the trained resume classifier pipeline (TF-IDF + Logistic Regression)
and predicts candidate career categories with confidence scores and probability distributions.
"""

import os
import joblib

_LOADED_MODEL = None

def get_classifier_model():
    """
    Loads and caches the trained scikit-learn classifier pipeline.
    """
    global _LOADED_MODEL
    if _LOADED_MODEL is not None:
        return _LOADED_MODEL
        
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, 'models', 'resume_classifier.joblib')
    
    if os.path.isfile(model_path):
        try:
            _LOADED_MODEL = joblib.load(model_path)
            return _LOADED_MODEL
        except Exception:
            return None
    return None


def classify_resume_text(resume_text):
    """
    Runs ML inference on extracted resume text.
    Returns:
        dict: {
            'predicted_role': str,
            'confidence': float (0-100),
            'class_probabilities': dict of {role: percentage},
            'model_name': str
        } or None if model unavailable or empty text.
    """
    if not resume_text or not resume_text.strip():
        return None
        
    model = get_classifier_model()
    if model is None:
        return None
        
    try:
        prediction = model.predict([resume_text])[0]
        # Get probability distribution if classifier supports predict_proba
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba([resume_text])[0]
            confidence = float(round(max(probabilities) * 100, 1))
            class_probs = {
                str(cls): float(round(prob * 100, 1))
                for cls, prob in zip(model.classes_, probabilities)
            }
            # Sort by highest probability first
            sorted_probs = dict(sorted(class_probs.items(), key=lambda item: item[1], reverse=True))
        else:
            confidence = 100.0
            sorted_probs = {str(prediction): 100.0}
            
        return {
            'predicted_role': str(prediction),
            'confidence': confidence,
            'class_probabilities': sorted_probs,
            'model_name': 'Scikit-Learn TF-IDF + Logistic Regression'
        }
    except Exception:
        return None
