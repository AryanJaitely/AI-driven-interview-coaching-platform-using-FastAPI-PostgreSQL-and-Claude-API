import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { analyticsAPI } from '../../services/api';
import toast from 'react-hot-toast';

const StatCard = ({ label, value, sub, color = '#6c63ff' }) => (
  <div className="card" style={{ flex: 1, minWidth: '160px' }}>
    <div style={{ fontSize: '28px', fontWeight: 700, color }}>{value}</div>
    <div style={{ fontSize: '13px', fontWeight: 600, marginTop: '4px' }}>{label}</div>
    {sub && <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>{sub}</div>}
  </div>
);

const ReadinessBadge = ({ score }) => {
  const category = score >= 75 ? 'Interview Ready' : score >= 45 ? 'Improving' : 'Not Ready';
  const color = score >= 75 ? '#00d4aa' : score >= 45 ? '#ffb347' : '#ff4d6d';
  const bg = score >= 75 ? 'rgba(0,212,170,0.1)' : score >= 45 ? 'rgba(255,179,71,0.1)' : 'rgba(255,77,109,0.1)';
  return (
    <span style={{ padding: '4px 12px', borderRadius: '999px', background: bg, color, fontSize: '12px', fontWeight: 700 }}>{category}</span>
  );
};

export default function DashboardPage() {
  const { user } = useSelector(s => s.auth);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsAPI.getDashboard()
      .then(r => setData(r.data))
      .catch(() => toast.error('Failed to load dashboard'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div style={{ textAlign: 'center' }}>
        <div className="spinner" style={{ width: 40, height: 40, border: '3px solid var(--border)', borderTopColor: '#6c63ff', borderRadius: '50%', margin: '0 auto 16px' }} />
        <p style={{ color: 'var(--text-secondary)' }}>Loading your dashboard...</p>
      </div>
    </div>
  );

  const readiness = data?.readiness_score ?? user?.readiness_score ?? 0;

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '6px' }}>
            Welcome back, {user?.full_name?.split(' ')[0] || user?.username} 👋
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Target: <strong style={{ color: 'white' }}>{user?.target_role || 'Not set'}</strong></p>
            {data && <ReadinessBadge score={readiness} />}
          </div>
        </div>
        <Link to="/interview">
          <button className="btn-primary" style={{ padding: '12px 24px', fontSize: '14px' }}>▶ Start Interview</button>
        </Link>
      </div>

      {/* Stats Row */}
      {data && (
        <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
          <StatCard label="Total Sessions" value={data.total_sessions} sub="interviews completed" color="#6c63ff" />
          <StatCard label="Readiness Score" value={`${readiness}%`} sub={data.readiness_category} color={readiness >= 75 ? '#00d4aa' : readiness >= 45 ? '#ffb347' : '#ff4d6d'} />
          <StatCard label="Accuracy" value={`${data.overall_accuracy?.toFixed(1)}%`} sub="overall correctness" color="#00d4aa" />
          <StatCard label="Avg Score" value={`${data.avg_session_score?.toFixed(1)}`} sub="per session" color="#a78bfa" />
          <StatCard label="Streak" value={`${data.current_streak}d`} sub="consecutive days" color="#ffb347" />
        </div>
      )}

      {/* Score Over Time */}
      {data?.score_over_time?.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '20px' }}>Score Progress</h2>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '6px', height: '120px' }}>
            {data.score_over_time.slice(-20).map((pt, i) => (
              <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                <div style={{ width: '100%', background: `rgba(108,99,255,${0.3 + (pt.score / 100) * 0.7})`, borderRadius: '4px 4px 0 0', height: `${Math.max(pt.score, 4)}%`, transition: 'height 0.3s', minHeight: '4px' }} title={`${pt.date}: ${pt.score}`} />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
            <span>{data.score_over_time[0]?.date}</span>
            <span>Last {Math.min(data.score_over_time.length, 20)} sessions</span>
            <span>{data.score_over_time[data.score_over_time.length - 1]?.date}</span>
          </div>
        </div>
      )}

      {/* Topic Performance + Behavioral */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {data?.topic_performance?.length > 0 && (
          <div className="card">
            <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Topic Performance</h2>
            {data.topic_performance.slice(0, 6).map((tp, i) => (
              <div key={i} style={{ marginBottom: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '13px' }}>
                  <span style={{ fontWeight: 500 }}>{tp.topic.replace(/_/g, ' ')}</span>
                  <span style={{ color: tp.accuracy >= 70 ? '#00d4aa' : tp.accuracy >= 40 ? '#ffb347' : '#ff4d6d', fontWeight: 600 }}>{tp.accuracy.toFixed(0)}%</span>
                </div>
                <div style={{ height: '6px', background: 'var(--bg-secondary)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${tp.accuracy}%`, background: tp.accuracy >= 70 ? '#00d4aa' : tp.accuracy >= 40 ? '#ffb347' : '#ff4d6d', borderRadius: '3px', transition: 'width 0.5s' }} />
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="card">
          <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Behavioral Insights</h2>
          {data?.behavioral_insights?.map((insight, i) => (
            <div key={i} style={{ display: 'flex', gap: '10px', marginBottom: '12px', padding: '12px', background: 'var(--bg-secondary)', borderRadius: '10px', fontSize: '13px' }}>
              <span>🧠</span><span style={{ color: 'var(--text-secondary)' }}>{insight}</span>
            </div>
          ))}
          <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div style={{ padding: '10px', background: 'var(--bg-secondary)', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '18px', fontWeight: 700, color: '#6c63ff' }}>{((data?.consistency_score || 0) * 100).toFixed(0)}%</div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Consistency</div>
            </div>
            <div style={{ padding: '10px', background: 'var(--bg-secondary)', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '18px', fontWeight: 700, color: '#ffb347' }}>{(data?.avg_response_time || 0).toFixed(0)}s</div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Avg Response</div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      {data?.total_sessions === 0 && (
        <div className="card" style={{ background: 'linear-gradient(135deg, rgba(108,99,255,0.1), rgba(0,212,170,0.05))', border: '1px solid rgba(108,99,255,0.2)', textAlign: 'center', padding: '40px' }}>
          <div style={{ fontSize: '40px', marginBottom: '16px' }}>🚀</div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '8px' }}>Start your first interview!</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>Upload your resume and take your first mock interview to get personalized insights.</p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <Link to="/resume"><button className="btn-secondary">📄 Upload Resume</button></Link>
            <Link to="/interview"><button className="btn-primary">🎯 Start Interview</button></Link>
          </div>
        </div>
      )}
    </div>
  );
}
