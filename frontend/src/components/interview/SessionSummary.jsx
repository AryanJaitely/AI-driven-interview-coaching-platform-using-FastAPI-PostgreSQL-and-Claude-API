import React from 'react';
import { Link } from 'react-router-dom';

export default function SessionSummary({ summary, onRetry }) {
  const { total_score = 0, accuracy_percentage = 0, correct_count = 0, incorrect_count = 0,
    partial_count = 0, total_questions = 0, duration_minutes = 0,
    panic_score = 0, consistency_score = 0, topic_breakdown = {},
    strongest_topic, weakest_topic, behavioral_insights = [], target_role } = summary;

  const readinessColor = total_score >= 75 ? '#00d4aa' : total_score >= 50 ? '#ffb347' : '#ff4d6d';

  return (
    <div className="fade-in" style={{ maxWidth: '720px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <div style={{ fontSize: '56px', marginBottom: '12px' }}>
          {total_score >= 75 ? '🏆' : total_score >= 50 ? '👍' : '💪'}
        </div>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '6px' }}>Session Complete!</h1>
        <p style={{ color: 'var(--text-secondary)' }}>{target_role} • {total_questions} questions • {duration_minutes.toFixed(0)} min</p>
      </div>

      {/* Score Hero */}
      <div className="card" style={{ textAlign: 'center', marginBottom: '24px', background: 'linear-gradient(135deg, rgba(108,99,255,0.1), rgba(0,212,170,0.05))', borderColor: 'rgba(108,99,255,0.2)' }}>
        <div style={{ fontSize: '72px', fontWeight: 800, color: readinessColor }}>{total_score.toFixed(0)}</div>
        <div style={{ fontSize: '16px', color: 'var(--text-secondary)', marginBottom: '20px' }}>Overall Score</div>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '40px' }}>
          <div><div style={{ fontSize: '28px', fontWeight: 700, color: '#00d4aa' }}>{correct_count}</div><div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Correct</div></div>
          <div><div style={{ fontSize: '28px', fontWeight: 700, color: '#ffb347' }}>{partial_count}</div><div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Partial</div></div>
          <div><div style={{ fontSize: '28px', fontWeight: 700, color: '#ff4d6d' }}>{incorrect_count}</div><div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Incorrect</div></div>
          <div><div style={{ fontSize: '28px', fontWeight: 700, color: '#a78bfa' }}>{accuracy_percentage.toFixed(0)}%</div><div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Accuracy</div></div>
        </div>
      </div>

      {/* Topic Breakdown + Behavioral */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '16px' }}>📊 Topic Breakdown</h3>
          {Object.entries(topic_breakdown).map(([topic, data]) => (
            <div key={topic} style={{ marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
                <span style={{ fontWeight: 500 }}>{topic.replace(/_/g,' ')}</span>
                <span style={{ color: data.accuracy >= 70 ? '#00d4aa' : data.accuracy >= 40 ? '#ffb347' : '#ff4d6d', fontWeight: 600 }}>{data.accuracy?.toFixed(0)}%</span>
              </div>
              <div style={{ height: '6px', background: 'var(--bg-secondary)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${data.accuracy}%`, background: data.accuracy >= 70 ? '#00d4aa' : data.accuracy >= 40 ? '#ffb347' : '#ff4d6d', borderRadius: '3px' }} />
              </div>
            </div>
          ))}
          {strongest_topic && <p style={{ fontSize: '12px', color: '#00d4aa', marginTop: '8px' }}>💪 Strongest: {strongest_topic.replace(/_/g,' ')}</p>}
          {weakest_topic && <p style={{ fontSize: '12px', color: '#ff4d6d', marginTop: '4px' }}>⚠️ Needs work: {weakest_topic.replace(/_/g,' ')}</p>}
        </div>

        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '16px' }}>🧠 Behavioral Analysis</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
            <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '22px', fontWeight: 700, color: consistency_score >= 0.7 ? '#00d4aa' : '#ffb347' }}>{(consistency_score * 100).toFixed(0)}%</div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Consistency</div>
            </div>
            <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '22px', fontWeight: 700, color: panic_score < 0.3 ? '#00d4aa' : '#ff4d6d' }}>{(panic_score * 100).toFixed(0)}%</div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Panic Index</div>
            </div>
          </div>
          {behavioral_insights.map((insight, i) => (
            <div key={i} style={{ padding: '10px 12px', background: 'var(--bg-secondary)', borderRadius: '8px', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              🧠 {insight}
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
        <button className="btn-secondary" onClick={onRetry}>🔄 New Interview</button>
        <Link to="/analytics"><button className="btn-secondary">📊 View Analytics</button></Link>
        <Link to="/recommendations"><button className="btn-primary">💡 Get Recommendations</button></Link>
      </div>
    </div>
  );
}
