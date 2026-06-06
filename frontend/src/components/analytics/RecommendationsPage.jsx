import React, { useEffect, useState } from 'react';
import { analyticsAPI } from '../../services/api';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';

const priorityLabel = { 1: 'CRITICAL', 2: 'HIGH', 3: 'HIGH', 4: 'MEDIUM', 5: 'MEDIUM' };
const priorityColor = { 1: '#ff4d6d', 2: '#ff4d6d', 3: '#ffb347', 4: '#ffb347', 5: '#6c63ff' };
const typeIcon = { topic: '📚', resume: '📄', behavioral: '🧠', question: '❓' };

function RecCard({ rec }) {
  const color = priorityColor[rec.priority] || '#6c63ff';
  const label = priorityLabel[rec.priority] || 'NORMAL';
  return (
    <div className="card" style={{ marginBottom: '12px', borderLeft: `3px solid ${color}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span>{typeIcon[rec.type] || '💡'}</span>
            <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '999px', background: `${color}20`, color, fontWeight: 700 }}>{label}</span>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{rec.type}</span>
          </div>
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '4px' }}>{rec.title}</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>{rec.description}</p>
        </div>
        {rec.action_url && (
          <Link to={rec.action_url}>
            <button className="btn-primary" style={{ padding: '8px 16px', fontSize: '12px', whiteSpace: 'nowrap' }}>Take Action →</button>
          </Link>
        )}
      </div>
    </div>
  );
}

export default function RecommendationsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsAPI.getRecommendations()
      .then(r => setData(r.data))
      .catch(() => toast.error('Failed to load recommendations'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div className="spinner" style={{ width: 40, height: 40, border: '3px solid var(--border)', borderTopColor: '#6c63ff', borderRadius: '50%' }} />
    </div>
  );

  return (
    <div className="fade-in">
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '6px' }}>💡 Smart Recommendations</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Personalized action items based on your performance data</p>
      </div>

      {data?.urgent?.length > 0 && (
        <div style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#ff4d6d', marginBottom: '12px' }}>🔴 Urgent — Address These First</h2>
          {data.urgent.map(rec => <RecCard key={rec.id} rec={rec} />)}
        </div>
      )}

      {data?.suggested?.length > 0 && (
        <div style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#ffb347', marginBottom: '12px' }}>🟡 Suggested Improvements</h2>
          {data.suggested.map(rec => <RecCard key={rec.id} rec={rec} />)}
        </div>
      )}

      {data?.optional?.length > 0 && (
        <div style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#6c63ff', marginBottom: '12px' }}>🔵 Optional Enhancements</h2>
          {data.optional.map(rec => <RecCard key={rec.id} rec={rec} />)}
        </div>
      )}

      {data?.total === 0 && (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-secondary)' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎉</div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>You're on track!</h2>
          <p>Complete more interviews to get personalized recommendations.</p>
          <Link to="/interview" style={{ display: 'inline-block', marginTop: '20px' }}>
            <button className="btn-primary">Start an Interview</button>
          </Link>
        </div>
      )}
    </div>
  );
}
