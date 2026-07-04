import cv2
import numpy as np
import time
from scipy.signal import butter, filtfilt
import mediapipe as mp


RECORD_TIME = 10.0 
TARGET_FPS = 30.0
TOTAL_FRAMES = int(RECORD_TIME * TARGET_FPS)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

def detect_hand_mediapipe(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    if not results.multi_hand_landmarks:
        return None, None
        
    hand_landmarks = results.multi_hand_landmarks[0]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    
    h, w, _ = frame.shape
    cx, cy = int(index_tip.x * w), int(index_tip.y * h)
    
    return hand_landmarks, (cx, cy)

def butter_lowpass_filter(data, cutoff, fs, order=4):
    nyq = 0.5 * fs
    if cutoff >= nyq:
        cutoff = nyq - 0.1
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y
def analyze_tremor(time_series, timestamps):
    t_uniform = np.linspace(timestamps[0], timestamps[-1], len(timestamps))
    dt = 1.0 / TARGET_FPS

    x_coords = np.array([pt[0] for pt in time_series])
    y_coords = np.array([pt[1] for pt in time_series])
    
    x_interp = np.interp(t_uniform, timestamps, x_coords)
    y_interp = np.interp(t_uniform, timestamps, y_coords)
    
    x_detrend = x_interp - np.mean(x_interp)
    y_detrend = y_interp - np.mean(y_interp)
    
    displacement = np.sqrt(x_detrend**2 + y_detrend**2)
    
    fs = TARGET_FPS
    filtered_signal = butter_lowpass_filter(displacement, cutoff=12.0, fs=fs, order=2)
    
    window = np.hanning(len(filtered_signal))
    windowed_signal = filtered_signal * window
    
    n = len(windowed_signal)
    fft_vals = np.fft.fft(windowed_signal)
    fft_freqs = np.fft.fftfreq(n, d=dt)
    
    pos_mask = fft_freqs >= 0
    freqs = fft_freqs[pos_mask]
    magnitude = np.abs(fft_vals[pos_mask])

    valid_mask = freqs >= 1.5
    valid_freqs = freqs[valid_mask]
    valid_mag = magnitude[valid_mask]
    
    if len(valid_freqs) == 0:
        return 0.0, 0.0, "Normal"
        
    peak_idx = np.argmax(valid_mag)
    dominant_frequency = valid_freqs[peak_idx]
    peak_amplitude = valid_mag[peak_idx]
    
    if 4.0 <= dominant_frequency <= 6.0:
        category = "Parkinsonian Rest Tremor Range (4-6 Hz)"
    elif 8.0 <= dominant_frequency <= 12.0:
        category = "Essential / Physiological Tremor Range (8-12 Hz)"
    else:
        category = "Normal / Low Activity"
        
    return dominant_frequency, peak_amplitude, category

def main():
    cap = cv2.VideoCapture(0)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("====================================================")
    print("  Webcam-Based Tremor Screening System (Prototype) ")
    print("====================================================")
    print("Instructions:")
    print("1. Stretch your hand in front of the camera (Postural Test).")
    print("2. Keep your hand as still as possible.")
    print("3. Press 'S' to start the 10-second capture.")
    print("4. Press 'Q' to quit anytime.")
    print("====================================================")
    
    recording = False
    start_time = 0
    
    coordinate_history = []
    timestamp_history = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break
            
        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        
        hand_landmarks, finger_tip = detect_hand_mediapipe(frame)
        
        hand_detected = False
        
        cv2.putText(frame, "Press 'S' to Start | Press 'Q' to Quit", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if finger_tip is not None:
            hand_detected = True
            cx, cy = finger_tip[0], finger_tip[1]
            
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            cv2.circle(frame, (cx, cy), 8, (0, 0, 255), -1)

            if recording:
                current_time = time.time()
                elapsed = current_time - start_time
                
                coordinate_history.append((cx / w, cy / h))
                timestamp_history.append(elapsed)
                
                cv2.circle(frame, (30, 70), 10, (0, 0, 255), -1)
                cv2.putText(frame, f"RECORDING: {elapsed:.1f}s / {RECORD_TIME}s", (50, 75),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            
                if elapsed >= RECORD_TIME:
                    recording = False
                    print("\nRecording complete! Processing data...")
                    
                    if len(coordinate_history) > 50:
                        freq, amp, result = analyze_tremor(coordinate_history, timestamp_history)
                        print("\n--- RESULTS ---")
                        print(f"Dominant Frequency: {freq:.2f} Hz")
                        print(f"Signal Amplitude: {amp:.5f}")
                        print(f"Category: {result}")
                        print("---------------\n")
                        
                        cv2.rectangle(frame, (50, 150), (590, 350), (0, 0, 0), -1)
                        cv2.putText(frame, "TEST COMPLETED", (70, 190),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        cv2.putText(frame, f"Peak Freq: {freq:.2f} Hz", (70, 240),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                        cv2.putText(frame, f"Diagnosis: {result}", (70, 290),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        cv2.imshow('Tremor Analyzer', frame)
                        cv2.waitKey(4000)
                    else:
                        print("Not enough frames recorded for reliable analysis.")
                        
                    coordinate_history = []
                    timestamp_history = []
            else:
                cv2.putText(frame, "Hand Detected - Ready", (10, 75),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            if recording:
                cv2.putText(frame, "WARNING: Hand Lost!", (10, 75),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "No Hand Detected", (10, 75),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow('Tremor Analyzer', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s') or key == ord('S'):
            if not recording and hand_detected:
                recording = True
                start_time = time.time()
                coordinate_history = []
                timestamp_history = []
                print("Recording started...")
        elif key == ord('q') or key == ord('Q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
if __name__ == "__main__":
    main()