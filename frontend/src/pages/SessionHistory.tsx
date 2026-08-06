import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { DailySummary } from '../types';
import { ShieldCheck, ShieldAlert, Sparkles } from 'lucide-react';

const SessionHistory: React.FC = () => {
  const [data, setData] = useState<DailySummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await api.get<DailySummary[]>('/analytics/daily', { params: { days: 30 } });
        setData(res.data);
      } catch (error) {
        console.error("Error fetching history", error);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center min-h-[400px]">
        <div className="animate-spin h-9 w-9 border-4 border-violet-500 border-t-transparent rounded-full shadow-lg shadow-violet-500/20"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      <div className="flex justify-between items-end">
        <div>
          <div className="flex items-center space-x-2 text-violet-400 font-semibold text-xs tracking-wider uppercase mb-1">
            <Sparkles className="w-4 h-4" />
            <span>Historical Logs</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Session History</h1>
          <p className="text-slate-400 text-sm mt-1">Detailed historical log of your daily posture performance.</p>
        </div>
      </div>

      <div className="glass-panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-950/60 border-b border-slate-800 text-xs uppercase font-bold tracking-wider text-slate-400">
                <th className="p-4">Date</th>
                <th className="p-4">Tracked Duration</th>
                <th className="p-4">Good Posture %</th>
                <th className="p-4">Slouch %</th>
                <th className="p-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm">
              {data.map((row) => (
                <tr key={row.date} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-4 font-semibold text-slate-200">{row.date}</td>
                  <td className="p-4 text-slate-300 font-medium">{Math.floor(row.total_tracked_seconds / 60)} mins</td>
                  <td className="p-4 font-bold text-emerald-400">{row.good_posture_percent.toFixed(1)}%</td>
                  <td className="p-4 font-bold text-amber-400">{row.bad_posture_percent.toFixed(1)}%</td>
                  <td className="p-4 text-right">
                    {row.good_posture_percent >= 70 ? (
                      <span className="badge-emerald">
                        <ShieldCheck className="w-3.5 h-3.5 mr-1" />
                        <span>Good</span>
                      </span>
                    ) : (
                      <span className="badge-amber">
                        <ShieldAlert className="w-3.5 h-3.5 mr-1" />
                        <span>Attention</span>
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-12 text-center text-slate-500 font-medium">
                    No session history recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SessionHistory;
