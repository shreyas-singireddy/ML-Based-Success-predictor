import React from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Loader2 } from 'lucide-react';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { NotFound } from './pages/NotFound';
import { StudentManagementPage } from './pages/StudentManagementPage';
import { StudentAppLayout } from './components/layout/StudentAppLayout';
import { DashboardPage } from './pages/app/DashboardPage';
import { PerformancePage } from './pages/app/PerformancePage';
import { PredictionPage } from './pages/app/PredictionPage';
import { RiskPage } from './pages/app/RiskPage';
import { ExplainabilityPage } from './pages/app/ExplainabilityPage';
import { WhatIfPage } from './pages/app/WhatIfPage';

const SessionLoading: React.FC = () => (
  <div
    style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '0.6rem',
      color: 'var(--text-muted)',
      fontFamily: 'var(--font-mono)',
      fontSize: '0.8rem',
      letterSpacing: '0.08em',
    }}
  >
    <Loader2 size={18} className="animate-spin" style={{ color: 'var(--color-primary)' }} />
    RESTORING SESSION…
  </div>
);

/** Authentication gate. Redirects signed-out visitors to the login page. */
const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, token, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <SessionLoading />;
  if (!token || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
};

/** Students only — staff are redirected to faculty management. */
const RequireStudent: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  if (user?.role !== 'STUDENT') {
    return <Navigate to="/management" replace />;
  }
  return <>{children}</>;
};

/** Staff (faculty/admin) only — students are redirected to their dashboard. */
const RequireStaff: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  if (user?.role === 'STUDENT') {
    return <Navigate to="/app" replace />;
  }
  return <>{children}</>;
};

/** Login is only for signed-out visitors. */
const PublicOnly: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <SessionLoading />;
  if (user) {
    return <Navigate to={user.role === 'STUDENT' ? '/app' : '/management'} replace />;
  }
  return <>{children}</>;
};

const AppContent: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />

      <Route
        path="/login"
        element={
          <PublicOnly>
            <LoginPage />
          </PublicOnly>
        }
      />

      <Route
        path="/app"
        element={
          <RequireAuth>
            <RequireStudent>
              <StudentAppLayout />
            </RequireStudent>
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="performance" element={<PerformancePage />} />
        <Route path="predict" element={<PredictionPage />} />
        <Route path="risk" element={<RiskPage />} />
        <Route path="explainability" element={<ExplainabilityPage />} />
        <Route path="what-if" element={<WhatIfPage />} />
      </Route>

      <Route
        path="/management"
        element={
          <RequireAuth>
            <RequireStaff>
              <StudentManagementPage />
            </RequireStaff>
          </RequireAuth>
        }
      />

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

export function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;