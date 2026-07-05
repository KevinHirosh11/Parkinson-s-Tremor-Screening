import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, Play, Square, User, Clock, Heart, TrendingUp, 
  AlertTriangle, CheckCircle2, Sliders, FileDown, History, 
  Settings, Bluetooth, Cpu, RefreshCw, Layers
} from 'lucide-react';
import { 
  ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, AreaChart, Area 
} from 'recharts';
import './App.css';

function App() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isEspConnected, setIsEspConnected] = useState(false);
  const [simulationMode, setSimulationMode] = useState(true);
  const [selectedTask, setSelectedTask] = useState('Finger Tapping'); // Tapping, Opening/Closing, Resting
  const [selectedHand, setSelectedHand] = useState('Right'); // Right or Left
  const [selectedTremorType, setSelectedTremorType] = useState('Resting'); // Resting, Postural, Action
  const [severityLevel, setSeverityLevel] = useState('Moderate'); // Normal, Mild, Moderate, Severe

  const [patientName, setPatientName] = useState('Sunil Perera');
  const [patientAge, setPatientAge] = useState('62');
  const [patientID, setPatientID] = useState('P-1092');

  const [timer, setTimer] = useState(0);
  const [currentFreq, setCurrentFreq] = useState(0);
  const [amplitude, setAmplitude] = useState(0);
  const [heartRate, setHeartRate] = useState(72);
  const [signalQuality, setSignalQuality] = useState(100);

  const [oscilloscopeData, setOscilloscopeData] = useState([]);
  const [fftData, setFftData] = useState([]);
  const [ppgData, setPpgData] = useState([]);
  const [historySessions, setHistorySessions] = useState([
    { id: 1, date: '2026-07-04', task: 'Finger Tapping', hand: 'Right', freq: '5.4 Hz', amplitude: '24.2 m/s²', type: 'Resting', severity: 'Moderate' },
    { id: 2, date: '2026-07-04', task: 'Hand Opening', hand: 'Right', freq: '5.2 Hz', amplitude: '18.5 m/s²', type: 'Postural', severity: 'Mild' },
    { id: 3, date: '2026-06-20', task: 'Resting Hand', hand: 'Left', freq: '1.8 Hz', amplitude: '1.2 m/s²', type: 'Normal', severity: 'Normal' },
  ]);

  const timerRef = useRef(null);
  const streamRef = useRef(null);

  const getTargetFrequency = () => {
    if (severityLevel === 'Normal') return 1.2 + Math.random() * 0.4;
    if (selectedTremorType === 'Resting') return 4.0 + Math.random() * 1.5; // Parkinsonian rest range: 4-6 Hz
    if (selectedTremorType === 'Postural') return 8.0 + Math.random() * 3.0; // Essential range: 8-12 Hz
    return 6.0 + Math.random() * 2.0; // Action range
  };

  const getTargetAmplitude = () => {
    switch(severityLevel) {
      case 'Normal': return 0.5 + Math.random() * 0.8;
      case 'Mild': return 5.0 + Math.random() * 4.0;
      case 'Moderate': return 18.0 + Math.random() * 8.0;
      case 'Severe': return 42.0 + Math.random() * 15.0;
      default: return 0.5;
    }
  };

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
      initFft.push({ freq: hz, amp: f === 2 ? 0.8 : 0.05 + Math.random() * 0.1 });
    }
    setOscilloscopeData(initOsc);
    setFftData(initFft);
    setPpgData(initPpg);
  }, []);

  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        setTimer(prev => prev + 1);
      }, 1000);
      let tick = 0;
      streamRef.current = setInterval(() => {
        tick++;
        const targetFreq = getTargetFrequency();
        const targetAmp = getTargetAmplitude();

        setCurrentFreq(Number(targetFreq.toFixed(2)));
        setAmplitude(Number(targetAmp.toFixed(2)));
        setHeartRate(Math.floor(70 + Math.sin(tick / 20) * 5 + (severityLevel === 'Severe' ? 12 : 0)));
        setSignalQuality(Math.floor(95 + Math.random() * 5));

        setOscilloscopeData(prev => {
          const slice = prev.slice(-39);
          const rad = (tick * targetFreq * Math.PI) / 15;
          const noise = (Math.random() - 0.5) * (targetAmp * 0.15);
          const tremorX = Math.sin(rad) * targetAmp + noise;
          const tremorY = Math.cos(rad * 0.9) * (targetAmp * 0.8) + noise;
          const tremorZ = Math.sin(rad * 1.2) * (targetAmp * 0.6) + noise;

          return [...slice, {
            time: tick,
            x: Number(tremorX.toFixed(2)),
            y: Number(tremorY.toFixed(2)),
            z: Number(tremorZ.toFixed(2))
          }];
        });

        setFftData(() => {
          const newFft = [];
          const peakHz = Number(targetFreq.toFixed(1));
          
          for (let f = 0; f < 30; f++) {
            const hz = (f * 0.5).toFixed(1);
            let amp = 0.02 + Math.random() * 0.08;
            
            const dist = Math.abs(parseFloat(hz) - peakHz);
            if (dist < 0.3) {
              amp += targetAmp * 1.2;
            } else if (dist < 0.8) {
              amp += targetAmp * 0.3;
            } else if (dist < 1.5) {
              amp += targetAmp * 0.08;
            }
            
            if (parseFloat(hz) === 1.0) {
              amp += 0.8;
            }

            newFft.push({ freq: `${hz}Hz`, amp: Number(amp.toFixed(2)) });
          }
          return newFft;
        });

        setPpgData(prev => {
          const slice = prev.slice(-39);
          const ppgRad = (tick * 1.3 * Math.PI) / 10;
          const pulse = Math.sin(ppgRad) > 0.7 ? 100 : Math.sin(ppgRad) < -0.6 ? 20 : 50;
          const ppgVal = pulse + (Math.random() - 0.5) * 5;
          return [...slice, { time: tick, val: Math.floor(ppgVal) }];
        });

      }, 100);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      if (streamRef.current) clearInterval(streamRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (streamRef.current) clearInterval(streamRef.current);
    };
  }, [isPlaying, selectedTremorType, severityLevel]);

  const formatTime = (timeInSeconds) => {
    const mins = Math.floor(timeInSeconds / 60);
    const secs = timeInSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStartSession = () => {
    setIsPlaying(true);
  };

  const handleStopSession = () => {
    setIsPlaying(false);

    if (timer > 0) {
      const newSession = {
        id: historySessions.length + 1,
        date: new Date().toISOString().slice(0,10),
        task: selectedTask,
        hand: selectedHand,
        freq: `${currentFreq} Hz`,
        amplitude: `${amplitude} m/s²`,
        type: selectedTremorType,
        severity: severityLevel
      };
      setHistorySessions(prev => [newSession, ...prev]);
    }
  };

  const handleResetSession = () => {
    setIsPlaying(false);
    setTimer(0);
    setCurrentFreq(0);
    setAmplitude(0);
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
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
              Webcam (MediaPipe) Active
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
              Hardware (ESP32): {isEspConnected ? 'Connected' : 'Simulating'}
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
                  <span>Showcase Parameters</span>
                  <span className="text-[10px] text-amber-500 bg-amber-950/30 border border-amber-800/30 px-1.5 py-0.5 rounded">SIMULATOR</span>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <label className="preset-label">Tremor Classification</label>
                    <select 
                      value={selectedTremorType}
                      onChange={(e) => setSelectedTremorType(e.target.value)}
                      className="preset-select"
                    >
                      <option value="Resting">Resting Tremor (Parkinsonian 4-6 Hz)</option>
                      <option value="Postural">Postural Tremor (Essential 8-12 Hz)</option>
                      <option value="Action">Action Tremor (Intention 6-8 Hz)</option>
                    </select>
                  </div>

                  <div>
                    <label className="preset-label">Severity Preset</label>
                    <div className="grid grid-cols-4 gap-1">
                      {['Normal', 'Mild', 'Moderate', 'Severe'].map(sev => (
                        <button
                          key={sev}
                          onClick={() => setSeverityLevel(sev)}
                          className={severityLevel === sev ? 'preset-btn-active' : 'preset-btn-inactive'}
                        >
                          {sev}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="space-y-3 pt-5 border-t border-slate-800 mt-6">
              {!isPlaying ? (
                <button onClick={handleStartSession} className="start-btn">
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
                  {isPlaying ? `${currentFreq.toFixed(1)} Hz` : '0.0 Hz'}
                </span>
                <span className="text-[10px] text-slate-500 block">
                  {isPlaying && currentFreq >= 4 && currentFreq <= 6 ? 'Parkinsonian Range' : isPlaying && currentFreq > 0 ? 'Physiological/Normal' : 'Ready'}
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
                  {isPlaying ? `${amplitude.toFixed(1)} m/s²` : '0.0 m/s²'}
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
                <span className="text-[10px] text-slate-500 block">Target: 02:00 mins</span>
              </div>
              <div className="bg-amber-500/10 p-2.5 rounded-lg border border-amber-500/20">
                <Clock className="h-5 w-5 text-amber-500" />
              </div>
            </div>
          </div>
          <div className="chart-card">
            <div className="chart-header-row">
              <div className="flex items-center space-x-2">
                <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping"></span>
                <h3 className="font-semibold text-slate-200">Real-Time Oscilloscope Stream</h3>
              </div>
              
              <div className="flex items-center space-x-2 text-xs">
                <span className="flex items-center space-x-1 text-[11px] text-cyan-400 font-medium">
                  <span className="h-1.5 w-6 bg-cyan-400/80 inline-block rounded-sm mr-1"></span>
                  X-Axis (Vibration)
                </span>
                <span className="flex items-center space-x-1 text-[11px] text-emerald-400 font-medium ml-3">
                  <span className="h-1.5 w-6 bg-emerald-400/80 inline-block rounded-sm mr-1"></span>
                  Y-Axis (Tapping)
                </span>
              </div>
            </div>
            <div className="osc-screen">
              {!isPlaying && (
                <div className="osc-pause-overlay">
                  <Play className="h-8 w-8 text-cyan-400/50 mb-2 animate-pulse" />
                  <p className="text-sm font-semibold text-slate-350">Signal Stream Paused</p>
                  <p className="text-xs text-slate-500 mt-1">Start session to stream live MPU6050 & MediaPipe data</p>
                </div>
              )}
              
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={oscilloscopeData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1c2541" />
                  <XAxis dataKey="time" hide />
                  <YAxis domain={['auto', 'auto']} stroke="#475569" fontSize={10} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0b132b', border: '1px solid #1e293b', borderRadius: 8, color: '#cbd5e1' }}
                    labelFormatter={() => 'Sample'}
                  />
                  <Line type="monotone" dataKey="x" stroke="#06b6d4" strokeWidth={1.8} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="y" stroke="#10b981" strokeWidth={1.5} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="z" stroke="#a855f7" strokeWidth={1} strokeDasharray="3 3" dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
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
                {!isPlaying && (
                  <div className="absolute inset-0 bg-[#070b19]/90 backdrop-blur-[1px] flex items-center justify-center z-10">
                    <p className="text-xs text-slate-500">FFT spectrum calculated in real-time</p>
                  </div>
                )}
                
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={fftData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1c2541" />
                    <XAxis dataKey="freq" stroke="#475569" fontSize={9} tickLine={false} />
                    <YAxis stroke="#475569" fontSize={9} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0b132b', border: '1px solid #1e293b', borderRadius: 8, color: '#cbd5e1' }}
                    />
                    <Bar dataKey="amp" fill="#8b5cf6" radius={[2, 2, 0, 0]} isAnimationActive={false} />
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
                    Moderate tremor patterns observed at <span className="text-amber-500 font-semibold">{currentFreq} Hz</span>. Tapping rhythm shows slight amplitude decrease (decrescendo).
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
              onClick={() => alert(`Report successfully generated for ${patientName} (${patientID})!\n- Current Task: ${selectedTask}\n- Frequency: ${currentFreq} Hz\n- Tremor Severity: ${severityLevel}\n- Hardware status: ${isEspConnected ? 'Sensor Connected' : 'Simulated'}`)}
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
