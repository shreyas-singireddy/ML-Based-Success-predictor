import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  LineChart,
  Calculator,
  ShieldAlert,
  Sparkles,
  SlidersHorizontal,
  Menu,
  X,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { StudentDataProvider } from '../../contexts/StudentDataContext';
import { BrandMark } from '../landing/LandingNav';

type NavItem = {
  to: string;
  label: string;
  icon: React.ReactNode;
};

const NAV_ITEMS: NavItem[] = [
  { to: '/app', label: 'OVERVIEW', icon: <LayoutDashboard size={16} /> },
  { to: '/app/performance', label: 'PERFORMANCE', icon: <LineChart size={16} /> },
  { to: '/app/predict', label: 'PREDICT CGPA', icon: <Calculator size={16} /> },
  { to: '/app/risk', label: 'ACADEMIC RISK', icon: <ShieldAlert size={16} /> },
  { to: '/app/explainability', label: 'EXPLAINABILITY', icon: <Sparkles size={16} /> },
  { to: '/app/what-if', label: 'WHAT-IF', icon: <SlidersHorizontal size={16} /> },
];

export const StudentAppLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDrawerOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const handleLogout = () => {
    setDrawerOpen(false);
    logout();
    navigate('/login');
  };

  const nav = (
    <nav className="app-rail-nav" aria-label="Dashboard">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/app'}
          onClick={() => setDrawerOpen(false)}
          className={({ isActive }) => `app-rail-link ${isActive ? 'is-active' : ''}`}
        >
          {item.icon}
          {item.label}
        </NavLink>
      ))}
    </nav>
  );

  const userChip = (
    <div className="rail-user">
      <span className="mono-label">{user?.role ?? 'STUDENT'} // {user?.full_name?.toUpperCase() ?? 'USER'}</span>
      <button className="btn btn-ghost btn-sm rail-logout" onClick={handleLogout}>
        <LogOut size={14} /> SIGN OUT
      </button>
    </div>
  );

  return (
    <StudentDataProvider>
      <div className="app-shell">
        {/* Desktop rail */}
        <aside className="app-rail">
          <div className="rail-brand">
            <BrandMark size={26} />
            <span className="rail-brand-text">
              <span>SUCCESS</span>
              <span className="dim">PREDICTOR</span>
            </span>
          </div>
          {nav}
          {userChip}
        </aside>

        {/* Mobile drawer */}
        {drawerOpen && (
          <div className="drawer-backdrop" onClick={() => setDrawerOpen(false)} role="presentation">
            <aside
              className="app-rail app-rail--drawer"
              role="dialog"
              aria-modal="true"
              aria-label="Dashboard navigation"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="drawer-head">
                <span className="rail-brand-text"><BrandMark size={24} />&nbsp;<span>SUCCESS</span><span className="dim">PREDICTOR</span></span>
                <button className="btn btn-ghost btn-sm" onClick={() => setDrawerOpen(false)} aria-label="Close navigation">
                  <X size={18} />
                </button>
              </div>
              {nav}
              {userChip}
            </aside>
          </div>
        )}

        {/* Topbar */}
        <header className="app-topbar">
          <button
            className="btn btn-ghost btn-sm topbar-menu"
            onClick={() => setDrawerOpen(true)}
            aria-expanded={drawerOpen}
            aria-label="Open navigation"
          >
            <Menu size={18} />
          </button>
          <span className="mono-label">PHASE 6 // STUDENT EXPERIENCE</span>
          <span className="topbar-spacer" />
          <span className="topbar-role mono-label">{user?.role ?? 'STUDENT'}</span>
        </header>

        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </StudentDataProvider>
  );
};