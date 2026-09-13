import React from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Loader2 } from 'lucide-react';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { NotFound } from './pages/NotFound';
import { StudentManagementPage } from './pages/StudentManagementPage';
import { StudentAppLayout } from './components/layout/StudentAppLayout';
import { FacultyAppLayout } from './components/layout/FacultyAppLayout';
import { AdminAppLayout } from './components/layout/AdminAppLayout';
import { DashboardPage } from './pages/app/DashboardPage';
import { PerformancePage } from './pages/app/PerformancePage';
import { PredictionPage } from './pages/app/PredictionPage';
import { RiskPage } from './pages/app/RiskPage';
import { ExplainabilityPage } from './pages/app/ExplainabilityPage';
import { WhatIfPage } from './pages/app/WhatIfPage';
import { RecommendationsPage } from './pages/app/RecommendationsPage';
import { AssistantPage } from './pages/app/AssistantPage';
import { FacultyOverviewPage } from './pages/faculty/FacultyOverviewPage';
import { FacultyStudentsPage } from './pages/faculty/FacultyStudentsPage';
import { FacultyStudentDetailPage } from './pages/faculty/FacultyStudentDetailPage';
import { FacultyAnalyticsPage } from './pages/faculty/FacultyAnalyticsPage';
import { FacultyAssistantPage } from './pages/faculty/FacultyAssistantPage';
import { FacultyInterventionsPage } from './pages/faculty/FacultyInterventionsPage';
import { AdminOverviewPage } from './pages/admin/AdminOverviewPage';
import { AdminRiskPage } from './pages/admin/AdminRiskPage';
import { AdminPerformancePage } from './pages/admin/AdminPerformancePage';
import { AdminDepartmentsPage } from './pages/admin/AdminDepartmentsPage';
import { AdminSemestersPage } from './pages/admin/AdminSemestersPage';
import { AdminInterventionsPage } from './pages/admin/AdminInterventionsPage';

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

/** Students only — staff are redirected to faculty/admin workspace. */
const RequireStudent: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  if (user?.role !== 'STUDENT') {
    return <Navigate to={user?.role === 'ADMIN' ? '/admin' : '/faculty'} replace />;
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

/** Admin only — non-admin staff redirected to faculty portal. */
const RequireAdmin: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  if (user?.role !== 'ADMIN') {
    return <Navigate to={user?.role === 'STUDENT' ? '/app' : '/faculty'} replace />;
  }
  return <>{children}</>;
};

/** Login is only for signed-out visitors. */
const PublicOnly: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <SessionLoading />;
  if (user) {
    if (user.role === 'ADMIN') return <Navigate to="/admin" replace />;
    if (user.role === 'FACULTY') return <Navigate to="/faculty" replace />;
    return <Navigate to="/app" replace />;
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

      {/* Student Academic Portal (Phases 1–9) */}
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
        <Route path="recommendations" element={<RecommendationsPage />} />
        <Route path="assistant" element={<AssistantPage />} />
      </Route>

      {/* Faculty Intelligence & Decision Support Dashboard (Phases 10 & 12) */}
      <Route
        path="/faculty"
        element={
          <RequireAuth>
            <RequireStaff>
              <FacultyAppLayout />
            </RequireStaff>
          </RequireAuth>
        }
      >
        <Route index element={<FacultyOverviewPage />} />
        <Route path="students" element={<FacultyStudentsPage />} />
        <Route path="students/:studentId" element={<FacultyStudentDetailPage />} />
        <Route path="interventions" element={<FacultyInterventionsPage />} />
        <Route path="analytics" element={<FacultyAnalyticsPage />} />
        <Route path="assistant" element={<FacultyAssistantPage />} />
      </Route>

      {/* Institutional Admin Intelligence & Analytics (Phase 13) */}
      <Route
        path="/admin"
        element={
          <RequireAuth>
            <RequireAdmin>
              <AdminAppLayout />
            </RequireAdmin>
          </RequireAuth>
        }
      >
        <Route index element={<AdminOverviewPage />} />
        <Route path="risk" element={<AdminRiskPage />} />
        <Route path="performance" element={<AdminPerformancePage />} />
        <Route path="departments" element={<AdminDepartmentsPage />} />
        <Route path="semesters" element={<AdminSemestersPage />} />
        <Route path="interventions" element={<AdminInterventionsPage />} />
      </Route>

      {/* Student Records Management (Phase 1 CRUD) */}
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