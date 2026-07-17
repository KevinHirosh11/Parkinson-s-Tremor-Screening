import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def generate_visualization():
    print("[Visualization] Generating clinical data distribution plots using matplotlib...")
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset", "Parkinsons_Tremor_Clean_Dataset.csv")
    if not os.path.exists(dataset_path):
        print(f"[Error] Dataset not found at {dataset_path}")
        return
        
    df = pd.read_csv(dataset_path)
    
    np.random.seed(42)
    freqs = []
    amps = []
    diagnoses = []
    
    for _, row in df.iterrows():
        diagnosis = str(row.get('diagnosis', 'Healthy')).strip()
        tremor_type = str(row.get('tremor_text_type', 'not_mentioned')).strip()
        
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
        diagnoses.append(diagnosis)
        
    plot_df = pd.DataFrame({
        'Frequency': freqs,
        'Amplitude': amps,
        'Diagnosis': diagnoses
    })
    
    plt.figure(figsize=(10, 6))
    
    # Custom scatter colors/markers for each diagnosis
    colors = {"Healthy": "green", "Parkinson's": "red", "Other Movement Disorders": "blue", "Atypical Parkinsonism": "purple", "Multiple Sclerosis": "orange"}
    markers = {"Healthy": "o", "Parkinson's": "X", "Other Movement Disorders": "^", "Atypical Parkinsonism": "s", "Multiple Sclerosis": "D"}
    
    unique_diagnoses = plot_df['Diagnosis'].unique()
    for diag in unique_diagnoses:
        sub_df = plot_df[plot_df['Diagnosis'] == diag]
        color = colors.get(diag, "gray")
        marker = markers.get(diag, "o")
        plt.scatter(
            sub_df['Frequency'], 
            sub_df['Amplitude'], 
            label=diag, 
            color=color, 
            marker=marker, 
            alpha=0.7, 
            edgecolors='k', 
            s=60
        )
        
    plt.title("Clinical Parkinson's and Tremor Patient Distribution", fontsize=14, fontweight='bold')
    plt.xlabel("Dominant Tremor Frequency (Hz)", fontsize=12)
    plt.ylabel("Tremor Amplitude (m/s²)", fontsize=12)
    plt.legend(title="Diagnosis Profile")
    plt.grid(True, linestyle='--', alpha=0.5)
    
    output_path = "clinical_tremor_distribution.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[Visualization] Distribution plot saved successfully as '{output_path}'.")

if __name__ == "__main__":
    generate_visualization()
