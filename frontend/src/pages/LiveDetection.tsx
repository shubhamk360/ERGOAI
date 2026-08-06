import React, { useRef, useEffect } from 'react';
import { Camera, AlertTriangle, Sparkles, VideoOff, Wifi } from 'lucide-react';
import api from '../services/api';
import { useTracking } from '../context/TrackingContext';

const LiveDetection: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  
  const { 
    isStreaming, 
    wsConnected, 
    analysis, 
    error, 
    startWebcam, 
    stopWebcam, 
    stream 
  } = useTracking();

  // Attach the global stream to the local video element for preview
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.srcObject = stream || null;
    }
  }, [stream]);

  const getPostureColor = (label: string) => {
    if (label === 'Good posture') return 'text-emerald-400';
    if (label === 'Calibrating') return 'text-blue-400';
    if (label === 'No pose detected') return 'text-slate-400';
    return 'text-amber-400';
  };

  return (
    <div className="h-full flex flex-col space-y-6 pb-12">
      <div className="flex justify-between items-end">
        <div>
          <div className="flex items-center space-x-2 text-violet-400 font-semibold text-xs tracking-wider uppercase mb-1">
            <Sparkles className="w-4 h-4" />
            <span>Real-time Vision</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Live Posture Monitor</h1>
          <p className="text-slate-400 text-sm mt-1">Computer vision pose landmark detection via WebSockets.</p>
        </div>
        {isStreaming && (
          <div className="flex items-center space-x-2 px-3 py-1 bg-slate-900 border border-slate-800 rounded-full">
            <Wifi className={`w-3.5 h-3.5 ${wsConnected ? 'text-emerald-400' : 'text-amber-400 animate-pulse'}`} />
            <span className="text-xs font-medium text-slate-300">
              {wsConnected ? 'WebSocket Live Stream' : 'Connecting WS...'}
            </span>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 px-4 py-3 rounded-2xl text-sm font-medium flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0">
        {/* Main Camera Frame */}
        <div className="flex-1 glass-panel p-6 flex flex-col min-h-[480px]">
          <div className="relative flex-1 bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 flex items-center justify-center shadow-inner">
            {!isStreaming && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 bg-slate-950/80 backdrop-blur-sm p-6 text-center">
                <div className="w-16 h-16 rounded-2xl bg-slate-900 flex items-center justify-center mb-4 border border-slate-800">
                  <VideoOff className="w-8 h-8 opacity-60 text-slate-400" />
                </div>
                <h3 className="text-lg font-semibold text-slate-300 mb-1">Webcam Disabled</h3>
                <p className="text-xs text-slate-500 max-w-sm">Enable your camera to start real-time computer vision posture telemetry.</p>
              </div>
            )}
            
            <video 
              ref={videoRef} 
              className={`w-full h-full object-cover ${isStreaming ? 'block' : 'hidden'}`}
              playsInline 
              muted 
              autoPlay
            />

            {/* Live Indicator Overlay */}
            {isStreaming && analysis && analysis.posture_label !== "No pose detected" && (
              <div className="absolute top-4 right-4 bg-slate-950/90 backdrop-blur-xl px-4 py-2 rounded-2xl border border-slate-800 shadow-2xl flex items-center space-x-2.5">
                <div className={`w-2.5 h-2.5 rounded-full ${analysis.posture_label === 'Good posture' ? 'bg-emerald-400 shadow-emerald-500/50 shadow-lg' : 'bg-amber-400 shadow-amber-500/50 shadow-lg'} animate-pulse`} />
                <span className={`font-bold text-xs uppercase tracking-wider ${getPostureColor(analysis.posture_label)}`}>
                  {analysis.posture_label}
                </span>
              </div>
            )}

            {isStreaming && analysis && analysis.calibration_message && (
              <div className="absolute top-16 right-4 bg-blue-950/90 backdrop-blur-xl px-4 py-2 rounded-2xl border border-blue-800 shadow-2xl flex items-center space-x-2.5">
                <span className="font-bold text-xs uppercase tracking-wider text-blue-400">
                  {analysis.calibration_message}
                </span>
              </div>
            )}
          </div>

          <div className="mt-6 flex justify-center space-x-4">
            {!isStreaming ? (
              <button onClick={startWebcam} className="btn-primary">
                <Camera className="w-4 h-4" />
                <span>Start WebSocket Feed</span>
              </button>
            ) : (
              <>
                <button 
                  onClick={async () => {
                    try {
                      await api.post('/calibration/start');
                    } catch (err) {
                      console.error("Failed to start calibration", err);
                    }
                  }} 
                  className="btn-primary bg-indigo-500 hover:bg-indigo-600"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Calibrate</span>
                </button>
                <button onClick={stopWebcam} className="btn-secondary text-rose-400 hover:bg-rose-500/10 border-rose-500/20">
                  <VideoOff className="w-4 h-4" />
                  <span>Stop Feed</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Live Telemetry Sidebar */}
        <div className="w-full lg:w-80 space-y-6 flex-shrink-0">
          <div className="glass-panel p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h3 className="text-base font-semibold text-white">Angle Telemetry</h3>
              <span className="badge-violet">Live</span>
            </div>
            
            <div className="space-y-3">
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Neck Angle</div>
                <div className="text-2xl font-extrabold text-sky-400">
                  {analysis?.neck_angle != null ? `${analysis.neck_angle.toFixed(1)}°` : '--'}
                </div>
              </div>

              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Back Angle</div>
                <div className="text-2xl font-extrabold text-purple-400">
                  {analysis?.back_angle != null ? `${analysis.back_angle.toFixed(1)}°` : '--'}
                </div>
              </div>
            </div>
          </div>

          {(analysis?.show_warning || analysis?.show_break || analysis?.show_fatigue) && (
            <div className="glass-panel p-6 bg-amber-500/10 border-amber-500/30">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-amber-400 font-bold text-sm mb-1 uppercase tracking-wider">Ergonomic Alerts</h3>
                  {analysis.show_warning && (
                    <p className="text-xs text-amber-200/90 mb-2 leading-relaxed">{analysis.warning_message}</p>
                  )}
                  {analysis.show_break && (
                    <p className="text-xs text-amber-200/90 mb-2 leading-relaxed">{analysis.break_message}</p>
                  )}
                  {analysis.show_fatigue && (
                    <p className="text-xs text-rose-400 mb-2 font-semibold leading-relaxed">{analysis.fatigue_message}</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LiveDetection;
