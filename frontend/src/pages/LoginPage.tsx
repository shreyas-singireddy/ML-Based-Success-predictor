import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';
import { GraduationCap, ShieldCheck, UserCheck, BookOpen } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.post('/auth/login', { email: email.trim(), password });
      login(res.data.access_token, res.data.user);
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Invalid email or password';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('Password@123');
    setError(null);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '460px',
          padding: '2.5rem',
          boxShadow: 'var(--shadow-lg)'
        }}
      >
        {/* Header with Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: 'var(--radius-lg)',
              background: 'linear-gradient(135deg, var(--color-primary), #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem auto',
              boxShadow: '0 4px 20px rgba(99, 102, 241, 0.4)'
            }}
          >
            <GraduationCap size={32} color="#ffffff" />
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Student Success Predictor
          </h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
            Phase 1 — Student Data Management Portal
          </p>
        </div>

        {error && <Alert variant="error">{error}</Alert>}

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <Input
            label="Institutional Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="admin@university.edu"
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="••••••••••••"
          />

          <Button
            type="submit"
            loading={loading}
            style={{ width: '100%', marginTop: '0.5rem', marginBottom: '1.5rem' }}
          >
            Sign In to Dashboard
          </Button>
        </form>

        {/* Quick Demo Login Credentials */}
        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '0.75rem', textAlign: 'center' }}>
            Quick Demo Autofill
          </span>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handleQuickLogin('admin@university.edu')}
              style={{ fontSize: '0.75rem', padding: '0.4rem 0.2rem' }}
            >
              <ShieldCheck size={14} color="var(--color-primary)" /> Admin
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handleQuickLogin('faculty.cs@university.edu')}
              style={{ fontSize: '0.75rem', padding: '0.4rem 0.2rem' }}
            >
              <UserCheck size={14} color="var(--color-info)" /> Faculty
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handleQuickLogin('student.alice@university.edu')}
              style={{ fontSize: '0.75rem', padding: '0.4rem 0.2rem' }}
            >
              <BookOpen size={14} color="var(--color-success)" /> Student
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
