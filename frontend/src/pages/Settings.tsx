import React, { useState, useEffect } from 'react';
import { Camera, Bell, Shield, Save, Trash2, Check, AlertCircle } from 'lucide-react';

// Default settings
const DEFAULT_SETTINGS = {
  slouchThreshold: 15,
  desktopNotifications: true,
  soundAlerts: true,
  alertFrequency: 'immediate',
  allowTelemetry: false,
  selectedCamera: 'default',
};

const Settings = () => {
  const [activeTab, setActiveTab] = useState('detection');
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // Load settings on mount
  useEffect(() => {
    const saved = localStorage.getItem('ergoai_settings');
    if (saved) {
      try {
        setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(saved) });
      } catch (e) {
        console.error("Failed to parse settings", e);
      }
    }
  }, []);

  // Generic handler for setting changes
  const updateSetting = (key: keyof typeof DEFAULT_SETTINGS, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    localStorage.setItem('ergoai_settings', JSON.stringify(newSettings));
    
    setSaveStatus('Preferences saved locally');
    setTimeout(() => setSaveStatus(null), 3000);
  };

  const clearCache = () => {
    localStorage.removeItem('ergoai_settings');
    setSettings(DEFAULT_SETTINGS);
    setSaveStatus('Local cache cleared! Restored to defaults.');
    setTimeout(() => setSaveStatus(null), 3000);
  };

  const tabs = [
    { id: 'detection', label: 'Detection', icon: Camera },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'privacy', label: 'Privacy', icon: Shield },
  ];

  return (
    <div className="space-y-6 max-w-4xl pb-12">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Settings</h1>
          <p className="text-slate-400 mt-1">Configure your ERGOAI preferences.</p>
        </div>
        {saveStatus && (
          <div className="flex items-center space-x-2 text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20 animate-fade-in text-sm font-medium">
            <Check className="w-4 h-4" />
            <span>{saveStatus}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
        {/* Navigation Sidebar */}
        <div className="space-y-2 sticky top-6">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full text-left px-4 py-3 rounded-xl font-medium flex items-center space-x-3 transition-all duration-200 ${
                  isActive 
                    ? 'bg-violet-600/10 text-violet-400 shadow-sm border border-violet-500/20' 
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border border-transparent'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-violet-400' : 'opacity-70'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content Area */}
        <div className="md:col-span-2 space-y-6">
          
          {/* DETECTION TAB */}
          {activeTab === 'detection' && (
            <div className="glass-panel p-6 animate-fade-in">
              <h3 className="text-lg font-semibold text-white mb-4">Detection Sensitivity</h3>
              <p className="text-slate-400 mb-6 text-sm">Adjust how strict the posture analysis should be.</p>
              
              <div className="space-y-6">
                <div>
                  <label className="flex justify-between text-sm font-medium text-slate-300 mb-2">
                    <span>Slouch Threshold Angle</span>
                    <span className="text-violet-400">{settings.slouchThreshold}°</span>
                  </label>
                  <input 
                    type="range" 
                    min="5" 
                    max="30" 
                    value={settings.slouchThreshold}
                    onChange={(e) => updateSetting('slouchThreshold', parseInt(e.target.value))}
                    className="w-full accent-violet-500 cursor-pointer"
                  />
                  <p className="text-xs text-slate-500 mt-2">
                    Lower values make the system more sensitive to small deviations in posture.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* NOTIFICATIONS TAB */}
          {activeTab === 'notifications' && (
            <div className="space-y-6 animate-fade-in">
              <div className="glass-panel p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Alert Preferences</h3>
                
                <div className="space-y-6">
                  {/* Desktop Notifications Toggle */}
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-slate-200">Desktop Notifications</h4>
                      <p className="text-xs text-slate-400 mt-1">Show native browser popups when posture degrades</p>
                      
                      <button 
                        onClick={() => {
                          if (!("Notification" in window)) {
                            alert("This browser does not support desktop notification");
                            return;
                          }
                          Notification.requestPermission().then((permission) => {
                            if (permission === "granted") {
                              const n = new Notification("ERGOAI Test Notification", {
                                body: "If you can see this, notifications are working!",
                                icon: "/favicon.ico"
                              });
                              n.onclick = () => window.focus();
                            } else {
                              alert(`Permission is currently: ${permission}. Please enable notifications in your browser settings (click the lock icon in the URL bar).`);
                            }
                          });
                        }}
                        className="mt-3 text-xs px-3 py-1.5 bg-violet-500/20 text-violet-300 rounded hover:bg-violet-500/30 transition-colors"
                      >
                        Test Notification
                      </button>
                      <p className="text-[10px] text-slate-500 mt-2">
                        * If you don't see the test popup, check your Mac's "Do Not Disturb" or System Settings &gt; Notifications &gt; Browser.
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={settings.desktopNotifications}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          if (checked && "Notification" in window) {
                            Notification.requestPermission();
                          }
                          updateSetting('desktopNotifications', checked);
                        }}
                      />
                      <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-500"></div>
                    </label>
                  </div>

                  {/* Sound Alerts Toggle */}
                  <div className="flex items-center justify-between pt-4 border-t border-slate-800">
                    <div>
                      <h4 className="text-sm font-medium text-slate-200">Sound Alerts</h4>
                      <p className="text-xs text-slate-400 mt-1">Play a subtle chime when you need to sit up</p>
                      
                      <button 
                        onClick={() => {
                          try {
                            const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
                            const oscillator = audioContext.createOscillator();
                            const gainNode = audioContext.createGain();
                            
                            oscillator.type = 'sine';
                            oscillator.frequency.setValueAtTime(440, audioContext.currentTime); // A4
                            oscillator.frequency.exponentialRampToValueAtTime(880, audioContext.currentTime + 0.1);
                            
                            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
                            gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.05);
                            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
                            
                            oscillator.connect(gainNode);
                            gainNode.connect(audioContext.destination);
                            
                            oscillator.start(audioContext.currentTime);
                            oscillator.stop(audioContext.currentTime + 0.5);
                          } catch (e) {
                            console.error("Audio playback failed", e);
                          }
                        }}
                        className="mt-3 text-xs px-3 py-1.5 bg-violet-500/20 text-violet-300 rounded hover:bg-violet-500/30 transition-colors"
                      >
                        Test Sound
                      </button>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={settings.soundAlerts}
                        onChange={(e) => updateSetting('soundAlerts', e.target.checked)}
                      />
                      <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-500"></div>
                    </label>
                  </div>

                  {/* Frequency Dropdown */}
                  <div className="pt-4 border-t border-slate-800">
                    <h4 className="text-sm font-medium text-slate-200 mb-3">Notification Frequency</h4>
                    <select 
                      value={settings.alertFrequency}
                      onChange={(e) => updateSetting('alertFrequency', e.target.value)}
                      className="bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg focus:ring-violet-500 focus:border-violet-500 block w-full p-2.5 outline-none"
                    >
                      <option value="immediate">Immediate (As soon as detected)</option>
                      <option value="1min">Wait 1 Minute</option>
                      <option value="5min">Wait 5 Minutes</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* PRIVACY TAB */}
          {activeTab === 'privacy' && (
            <div className="space-y-6 animate-fade-in">
              <div className="glass-panel p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Data & Privacy</h3>
                
                <div className="space-y-6">
                  {/* Telemetry Toggle */}
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-slate-200">Anonymous Telemetry</h4>
                      <p className="text-xs text-slate-400 mt-1 max-w-[250px]">Help improve our AI model by submitting anonymous angle readings.</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={settings.allowTelemetry}
                        onChange={(e) => updateSetting('allowTelemetry', e.target.checked)}
                      />
                      <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-500"></div>
                    </label>
                  </div>

                  {/* Clear Cache */}
                  <div className="pt-4 border-t border-slate-800">
                    <h4 className="text-sm font-medium text-slate-200 mb-2">Local Storage Cache</h4>
                    <p className="text-xs text-slate-400 mb-4">Clear all locally saved preferences and authentication tokens on this browser.</p>
                    
                    <button 
                      onClick={clearCache}
                      className="flex items-center space-x-2 px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-sm font-medium rounded-lg border border-rose-500/30 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span>Clear Local Cache</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default Settings;
