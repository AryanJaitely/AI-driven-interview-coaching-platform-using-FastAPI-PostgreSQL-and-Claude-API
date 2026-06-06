import React, { useState } from 'react';
import { interviewAPI } from '../../services/api';
import toast from 'react-hot-toast';
import InterviewSession from './InterviewSession';
import SessionSummary from './SessionSummary';

const ROLES = ['Backend Engineer','Frontend Engineer','Full Stack Engineer','Data Scientist','DevOps Engineer','Software Engineer'];
const DIFFICULTIES = ['easy','medium','hard'];

export default function InterviewPage() {
  const [phase, setPhase] = useState('setup'); // setup | active | summary
  const [session, setSession] = useState(null);
  const [summary, setSummary] = useState(null);
  const [config, setConfig] = useState({ target_role: 'Backend Engineer', total_questions: 10, starting_difficulty: 'easy' });
  const [loading, setLoading] = useState(false);

  const startInterview = async () => {
    setLoading(true);
    try {
      const r = await interviewAPI.start(config);
      setSession(r.data);
      setPhase('active');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to start interview');
    } finally {
      setLoading(false);
    }
  };

  const handleSessionComplete = async (sessionId) => {
    try {
      const r = await interviewAPI.getSummary(sessionId);
      setSummary(r.data);
      setPhase('summary');
    } catch {
      toast.error('Failed to load summary');
      setPhase('setup');
    }
  };

  if (phase === 'active' && session) {
    return <InterviewSession sessionData={session} onComplete={handleSessionComplete} />;
  }

  if (phase === 'summary' && summary) {
    return <SessionSummary summary={summary} onRetry={() => { setSummary(null); setPhase('setup'); }} />;
  }

  return (
    <div className="fade-in" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '12px' }}>🎯</div>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '6px' }}>Start a Mock Interview</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>AI-powered adaptive questions tailored to your target role</p>
      </div>

      <div className="card">
        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>Target Role</label>
          <select className="input-field" value={config.target_role} onChange={e => setConfig({ ...config, target_role: e.target.value })}>
            {ROLES.map(r => <option key={r}>{r}</option>)}
          </select>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>Questions</label>
            <select className="input-field" value={config.total_questions} onChange={e => setConfig({ ...config, total_questions: parseInt(e.target.value) })}>
              {[5,10,15,20].map(n => <option key={n} value={n}>{n} Questions</option>)}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>Starting Difficulty</label>
            <select className="input-field" value={config.starting_difficulty} onChange={e => setConfig({ ...config, starting_difficulty: e.target.value })}>
              {DIFFICULTIES.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase()+d.slice(1)}</option>)}
            </select>
          </div>
        </div>

        {/* Info cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '28px' }}>
          {[
            { icon: '🧠', title: 'Adaptive AI', desc: 'Difficulty adjusts based on your answers' },
            { icon: '⚡', title: 'Real Feedback', desc: 'GPT-4 evaluates every answer instantly' },
            { icon: '📊', title: 'Full Analytics', desc: 'Detailed breakdown after each session' },
          ].map((item, i) => (
            <div key={i} style={{ padding: '14px', background: 'var(--bg-secondary)', borderRadius: '10px', textAlign: 'center' }}>
              <div style={{ fontSize: '24px', marginBottom: '6px' }}>{item.icon}</div>
              <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>{item.title}</div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{item.desc}</div>
            </div>
          ))}
        </div>

        <button className="btn-primary" onClick={startInterview} disabled={loading} style={{ width: '100%', padding: '14px', fontSize: '15px' }}>
          {loading ? 'Starting...' : '▶ Begin Interview'}
        </button>
      </div>
    </div>
  );
}
