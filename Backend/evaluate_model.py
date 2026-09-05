import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

def evaluate_saved_model():
    print("[Evaluation] Loading dataset and saved ML model...")
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(backend_dir, "models", "tremor_multi_model.pkl")
    
    if not os.path.exists(model_path):
        print(f"[Error] Trained model file not found at {model_path}. Please train the model first.")
        return

    try:
        from run import load_video_coordinates, analyze_tremor
        dataset_dir = os.path.join(os.path.dirname(backend_dir), "dataset")
        video_mappings = {
            "gettyimages-1194817476-640_adpp.mp4": "Parkinson's",
            "YTDown.com_Shorts_Parkinson-s-Disease-with-Tremors-of-hand_Media_hR_4m41cQyc_001_720p.mp4": "Parkinson's",
            "videoplayback.mp4": "Essential Tremor",
            "videoplayback (1).mp4": "Healthy",
            "gettyimages-1770742792-640_adpp.mp4": "Healthy",
            "video_preview_h264.mp4": "Other Movement Disorders"
        }
        
        extracted_data = {}
        for video_name, diagnosis in video_mappings.items():
            video_path = os.path.join(dataset_dir, video_name)
            if os.path.exists(video_path):
                coords, times, fps = load_video_coordinates(video_path)
                if coords and len(coords) >= 20:
                    extracted_data[video_name] = {
                        "coords": coords,
                        "times": times,
                        "fps": fps,
                        "diagnosis": diagnosis
                    }

        if not extracted_data:
            raise Exception("No videos found")

        np.random.seed(42)
        freqs = []
        amps = []
        y_severity = []
        y_category = []
        y_stage = []

        for video_name, data in extracted_data.items():
            coords = np.array(data["coords"])
            times = np.array(data["times"])
            fps = data["fps"]
            diagnosis = data["diagnosis"]
            
            mean_coords = np.mean(coords, axis=0)
            coords_detrend = coords - mean_coords
            
            num_augs = 200 # smaller size for quick test eval
            for _ in range(num_augs):
                if diagnosis == "Healthy":
                    alpha = np.random.uniform(0.8, 3.0)
                    beta = np.random.uniform(0.1, 1.3)
                elif diagnosis == "Parkinson's":
                    alpha = np.random.uniform(0.6, 1.5)
                    beta = np.random.uniform(1.2, 8.0)
                elif diagnosis == "Essential Tremor":
                    alpha = np.random.uniform(0.3, 0.9)
                    beta = np.random.uniform(1.0, 7.0)
                else:
                    alpha = np.random.uniform(0.4, 2.5)
                    beta = np.random.uniform(0.5, 4.0)
                    
                aug_times = times * alpha
                aug_coords = (coords_detrend * beta) + mean_coords
                aug_coords += np.random.normal(0, 0.001, aug_coords.shape)
                
                f, a, _, _ = analyze_tremor(aug_coords.tolist(), aug_times.tolist())
                if f <= 0 or a <= 0:
                    continue
                    
                if a < 1.5:
                    sev = "Normal"
                elif 1.5 <= a < 5.0:
                    sev = "Mild"
                elif 5.0 <= a <= 15.0:
                    sev = "Moderate"
                else:
                    sev = "Severe"
                    
                if 4.0 <= f <= 6.5 and (diagnosis == "Parkinson's" or diagnosis == "Other Movement Disorders"):
                    cat = "Parkinsonian Rest Tremor Range (4-6 Hz)"
                elif 7.5 <= f <= 12.5:
                    cat = "Essential / Physiological Tremor Range (8-12 Hz)"
                elif diagnosis == "Healthy" or (f < 3.0 and a < 1.5):
                    cat = "Normal / Low Activity"
                else:
                    cat = "Mixed / Unspecified Tremor"
                    
                stg = "Stage 0 (No Tremor)"
                if diagnosis == "Parkinson's" or cat == "Parkinsonian Rest Tremor Range (4-6 Hz)":
                    if sev == "Mild":
                        stg = "Stage 1 (Unilateral involvement only)"
                    elif sev == "Moderate":
                        stg = "Stage 2 (Bilateral involvement, without impairment of balance)"
                    elif sev == "Severe":
                        stg = "Stage 3 (Mild to moderate bilateral disease; some postural instability)"
                
                freqs.append(f)
                amps.append(a)
                y_severity.append(sev)
                y_category.append(cat)
                y_stage.append(stg)

        X = np.stack([freqs, amps], axis=1)
        y = np.column_stack([y_severity, y_category, y_stage])
        _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        tremor_clf = joblib.load(model_path)
        predictions = tremor_clf.predict(X_test)

    except Exception as e:
        print(f"[Evaluation Warning] Video-based evaluation failed: {e}")
        return

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
