import React, { useEffect, useState } from 'react';
import { analyticsAPI } from '../../services/api';
import toast from 'react-hot-toast';

export default function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([analyticsAPI.getDashboard(), analyticsAPI.getReadiness()])
      .then(([d, r]) => { setData(d.data); setReadiness(r.data); })
      .catch(() => toast.error('Failed to load analytics'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div className="spinner" style={{ width: 40, height: 40, border: '3px solid var(--border)', borderTopColor: '#6c63ff', borderRadius: '50%' }} />
    </div>
  );

  const readinessColor = readiness?.overall_score >= 75 ? '#00d4aa' : readiness?.overall_score >= 45 ? '#ffb347' : '#ff4d6d';

  return (
    <div className="fade-in">
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '6px' }}>Analytics & Insights</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Your full performance intelligence dashboard</p>
      </div>

      {/* Readiness Card */}
      {readiness && (
        <div className="card" style={{ marginBottom: '24px', background: 'linear-gradient(135deg, rgba(108,99,255,0.1), rgba(0,212,170,0.05))', borderColor: 'rgba(108,99,255,0.2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '4px' }}>Readiness Score</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{readiness.next_milestone}</p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '64px', fontWeight: 800, color: readinessColor }}>{readiness.overall_score?.toFixed(0)}</div>
              <div style={{ padding: '4px 16px', borderRadius: '999px', background: `${readinessColor}20`, color: readinessColor, fontSize: '13px', fontWeight: 700 }}>{readiness.category}</div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {[
                { label: 'Resume', value: readiness.resume_score?.toFixed(0) + '%' },
                { label: 'Performance', value: readiness.performance_score?.toFixed(0) + '%' },
                { label: 'Consistency', value: (readiness.consistency_score * 100)?.toFixed(0) + '%' },
                { label: 'Improvement', value: '+' + (readiness.improvement_rate * 10)?.toFixed(1) + '%' },
              ].map((item, i) => (
                <div key={i} style={{ padding: '10px 14px', background: 'var(--bg-card)', borderRadius: '8px', textAlign: 'center' }}>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#6c63ff' }}>{item.value}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Weekly Trends Table */}
      {data?.weekly_trends?.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '20px' }}>📅 Weekly Trends</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['Week', 'Sessions', 'Avg Score', 'Accuracy', 'Questions'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--text-secondary)', fontWeight: 600 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.weekly_trends.map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '10px 12px' }}>{row.week_start}</td>
                    <td style={{ padding: '10px 12px', color: '#6c63ff', fontWeight: 600 }}>{row.sessions}</td>
                    <td style={{ padding: '10px 12px', color: row.avg_score >= 70 ? '#00d4aa' : '#ffb347', fontWeight: 600 }}>{row.avg_score?.toFixed(1)}</td>
                    <td style={{ padding: '10px 12px' }}>{row.accuracy?.toFixed(1)}%</td>
                    <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>{row.questions_attempted}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Topic Performance Bars */}
      {data?.topic_performance?.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '20px' }}>🏷️ Topic Performance Breakdown</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {data.topic_performance.map((tp, i) => (
              <div key={i}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 500 }}>{tp.topic.replace(/_/g,' ')}</span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{tp.total_attempts} attempts</span>
                    <span style={{ color: tp.accuracy >= 70 ? '#00d4aa' : tp.accuracy >= 40 ? '#ffb347' : '#ff4d6d', fontWeight: 700 }}>{tp.accuracy.toFixed(0)}%</span>
                  </div>
                </div>
                <div style={{ height: '8px', background: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${tp.accuracy}%`, background: tp.accuracy >= 70 ? '#00d4aa' : tp.accuracy >= 40 ? '#ffb347' : '#ff4d6d', borderRadius: '4px', transition: 'width 0.6s' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Behavioral Insights */}
      {data?.behavioral_insights?.length > 0 && (
        <div className="card">
          <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>🧠 Behavioral Intelligence</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '20px' }}>
            {[
              { label: 'Panic Frequency', value: ((data.panic_frequency || 0) * 100).toFixed(0) + '%', color: (data.panic_frequency || 0) < 0.3 ? '#00d4aa' : '#ff4d6d' },
              { label: 'Consistency', value: ((data.consistency_score || 0) * 100).toFixed(0) + '%', color: '#6c63ff' },
              { label: 'Avg Response', value: (data.avg_response_time || 0).toFixed(0) + 's', color: '#ffb347' },
            ].map((item, i) => (
              <div key={i} style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: '10px', textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 700, color: item.color }}>{item.value}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>{item.label}</div>
              </div>
            ))}
          </div>
          {data.behavioral_insights.map((insight, i) => (
            <div key={i} style={{ padding: '12px 16px', background: 'var(--bg-secondary)', borderRadius: '10px', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              🧠 {insight}
            </div>
          ))}
        </div>
      )}

      {!data?.total_sessions && (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-secondary)' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
          <p>No data yet. Complete some interviews to see your analytics!</p>
        </div>
      )}
    </div>
  );
}
