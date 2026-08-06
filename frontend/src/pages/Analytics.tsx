import React, { useEffect, useState, useMemo } from 'react';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, AreaChart, Area 
} from 'recharts';
import { TrendingUp, TrendingDown, Award, Clock, Activity, AlertCircle, Sparkles } from 'lucide-react';
import api from '../services/api';
import type { DailySummary } from '../types';

const COLORS = ['#10b981', '#f59e0b', '#f43f5e'];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-950/90 backdrop-blur-md border border-slate-800 p-3 rounded-xl shadow-2xl text-xs">
        <p className="font-semibold text-slate-300 mb-1">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={`item-${index}`} className="flex items-center space-x-2 my-0.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }}></span>
            <span className="text-slate-400">{entry.name}:</span>
            <span className="font-bold text-white">{entry.value}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

const Analytics: React.FC = () => {
  const [data, setData] = useState<DailySummary[]>([]);
  const [days, setDays] = useState<number>(14);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      try {
        const res = await api.get<DailySummary[]>('/analytics/daily', { params: { days } });
        // Chronological order (oldest to newest)
        setData(res.data.reverse());
      } catch (error) {
        console.error("Error fetching analytics", error);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [days]);

  // Derived metrics
  const stats = useMemo(() => {
    if (data.length === 0) {
      return {
        avgErgonomicScore: 0,
        scoreTrendDelta: 0,
        totalTrackedHours: 0,
        timeTrendDelta: 0,
        avgNeckAngle: 0,
        totalSlouchEvents: 0,
        distribution: [
          { name: 'Good Posture', value: 0 },
          { name: 'Mild Slouch', value: 0 },
          { name: 'Severe Slouch', value: 0 },
        ],
      };
    }

    const half = Math.floor(data.length / 2);
    const recentData = data.slice(half);
    const priorData = data.slice(0, half);

    // Ergonomic score calculation
    const calcAvgScore = (items: DailySummary[]) => {
      if (items.length === 0) return 0;
      const sum = items.reduce((acc, curr) => acc + (curr.good_posture_percent || 0), 0);
      return sum / items.length;
    };

    const recentScore = calcAvgScore(recentData);
    const priorScore = calcAvgScore(priorData);
    const scoreTrendDelta = priorScore > 0 ? ((recentScore - priorScore) / priorScore) * 100 : 0;

    // Tracked time calculation
    const calcTotalSeconds = (items: DailySummary[]) => items.reduce((acc, curr) => acc + (curr.total_tracked_seconds || 0), 0);
    const recentTime = calcTotalSeconds(recentData);
    const priorTime = calcTotalSeconds(priorData);
    const timeTrendDelta = priorTime > 0 ? ((recentTime - priorTime) / priorTime) * 100 : 0;

    const totalTrackedSeconds = calcTotalSeconds(data);
    const totalGood = data.reduce((acc, curr) => acc + (curr.good_posture_seconds || 0), 0);
    const totalMild = data.reduce((acc, curr) => acc + (curr.mild_slouch_seconds || 0), 0);
    const totalSevere = data.reduce((acc, curr) => acc + (curr.severe_slouch_seconds || 0), 0);

    // Neck angle average
    const itemsWithNeck = data.filter(d => d.avg_neck_angle != null);
    const avgNeckAngle = itemsWithNeck.length > 0 
      ? itemsWithNeck.reduce((acc, curr) => acc + (curr.avg_neck_angle || 0), 0) / itemsWithNeck.length 
      : 0;

    const totalSlouchEvents = data.reduce((acc, curr) => acc + (curr.mild_slouch_count + curr.severe_slouch_count), 0);

    return {
      avgErgonomicScore: Math.round(recentScore),
      scoreTrendDelta: Math.round(scoreTrendDelta),
      totalTrackedHours: (totalTrackedSeconds / 3600).toFixed(1),
      timeTrendDelta: Math.round(timeTrendDelta),
      avgNeckAngle: avgNeckAngle.toFixed(1),
      totalSlouchEvents,
      distribution: [
        { name: 'Good Posture', value: Math.round(totalGood / 60) },
        { name: 'Mild Slouch', value: Math.round(totalMild / 60) },
        { name: 'Severe Slouch', value: Math.round(totalSevere / 60) },
      ],
    };
  }, [data]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center min-h-[400px]">
        <div className="animate-spin h-9 w-9 border-4 border-violet-500 border-t-transparent rounded-full shadow-lg shadow-violet-500/20"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Header with Timeframe Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-violet-400 font-semibold text-xs tracking-wider uppercase mb-1">
            <Sparkles className="w-4 h-4" />
            <span>Ergonomic Analytics</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Posture Analytics</h1>
          <p className="text-slate-400 text-sm mt-1">Comprehensive breakdown of your posture performance & ergonomic metrics.</p>
        </div>

        <div className="flex items-center space-x-1.5 bg-slate-950/80 p-1.5 rounded-2xl border border-slate-800/80 self-start sm:self-auto shadow-inner">
          {[7, 14, 30].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-4 py-1.5 text-xs font-semibold rounded-xl transition-all duration-200 ${
                days === d 
                  ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-md shadow-violet-600/30' 
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              {d} Days
            </button>
          ))}
        </div>
      </div>

      {/* Weekly Progress & KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Ergonomic Score */}
        <div className="glass-panel-interactive p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Ergonomic Score</span>
            <div className="p-2.5 bg-violet-500/10 rounded-xl text-violet-400 border border-violet-500/20">
              <Award className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">{stats.avgErgonomicScore}%</span>
            <span className={`text-xs font-semibold flex items-center ${stats.scoreTrendDelta >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {stats.scoreTrendDelta >= 0 ? <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> : <TrendingDown className="w-3.5 h-3.5 mr-0.5" />}
              {Math.abs(stats.scoreTrendDelta)}%
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">vs previous period</p>
        </div>

        {/* Total Tracked Time */}
        <div className="glass-panel-interactive p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Tracked</span>
            <div className="p-2.5 bg-blue-500/10 rounded-xl text-blue-400 border border-blue-500/20">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">{stats.totalTrackedHours}h</span>
            <span className={`text-xs font-semibold flex items-center ${stats.timeTrendDelta >= 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
              {stats.timeTrendDelta >= 0 ? <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> : <TrendingDown className="w-3.5 h-3.5 mr-0.5" />}
              {Math.abs(stats.timeTrendDelta)}%
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">in last {days} days</p>
        </div>

        {/* Avg Neck Angle */}
        <div className="glass-panel-interactive p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Neck Angle</span>
            <div className="p-2.5 bg-emerald-500/10 rounded-xl text-emerald-400 border border-emerald-500/20">
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">
              {Number(stats.avgNeckAngle) > 0 ? `${stats.avgNeckAngle}°` : 'N/A'}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">Optimal posture is ≤ 15°</p>
        </div>

        {/* Total Slouch Events */}
        <div className="glass-panel-interactive p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Slouch Alerts</span>
            <div className="p-2.5 bg-amber-500/10 rounded-xl text-amber-400 border border-amber-500/20">
              <AlertCircle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">{stats.totalSlouchEvents}</span>
          </div>
          <p className="text-xs text-slate-500 mt-2">Mild & severe posture triggers</p>
        </div>
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Ergonomic Score Trend */}
        <div className="glass-panel p-6 lg:col-span-2 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-semibold text-white">Ergonomic Score Trend</h3>
              <p className="text-xs text-slate-400">Daily percentage of good posture duration</p>
            </div>
          </div>
          {data.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-slate-500 text-sm">No data available</div>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.45}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} unit="%" />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="good_posture_percent" name="Ergonomic Score (%)" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#scoreGradient)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Posture Distribution Donut Chart */}
        <div className="glass-panel p-6 flex flex-col justify-between">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-white">Posture Distribution</h3>
            <p className="text-xs text-slate-400">Total time spent across posture states (Minutes)</p>
          </div>
          {data.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-slate-500 text-sm">No data available</div>
          ) : (
            <div className="h-64 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={88}
                    paddingAngle={6}
                    dataKey="value"
                  >
                    {stats.distribution.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="transparent" />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Neck Angle Trend */}
        <div className="glass-panel p-6 lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-semibold text-white">Neck & Back Flexion Angles</h3>
              <p className="text-xs text-slate-400">Average postural flexion angles in degrees (°)</p>
            </div>
          </div>
          {data.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-slate-500 text-sm">No data available</div>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} unit="°" />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Line type="monotone" dataKey="avg_neck_angle" name="Avg Neck Angle (°)" stroke="#38bdf8" strokeWidth={2.5} dot={{ r: 4, fill: '#38bdf8' }} />
                  <Line type="monotone" dataKey="avg_back_angle" name="Avg Back Angle (°)" stroke="#a78bfa" strokeWidth={2.5} dot={{ r: 4, fill: '#a78bfa' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Daily Sessions Breakdown */}
        <div className="glass-panel p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-semibold text-white">Daily Sessions</h3>
              <p className="text-xs text-slate-400">Tracked duration per day (Minutes)</p>
            </div>
          </div>
          {data.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-slate-500 text-sm">No data available</div>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart 
                  data={data.map(d => ({
                    ...d,
                    good_mins: Math.round(d.good_posture_seconds / 60),
                    mild_mins: Math.round(d.mild_slouch_seconds / 60),
                    severe_mins: Math.round(d.severe_slouch_seconds / 60),
                  }))} 
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} unit="m" />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="good_mins" name="Good" stackId="a" fill="#10b981" />
                  <Bar dataKey="mild_mins" name="Mild" stackId="a" fill="#f59e0b" />
                  <Bar dataKey="severe_mins" name="Severe" stackId="a" fill="#f43f5e" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default Analytics;
