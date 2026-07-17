import cv2
import numpy as np
import time
import json
import base64
import asyncio
import threading
import os
from scipy.signal import butter, filtfilt
import mediapipe as mp
import serial
import serial.tools.list_ports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
import shutil
import tempfile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from pdf_generator import generate_screening_pdf
import joblib
from sklearn.ensemble import RandomForestClassifier

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

SEVERITY_MODEL_PATH = os.path.join(MODELS_DIR, "severity_model.pkl")
CATEGORY_MODEL_PATH = os.path.join(MODELS_DIR, "category_model.pkl")
STAGE_MODEL_PATH = os.path.join(MODELS_DIR, "stage_model.pkl")

def train_and_save_models():
    print("[ML Startup] Training ML models on clinical rules...")
    np.random.seed(42)
    n_samples = 10000

    freqs = np.random.uniform(0.0, 15.0, n_samples)
    amps = np.random.uniform(0.0, 30.0, n_samples)
    
    X = np.stack([freqs, amps], axis=1)
    
    y_severity = []
    y_category = []
    y_stage = []
    
    for f, a in X:
        if f < 3.0 or a < 1.5:
            sev = "Normal"
        elif 1.5 <= a < 5.0:
            sev = "Mild"
        elif 5.0 <= a <= 15.0:
            sev = "Moderate"
        else:
            sev = "Severe"
        y_severity.append(sev)

        if 4.0 <= f <= 6.0:
            cat = "Parkinsonian Rest Tremor Range (4-6 Hz)"
        elif 8.0 <= f <= 12.0:
            cat = "Essential / Physiological Tremor Range (8-12 Hz)"
        else:
            cat = "Normal / Low Activity"
        y_category.append(cat)

        stg = "Stage 0 (No Tremor)"
        if sev == "Mild":
            stg = "Stage 1 (Unilateral involvement only)"
        elif sev == "Moderate":
            stg = "Stage 2 (Bilateral involvement, without impairment of balance)"
        elif sev == "Severe":
            stg = "Stage 3 (Mild to moderate bilateral disease; some postural instability)"
        y_stage.append(stg)
        
    severity_clf = RandomForestClassifier(n_estimators=50, random_state=42)
    severity_clf.fit(X, y_severity)
    joblib.dump(severity_clf, SEVERITY_MODEL_PATH)
    
    category_clf = RandomForestClassifier(n_estimators=50, random_state=42)
    category_clf.fit(X, y_category)
    joblib.dump(category_clf, CATEGORY_MODEL_PATH)
    
    stage_clf = RandomForestClassifier(n_estimators=50, random_state=42)
    stage_clf.fit(X, y_stage)
    joblib.dump(stage_clf, STAGE_MODEL_PATH)
    print("[ML Startup] Models trained and saved successfully.")

if not (os.path.exists(SEVERITY_MODEL_PATH) and os.path.exists(CATEGORY_MODEL_PATH) and os.path.exists(STAGE_MODEL_PATH)):
    train_and_save_models()

severity_clf = joblib.load(SEVERITY_MODEL_PATH)
category_clf = joblib.load(CATEGORY_MODEL_PATH)
stage_clf = joblib.load(STAGE_MODEL_PATH)

app = FastAPI(title="Tremor Plot Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

RECORD_TIME = 30.0 
TARGET_FPS = 30.0
dt = 1.0 / TARGET_FPS

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1
)
mp_draw = mp.solutions.drawing_utils
class SerialSensorReader:
    def __init__(self):
        self.ser = None
        self.running = False
        self.latest_imu = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.latest_ppg = 50
        self.latest_bpm = 0
        self.thread = None

    def find_esp32_port(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "CP210" in port.description or "CH340" in port.description or "USB" in port.description:
                return port.device
        if ports:
            return ports[0].device
        return None

    def start(self):
        port = self.find_esp32_port()
        if not port:
            msg = "No ESP32/USB Serial device detected. Falling back to software simulation."
            print(f"[Hardware] {msg}")
            self.running = True
            self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.thread.start()
            return False, msg
        
        try:
            self.ser = serial.Serial(port, 115200, timeout=0.1)
            self.ser.setDTR(False)
            self.ser.setRTS(False)
            self.ser.reset_input_buffer()
            import time
            time.sleep(2)
            self.ser.reset_input_buffer()
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            msg = f"Connected to ESP32 on port {port}"
            print(f"[Hardware] {msg}")
            return True, msg
        except Exception as e:
            msg = f"Failed to open serial port {port}: {e}. Falling back to software simulation."
            print(f"[Hardware] {msg}")
            self.running = True
            self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.thread.start()
            return False, msg

    def _simulation_loop(self):
        t = 0.0
        while self.running:
            # Simulate PPG signal (sine wave + noise)
            ppg_val = int(2048 + 400 * np.sin(2 * np.pi * 1.25 * t) + np.random.normal(0, 15))
            self.latest_ppg = ppg_val
            # Simulate a realistic heart rate (e.g. oscillating between 71 and 75)
            self.latest_bpm = int(73 + 2 * np.sin(2 * np.pi * 0.03 * t))
            
            # Simulate minor IMU jitter
            self.latest_imu = {
                "x": float(np.random.normal(0, 0.03)),
                "y": float(np.random.normal(0, 0.03)),
                "z": float(9.8 + np.random.normal(0, 0.03))
            }
            
            t += 0.033
            import time
            time.sleep(0.033)

    def _read_loop(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    if "IMU:" in line or "PPG:" in line:
                        parts = line.split("|")
                        for part in parts:
                            if part.startswith("IMU:"):
                                vals = part.replace("IMU:", "").split(",")
                                if len(vals) >= 3:
                                    self.latest_imu = {
                                        "x": float(vals[0]),
                                        "y": float(vals[1]),
                                        "z": float(vals[2])
                                    }
                            elif part.startswith("PPG:"):
                                try:
                                    self.latest_ppg = int(part.replace("PPG:", ""))
                                except ValueError:
                                    pass
                            elif part.startswith("BPM:"):
                                try:
                                    self.latest_bpm = int(part.replace("BPM:", ""))
                                except ValueError:
                                    pass
                    else:
                        print(f"[Hardware] Raw line: {line}")
            except Exception as e:
                pass

    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None

serial_reader = SerialSensorReader()

def detect_hand_mediapipe(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    if not results.multi_hand_landmarks:
        return None, None
        
    hand_landmarks = results.multi_hand_landmarks[0]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

    tx = index_tip.x * 0.7 + mcp.x * 0.2 + wrist.x * 0.1
    ty = index_tip.y * 0.7 + mcp.y * 0.2 + wrist.y * 0.1
    
    h, w, _ = frame.shape
    cx, cy = int(tx * w), int(ty * h)
    
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
    if len(time_series) < 20:
        return 0.0, 0.0, "Normal / Insufficient Data", "Normal"
        
    t_uniform = np.linspace(timestamps[0], timestamps[-1], len(timestamps))

    x_coords = np.array([pt[0] for pt in time_series])
    y_coords = np.array([pt[1] for pt in time_series])
    
    x_interp = np.interp(t_uniform, timestamps, x_coords)
    y_interp = np.interp(t_uniform, timestamps, y_coords)
    
    x_detrend = x_interp - np.mean(x_interp)
    y_detrend = y_interp - np.mean(y_interp)
    
    displacement = np.sqrt(x_detrend**2 + y_detrend**2)
    
    fs = TARGET_FPS
    try:
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
            return 0.0, 0.0, "Normal", "Normal"
            
        peak_idx = np.argmax(valid_mag)
        dominant_frequency = valid_freqs[peak_idx]
        peak_amplitude = valid_mag[peak_idx]
    except Exception as e:
        print(f"DSP Error: {e}")
        return 0.0, 0.0, "Normal / Calculation Error", "Normal"
    scaled_amp = peak_amplitude * 100

    features = np.array([[float(dominant_frequency), float(scaled_amp)]])
    try:
        severity = severity_clf.predict(features)[0]
        category = category_clf.predict(features)[0]
    except Exception as e:
        print(f"[ML Prediction Error] {e}")
        severity = "Normal"
        category = "Normal / Low Activity"
        
    return float(dominant_frequency), float(scaled_amp), category, severity

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Client connected")
    
    cap = None
    recording = False
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            
            if action == "start":
                hw_connected, hw_msg = serial_reader.start()
                await websocket.send_json({
                    "event": "hardware_status",
                    "connected": hw_connected,
                    "message": hw_msg
                })
                
                cap = None
                try:
                    cap = cv2.VideoCapture(0)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    if not cap.isOpened():
                        print("[WS] Webcam not available, running in sensor-only mode")
                        cap.release()
                        cap = None
                    else:
                        print("[WS] Webcam opened successfully")
                except Exception as e:
                    print(f"[WS] Webcam error: {e}")
                    cap = None
                
                recording = True
                start_time = time.time()
                coordinate_history = []
                timestamp_history = []
                
                print("[WS] Started live session")
                while recording:
                    current_time = time.time()
                    elapsed = current_time - start_time

                    hand_detected = False
                    frame_base64 = ""
                    cx, cy = 0, 0

                    if cap and cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break
                            
                        frame = cv2.flip(frame, 1)
                        h, w, c = frame.shape
                        
                        hand_landmarks, finger_tip = detect_hand_mediapipe(frame)
                        
                        if finger_tip is not None:
                            hand_detected = True
                            cx, cy = finger_tip[0], finger_tip[1]
                            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                            cv2.circle(frame, (cx, cy), 8, (0, 0, 255), -1)
                        
                        if hand_detected:
                            coordinate_history.append((cx / w, cy / h))
                            timestamp_history.append(elapsed)
                        
                        _, buffer = cv2.imencode('.jpg', frame)
                        frame_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
                    
                    imu_data = serial_reader.latest_imu
                    ppg_data = serial_reader.latest_ppg
                    bpm_data = serial_reader.latest_bpm

                    live_freq = 0.0
                    live_amp = 0.0
                    live_severity = "Normal"
                    if len(coordinate_history) > 15:
                        try:
                            recent_coords = coordinate_history[-30:]
                            recent_times = timestamp_history[-30:]
                            live_freq, live_amp, _, live_severity = analyze_tremor(recent_coords, recent_times)
                        except Exception:
                            pass
                    
                    await websocket.send_json({
                        "event": "data",
                        "frame": frame_base64,
                        "hand_detected": hand_detected,
                        "elapsed": round(elapsed, 1),
                        "live_frequency": round(live_freq, 1),
                        "live_amplitude": round(live_amp, 1),
                        "live_severity": live_severity,
                        "imu": imu_data,
                        "ppg": ppg_data,
                        "bpm": bpm_data
                    })
                    if elapsed >= RECORD_TIME:
                        recording = False
                        break
                    await asyncio.sleep(0.033)
                print("[WS] Session capture complete, processing...")
                if len(coordinate_history) > 30:
                    final_freq, final_amp, category, severity = analyze_tremor(coordinate_history, timestamp_history)
                else:
                    final_freq, final_amp, category, severity = 0.0, 0.0, "No Hand Detected / Insufficient Data", "Normal"
                    
                await websocket.send_json({
                    "event": "completed",
                    "final_frequency": round(final_freq, 2),
                    "final_amplitude": round(final_amp, 2),
                    "category": category,
                    "severity": severity
                })
                if cap:
                    cap.release()
                    cap = None
                serial_reader.stop()
                
            elif action == "stop":
                print("[WS] Session stopped by user command")
                recording = False
                if cap:
                    cap.release()
                    cap = None
                serial_reader.stop()
                await websocket.send_json({
                    "event": "stopped"
                })
                
    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS] Error in socket handler: {e}")
    finally:
        if cap:
            cap.release()
        serial_reader.stop()

class DiagnosticReportRequest(BaseModel):
    patientName: str
    patientAge: str
    patientID: str
    selectedTask: str
    selectedHand: str
    currentFreq: float
    amplitude: float
    severityLevel: str
    heartRate: int
    isEspConnected: bool

@app.post("/api/generate-pdf")
def create_pdf_report(report_data: DiagnosticReportRequest):
    try:
        report_file = generate_screening_pdf(report_data.dict())
        return FileResponse(
            path=report_file,
            media_type="application/pdf",
            filename=os.path.basename(report_file)
        )
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return {"error": str(e)}

@app.post("/api/upload-video")
async def upload_video(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            shutil.copyfileobj(file.file, temp_video)
            temp_path = temp_video.name
            
        print(f"[Video Analysis] Saved uploaded video to {temp_path}")
        
        cap = cv2.VideoCapture(temp_path)
        coordinate_history = []
        timestamp_history = []
        
        fps = cap.get(cv2.CAP_PROP_FPS) or TARGET_FPS
        frame_delay = 1.0 / fps
        elapsed = 0.0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            hand_landmarks, index_tip_coords = detect_hand_mediapipe(frame)
            if hand_landmarks and index_tip_coords:
                h, w, _ = frame.shape
                cx, cy = index_tip_coords
                coordinate_history.append((cx / w, cy / h))
                timestamp_history.append(elapsed)
                
            elapsed += frame_delay
            
        cap.release()
        
        try:
            os.remove(temp_path)
        except Exception:
            pass
            
        print(f"[Video Analysis] Extracted {len(coordinate_history)} coordinates from video")
        
        if len(coordinate_history) > 20:
            frequency, amplitude, category, severity = analyze_tremor(coordinate_history, timestamp_history)
        else:
            frequency, amplitude, category, severity = 0.0, 0.0, "Insufficient Data", "Normal"
            
        # Predict stage using ML model
        try:
            features = np.array([[float(frequency), float(amplitude)]])
            stage = stage_clf.predict(features)[0]
        except Exception as e:
            print(f"[ML Stage Prediction Error] {e}")
            stage = "Stage 0 (No Tremor)"
            
        return {
            "frequency": round(frequency, 2),
            "amplitude": round(amplitude, 2),
            "category": category,
            "severity": severity,
            "stage": stage
        }
    except Exception as e:
        print(f"Error processing video upload: {e}")
        return {"error": str(e), "frequency": 0.0, "amplitude": 0.0, "severity": "Normal", "stage": "Stage 0"}

@app.get("/")
def read_root():
    port = int(os.environ.get("TREMOR_BACKEND_PORT", "8000"))
    return {"status": "Tremor Plot Backend Active", "port": port}

if __name__ == "__main__":
    host = os.environ.get("TREMOR_BACKEND_HOST", "127.0.0.1")
    port = int(os.environ.get("TREMOR_BACKEND_PORT", "8000"))
    uvicorn.run("run:app", host=host, port=port, reload=True)
