import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '../../store/slices/authSlice';

const NAV = [
  { path: '/dashboard', icon: '⊞', label: 'Dashboard' },
  { path: '/resume', icon: '📄', label: 'Resume' },
  { path: '/interview', icon: '🎯', label: 'Interview' },
  { path: '/analytics', icon: '📊', label: 'Analytics' },
  { path: '/recommendations', icon: '💡', label: 'Recommendations' },
];

export default function Sidebar() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user } = useSelector(s => s.auth);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  const initials = (user?.full_name || user?.username || 'U').slice(0, 2).toUpperCase();
  const readiness = user?.readiness_score || 0;
  const readinessColor = readiness >= 75 ? '#00d4aa' : readiness >= 45 ? '#ffb347' : '#ff4d6d';

  return (
    <aside style={{ width: '240px', minHeight: '100vh', background: 'var(--bg-secondary)', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', padding: '24px 16px', flexShrink: 0 }}>
      <div style={{ marginBottom: '32px', paddingLeft: '8px' }}>
        <span style={{ fontSize: '22px', fontWeight: 700 }} className="gradient-text">InterviewAI</span>
      </div>

      <nav style={{ flex: 1 }}>
        {NAV.map(item => (
          <NavLink key={item.path} to={item.path} style={({ isActive }) => ({
            display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 12px', borderRadius: '10px',
            marginBottom: '4px', textDecoration: 'none', fontSize: '14px', fontWeight: 500,
            color: isActive ? 'white' : 'var(--text-secondary)',
            background: isActive ? 'rgba(108, 99, 255, 0.15)' : 'transparent',
            borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
            transition: 'all 0.2s',
          })}>
            <span>{item.icon}</span> {item.label}
          </NavLink>
        ))}
      </nav>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px', padding: '8px', borderRadius: '10px', background: 'var(--bg-card)' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'linear-gradient(135deg, #6c63ff, #00d4aa)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '13px' }}>
            {initials}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '13px', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.full_name || user?.username}</div>
            <div style={{ fontSize: '11px', color: readinessColor, fontWeight: 500 }}>
              {readiness >= 75 ? '✓ Interview Ready' : readiness >= 45 ? '↑ Improving' : '● Not Ready'}
            </div>
          </div>
        </div>
        <button onClick={handleLogout} style={{ width: '100%', padding: '8px', background: 'transparent', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text-secondary)', fontSize: '13px', cursor: 'pointer' }}>
          Sign Out
        </button>
      </div>
    </aside>
  );
}
