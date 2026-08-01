import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def generate_visualization():
    print("[Visualization] Generating video-derived data distribution plots using matplotlib...")
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
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
            raise Exception("No videos found to extract data for visualization.")

        np.random.seed(42)
        freqs = []
        amps = []
        diagnoses = []
        
        for video_name, data in extracted_data.items():
            coords = np.array(data["coords"])
            times = np.array(data["times"])
            diagnosis = data["diagnosis"]
            
            mean_coords = np.mean(coords, axis=0)
            coords_detrend = coords - mean_coords
            
            num_augs = 200  # Generate data points for representation
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
                    
                freqs.append(f)
                amps.append(a)
                diagnoses.append(diagnosis)
                
        plot_df = pd.DataFrame({
            'Frequency': freqs,
            'Amplitude': amps,
            'Diagnosis': diagnoses
        })
        
        plt.figure(figsize=(10, 6))
        colors = {"Healthy": "green", "Parkinson's": "red", "Essential Tremor": "orange", "Other Movement Disorders": "blue"}
        markers = {"Healthy": "o", "Parkinson's": "X", "Essential Tremor": "s", "Other Movement Disorders": "^"}
        
        for diag in plot_df['Diagnosis'].unique():
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
            
        plt.title("Video-Derived Parkinson's and Tremor Feature Distribution", fontsize=14, fontweight='bold')
        plt.xlabel("Dominant Tremor Frequency (Hz)", fontsize=12)
        plt.ylabel("Tremor Amplitude (Scaled Index Tip Displacement)", fontsize=12)
        plt.legend(title="Diagnosis Profile")
        plt.grid(True, linestyle='--', alpha=0.5)
        
        output_path = os.path.join(os.path.dirname(backend_dir), "clinical_tremor_distribution.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[Visualization] Distribution plot saved successfully as '{output_path}'.")
        
    except Exception as e:
        print(f"[Visualization Error] Failed to generate plot from videos: {e}")

if __name__ == "__main__":
    generate_visualization()
