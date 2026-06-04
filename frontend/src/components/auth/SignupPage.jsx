import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { signupUser } from '../../store/slices/authSlice';
import toast from 'react-hot-toast';

const ROLES = ['Backend Engineer','Frontend Engineer','Full Stack Engineer','Data Scientist','DevOps Engineer','Software Engineer'];
const LEVELS = ['fresher','junior','mid','senior'];

export default function SignupPage() {
  const [form, setForm] = useState({ email: '', username: '', password: '', full_name: '', target_role: 'Backend Engineer', experience_level: 'fresher' });
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading } = useSelector(s => s.auth);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await dispatch(signupUser(form));
    if (signupUser.fulfilled.match(result)) {
      toast.success('Welcome to InterviewAI!');
      navigate('/dashboard');
    } else {
      toast.error(result.payload || 'Signup failed');
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)', padding: '20px' }}>
      <div style={{ width: '100%', maxWidth: '480px' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ fontSize: '36px', fontWeight: 700, marginBottom: '8px' }} className="gradient-text">InterviewAI</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Create your account and start preparing</p>
        </div>
        <div className="card">
          <form onSubmit={handleSubmit}>
            {[
              { key: 'full_name', label: 'Full Name', type: 'text', placeholder: 'John Doe' },
              { key: 'email', label: 'Email', type: 'email', placeholder: 'you@example.com' },
              { key: 'username', label: 'Username', type: 'text', placeholder: 'john_doe' },
              { key: 'password', label: 'Password', type: 'password', placeholder: 'Min 8 chars' },
            ].map(field => (
              <div key={field.key} style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>{field.label}</label>
                <input className="input-field" type={field.type} placeholder={field.placeholder}
                  value={form[field.key]} onChange={e => setForm({ ...form, [field.key]: e.target.value })} required />
              </div>
            ))}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>Target Role</label>
                <select className="input-field" value={form.target_role} onChange={e => setForm({ ...form, target_role: e.target.value })}>
                  {ROLES.map(r => <option key={r}>{r}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>Experience</label>
                <select className="input-field" value={form.experience_level} onChange={e => setForm({ ...form, experience_level: e.target.value })}>
                  {LEVELS.map(l => <option key={l} value={l}>{l.charAt(0).toUpperCase()+l.slice(1)}</option>)}
                </select>
              </div>
            </div>
            <button className="btn-primary" type="submit" disabled={loading} style={{ width: '100%', padding: '14px' }}>
              {loading ? 'Creating...' : 'Create Account'}
            </button>
          </form>
          <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            Already have an account? <Link to="/login" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
