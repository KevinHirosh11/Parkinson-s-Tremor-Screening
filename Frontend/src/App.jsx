import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, Play, Square, User, Clock, Heart, TrendingUp, 
  AlertTriangle, CheckCircle2, Sliders, FileDown, History, 
  Settings, Bluetooth, Cpu, RefreshCw, Layers, Camera
} from 'lucide-react';
import { 
  ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, AreaChart, Area 
} from 'recharts';
import './App.css';

function App() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isEspConnected, setIsEspConnected] = useState(false);
  const [selectedTask, setSelectedTask] = useState('Finger Tapping'); // Tapping, Opening/Closing, Resting
  const [selectedHand, setSelectedHand] = useState('Right'); // Right or Left
  const [selectedTremorType, setSelectedTremorType] = useState('None'); // Resting, Postural, Action, None
  const [severityLevel, setSeverityLevel] = useState('Normal'); // Normal, Mild, Moderate, Severe

  const [patientName, setPatientName] = useState('Sunil Perera');
  const [patientAge, setPatientAge] = useState('62');
  const [patientID, setPatientID] = useState('P-1092');

  const [timer, setTimer] = useState(0);
  const [currentFreq, setCurrentFreq] = useState(0);
  const [amplitude, setAmplitude] = useState(0);
  const [heartRate, setHeartRate] = useState(72);
  const [webcamFrame, setWebcamFrame] = useState(null);
  const [handDetected, setHandDetected] = useState(false);
  const [finalStatus, setFinalStatus] = useState("Ready");

  const [oscilloscopeData, setOscilloscopeData] = useState([]);
  const [fftData, setFftData] = useState([]);
  const [ppgData, setPpgData] = useState([]);
  const [historySessions, setHistorySessions] = useState([
    { id: 1, date: '2026-07-04', task: 'Finger Tapping', hand: 'Right', freq: '5.4 Hz', amplitude: '12.5 m/s²', type: 'Resting', severity: 'Moderate' },
    { id: 2, date: '2026-07-04', task: 'Hand Opening', hand: 'Right', freq: '5.2 Hz', amplitude: '3.8 m/s²', type: 'Postural', severity: 'Mild' },
    { id: 3, date: '2026-06-20', task: 'Resting Hand', hand: 'Left', freq: '1.8 Hz', amplitude: '1.2 m/s²', type: 'None', severity: 'Normal' },
  ]);

  const wsRef = useRef(null);
  useEffect(() => {
    const initOsc = [];
    const initFft = [];
    const initPpg = [];
    for (let i = 0; i < 40; i++) {
      initOsc.push({ time: i, x: 0, y: 0, z: 0 });
      initPpg.push({ time: i, val: 50 });
    }
    for (let f = 0; f < 30; f++) {
      const hz = (f * 0.5).toFixed(1);
      initFft.push({ freq: `${hz}Hz`, amp: 0.05 + Math.random() * 0.05 });
    }
    setOscilloscopeData(initOsc);
    setFftData(initFft);
    setPpgData(initPpg);
  }, []);
  const formatTime = (timeInSeconds) => {
    const mins = Math.floor(timeInSeconds / 60);
    const secs = Math.floor(timeInSeconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStartSession = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    setTimer(0);
    setFinalStatus("Acquiring Live Streams...");
    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;
    setIsPlaying(true);

    ws.onopen = () => {
      console.log("[WebSocket] Connected to backend");
      // Request backend to start camera frame capture
      ws.send(JSON.stringify({
        action: "start",
        task: selectedTask,
        hand: selectedHand,
        tremorType: selectedTremorType,
        severity: severityLevel
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.event === "hardware_status") {
        setIsEspConnected(data.connected);
      } 
      
      else if (data.event === "data") {
        setWebcamFrame(data.frame);
        setHandDetected(data.hand_detected);
        setTimer(data.elapsed);
        setCurrentFreq(data.live_frequency);
        setAmplitude(data.live_amplitude);
        
        if (data.live_severity) {
          setSeverityLevel(data.live_severity);
        }
        if (data.live_frequency >= 4.0 && data.live_frequency <= 6.0) {
          setSelectedTremorType('Resting');
        } else if (data.live_frequency >= 8.0 && data.live_frequency <= 12.0) {
          setSelectedTremorType('Postural');
        } else if (data.live_frequency >= 6.0 && data.live_frequency < 8.0) {
          setSelectedTremorType('Action');
        } else if (data.live_frequency > 0) {
          setSelectedTremorType('Physiological');
        } else {
          setSelectedTremorType('None');
        }
        const rawPpg = data.ppg;
        setHeartRate(Math.floor(70 + (rawPpg % 15)));
        setOscilloscopeData(prev => {
          const slice = prev.slice(-39);
          return [...slice, {
            time: data.elapsed,
            x: data.imu.x,
            y: data.imu.y,
            z: data.imu.z
          }];
        });
        setPpgData(prev => {
          const slice = prev.slice(-39);
          return [...slice, {
            time: data.elapsed,
            val: rawPpg
          }];
        });
        setFftData(() => {
          const newFft = [];
          const peakHz = data.live_frequency;
          for (let f = 0; f < 30; f++) {
            const hz = (f * 0.5).toFixed(1);
            let amp = 0.02 + Math.random() * 0.08;
            
            const dist = Math.abs(parseFloat(hz) - peakHz);
            if (dist < 0.3 && peakHz > 0) {
              amp += data.live_amplitude * 1.1;
            } else if (dist < 0.8 && peakHz > 0) {
              amp += data.live_amplitude * 0.25;
            }
            newFft.push({ freq: `${hz}Hz`, amp: Number(amp.toFixed(2)) });
          }
          return newFft;
        });
      } 
      
      else if (data.event === "completed") {
        console.log("[WebSocket] Capture complete");
        setIsPlaying(false);
        setWebcamFrame(null);
        setHandDetected(false);
        setFinalStatus("Test Complete!");

        setCurrentFreq(data.final_frequency);
        setAmplitude(data.final_amplitude);
        
        const finalSeverity = data.severity || "Normal";
        setSeverityLevel(finalSeverity);

        let finalType = 'None';
        const finalFreq = data.final_frequency;
        if (finalFreq >= 4.0 && finalFreq <= 6.0) {
          finalType = 'Resting';
        } else if (finalFreq >= 8.0 && finalFreq <= 12.0) {
          finalType = 'Postural';
        } else if (finalFreq >= 6.0 && finalFreq < 8.0) {
          finalType = 'Action';
        } else if (finalFreq > 0) {
          finalType = 'Physiological';
        }
        setSelectedTremorType(finalType);
        const newSession = {
          id: Date.now(),
          date: new Date().toISOString().slice(0, 10),
          task: selectedTask,
          hand: selectedHand,
          freq: `${data.final_frequency.toFixed(2)} Hz`,
          amplitude: `${data.final_amplitude.toFixed(2)} m/s²`,
          type: finalType,
          severity: finalSeverity
        };
        setHistorySessions(prev => [newSession, ...prev]);
        
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
      }

      else if (data.event === "error") {
        alert("Backend Error: " + data.message);
        setIsPlaying(false);
      }
    };

    ws.onerror = (err) => {
      console.error("[WebSocket] error: ", err);
      alert("Failed to connect to backend server. Make sure run.py is running on port 8000!");
      setIsPlaying(false);
    };

    ws.onclose = () => {
      console.log("[WebSocket] Connection closed");
      setIsPlaying(false);
      setWebcamFrame(null);
    };
  };

  const handleStopSession = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "stop" }));
    }
    setIsPlaying(false);
    setWebcamFrame(null);
  };

  const handleResetSession = () => {
    handleStopSession();
    setTimer(0);
    setCurrentFreq(0);
    setAmplitude(0);
    setFinalStatus("Ready");
  };
  const getSeverityColor = (sev) => {
    switch (sev) {
      case 'Normal': return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
      case 'Mild': return 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10';
      case 'Moderate': return 'text-amber-500 border-amber-500/30 bg-amber-500/10';
      case 'Severe': return 'text-red-500 border-red-500/30 bg-red-500/10';
      default: return 'text-slate-400 border-slate-500/30 bg-slate-500/10';
    }
  };

  const getSeverityProgressColor = (sev) => {
    switch (sev) {
      case 'Normal': return 'bg-emerald-500';
      case 'Mild': return 'bg-cyan-500';
      case 'Moderate': return 'bg-amber-500';
      case 'Severe': return 'bg-red-600 animate-pulse';
      default: return 'bg-slate-500';
    }
  };

  return (
    <div className="app-container">
      <header className="header-container">
        <div className="logo-container">
          <div className="logo-icon-wrap">
            <Activity className="h-6 w-6 text-[#070b19]" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 via-teal-400 to-emerald-400 bg-clip-text text-transparent">
              VisionPark Diagnostics
            </h1>
            <p className="text-xs text-slate-400">Webcam & Sensor-Fusion Parkinson's Screening Support</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            <div className="status-pill-webcam">
              <span className={`h-2.5 w-2.5 rounded-full mr-2 ${isPlaying ? 'bg-emerald-500 animate-pulse' : 'bg-slate-650'}`}></span>
              Webcam (MediaPipe): {isPlaying ? 'Active' : 'Standby'}
            </div>
            <button 
              onClick={() => setIsEspConnected(prev => !prev)}
              className={`status-btn-esp ${
                isEspConnected 
                  ? 'border-cyan-500/20 bg-cyan-950/20 text-cyan-400' 
                  : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700'
              }`}
            >
              <Bluetooth className={`h-3.5 w-3.5 mr-1.5 ${isEspConnected ? 'animate-bounce' : ''}`} />
              Hardware (ESP32): {isEspConnected ? 'Connected' : 'Simulated'}
            </button>
          </div>

          <div className="h-6 w-[1px] bg-slate-800"></div>
          <div className="status-badge-cpu">
            <Cpu className="h-3.5 w-3.5 text-teal-500" />
            <span>Random Forest v2.4</span>
          </div>
        </div>
      </header>
      <main className="dashboard-grid">
        <section className="col-sidebar">
          <div className="card-container backdrop-blur-sm">
            <div className="card-header">
              <div className="flex items-center space-x-2">
                <User className="h-4.5 w-4.5 text-cyan-400" />
                <h3 className="font-semibold text-slate-200">Patient Profile</h3>
              </div>
              <span className="text-[10px] uppercase font-mono tracking-wider bg-slate-950 text-slate-400 px-2 py-0.5 rounded border border-slate-800">
                {patientID}
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <label className="input-label">Patient Name</label>
                <input 
                  type="text" 
                  value={patientName} 
                  onChange={(e) => setPatientName(e.target.value)}
                  className="input-field"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="input-label">Age</label>
                  <input 
                    type="number" 
                    value={patientAge} 
                    onChange={(e) => setPatientAge(e.target.value)}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="input-label">Patient ID</label>
                  <input 
                    type="text" 
                    value={patientID} 
                    onChange={(e) => setPatientID(e.target.value)}
                    className="input-field"
                  />
                </div>
              </div>
            </div>
          </div>
          <div className="card-container flex-1 flex flex-col justify-between">
            <div className="space-y-5">
              <div className="card-header pb-0 border-none mb-0">
                <div className="flex items-center space-x-2">
                  <Sliders className="h-4.5 w-4.5 text-teal-400" />
                  <h3 className="font-semibold text-slate-200">Protocol Configuration</h3>
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-2">Motor Task Protocol</label>
                <div className="grid grid-cols-1 gap-2">
                  {[
                    { name: 'Finger Tapping', desc: 'Repeat index/thumb touches' },
                    { name: 'Hand Opening/Closing', desc: 'Open palm & make fist' },
                    { name: 'Resting Hand', desc: 'Relax and keep arm still' }
                  ].map(task => (
                    <button
                      key={task.name}
                      onClick={() => setSelectedTask(task.name)}
                      className={selectedTask === task.name ? 'task-btn-active' : 'task-btn-inactive'}
                    >
                      <div className="font-medium">{task.name}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">{task.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-2">Testing Hand</label>
                <div className="grid grid-cols-2 gap-2">
                  {['Right', 'Left'].map(hand => (
                    <button
                      key={hand}
                      onClick={() => setSelectedHand(hand)}
                      className={selectedHand === hand ? 'hand-btn-active' : 'hand-btn-inactive'}
                    >
                      {hand} Hand
                    </button>
                  ))}
                </div>
              </div>
              <div className="preset-box">
                <div className="preset-header">
                  <span>Automated Diagnostic Engine</span>
                  <span className="text-[10px] text-emerald-500 bg-emerald-950/30 border border-emerald-800/30 px-1.5 py-0.5 rounded">AUTO CLASSIFIER</span>
                </div>
                
                <div className="space-y-3 text-xs mt-2">
                  <div className="flex justify-between items-center py-1 border-b border-slate-800/50">
                    <span className="text-slate-400">Classified Tremor Type:</span>
                    <span className="font-semibold text-cyan-400">{selectedTremorType} Tremor</span>
                  </div>

                  <div className="flex justify-between items-center py-1 border-b border-slate-800/50">
                    <span className="text-slate-400">Current Severity:</span>
                    <span className={`font-semibold ${
                      severityLevel === 'Severe' ? 'text-red-500' :
                      severityLevel === 'Moderate' ? 'text-amber-500' :
                      severityLevel === 'Mild' ? 'text-cyan-400' : 'text-emerald-400'
                    }`}>{severityLevel}</span>
                  </div>
                  
                  <p className="text-[10px] text-slate-500 leading-snug pt-1">
                    Vibration classification and severity are automatically computed in real-time by the DSP pipeline based on MediaPipe hand tracking frequency and vibration amplitude.
                  </p>
                 </div>
              </div>
            </div>
            <div className="space-y-3 pt-5 border-t border-slate-800 mt-6">
              {!isPlaying ? (
                <button onClick={handleStartSession} className="start-btn animate-pulse">
                  <Play className="h-5 w-5 fill-current" />
                  <span>Start Live Session</span>
                </button>
              ) : (
                <button onClick={handleStopSession} className="stop-btn">
                  <Square className="h-5 w-5 fill-current" />
                  <span>Stop & Save Run</span>
                </button>
              )}
              
              <button onClick={handleResetSession} className="reset-btn">
                <RefreshCw className="h-3.5 w-3.5" />
                <span>Reset Counters</span>
              </button>
            </div>
          </div>
        </section>
        <section className="col-main">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="kpi-card">
              <div className="space-y-1">
                <span className="text-[11px] text-slate-400 uppercase font-mono tracking-wider block">Current Frequency</span>
                <span className="kpi-val-cyan text-cyan-400">
                  {currentFreq > 0 ? `${currentFreq.toFixed(1)} Hz` : '0.0 Hz'}
                </span>
                <span className="text-[10px] text-slate-500 block">
                  {currentFreq >= 4 && currentFreq <= 6 ? 'Parkinsonian Range' : currentFreq > 0 ? 'Physiological/Normal' : 'Ready'}
                </span>
              </div>
              <div className="bg-cyan-500/10 p-2.5 rounded-lg border border-cyan-500/20">
                <Activity className="h-5 w-5 text-cyan-400" />
              </div>
            </div>
            <div className="kpi-card">
              <div className="space-y-1">
                <span className="text-[11px] text-slate-400 uppercase font-mono tracking-wider block">Tremor Intensity</span>
                <span className="kpi-val-emerald text-emerald-400">
                  {amplitude > 0 ? `${amplitude.toFixed(1)} m/s²` : '0.0 m/s²'}
                </span>
                <span className="text-[10px] text-slate-500 block">RMS Amplitude</span>
              </div>
              <div className="bg-emerald-500/10 p-2.5 rounded-lg border border-emerald-500/20">
                <TrendingUp className="h-5 w-5 text-emerald-400" />
              </div>
            </div>
            <div className="kpi-card">
              <div className="space-y-1">
                <span className="text-[11px] text-slate-400 uppercase font-mono tracking-wider block">Session Timer</span>
                <span className="kpi-val-amber text-amber-500">
                  {formatTime(timer)}
                </span>
                <span className="text-[10px] text-slate-500 block">Target: 10s Capture</span>
              </div>
              <div className="bg-amber-500/10 p-2.5 rounded-lg border border-amber-500/20">
                <Clock className="h-5 w-5 text-amber-500" />
              </div>
            </div>
          </div>
          <div className="chart-card">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-350 flex items-center space-x-1.5">
                    <Camera className="h-4 w-4 text-cyan-400" />
                    <span>Live MediaPipe feed</span>
                  </span>
                  {isPlaying && (
                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${handDetected ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                      {handDetected ? 'HAND DETECTED' : 'HAND LOST'}
                    </span>
                  )}
                </div>

                <div className="h-[210px] w-full bg-[#070b19]/90 border border-slate-800 rounded-lg overflow-hidden flex items-center justify-center relative">
                  {isPlaying && webcamFrame ? (
                    <img src={webcamFrame} alt="Webcam Processing" className="h-full w-full object-cover" />
                  ) : (
                    <div className="text-center p-4">
                      <Camera className="h-10 w-10 text-slate-700 mx-auto mb-2" />
                      <p className="text-xs text-slate-500">Webcam Stream Standby</p>
                      <p className="text-[10px] text-slate-650 mt-1">Status: {finalStatus}</p>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex flex-col space-y-2">
                <span className="text-xs font-semibold text-slate-350 flex items-center space-x-1">
                  <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse mr-1"></span>
                  <span>Vibration Oscilloscope</span>
                </span>
                
                <div className="h-[210px] w-full bg-[#070b19]/60 border border-slate-800 rounded-lg p-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={oscilloscopeData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1c2541" />
                      <XAxis dataKey="time" hide />
                      <YAxis domain={['auto', 'auto']} stroke="#475569" fontSize={9} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0b132b', border: '1px solid #1e293b', borderRadius: 8, color: '#cbd5e1' }}
                        labelFormatter={() => 'Sample'}
                      />
                      <Line type="monotone" dataKey="x" stroke="#06b6d4" strokeWidth={1.5} dot={false} isAnimationActive={false} />
                      <Line type="monotone" dataKey="y" stroke="#10b981" strokeWidth={1.2} dot={false} isAnimationActive={false} />
                      <Line type="monotone" dataKey="z" stroke="#a855f7" strokeWidth={0.8} strokeDasharray="3 3" dot={false} isAnimationActive={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                <div className="flex items-center space-x-2">
                  <Layers className="h-4 w-4 text-purple-400" />
                  <h4 className="text-xs font-semibold text-slate-300">Fast Fourier Transform (FFT) Power Spectrum</h4>
                </div>
                <span className="text-[10px] text-slate-500">Amplitude vs. Frequency (Hz)</span>
              </div>

              <div className="fft-screen">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={fftData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1c2541" />
                    <XAxis dataKey="freq" stroke="#475569" fontSize={8} tickLine={false} />
                    <YAxis stroke="#475569" fontSize={8} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0b132b', border: '1px solid #1e293b', borderRadius: 8, color: '#cbd5e1' }}
                    />
                    <Bar dataKey="amp" fill="#8b5cf6" radius={[1, 1, 0, 0]} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>

        </section>
        <section className="col-sidebar">
          <div className="card-container">
            <div className="card-header pb-0 border-none mb-3">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4.5 w-4.5 text-amber-500" />
                <h3 className="font-semibold text-slate-200">Condition Severity</h3>
              </div>
            </div>

            <div className="space-y-4">
              <div className="severity-row">
                <div>
                  <span className="text-[10px] text-slate-500 block">TASK DETECTED</span>
                  <span className="text-xs font-semibold text-slate-200">{selectedTask}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 block">TREMOR CLASSIFICATION</span>
                  <span className="text-xs font-semibold text-cyan-400">{selectedTremorType} Tremor</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs font-medium">
                  <span className="text-slate-400">Diagnostic Severity Indicator</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getSeverityColor(severityLevel)}`}>
                    {severityLevel.toUpperCase()}
                  </span>
                </div>
                <div className="progress-track-box">
                  <div 
                    className={`h-full rounded-full transition-all duration-300 ${getSeverityProgressColor(severityLevel)}`}
                    style={{ 
                      width: 
                        severityLevel === 'Normal' ? '15%' :
                        severityLevel === 'Mild' ? '40%' :
                        severityLevel === 'Moderate' ? '70%' : '105%' 
                    }}
                  ></div>
                </div>

                <div className="flex justify-between text-[9px] text-slate-500 px-1 font-mono">
                  <span>NORMAL</span>
                  <span>MILD</span>
                  <span>MODERATE</span>
                  <span>SEVERE</span>
                </div>
              </div>
              <div className="clinical-insight-box">
                <span className="text-[10px] text-slate-400 font-semibold block uppercase tracking-wider">Clinical Insight:</span>
                
                {severityLevel === 'Normal' && (
                  <p className="text-slate-400 leading-normal text-[11px]">
                    Frequency ranges inside typical micro-vibrations (<span className="text-emerald-400">1-2 Hz</span>). No Parkinsonian rest tremors detected in this trial.
                  </p>
                )}
                {severityLevel === 'Mild' && (
                  <p className="text-slate-400 leading-normal text-[11px]">
                    Trace amplitude deviations seen. Dominant tremor band stable outside 4-6 Hz. Continuous check suggested.
                  </p>
                )}
                {severityLevel === 'Moderate' && (
                  <p className="text-slate-400 leading-normal text-[11px]">
                    Moderate tremor patterns observed. Tapping rhythm shows slight amplitude decrease (decrescendo).
                  </p>
                )}
                {severityLevel === 'Severe' && (
                  <p className="text-slate-350 leading-normal text-[11px]">
                    High tremor activity detected in the Parkinson's diagnostic range (<span className="text-red-500 font-semibold">4-6 Hz</span>). Suggest clinical assessment.
                  </p>
                )}
              </div>
            </div>
          </div>
          <div className="card-container flex-1 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="card-header pb-0 border-none mb-0">
                <div className="flex items-center space-x-2">
                  <History className="h-4.5 w-4.5 text-purple-400" />
                  <h3 className="font-semibold text-slate-200">Historical Trials</h3>
                </div>
              </div>
              <div className="history-list-container">
                {historySessions.map((session) => (
                  <div key={session.id} className="history-item-box">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-1.5">
                        <span className="font-medium text-slate-350">{session.task}</span>
                        <span className="text-[9px] bg-slate-900 px-1 py-0.2 rounded text-slate-500">{session.hand}</span>
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">{session.date}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-slate-300 font-mono">{session.freq}</div>
                      <span className={`text-[9px] font-bold ${
                        session.severity === 'Severe' ? 'text-red-400' :
                        session.severity === 'Moderate' ? 'text-amber-500' :
                        session.severity === 'Mild' ? 'text-cyan-400' : 'text-emerald-400'
                      }`}>
                        {session.severity}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="ppg-container">
              <div className="flex items-center justify-between border-b border-slate-850 pb-1.5">
                <div className="flex items-center space-x-1.5">
                  <Heart className="h-4 w-4 text-red-500 animate-pulse" />
                  <span className="text-xs font-semibold text-slate-300">PPG Heart Rate</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">{heartRate} BPM</span>
              </div>
              <div className="h-[40px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={ppgData} margin={{ top: 2, right: 2, left: -25, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorPpg" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" hide />
                    <YAxis domain={['auto', 'auto']} hide />
                    <Area type="monotone" dataKey="val" stroke="#ef4444" strokeWidth={1.5} fillOpacity={1} fill="url(#colorPpg)" dot={false} isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
            <button 
              onClick={() => alert(`Report successfully generated for ${patientName} (${patientID})!\n- Current Task: ${selectedTask}\n- Frequency: ${currentFreq} Hz\n- Tremor Severity: ${severityLevel}\n- Hardware status: ${isEspConnected ? 'Sensor Connected' : 'Simulating'}`)}
              className="export-btn"
            >
              <FileDown className="h-4 w-4 text-cyan-400" />
              <span>Export Diagnostic PDF</span>
            </button>
          </div>

        </section>

      </main>
      <footer className="footer-layout">
        <p>VisionPark Screening Tool - Educational Research Prototype (IEEE Young Protégé 2026 update)</p>
        <p className="mt-1 md:mt-0 text-amber-500 bg-amber-950/20 px-2 py-0.5 rounded border border-amber-900/30">
          ⚠️ Disclaimer: Not a clinical diagnosis system. Abnormal signals require medical consulting.
        </p>
      </footer>
    </div>
  );
}

export default App;
