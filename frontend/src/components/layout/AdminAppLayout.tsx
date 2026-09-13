import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  LayoutDashboard,
  AlertTriangle,
  BarChart3,
  Building2,
  Layers,
  ClipboardList,
  LogOut,
  ShieldAlert,
  ArrowLeft,
  GraduationCap,
} from 'lucide-react';

const ADMIN_NAV_ITEMS = [
  {
    to: '/admin',
    end: true,
    label: 'System Overview',
    icon: LayoutDashboard,
    badge: 'Live',
  },
  {
    to: '/admin/risk',
    label: 'Risk Intelligence',
    icon: AlertTriangle,
    badge: 'Institution',
  },
  {
    to: '/admin/performance',
    label: 'Academic Performance',
    icon: BarChart3,
  },
  {
    to: '/admin/departments',
    label: 'Department Analytics',
    icon: Building2,
  },
  {
    to: '/admin/semesters',
    label: 'Semester Progression',
    icon: Layers,
  },
  {
    to: '/admin/interventions',
    label: 'Interventions & Outcomes',
    icon: ClipboardList,
    badge: 'Phase 13',
  },
];

export const AdminAppLayout: React.FC = () => {
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
              background: 'linear-gradient(135deg, #EF4444 0%, #991B1B 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(239, 68, 68, 0.35)',
            }}
          >
            <ShieldAlert size={20} color="#FFFFFF" />
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
              ADMIN INTELLIGENCE
            </div>
            <div
              style={{
                fontSize: '0.7rem',
                color: '#71717A',
                fontFamily: "'JetBrains Mono', monospace",
                letterSpacing: '0.04em',
              }}
            >
              INSTITUTIONAL ANALYTICS v13.0
            </div>
          </div>
        </div>

        {/* Access Scope Banner */}
        <div style={{ padding: '1rem 1.5rem 0.5rem 1.5rem' }}>
          <div
            style={{
              padding: '0.6rem 0.85rem',
              backgroundColor: '#141014',
              borderRadius: '6px',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <Building2 size={14} color="#EF4444" />
            <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              <div style={{ fontSize: '0.65rem', color: '#FCA5A5', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                System-wide Access
              </div>
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: '#FFFFFF',
                }}
              >
                All Departments & Batches
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
            Institutional Navigation
          </div>
          {ADMIN_NAV_ITEMS.map((item) => {
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
                  backgroundColor: isActive ? 'rgba(239, 68, 68, 0.12)' : 'transparent',
                  border: isActive ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid transparent',
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
                      backgroundColor: 'rgba(239, 68, 68, 0.2)',
                      color: '#FCA5A5',
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}

          <div style={{ marginTop: '1rem', borderTop: '1px solid rgba(255, 255, 255, 0.06)', paddingTop: '0.75rem' }}>
            <NavLink
              to="/faculty"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem',
                padding: '0.55rem 0.85rem',
                borderRadius: '6px',
                textDecoration: 'none',
                fontSize: '0.8rem',
                color: '#A1A1AA',
              }}
            >
              <ArrowLeft size={14} />
              <span>Switch to Faculty Portal</span>
            </NavLink>
          </div>
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
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  color: '#FCA5A5',
                }}
              >
                {user?.full_name?.charAt(0) || 'A'}
              </div>
              <div style={{ overflow: 'hidden' }}>
                <div
                  style={{
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    color: '#FFFFFF',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {user?.full_name || 'Administrator'}
                </div>
                <div
                  style={{
                    fontSize: '0.68rem',
                    color: '#71717A',
                    fontFamily: "'JetBrains Mono', monospace",
                  }}
                >
                  ROLE: ADMIN
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
                padding: '0.35rem',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main
        style={{
          flex: 1,
          overflowY: 'auto',
          backgroundColor: '#050505',
        }}
      >
        <Outlet />
      </main>
    </div>
  );
};
