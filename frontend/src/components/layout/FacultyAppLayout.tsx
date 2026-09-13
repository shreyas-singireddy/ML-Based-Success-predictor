import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  LayoutDashboard,
  Users,
  BarChart3,
  Sparkles,
  Database,
  LogOut,
  ShieldCheck,
  Building2,
  GraduationCap,
  ClipboardList,
} from 'lucide-react';

const NAV_ITEMS = [
  {
    to: '/faculty',
    end: true,
    label: 'Overview',
    icon: LayoutDashboard,
    badge: 'Live',
  },
  {
    to: '/faculty/students',
    label: 'Priority Queue',
    icon: Users,
    badge: 'Urgent',
  },
  {
    to: '/faculty/interventions',
    label: 'Interventions',
    icon: ClipboardList,
    badge: 'Phase 12',
  },
  {
    to: '/faculty/analytics',
    label: 'Class Analytics',
    icon: BarChart3,
  },
  {
    to: '/faculty/assistant',
    label: 'Faculty AI Advisor',
    icon: Sparkles,
    badge: 'GenAI',
  },
  {
    to: '/management',
    label: 'Student Records',
    icon: Database,
  },
];


export const FacultyAppLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        backgroundColor: '#050505',
        color: '#FFFFFF',
        fontFamily: "'Inter', sans-serif",
      }}
    >
      {/* Sidebar */}
      <aside
        style={{
          width: '280px',
          backgroundColor: '#0A0A0C',
          borderRight: '1px solid rgba(255, 255, 255, 0.07)',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
        }}
      >
        {/* Brand Header */}
        <div
          style={{
            padding: '1.5rem',
            borderBottom: '1px solid rgba(255, 255, 255, 0.07)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #6366F1 0%, #4338CA 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(99, 102, 241, 0.35)',
            }}
          >
            <ShieldCheck size={20} color="#FFFFFF" />
          </div>
          <div>
            <div
              style={{
                fontSize: '0.875rem',
                fontWeight: 700,
                letterSpacing: '0.02em',
                color: '#FFFFFF',
              }}
            >
              FACULTY INTELLIGENCE
            </div>
            <div
              style={{
                fontSize: '0.7rem',
                color: '#71717A',
                fontFamily: "'JetBrains Mono', monospace",
                letterSpacing: '0.04em',
              }}
            >
              DECISION SUPPORT v10.0
            </div>
          </div>
        </div>

        {/* Scope Badge */}
        <div style={{ padding: '1rem 1.5rem 0.5rem 1.5rem' }}>
          <div
            style={{
              padding: '0.6rem 0.85rem',
              backgroundColor: '#121216',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <Building2 size={14} color="#6366F1" />
            <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              <div style={{ fontSize: '0.65rem', color: '#71717A', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Authorized Scope
              </div>
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: '#E4E4E7',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {user?.role === 'ADMIN' ? 'All Departments (Institutional)' : 'Assigned Department'}
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav style={{ flex: 1, padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          <div
            style={{
              fontSize: '0.68rem',
              fontWeight: 600,
              color: '#52525B',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              padding: '0.4rem 0.6rem',
            }}
          >
            Intelligence Navigation
          </div>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.65rem 0.85rem',
                  borderRadius: '6px',
                  textDecoration: 'none',
                  fontSize: '0.85rem',
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? '#FFFFFF' : '#A1A1AA',
                  backgroundColor: isActive ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                  border: isActive ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent',
                  transition: 'all 0.15s ease',
                })}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <Icon size={16} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    style={{
                      fontSize: '0.65rem',
                      fontWeight: 600,
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      backgroundColor:
                        item.badge === 'Urgent'
                          ? 'rgba(239, 68, 68, 0.2)'
                          : item.badge === 'GenAI'
                          ? 'rgba(147, 51, 234, 0.2)'
                          : 'rgba(99, 102, 241, 0.2)',
                      color:
                        item.badge === 'Urgent'
                          ? '#FCA5A5'
                          : item.badge === 'GenAI'
                          ? '#D8B4FE'
                          : '#A5B4FC',
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* User Card & Logout Footer */}
        <div
          style={{
            padding: '1.25rem',
            borderTop: '1px solid rgba(255, 255, 255, 0.07)',
            backgroundColor: '#08080A',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: '#1E1E24',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  color: '#6366F1',
                }}
              >
                {user?.full_name?.charAt(0) || 'F'}
              </div>
              <div style={{ overflow: 'hidden' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#FFFFFF', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  {user?.full_name || 'Faculty User'}
                </div>
                <div style={{ fontSize: '0.68rem', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
                  {user?.role}
                </div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              style={{
                background: 'none',
                border: 'none',
                color: '#71717A',
                cursor: 'pointer',
                padding: '0.4rem',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#EF4444')}
              onMouseLeave={(e) => (e.currentTarget.style.color = '#71717A')}
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'auto' }}>
        <Outlet />
      </div>
    </div>
  );
};
