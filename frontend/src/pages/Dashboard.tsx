import React, { useEffect, useState } from 'react';
import { Activity, Clock, ShieldCheck, ShieldAlert, Sparkles, Zap } from 'lucide-react';
import api from '../services/api';
import { DailySummary, LiveSessionSnapshot } from '../types';

const Dashboard: React.FC = () => {
  const [dailyStat, setDailyStat] = useState<DailySummary | null>(null);
  const [recentSession, setRecentSession] = useState<LiveSessionSnapshot | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dailyRes, sessionRes] = await Promise.allSettled([
          api.get('/analytics/daily', { params: { days: 1 } }),
          api.get('/sessions/live')
        ]);
        
        if (dailyRes.status === 'fulfilled' && dailyRes.value.data && dailyRes.value.data.length > 0) {
          setDailyStat(dailyRes.value.data[0]);
        }
        
        if (sessionRes.status === 'fulfilled' && sessionRes.value.data && sessionRes.value.data.status !== "No active session") {
           setRecentSession(sessionRes.value.data);
        }
      } catch (error) {
        console.error("Error fetching dashboard data", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center min-h-[400px]">
        <div className="animate-spin h-9 w-9 border-4 border-violet-500 border-t-transparent rounded-full shadow-lg shadow-violet-500/20"></div>
      </div>
    );
  }

  const goodPercent = dailyStat?.good_posture_percent ?? 0;
  const isGoodPosture = goodPercent >= 70;

  return (
    <div className="space-y-8 pb-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <div className="flex items-center space-x-2 text-violet-400 font-semibold text-xs tracking-wider uppercase mb-1">
            <Sparkles className="w-4 h-4" />
            <span>Ergonomic Intelligence</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Posture Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">Real-time overview of your daily physical health and posture scores.</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <span className="badge-violet px-3 py-1 text-xs">
            <Zap className="w-3.5 h-3.5 mr-1 text-violet-400 animate-pulse" /> AI Monitor Active
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Good Posture Card */}
        <div className="glass-panel-interactive p-6 relative overflow-hidden group">
          <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-violet-500/10 rounded-full blur-2xl group-hover:bg-violet-500/20 transition-all"></div>
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-violet-500/10 rounded-xl text-violet-400 border border-violet-500/20">
              <Activity className="w-6 h-6" />
            </div>
            <span className="badge-violet">Today</span>
          </div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Ergonomic Posture</h3>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-4xl font-extrabold text-white">{goodPercent.toFixed(1)}%</span>
            <span className="text-xs text-slate-400 font-medium">good posture</span>
          </div>
          
          <div className="w-full bg-slate-800/80 rounded-full h-2 mt-4 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-violet-500 to-indigo-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(0, goodPercent))}%` }}
            ></div>
          </div>
        </div>

        {/* Tracked Time Card */}
        <div className="glass-panel-interactive p-6 relative overflow-hidden group">
          <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/20 transition-all"></div>
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400 border border-blue-500/20">
              <Clock className="w-6 h-6" />
            </div>
            <span className="badge-emerald">Tracked</span>
          </div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Tracked Time</h3>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-4xl font-extrabold text-white">
              {Math.floor((dailyStat?.total_tracked_seconds ?? 0) / 60)}
            </span>
            <span className="text-xs text-slate-400 font-medium">minutes</span>
          </div>
          
          <p className="text-xs text-slate-500 mt-4">Calculated across active webcam sessions</p>
        </div>

        {/* Status Card */}
        <div className="glass-panel-interactive p-6 relative overflow-hidden group">
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-xl border ${isGoodPosture ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'}`}>
              {isGoodPosture ? (
                <ShieldCheck className="w-6 h-6" />
              ) : (
                <ShieldAlert className="w-6 h-6" />
              )}
            </div>
            <span className={isGoodPosture ? 'badge-emerald' : 'badge-amber'}>
              {isGoodPosture ? 'Optimal' : 'Attention Required'}
            </span>
          </div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Ergonomic Health Status</h3>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className={`text-2xl font-extrabold ${isGoodPosture ? 'text-emerald-400' : 'text-amber-400'}`}>
              {isGoodPosture ? 'Looking Good' : 'Needs Attention'}
            </span>
          </div>
          
          <p className="text-xs text-slate-500 mt-4">
            {isGoodPosture ? 'Posture baseline within healthy posture range.' : 'Frequent slouching detected. Take a micro-break!'}
          </p>
        </div>
      </div>

      {recentSession && (
        <div className="glass-panel p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-white">Live Session Snapshot</h3>
              <p className="text-xs text-slate-400">Active metrics captured from your live session pipeline</p>
            </div>
            <span className="badge-violet">Live Feed</span>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
             <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
               <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Posture Status</div>
               <div className="text-base font-semibold text-white">{recentSession.current_posture_label}</div>
             </div>
             <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
               <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Neck Flexion Angle</div>
               <div className="text-base font-semibold text-sky-400">{recentSession.neck_angle?.toFixed(1) || '--'}°</div>
             </div>
             <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
               <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Back Slouch Angle</div>
               <div className="text-base font-semibold text-purple-400">{recentSession.back_angle?.toFixed(1) || '--'}°</div>
             </div>
             <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
               <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Total Session Duration</div>
               <div className="text-base font-semibold text-white">{recentSession.total_tracked_seconds}s</div>
             </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
