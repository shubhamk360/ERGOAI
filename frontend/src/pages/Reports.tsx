import React, { useState, useEffect, useRef } from 'react';
import { Download, FileText, CheckCircle, AlertTriangle } from 'lucide-react';
import api from '../services/api';
import type { ReportResponse, DailySummary } from '../types';
import html2pdf from 'html2pdf.js';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const COLORS = ['#10b981', '#f59e0b', '#ef4444'];

const Reports = () => {
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const reportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchReportData = async () => {
      setLoading(true);
      try {
        const [reportRes, historyRes] = await Promise.all([
          api.get<ReportResponse>('/analytics/report', { params: { days: 7 } }),
          api.get<DailySummary[]>('/analytics/daily', { params: { days: 7 } })
        ]);
        setReport(reportRes.data);
        
        // Build chart data from history
        const data = historyRes.data;
        const totalGood = data.reduce((acc, curr) => acc + (curr.good_posture_seconds || 0), 0);
        const totalMild = data.reduce((acc, curr) => acc + (curr.mild_slouch_seconds || 0), 0);
        const totalSevere = data.reduce((acc, curr) => acc + (curr.severe_slouch_seconds || 0), 0);
        
        setChartData([
          { name: 'Good Posture', value: Math.round(totalGood / 60) },
          { name: 'Mild Slouch', value: Math.round(totalMild / 60) },
          { name: 'Severe Slouch', value: Math.round(totalSevere / 60) }
        ]);
      } catch (error) {
        console.error("Failed to load report data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchReportData();
  }, []);

  const handleDownloadPdf = async () => {
    if (!reportRef.current) return;
    
    setGenerating(true);
    
    // We clone the ref, but html2pdf handles it nicely.
    const element = reportRef.current;
    
    const opt = {
      margin:       10,
      filename:     `ERGOAI-Posture-Report-${new Date().toISOString().split('T')[0]}.pdf`,
      image:        { type: 'jpeg' as const, quality: 0.98 },
      html2canvas:  { scale: 2, useCORS: true, logging: false },
      jsPDF:        { unit: 'mm' as const, format: 'a4', orientation: 'portrait' as const }
    };

    try {
      await html2pdf().set(opt).from(element).save();
    } catch (err) {
      console.error("PDF generation failed", err);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center min-h-[400px]">
        <div className="animate-spin h-8 w-8 border-4 border-violet-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Posture Reports</h1>
          <p className="text-slate-400 mt-1">Generate and export your personalized ergonomic report.</p>
        </div>
        <button 
          onClick={handleDownloadPdf} 
          disabled={generating || !report}
          className="btn-primary flex items-center space-x-2"
        >
          <Download className="w-5 h-5" />
          <span>{generating ? 'Generating PDF...' : 'Download PDF Report'}</span>
        </button>
      </div>

      <div className="glass-panel p-8 relative overflow-hidden bg-slate-900/90 shadow-2xl border border-slate-800">
        <h3 className="text-lg font-semibold text-white mb-6">Report Preview (Last 7 Days)</h3>
        
        {/* The Actual Report HTML to be PDF'd - Uses light theme for printable PDF */}
        <div className="bg-slate-50 p-8 rounded-xl shadow-inner text-slate-800 overflow-x-auto">
          <div 
            ref={reportRef} 
            className="bg-white min-w-[700px] w-full p-10 text-slate-900 font-sans leading-relaxed box-border"
          >
            {/* Report Header */}
            <div className="border-b-2 border-slate-200 pb-6 mb-8 flex justify-between items-end">
              <div>
                <h1 className="text-4xl font-extrabold text-indigo-900 tracking-tight flex items-center">
                  <FileText className="w-8 h-8 mr-3 text-indigo-600" />
                  ERGOAI
                </h1>
                <h2 className="text-xl font-medium text-slate-500 mt-2">Personalized Posture Report</h2>
              </div>
              <div className="text-right text-sm text-slate-500">
                <p>Generated: {new Date().toLocaleDateString()}</p>
                <p>Period: Last 7 Days</p>
              </div>
            </div>

            {/* Ergonomic Score & Summary */}
            <div className="grid grid-cols-3 gap-8 mb-10">
              <div className="col-span-1 bg-indigo-50 p-6 rounded-2xl flex flex-col items-center justify-center text-center border border-indigo-100">
                <h3 className="text-sm font-semibold text-indigo-400 uppercase tracking-wider mb-2">Ergonomic Score</h3>
                <div className="text-5xl font-black text-indigo-700">{report?.ergonomic_score}%</div>
                <p className="text-xs text-indigo-500 mt-2">Overall posture health</p>
              </div>
              <div className="col-span-2 flex flex-col justify-center">
                <h3 className="text-xl font-bold text-slate-800 mb-3">Posture Summary</h3>
                <p className="text-slate-600 text-lg leading-relaxed">{report?.posture_summary}</p>
              </div>
            </div>

            {/* Charts Section */}
            <div className="mb-10">
              <h3 className="text-xl font-bold text-slate-800 mb-6 border-b border-slate-200 pb-2">Posture Distribution (Minutes)</h3>
              <div className="h-[300px] w-full flex items-center justify-center bg-slate-50 rounded-2xl border border-slate-200 p-4">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={80}
                      outerRadius={110}
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {chartData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', color: '#0f172a' }}
                      formatter={(value: any) => [`${value} mins`, 'Duration']}
                    />
                    <Legend verticalAlign="bottom" height={36} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Recommendations */}
            <div>
              <h3 className="text-xl font-bold text-slate-800 mb-6 border-b border-slate-200 pb-2">Personalized Recommendations</h3>
              <div className="space-y-4">
                {report?.recommendations.map((rec, i) => {
                  const isPositive = rec.toLowerCase().includes('excellent') || rec.toLowerCase().includes('great');
                  return (
                    <div key={i} className={`flex items-start p-4 rounded-xl border ${isPositive ? 'bg-emerald-50 border-emerald-100' : 'bg-amber-50 border-amber-100'}`}>
                      {isPositive ? (
                        <CheckCircle className="w-6 h-6 text-emerald-500 mr-3 flex-shrink-0 mt-0.5" />
                      ) : (
                        <AlertTriangle className="w-6 h-6 text-amber-500 mr-3 flex-shrink-0 mt-0.5" />
                      )}
                      <p className={`text-base ${isPositive ? 'text-emerald-900' : 'text-amber-900'}`}>{rec}</p>
                    </div>
                  );
                })}
              </div>
            </div>
            
            {/* Footer */}
            <div className="mt-16 text-center text-sm text-slate-400 border-t border-slate-200 pt-6">
              <p>ERGOAI Posture Monitoring System</p>
              <p>Confidential & Personal Report</p>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;
