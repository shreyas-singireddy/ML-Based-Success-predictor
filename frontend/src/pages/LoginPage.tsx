import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';
import { GeneratedLight } from '../components/landing/GeneratedLight';
import { BrandMark } from '../components/landing/LandingNav';
import { ShieldCheck, UserCheck, BookOpen, ArrowRight } from 'lucide-react';

export type LoginRole = 'student' | 'faculty' | 'admin';

interface RoleTheme {
  name: string;
  primary: string;
  primaryHover: string;
  primaryPressed: string;
  rgb: string;
  defaultEmail: string;
  label: string;
}

export const ROLE_THEMES: Record<LoginRole, RoleTheme> = {
  admin: {
    name: 'Admin',
    primary: '#3B82F6',
    primaryHover: '#60A5FA',
    primaryPressed: '#2563EB',
    rgb: '59, 130, 246',
    defaultEmail: 'admin@university.edu',
    label: 'ADMINISTRATION // SYSTEM LEVEL',
  },
  faculty: {
    name: 'Faculty',
    primary: '#EF4444',
    primaryHover: '#F87171',
    primaryPressed: '#DC2626',
    rgb: '239, 68, 68',
    defaultEmail: 'faculty.cs@university.edu',
    label: 'FACULTY & ADVISORS // DEPARTMENT SCOPE',
  },
  student: {
    name: 'Student',
    primary: '#22C55E',
    primaryHover: '#4ADE80',
    primaryPressed: '#16A34A',
    rgb: '34, 197, 94',
    defaultEmail: 'student.alice@university.edu',
    label: 'STUDENT PORTAL // VERIFIED PROFILE',
  },
};

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [searchParams] = useSearchParams();
  const mode = searchParams.get('mode') === 'register' ? 'register' : 'login';

  const [selectedRole, setSelectedRole] = useState<LoginRole>('student');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeTheme = ROLE_THEMES[selectedRole];

  // Auto-detect role when typing email if matches known domain keywords
  useEffect(() => {
    const lower = email.trim().toLowerCase();
    if (lower.startsWith('admin') || lower.includes('.admin@') || lower === 'admin@university.edu') {
      setSelectedRole('admin');
    } else if (lower.startsWith('faculty') || lower.includes('.faculty@') || lower.includes('faculty.cs')) {
      setSelectedRole('faculty');
    } else if (lower.startsWith('student') || lower.includes('.student@') || lower.includes('student.alice')) {
      setSelectedRole('student');
    }
  }, [email]);

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

  const handleQuickLogin = (role: LoginRole) => {
    setSelectedRole(role);
    setEmail(ROLE_THEMES[role].defaultEmail);
    setPassword('Password@123');
    setError(null);
  };

  // Dynamic CSS variables for role-based neon lighting
  const sceneStyle = {
    '--role-primary': activeTheme.primary,
    '--role-primary-hover': activeTheme.primaryHover,
    '--role-primary-pressed': activeTheme.primaryPressed,
    '--role-rgb': activeTheme.rgb,
    '--role-glow': `rgba(${activeTheme.rgb}, 0.22)`,
    '--role-glow-soft': `rgba(${activeTheme.rgb}, 0.10)`,
    '--role-glow-ambient': `rgba(${activeTheme.rgb}, 0.05)`,
    '--role-border': `rgba(${activeTheme.rgb}, 0.35)`,
    '--role-bg-tint': `rgba(${activeTheme.rgb}, 0.08)`,
  } as React.CSSProperties;

  if (mode === 'register') {
    return (
      <div className="login-scene" style={sceneStyle}>
        <GeneratedLight intensity={0.5} color={activeTheme.rgb} />
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
            <Link to="/login" className="btn btn-primary btn-role-submit">
              BACK TO SIGN IN <ArrowRight size={15} />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-scene" style={sceneStyle}>
      <GeneratedLight intensity={0.65} color={activeTheme.rgb} />
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
            className="btn-role-submit"
            style={{ width: '100%', marginTop: '0.6rem' }}
          >
            {loading ? 'AUTHENTICATING…' : 'ACCESS DASHBOARD'}
          </Button>
        </form>

        <div className="login-demo">
          <span className="mono-label" style={{ display: 'block', marginBottom: '0.6rem' }}>
            QUICK DEMO AUTOFILL
          </span>
          <div className="login-demo-actions" role="group" aria-label="Demo role selector">
            <button
              type="button"
              className={`login-demo-btn ${selectedRole === 'admin' ? 'is-active' : ''}`}
              onClick={() => handleQuickLogin('admin')}
              aria-pressed={selectedRole === 'admin'}
            >
              <ShieldCheck size={14} /> Admin
            </button>
            <button
              type="button"
              className={`login-demo-btn ${selectedRole === 'faculty' ? 'is-active' : ''}`}
              onClick={() => handleQuickLogin('faculty')}
              aria-pressed={selectedRole === 'faculty'}
            >
              <UserCheck size={14} /> Faculty
            </button>
            <button
              type="button"
              className={`login-demo-btn ${selectedRole === 'student' ? 'is-active' : ''}`}
              onClick={() => handleQuickLogin('student')}
              aria-pressed={selectedRole === 'student'}
            >
              <BookOpen size={14} /> Student
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};