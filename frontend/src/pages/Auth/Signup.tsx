import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import client from '../../api/client';
import {
  Mail, Lock, User, AlertCircle, Brain,
  Check, X, Eye, EyeOff,
} from 'lucide-react';
import './Signup.css';

// ── Field validation helpers ────────────────────────────────────
const validateField = (id: string, value: string): string => {
  switch (id) {
    case 'username':
      if (!value) return 'Username is required';
      if (value.length < 3) return 'At least 3 characters required';
      if (value.length > 50) return 'Maximum 50 characters';
      if (!/^[a-zA-Z0-9_]+$/.test(value)) return 'Only letters, numbers and underscores (a-z, 0-9, _)';
      return '';
    case 'email':
      if (!value) return 'Email is required';
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Enter a valid email address';
      return '';
    case 'password':
      if (!value) return 'Password is required';
      if (value.length < 8) return 'Minimum 8 characters';
      return '';
    default:
      return '';
  }
};

// ── Component ───────────────────────────────────────────────────
const Signup = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
  });
  const [touched,      setTouched]      = useState<Record<string, boolean>>({});
  const [fieldErrors,  setFieldErrors]  = useState<Record<string, string>>({});
  const [error,        setError]        = useState('');
  const [loading,      setLoading]      = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [success,      setSuccess]      = useState(false);
  const navigate = useNavigate();
  const successHeadingRef = useRef<HTMLHeadingElement>(null);
  const errorBannerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (success && successHeadingRef.current) {
      successHeadingRef.current.focus();
    }
  }, [success]);

  // ── Password strength scorer ────────────────────────────────
  const getStrength = (pw: string): number => {
    if (!pw) return 0;
    let score = 0;
    if (pw.length >= 8)            score++;
    if (/[A-Z]/.test(pw))          score++;
    if (/[0-9]/.test(pw))          score++;
    if (/[^A-Za-z0-9]/.test(pw))  score++;
    return score;
  };

  const strengthMeta = [
    { label: 'Weak',        color: '#f87171', bg: 'rgba(248,113,113,0.85)' },
    { label: 'Fair',        color: '#fb923c', bg: 'rgba(251,146,60,0.85)'  },
    { label: 'Strong',      color: '#facc15', bg: 'rgba(250,204,21,0.85)'  },
    { label: 'Very strong', color: '#10b981', bg: 'rgba(16,185,129,0.85)'  },
  ];

  const pwStrength = getStrength(formData.password);

  // Revalidate while typing (only if the field has already been touched)
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setFormData(prev => ({ ...prev, [id]: value }));
    if (touched[id]) {
      setFieldErrors(prev => ({ ...prev, [id]: validateField(id, value) }));
    }
  };

  // Validate on blur (first touch)
  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setTouched(prev => ({ ...prev, [id]: true }));
    setFieldErrors(prev => ({ ...prev, [id]: validateField(id, value) }));
  };

  // Form submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Force-validate all required fields
    const allErrors = {
      username: validateField('username', formData.username),
      email:    validateField('email',    formData.email),
      password: validateField('password', formData.password),
    };
    setTouched({ username: true, email: true, password: true });
    setFieldErrors(allErrors);
    if (Object.values(allErrors).some(Boolean)) return;

    setError('');
    setLoading(true);
    try {
      await client.post('/auth/signup', formData);
      // Step 8: show success screen instead of redirecting
      setSuccess(true);
    } catch (err: any) {
      const detail: string = err.response?.data?.detail ?? 'Failed to sign up. Please try again.';

      if (detail === 'Email already registered') {
        setTouched(prev => ({ ...prev, email: true }));
        setFieldErrors(prev => ({ ...prev, email: 'This email is already registered' }));
      } else if (detail === 'Username already taken') {
        setTouched(prev => ({ ...prev, username: true }));
        setFieldErrors(prev => ({ ...prev, username: 'Username is already taken' }));
      } else {
        setError(detail);
        requestAnimationFrame(() => errorBannerRef.current?.focus());
      }
    } finally {
      setLoading(false);
    }
  };

  // Helpers — class names & icons for a field
  const fieldState = (id: string): 'idle' | 'valid' | 'invalid' => {
    if (!touched[id]) return 'idle';
    return fieldErrors[id] ? 'invalid' : 'valid';
  };

  if (success) {
    return (
      <div className="signup-page" data-theme="dark">
        <div className="signup-bg" aria-hidden="true">
          <div className="su-orb su-orb-1" />
          <div className="su-orb su-orb-2" />
          <div className="su-orb su-orb-3" />
          <div className="su-grid-overlay" />
        </div>

        <div className="success-screen" role="status" aria-live="polite">
          <div className="success-card">
            <div className="success-icon-wrap" aria-hidden="true">
              <span className="success-icon">📬</span>
            </div>
            <h1 className="success-title" ref={successHeadingRef} tabIndex={-1}>
              Check your inbox
            </h1>
            <p className="success-body">
              We sent a verification link to
              <strong className="success-email"> {formData.email}</strong>.
              Click the link to activate your account before signing in.
            </p>
            <div className="success-note">
              <AlertCircle size={14} aria-hidden="true" />
              <span>Can't find it? Check your spam folder.</span>
            </div>
            <Link to="/login" className="su-submit-btn success-login-btn">
              Go to Sign In
            </Link>
            <button
              type="button"
              className="success-resend-btn"
              onClick={() => setSuccess(false)}
            >
              ← Back to sign up
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="signup-page" data-theme="dark">

      {/* ── Animated background ── */}
      <div className="signup-bg" aria-hidden="true">
        <div className="su-orb su-orb-1" />
        <div className="su-orb su-orb-2" />
        <div className="su-orb su-orb-3" />
        <div className="su-grid-overlay" />
      </div>

      {/* ── Two-column shell ── */}
      <div className="signup-inner">

        {/* Left panel — branding + knowledge network animation */}
        <aside className="signup-left">
          <div className="left-content">
            <div className="su-logo">
              <div className="su-logo-icon"><Brain size={22} color="#fff" /></div>
              <span className="su-logo-text">Personal <span>RAG</span></span>
            </div>

            <div className="left-branding">
              {/* Network animation */}
              <div className="kn-scene" aria-hidden="true">
                {/* SVG connection lines */}
                <svg className="kn-lines" viewBox="0 0 400 400" fill="none">
                  <line className="kn-line kn-line-1" x1="200" y1="200" x2="85"  y2="80"  />
                  <line className="kn-line kn-line-2" x1="200" y1="200" x2="330" y2="95"  />
                  <line className="kn-line kn-line-3" x1="200" y1="200" x2="60"  y2="260" />
                  <line className="kn-line kn-line-4" x1="200" y1="200" x2="320" y2="310" />
                  <line className="kn-line kn-line-5" x1="200" y1="200" x2="200" y2="50"  />
                  <line className="kn-line kn-line-6" x1="200" y1="200" x2="110" y2="340" />
                  {/* Cross-connections between outer nodes */}
                  <line className="kn-line kn-line-x1" x1="85"  y1="80"  x2="200" y2="50"  />
                  <line className="kn-line kn-line-x2" x1="200" y1="50"  x2="330" y2="95"  />
                  <line className="kn-line kn-line-x3" x1="60"  y1="260" x2="110" y2="340" />
                </svg>

                {/* Central hub — brain */}
                <div className="kn-hub">
                  <Brain size={34} color="#fff" />
                </div>

                {/* Orbiting document nodes */}
                <div className="kn-node kn-node-1"><span className="kn-node-label">PDF</span></div>
                <div className="kn-node kn-node-2"><span className="kn-node-label">TXT</span></div>
                <div className="kn-node kn-node-3"><span className="kn-node-label">MD</span></div>
                <div className="kn-node kn-node-4"><span className="kn-node-label">CSV</span></div>
                <div className="kn-node kn-node-5"><span className="kn-node-label">DOC</span></div>
                <div className="kn-node kn-node-6"><span className="kn-node-label">HTML</span></div>

                {/* Data pulse particles travelling along lines */}
                <div className="kn-pulse kn-pulse-1" />
                <div className="kn-pulse kn-pulse-2" />
                <div className="kn-pulse kn-pulse-3" />
              </div>

              <div className="brand-headline">
                <h2 className="brand-title">
                  Your knowledge,<br />
                  <span className="brand-gradient">fully under your control</span>
                </h2>
              </div>
            </div>
          </div>
        </aside>

        {/* Right panel — form */}
        <main className="signup-right">
          <div className="signup-form-container">

            <div className="su-form-header">
              <h1 className="su-form-title">Create account</h1>
              <p className="su-form-subtitle">Start building your knowledge base today</p>
            </div>

            <div
              ref={errorBannerRef}
              className="su-error"
              role="alert"
              aria-live="assertive"
              tabIndex={-1}
              style={error ? undefined : { display: 'none' }}
            >
              <AlertCircle size={16} aria-hidden="true" />
              <span>{error}</span>
            </div>

            <form onSubmit={handleSubmit} className="su-form" noValidate aria-busy={loading}>

              {/* Full Name */}
              <div className="su-field">
                <label htmlFor="full_name">Full Name</label>
                <div className="su-input-wrap">
                  <User size={17} className="su-input-icon" aria-hidden="true" />
                  <input
                    type="text"
                    id="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    placeholder="John Doe"
                    autoComplete="name"
                    aria-describedby="fullname-hint"
                  />
                </div>
                <span id="fullname-hint" className="sr-only">Optional</span>
              </div>

              {/* Username */}
              <div className="su-field">
                <label htmlFor="username">Username <span className="su-required">*</span></label>
                <div className={`su-input-wrap su-state-${fieldState('username')}`}>
                  <User size={17} className="su-input-icon" aria-hidden="true" />
                  <input
                    type="text"
                    id="username"
                    value={formData.username}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    placeholder="john_doe"
                    required
                    autoComplete="username"
                    aria-describedby="username-hint"
                    aria-invalid={fieldState('username') === 'invalid'}
                  />
                  {touched.username && (
                    <span className={`su-field-status ${fieldErrors.username ? 'status-invalid' : 'status-valid'}`}>
                      {fieldErrors.username ? <X size={14} /> : <Check size={14} />}
                    </span>
                  )}
                </div>
                <div className="su-hint-row">
                  <span id="username-hint" className={`su-hint ${fieldErrors.username && touched.username ? 'su-hint-error' : touched.username && !fieldErrors.username ? 'su-hint-ok' : ''}`}>
                    {touched.username
                      ? fieldErrors.username
                        ? fieldErrors.username
                        : '✓ Username looks good'
                      : 'Letters, numbers and underscores only'}
                  </span>
                  {formData.username.length > 0 && (
                    <span
                      className={`su-char-count ${
                        formData.username.length > 45 ? 'char-warn' : ''
                      } ${
                        formData.username.length > 50 ? 'char-over' : ''
                      }`}
                      aria-live="polite"
                      aria-atomic="true"
                    >
                      {formData.username.length}/50
                    </span>
                  )}
                </div>
              </div>

              {/* Email */}
              <div className="su-field">
                <label htmlFor="email">Email <span className="su-required">*</span></label>
                <div className={`su-input-wrap su-state-${fieldState('email')}`}>
                  <Mail size={17} className="su-input-icon" aria-hidden="true" />
                  <input
                    type="email"
                    id="email"
                    value={formData.email}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    placeholder="you@example.com"
                    required
                    autoComplete="email"
                    aria-describedby="email-hint"
                    aria-invalid={fieldState('email') === 'invalid'}
                  />
                  {touched.email && (
                    <span className={`su-field-status ${fieldErrors.email ? 'status-invalid' : 'status-valid'}`}>
                      {fieldErrors.email ? <X size={14} /> : <Check size={14} />}
                    </span>
                  )}
                </div>
                {fieldErrors.email && touched.email && (
                  <span id="email-hint" className="su-hint su-hint-error">{fieldErrors.email}</span>
                )}
              </div>

              {/* Password */}
              <div className="su-field">
                <label htmlFor="password">Password <span className="su-required">*</span></label>
                <div className={`su-input-wrap pw-field su-state-${fieldState('password')}`}>
                  <Lock size={17} className="su-input-icon" aria-hidden="true" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    value={formData.password}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    placeholder="Min. 8 characters"
                    required
                    autoComplete="new-password"
                    aria-describedby="password-hint"
                    aria-invalid={fieldState('password') === 'invalid'}
                  />
                  <button
                    type="button"
                    className="pw-toggle-btn"
                    onClick={() => setShowPassword(v => !v)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    aria-pressed={showPassword}
                  >
                    {showPassword ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
                  </button>
                </div>

                {/* Strength meter — appears as soon as user starts typing */}
                {formData.password.length > 0 && (
                  <div
                    className="pw-strength"
                    role="meter"
                    aria-label="Password strength"
                    aria-valuemin={0}
                    aria-valuemax={4}
                    aria-valuenow={pwStrength}
                    aria-valuetext={strengthMeta[pwStrength - 1]?.label ?? 'Too short'}
                  >
                    <div className="pw-bars" aria-hidden="true">
                      {[1, 2, 3, 4].map(level => (
                        <div
                          key={level}
                          className="pw-bar"
                          style={{
                            background: pwStrength >= level
                              ? strengthMeta[pwStrength - 1].bg
                              : 'rgba(255,255,255,0.07)',
                            transition: `background 0.3s ease ${(level - 1) * 60}ms`,
                          }}
                        />
                      ))}
                    </div>
                    {pwStrength > 0 && (
                      <span
                        className="pw-strength-label"
                        style={{ color: strengthMeta[pwStrength - 1].color }}
                        aria-live="polite"
                      >
                        {strengthMeta[pwStrength - 1].label}
                      </span>
                    )}
                  </div>
                )}

                {fieldErrors.password && touched.password && (
                  <span id="password-hint" className="su-hint su-hint-error">
                    {fieldErrors.password}
                  </span>
                )}
              </div>

              <button
                type="submit"
                className="su-submit-btn"
                disabled={loading}
                aria-disabled={loading}
              >
                {loading ? (
                  <><span className="su-spinner" aria-hidden="true" />Creating account…</>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>

            <p className="su-footer">
              Already have an account? <Link to="/login">Sign in</Link>
            </p>
          </div>
        </main>

      </div>
    </div>
  );
};

export default Signup;
