import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

def evaluate_saved_model():
    print("[Evaluation] Loading dataset and saved ML model...")
    
    # Path configurations
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(os.path.dirname(backend_dir), "dataset", "Parkinsons_Tremor_Clean_Dataset.csv")
    model_path = os.path.join(backend_dir, "models", "tremor_multi_model.pkl")
    
    if not os.path.exists(model_path):
        print(f"[Error] Trained model file not found at {model_path}. Please train the model first.")
        return
        
    if not os.path.exists(dataset_path):
        print(f"[Error] Dataset file not found at {dataset_path}.")
        return

    # Load dataset
    df = pd.read_csv(dataset_path)
    print(f"[Evaluation] Loaded {len(df)} patient records.")

    # Reconstruct the augmented testing set (same preprocessing as run.py)
    np.random.seed(42)
    freqs = []
    amps = []
    y_severity = []
    y_category = []
    y_stage = []

    diag_aug_map = {
        "Parkinson's": 40,
        "Healthy": 140,
        "Other Movement Disorders": 180,
        "Essential Tremor": 390,
        "Atypical Parkinsonism": 730,
        "Multiple Sclerosis": 1000
    }

    for _, row in df.iterrows():
        diagnosis = str(row.get('diagnosis', 'Healthy')).strip()
        tremor_type = str(row.get('tremor_text_type', 'not_mentioned')).strip()
        
        n_augs = diag_aug_map.get(diagnosis, 40)
        for _ in range(n_augs):
            if diagnosis == 'Healthy':
                f = np.random.uniform(0.0, 3.0)
                a = np.random.uniform(0.1, 1.4)
            elif diagnosis == "Parkinson's":
                if tremor_type in ['resting', 'tremor_dominant']:
                    f = np.random.uniform(4.0, 6.0)
                    a = np.random.uniform(2.0, 25.0) 
                else:
                    f = np.random.uniform(4.0, 7.0)
                    a = np.random.uniform(1.5, 10.0)
            elif 'Essential' in tremor_type or diagnosis == 'Other Movement Disorders':
                f = np.random.uniform(8.0, 12.0)
                a = np.random.uniform(1.5, 15.0)
            else:
                f = np.random.uniform(1.0, 15.0)
                a = np.random.uniform(0.5, 4.0)
                
            freqs.append(f)
            amps.append(a)

            if f < 3.0 or a < 1.5:
                sev = "Normal"
            elif 1.5 <= a < 5.0:
                sev = "Mild"
            elif 5.0 <= a <= 15.0:
                sev = "Moderate"
            else:
                sev = "Severe"
            y_severity.append(sev)

            if 4.0 <= f <= 6.0 and diagnosis == "Parkinson's":
                cat = "Parkinsonian Rest Tremor Range (4-6 Hz)"
            elif 8.0 <= f <= 12.0:
                cat = "Essential / Physiological Tremor Range (8-12 Hz)"
            elif diagnosis == "Healthy":
                cat = "Normal / Low Activity"
            else:
                cat = "Mixed / Unspecified Tremor"
            y_category.append(cat)

            stg = "Stage 0 (No Tremor)"
            if diagnosis == "Parkinson's":
                if sev == "Mild":
                    stg = "Stage 1 (Unilateral involvement only)"
                elif sev == "Moderate":
                    stg = "Stage 2 (Bilateral involvement, without impairment of balance)"
                elif sev == "Severe":
                    stg = "Stage 3 (Mild to moderate bilateral disease; some postural instability)"
            y_stage.append(stg)

    X = np.stack([freqs, amps], axis=1)
    y = np.column_stack([y_severity, y_category, y_stage])

    # Split dataset into training/testing (testing set is 20%)
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Load saved model
    tremor_clf = joblib.load(model_path)
    predictions = tremor_clf.predict(X_test)

    # Calculate metrics
    print("\n" + "="*50)
    print("           ML MODEL ACCURACY EVALUATION")
    print("="*50)
    
    # 1. Severity Model
    sev_acc = accuracy_score(y_test[:, 0], predictions[:, 0])
    print(f"\n1. Severity Classifier Accuracy: {sev_acc * 100:.2f}%")
    print("-" * 50)
    print(classification_report(y_test[:, 0], predictions[:, 0]))

    # 2. Category Model
    cat_acc = accuracy_score(y_test[:, 1], predictions[:, 1])
    print(f"\n2. Category Classifier Accuracy: {cat_acc * 100:.2f}%")
    print("-" * 50)
    print(classification_report(y_test[:, 1], predictions[:, 1]))

    # 3. Stage Model
    stg_acc = accuracy_score(y_test[:, 2], predictions[:, 2])
    print(f"\n3. Stage Classifier Accuracy: {stg_acc * 100:.2f}%")
    print("-" * 50)
    print(classification_report(y_test[:, 2], predictions[:, 2]))
    print("="*50 + "\n")

if __name__ == "__main__":
    evaluate_saved_model()
