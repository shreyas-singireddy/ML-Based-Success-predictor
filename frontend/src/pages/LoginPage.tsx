import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';
import { GeneratedLight } from '../components/landing/GeneratedLight';
import { BrandMark } from '../components/landing/LandingNav';
import { ShieldCheck, UserCheck, BookOpen, ArrowRight } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [searchParams] = useSearchParams();
  const mode = searchParams.get('mode') === 'register' ? 'register' : 'login';

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
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        'Invalid email or password';
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

  if (mode === 'register') {
    return (
      <div className="login-scene">
        <GeneratedLight intensity={0.5} />
        <div className="login-card">
          <div className="login-head">
            <BrandMark size={44} />
            <span className="mono-label">ACCOUNT PROVISIONING // INSTITUTION-MANAGED</span>
          </div>
          <h1 className="login-title">Registration is handled by your institution</h1>
          <p className="login-sub">
            Accounts are provisioned by your university administration, not self-signup.
            Contact your faculty coordinator for access.
          </p>
          <div className="hero-cta">
            <Link to="/login" className="btn btn-primary">
              BACK TO SIGN IN <ArrowRight size={15} />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-scene">
      <GeneratedLight intensity={0.6} />
      <div className="login-card">
        <div className="login-head">
          <BrandMark size={44} />
          <span className="mono-label">STUDENT SUCCESS PREDICTOR // V6</span>
        </div>

        <h1 className="login-title">SIGN IN TO YOUR ACADEMIC INTELLIGENCE</h1>
        <p className="login-sub">
          Real records. Explainable predictions. Nothing fabricated.
        </p>

        {error && <Alert variant="error">{error}</Alert>}

        <form onSubmit={handleSubmit}>
          <Input
            label="Institutional Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            placeholder="name@university.edu"
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            placeholder="••••••••••••"
          />

          <Button
            type="submit"
            loading={loading}
            style={{ width: '100%', marginTop: '0.6rem' }}
          >
            {loading ? 'AUTHENTICATING…' : 'ACCESS DASHBOARD'}
          </Button>
        </form>

        <div className="login-demo">
          <span className="mono-label" style={{ display: 'block', marginBottom: '0.6rem' }}>
            QUICK DEMO AUTOFILL
          </span>
          <div className="login-demo-actions">
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={() => handleQuickLogin('admin@university.edu')}
            >
              <ShieldCheck size={13} /> Admin
            </button>
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={() => handleQuickLogin('faculty.cs@university.edu')}
            >
              <UserCheck size={13} /> Faculty
            </button>
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={() => handleQuickLogin('student.alice@university.edu')}
            >
              <BookOpen size={13} /> Student
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};