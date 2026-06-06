import React, { useState, useEffect, useRef, useCallback } from 'react';
import { interviewAPI } from '../../services/api';
import toast from 'react-hot-toast';

const diffColor = { easy: '#00d4aa', medium: '#ffb347', hard: '#ff4d6d' };

export default function InterviewSession({ sessionData, onComplete }) {
  const [currentQuestion, setCurrentQuestion] = useState(sessionData.first_question);
  const [sessionId] = useState(sessionData.session_id);
  const [answer, setAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [timer, setTimer] = useState(0);
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [diffChange, setDiffChange] = useState(null);
  const intervalRef = useRef();

  useEffect(() => {
    intervalRef.current = setInterval(() => setTimer(t => t + 1), 1000);
    return () => clearInterval(intervalRef.current);
  }, [currentQuestion]);

  const formatTime = (s) => `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`;

  const handleSubmit = async () => {
    if (!answer.trim()) { toast.error('Please write an answer'); return; }
    setSubmitting(true);
    clearInterval(intervalRef.current);
    const timeTaken = (Date.now() - questionStartTime) / 1000;

    try {
      const r = await interviewAPI.submitAnswer({ session_id: sessionId, question_id: currentQuestion.id, answer, time_taken: timeTaken });
      const data = r.data;
      setFeedback(data.feedback);
      setDiffChange(data.difficulty_changed);

      if (data.session_complete) {
        setTimeout(() => onComplete(sessionId), 3000);
      } else {
        setTimeout(() => {
          setCurrentQuestion(data.next_question);
          setAnswer('');
          setFeedback(null);
          setDiffChange(null);
          setTimer(0);
          setQuestionStartTime(Date.now());
        }, 3500);
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  const progress = ((currentQuestion.question_number - 1) / currentQuestion.total_questions) * 100;

  return (
    <div className="fade-in" style={{ maxWidth: '760px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Question </span>
          <strong>{currentQuestion.question_number}</strong>
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}> of {currentQuestion.total_questions}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {diffChange && (
            <span style={{ fontSize: '12px', padding: '4px 10px', borderRadius: '999px', background: diffChange === 'increased' ? 'rgba(255,77,109,0.1)' : 'rgba(0,212,170,0.1)', color: diffChange === 'increased' ? '#ff4d6d' : '#00d4aa', fontWeight: 600 }}>
              {diffChange === 'increased' ? '⬆ Harder' : '⬇ Easier'}
            </span>
          )}
          <span style={{ padding: '4px 12px', borderRadius: '999px', background: `${diffColor[currentQuestion.difficulty]}20`, color: diffColor[currentQuestion.difficulty], fontSize: '12px', fontWeight: 700 }}>
            {currentQuestion.difficulty?.toUpperCase()}
          </span>
          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '16px', fontWeight: 600, color: timer > 120 ? '#ff4d6d' : 'var(--text-primary)' }}>{formatTime(timer)}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ height: '4px', background: 'var(--border)', borderRadius: '2px', marginBottom: '28px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${progress}%`, background: 'linear-gradient(90deg, #6c63ff, #00d4aa)', transition: 'width 0.5s' }} />
      </div>

      {/* Question */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <span style={{ fontSize: '11px', padding: '3px 10px', borderRadius: '999px', background: 'rgba(108,99,255,0.15)', color: '#a78bfa', fontWeight: 600 }}>
            {currentQuestion.category?.replace(/_/g,' ').toUpperCase()}
          </span>
          <span style={{ fontSize: '11px', padding: '3px 10px', borderRadius: '999px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)', fontWeight: 500 }}>
            {currentQuestion.question_type}
          </span>
        </div>
        <p style={{ fontSize: '17px', fontWeight: 600, lineHeight: '1.6' }}>{currentQuestion.text}</p>
        {currentQuestion.avg_response_time && (
          <p style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>Expected time: ~{currentQuestion.avg_response_time}s</p>
        )}
      </div>

      {/* Answer area */}
      {!feedback && (
        <div>
          <textarea
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            placeholder="Type your answer here... Be as detailed as you can. Mention key concepts, examples, and tradeoffs."
            style={{ width: '100%', minHeight: '180px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px', color: 'var(--text-primary)', fontFamily: 'Space Grotesk, sans-serif', fontSize: '14px', outline: 'none', resize: 'vertical', lineHeight: '1.6' }}
            onFocus={e => e.target.style.borderColor = '#6c63ff'}
            onBlur={e => e.target.style.borderColor = 'var(--border)'}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{answer.split(/\s+/).filter(Boolean).length} words</span>
            <button className="btn-primary" onClick={handleSubmit} disabled={submitting || !answer.trim()} style={{ padding: '12px 32px' }}>
              {submitting ? 'Evaluating...' : 'Submit Answer →'}
            </button>
          </div>
        </div>
      )}

      {/* Feedback */}
      {feedback && (
        <div className="card fade-in" style={{ borderColor: feedback.result === 'correct' ? '#00d4aa' : feedback.result === 'partial' ? '#ffb347' : '#ff4d6d' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '24px' }}>{feedback.result === 'correct' ? '✅' : feedback.result === 'partial' ? '🟡' : '❌'}</span>
              <span style={{ fontSize: '16px', fontWeight: 700, color: feedback.result === 'correct' ? '#00d4aa' : feedback.result === 'partial' ? '#ffb347' : '#ff4d6d' }}>
                {feedback.result === 'correct' ? 'Correct!' : feedback.result === 'partial' ? 'Partially Correct' : 'Incorrect'}
              </span>
            </div>
            <span style={{ fontSize: '28px', fontWeight: 800, color: '#6c63ff' }}>{feedback.score.toFixed(0)}<span style={{ fontSize: '14px' }}>/100</span></span>
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '16px' }}>{feedback.ai_feedback}</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
            {feedback.strengths?.length > 0 && (
              <div style={{ padding: '12px', background: 'rgba(0,212,170,0.05)', borderRadius: '8px', border: '1px solid rgba(0,212,170,0.1)' }}>
                <div style={{ fontSize: '12px', color: '#00d4aa', fontWeight: 600, marginBottom: '6px' }}>✓ Strengths</div>
                {feedback.strengths.map((s,i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '2px' }}>• {s}</div>)}
              </div>
            )}
            {feedback.weaknesses?.length > 0 && (
              <div style={{ padding: '12px', background: 'rgba(255,77,109,0.05)', borderRadius: '8px', border: '1px solid rgba(255,77,109,0.1)' }}>
                <div style={{ fontSize: '12px', color: '#ff4d6d', fontWeight: 600, marginBottom: '6px' }}>✗ Gaps</div>
                {feedback.weaknesses.map((s,i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '2px' }}>• {s}</div>)}
              </div>
            )}
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', textAlign: 'center' }}>Next question loading...</p>
        </div>
      )}
    </div>
  );
}
