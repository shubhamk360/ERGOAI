import React, { createContext, useContext, useState, useRef, useEffect, useCallback, ReactNode } from 'react';
import { AnalysisResponse } from '../types';

interface TrackingContextType {
  isStreaming: boolean;
  wsConnected: boolean;
  analysis: AnalysisResponse | null;
  error: string;
  startWebcam: () => Promise<void>;
  stopWebcam: () => void;
  stream: MediaStream | null;
}

const TrackingContext = createContext<TrackingContextType | undefined>(undefined);

export const TrackingProvider = ({ children }: { children: ReactNode }) => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState('');
  const [stream, setStream] = useState<MediaStream | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const frameIntervalRef = useRef<number | null>(null);

  const connectWebSocket = useCallback(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication token missing. Please log in again.');
      return null;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname || 'localhost';
    const wsUrl = `${protocol}//${host}:8000/api/v1/analysis/ws?token=${token}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setWsConnected(true);
      setError('');
    };

    ws.onmessage = (event) => {
      try {
        const data: AnalysisResponse = JSON.parse(event.data);
        setAnalysis(data);
      } catch (err) {
        console.error("Failed to parse telemetry JSON", err);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      setWsConnected(false);
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    return ws;
  }, []);

  const startWebcam = async () => {
    setError('');
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480 } 
      });
      
      setStream(mediaStream);
      setIsStreaming(true);
      wsRef.current = connectWebSocket();

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        videoRef.current.play();
      }
    } catch (err: any) {
      setError('Could not access webcam. Please check camera permissions in your browser.');
      console.error("Webcam error:", err);
    }
  };

  const stopWebcam = useCallback(() => {
    // Explicitly stop all tracks to turn off the hardware camera light
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    if (videoRef.current && videoRef.current.srcObject) {
      const vidStream = videoRef.current.srcObject as MediaStream;
      vidStream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsStreaming(false);
    setWsConnected(false);
    setStream(null);
    setAnalysis(null);
    
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
  }, [stream]);

  const sendFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || !isStreaming || !wsRef.current) return;
    if (wsRef.current.readyState !== WebSocket.OPEN) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    if (context && video.readyState === video.HAVE_ENOUGH_DATA) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      canvas.toBlob((blob) => {
        if (blob && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(blob);
        }
      }, 'image/jpeg', 0.7);
    }
  }, [isStreaming]);

  useEffect(() => {
    if (isStreaming && wsConnected) {
      frameIntervalRef.current = window.setInterval(() => {
        sendFrame();
      }, 150); // ~6.6 FPS
    } else if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
    
    return () => {
      if (frameIntervalRef.current) clearInterval(frameIntervalRef.current);
    };
  }, [isStreaming, wsConnected, sendFrame]);

  const previousAnalysisRef = useRef<AnalysisResponse | null>(null);
  const lastAlertTimeRef = useRef<number>(0);

  // Trigger actual notifications
  useEffect(() => {
    if (!analysis) return;
    
    const prev = previousAnalysisRef.current;
    const isWarning = analysis.show_warning || analysis.show_break || analysis.show_fatigue;
    
    if (isWarning) {
      let settings = { desktopNotifications: true, soundAlerts: true, alertFrequency: 'immediate' };
      try {
        const saved = localStorage.getItem('ergoai_settings');
        if (saved) settings = { ...settings, ...JSON.parse(saved) };
      } catch (e) {}
      
      let frequencyMs = 0;
      if (settings.alertFrequency === '1min') frequencyMs = 60 * 1000;
      if (settings.alertFrequency === '5min') frequencyMs = 5 * 60 * 1000;
      
      const now = Date.now();
      
      const freshTransition = (analysis.show_warning && (!prev || !prev.show_warning)) ||
                              (analysis.show_break && (!prev || !prev.show_break)) ||
                              (analysis.show_fatigue && (!prev || !prev.show_fatigue));
                              
      const pastThrottle = frequencyMs > 0 && (now - lastAlertTimeRef.current > frequencyMs);
      
      if (freshTransition || pastThrottle) {
        lastAlertTimeRef.current = now;
        const msg = analysis.show_break ? analysis.break_message : 
                    analysis.show_fatigue ? analysis.fatigue_message : 
                    analysis.warning_message;
                    
        if (msg) {
          if (settings.desktopNotifications && "Notification" in window && Notification.permission === "granted") {
            new Notification("ERGOAI Alert", { body: msg, icon: "/favicon.ico" });
          }
          
          if (settings.soundAlerts) {
            try {
              const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
              const oscillator = audioContext.createOscillator();
              const gainNode = audioContext.createGain();
              oscillator.type = 'sine';
              oscillator.frequency.setValueAtTime(440, audioContext.currentTime);
              oscillator.frequency.exponentialRampToValueAtTime(880, audioContext.currentTime + 0.1);
              gainNode.gain.setValueAtTime(0, audioContext.currentTime);
              gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.05);
              gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
              oscillator.connect(gainNode);
              gainNode.connect(audioContext.destination);
              oscillator.start(audioContext.currentTime);
              oscillator.stop(audioContext.currentTime + 0.5);
            } catch (e) {}
          }
        }
      }
    } else {
      if (prev && (prev.show_warning || prev.show_break || prev.show_fatigue)) {
        lastAlertTimeRef.current = 0;
      }
    }
    
    previousAnalysisRef.current = analysis;
  }, [analysis]);

  // Clean up on global unmount (e.g. logout)
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (frameIntervalRef.current) clearInterval(frameIntervalRef.current);
      
      // Stop webcam tracks to turn off the light
      if (videoRef.current && videoRef.current.srcObject) {
        const vidStream = videoRef.current.srcObject as MediaStream;
        vidStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return (
    <TrackingContext.Provider value={{
      isStreaming,
      wsConnected,
      analysis,
      error,
      startWebcam,
      stopWebcam,
      stream
    }}>
      {/* Hidden elements required for frame capture in the background */}
      <video ref={videoRef} className="hidden" playsInline muted />
      <canvas ref={canvasRef} className="hidden" />
      
      {children}
    </TrackingContext.Provider>
  );
};

export const useTracking = () => {
  const context = useContext(TrackingContext);
  if (context === undefined) {
    throw new Error('useTracking must be used within a TrackingProvider');
  }
  return context;
};
