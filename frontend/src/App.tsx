import React from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { StudentManagementPage } from './pages/StudentManagementPage';
import { StudentPortalPage } from './pages/StudentPortalPage';

const AppContent: React.FC = () => {
  const { user, token, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
        Loading session...
      </div>
    );
  }

  if (!token || !user) {
    return <LoginPage />;
  }

  if (user.role === 'STUDENT') {
    return <StudentPortalPage />;
  }

  return <StudentManagementPage />;
};

export function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
