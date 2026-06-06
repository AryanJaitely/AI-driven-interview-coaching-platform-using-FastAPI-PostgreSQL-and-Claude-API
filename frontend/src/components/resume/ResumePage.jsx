import React, { useCallback, useEffect, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { resumeAPI } from '../../services/api';
import toast from 'react-hot-toast';

const ScoreRing = ({ score, label, color }) => (
  <div style={{ textAlign: 'center' }}>
    <div style={{ position: 'relative', width: 80, height: 80, margin: '0 auto 8px' }}>
      <svg viewBox="0 0 80 80" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="40" cy="40" r="32" fill="none" stroke="var(--border)" strokeWidth="8" />
        <circle cx="40" cy="40" r="32" fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${2 * Math.PI * 32}`}
          strokeDashoffset={`${2 * Math.PI * 32 * (1 - score / 100)}`}
          strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '15px', fontWeight: 700, color }}>{score.toFixed(0)}</div>
    </div>
    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>{label}</div>
  </div>
);

export default function ResumePage() {
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [polling, setPolling] = useState(false);

  const fetchAnalysis = async (silent = false) => {
    try {
      const r = await resumeAPI.getAnalysis();
      setResume(r.data);
      if (r.data.status === 'processing' || r.data.status === 'pending') setPolling(true);
      else setPolling(false);
    } catch {
      if (!silent) setResume(null);
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => { fetchAnalysis(); }, []);

  useEffect(() => {
    if (!polling) return;
    const id = setInterval(() => fetchAnalysis(true), 3000);
    return () => clearInterval(id);
  }, [polling]);

  const onDrop = useCallback(async (files) => {
    if (!files[0]) return;
    setLoading(true);
    try {
      await resumeAPI.upload(files[0]);
      toast.success('Resume uploaded! Analyzing now...');
      setPolling(true);
      await fetchAnalysis(true);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Upload failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'application/pdf': ['.pdf'] }, maxFiles: 1 });

  const severityColor = { critical: '#ff4d6d', important: '#ffb347', minor: '#6c63ff' };

  return (
    <div className="fade-in">
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '6px' }}>Resume Analyzer</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Upload your PDF resume for AI-powered analysis and ATS scoring</p>
      </div>

      {/* Dropzone */}
      <div {...getRootProps()} style={{ border: `2px dashed ${isDragActive ? '#6c63ff' : 'var(--border)'}`, borderRadius: '16px', padding: '40px', textAlign: 'center', cursor: 'pointer', marginBottom: '32px', background: isDragActive ? 'rgba(108,99,255,0.05)' : 'transparent', transition: 'all 0.2s' }}>
        <input {...getInputProps()} />
        <div style={{ fontSize: '40px', marginBottom: '12px' }}>📄</div>
        <p style={{ fontSize: '16px', fontWeight: 600, marginBottom: '6px' }}>{loading ? 'Uploading...' : isDragActive ? 'Drop it here!' : 'Drop your PDF resume here'}</p>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>or click to browse • PDF only • max 10MB</p>
      </div>

      {/* Loading / Processing */}
      {(fetching || polling) && (
        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
          <div className="spinner" style={{ width: 40, height: 40, border: '3px solid var(--border)', borderTopColor: '#6c63ff', borderRadius: '50%', margin: '0 auto 16px' }} />
          <p style={{ color: 'var(--text-secondary)' }}>{fetching ? 'Loading analysis...' : 'Analyzing your resume with AI...'}</p>
        </div>
      )}

      {/* Analysis Results */}
      {resume && !polling && resume.status === 'analyzed' && (
        <div>
          {/* Scores */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <h2 style={{ fontSize: '18px', fontWeight: 700 }}>{resume.original_filename}</h2>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Detected role: <strong style={{ color: '#6c63ff' }}>{resume.detected_role?.replace(/_/g, ' ')}</strong> • Match: {resume.role_match_score?.toFixed(0)}%</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '48px', fontWeight: 800 }} className="gradient-text">{resume.overall_score?.toFixed(0)}</div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Overall Score</div>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-around', padding: '20px 0', borderTop: '1px solid var(--border)' }}>
              <ScoreRing score={resume.skills_score || 0} label="Skills" color="#6c63ff" />
              <ScoreRing score={resume.experience_score || 0} label="Experience" color="#00d4aa" />
              <ScoreRing score={resume.format_score || 0} label="Format" color="#a78bfa" />
              <ScoreRing score={resume.ats_score || 0} label="ATS" color="#ffb347" />
            </div>
          </div>

          {/* Skills + Missing */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
            <div className="card">
              <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '16px' }}>✅ Detected Skills ({resume.extracted_skills?.length || 0})</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {(resume.extracted_skills || []).map((s, i) => (
                  <span key={i} style={{ padding: '4px 12px', borderRadius: '999px', background: 'rgba(108,99,255,0.15)', color: '#a78bfa', fontSize: '12px', fontWeight: 500 }}>{s}</span>
                ))}
              </div>
            </div>
            <div className="card">
              <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '16px' }}>⚠️ Missing Skills ({resume.missing_skills?.length || 0})</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {(resume.missing_skills || []).map((s, i) => (
                  <span key={i} style={{ padding: '4px 12px', borderRadius: '999px', background: 'rgba(255,77,109,0.1)', color: '#ff4d6d', fontSize: '12px', fontWeight: 500 }}>{s}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Suggestions */}
          {resume.suggestions?.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '16px' }}>💡 Improvement Suggestions</h3>
              {resume.suggestions.map((s, i) => (
                <div key={i} style={{ display: 'flex', gap: '12px', marginBottom: '12px', padding: '14px', borderRadius: '10px', background: 'var(--bg-secondary)', borderLeft: `3px solid ${severityColor[s.severity] || '#6c63ff'}` }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '999px', background: `${severityColor[s.severity]}20`, color: severityColor[s.severity], fontWeight: 700 }}>{s.severity?.toUpperCase()}</span>
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{s.category}</span>
                    </div>
                    <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>{s.message}</p>
                    <p style={{ fontSize: '12px', color: '#00d4aa' }}>→ {s.action}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {!fetching && !polling && !resume && (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
          <p>No resume uploaded yet. Drop your PDF above to get started.</p>
        </div>
      )}
    </div>
  );
}
