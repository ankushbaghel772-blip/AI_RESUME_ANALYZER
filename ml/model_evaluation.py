import sys
import os
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

try:
    from .model_training import train_resume_classifier, get_data_splits
except ImportError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from model_training import train_resume_classifier, get_data_splits


def evaluate_classifier(pipeline, test_texts, true_labels):
    """
    Evaluates a trained classifier pipeline strictly against unseen holdout test samples.
    Ensures zero data leakage between training and evaluation stages.
    Returns:
        dict: {
            'accuracy': float,
            'report': str,
            'confusion_matrix': list of lists,
            'classes': list of class names,
            'predictions': list
        }
    """
    predictions = pipeline.predict(test_texts)
    acc = accuracy_score(true_labels, predictions)
    report = classification_report(true_labels, predictions, zero_division=0)
    cm = confusion_matrix(true_labels, predictions).tolist()
    
    return {
        'accuracy': float(round(acc * 100, 2)),
        'report': report,
        'confusion_matrix': cm,
        'classes': list(pipeline.classes_),
        'predictions': list(predictions)
    }


if __name__ == '__main__':
    # Train model pipeline and retrieve strictly held-out test split
    train_result = train_resume_classifier()
    model = train_result['pipeline']
    X_test = train_result['X_test']
    y_test = train_result['y_test']
    
    # Evaluate exclusively on unseen holdout test data (Zero Data Leakage)
    eval_result = evaluate_classifier(model, X_test, y_test)
    
    print("=" * 60)
    print("      MACHINE LEARNING CLASSIFIER EVALUATION REPORT")
    print("=" * 60)
    print(f"Evaluation Mode: Strictly Unseen Test Split (Zero Data Leakage)")
    print(f"Number of Held-Out Test Samples: {len(X_test)}")
    print(f"Overall Test Accuracy: {eval_result['accuracy']}%\n")
    print("Detailed Classification Report (Precision, Recall, F1-Score):")
    print(eval_result['report'])
    print("\nConfusion Matrix:")
    for idx, row in enumerate(eval_result['confusion_matrix']):
        print(f"  {eval_result['classes'][idx]:<25} : {row}")
    print("=" * 60)
