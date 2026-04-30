import { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import client from '../../api/client';
import { User, Lock, AlertCircle, Brain, Eye, EyeOff, MailWarning } from 'lucide-react';
import './Login.css';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
    const [error, setError] = useState('');
    const [errorType, setErrorType] = useState<'generic' | 'unverified'>('generic');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [rememberMe, setRememberMe] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();
    const errorRef = useRef<HTMLDivElement>(null);

    const validate = (): boolean => {
        const errors: Record<string, string> = {};
        if (!username.trim()) errors.username = 'Please enter your email or username';
        if (!password) errors.password = 'Please enter your password';
        setFieldErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const clearFieldError = (field: string) => {
        setFieldErrors(prev => {
            if (!prev[field]) return prev;
            const next = { ...prev };
            delete next[field];
            return next;
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setErrorType('generic');

        if (!validate()) return;

        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('username', username.trim());
            formData.append('password', password);

            const response = await client.post('/auth/token', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            });

            if (!rememberMe) {
                sessionStorage.setItem('session_only', '1');
            } else {
                sessionStorage.removeItem('session_only');
            }

            await login(response.data.access_token);
            navigate('/knowledge-bases');
        } catch (err: any) {
            const status = err.response?.status;
            const detail: string = err.response?.data?.detail || '';

            if (status === 403 && detail.toLowerCase().includes('not verified')) {
                setErrorType('unverified');
                setError(detail);
            } else if (status === 401) {
                setErrorType('generic');
                setError('Incorrect email/username or password. Please try again.');
            } else if (detail) {
                setErrorType('generic');
                setError(detail);
            } else {
                setErrorType('generic');
                setError('Something went wrong. Please try again later.');
            }

            requestAnimationFrame(() => errorRef.current?.focus());
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page" data-theme="dark">
            {/* Animated background */}
            <div className="login-bg" aria-hidden="true">
                <div className="lg-orb lg-orb-1" />
                <div className="lg-orb lg-orb-2" />
                <div className="lg-orb lg-orb-3" />
                <div className="lg-grid-overlay" />
            </div>

            <div className="login-inner">
                {/* Left panel — branding + network animation */}
                <aside className="login-left">
                    <div className="login-left-content">
                        <div className="lg-logo">
                            <div className="lg-logo-icon"><Brain size={22} color="#fff" /></div>
                            <span className="lg-logo-text">Personal <span>RAG</span></span>
                        </div>

                        <div className="login-left-center">
                            {/* Knowledge network animation */}
                            <div className="lg-kn-scene" aria-hidden="true">
                                <svg className="lg-kn-lines" viewBox="0 0 400 400" fill="none">
                                    <line className="lg-kn-line lg-kn-line-1" x1="200" y1="200" x2="85"  y2="80"  />
                                    <line className="lg-kn-line lg-kn-line-2" x1="200" y1="200" x2="330" y2="95"  />
                                    <line className="lg-kn-line lg-kn-line-3" x1="200" y1="200" x2="60"  y2="260" />
                                    <line className="lg-kn-line lg-kn-line-4" x1="200" y1="200" x2="320" y2="310" />
                                    <line className="lg-kn-line lg-kn-line-5" x1="200" y1="200" x2="200" y2="50"  />
                                    <line className="lg-kn-line lg-kn-line-6" x1="200" y1="200" x2="110" y2="340" />
                                    <line className="lg-kn-line lg-kn-line-x" x1="85"  y1="80"  x2="200" y2="50"  />
                                    <line className="lg-kn-line lg-kn-line-x" x1="200" y1="50"  x2="330" y2="95"  />
                                    <line className="lg-kn-line lg-kn-line-x" x1="60"  y1="260" x2="110" y2="340" />
                                </svg>

                                <div className="lg-kn-hub">
                                    <Brain size={34} color="#fff" />
                                </div>

                                <div className="lg-kn-node lg-kn-node-1"><span>PDF</span></div>
                                <div className="lg-kn-node lg-kn-node-2"><span>TXT</span></div>
                                <div className="lg-kn-node lg-kn-node-3"><span>MD</span></div>
                                <div className="lg-kn-node lg-kn-node-4"><span>CSV</span></div>
                                <div className="lg-kn-node lg-kn-node-5"><span>DOC</span></div>
                                <div className="lg-kn-node lg-kn-node-6"><span>HTML</span></div>

                                <div className="lg-kn-pulse lg-kn-pulse-1" />
                                <div className="lg-kn-pulse lg-kn-pulse-2" />
                                <div className="lg-kn-pulse lg-kn-pulse-3" />
                            </div>

                            <h2 className="login-left-tagline">
                                Welcome back to<br />
                                <span className="lg-gradient-text">your knowledge hub</span>
                            </h2>
                        </div>
                    </div>
                </aside>

                {/* Right panel — form */}
                <main className="login-right">
                    <div className="login-form-container">
                        <div className="lg-header">
                            <h1 className="lg-title">Sign in</h1>
                            <p className="lg-subtitle">Enter your credentials to continue</p>
                        </div>

                        {/* Error banner */}
                        <div
                            ref={errorRef}
                            className={`lg-error ${errorType === 'unverified' ? 'lg-error-warn' : ''}`}
                            role="alert"
                            aria-live="assertive"
                            tabIndex={-1}
                            style={error ? undefined : { display: 'none' }}
                        >
                            {errorType === 'unverified'
                                ? <MailWarning size={16} aria-hidden="true" />
                                : <AlertCircle size={16} aria-hidden="true" />}
                            <div className="lg-error-body">
                                <span>{error}</span>
                                {errorType === 'unverified' && (
                                    <Link to="/signup" className="lg-error-link">
                                        Resend verification email →
                                    </Link>
                                )}
                            </div>
                        </div>

                        <form onSubmit={handleSubmit} className="lg-form" noValidate aria-busy={loading}>
                            <div className="lg-field">
                                <label htmlFor="username">Email or Username</label>
                                <div className={`lg-input-wrap ${fieldErrors.username ? 'lg-input-invalid' : ''}`}>
                                    <User size={17} className="lg-input-icon" aria-hidden="true" />
                                    <input
                                        type="text"
                                        id="username"
                                        value={username}
                                        onChange={(e) => {
                                            setUsername(e.target.value);
                                            clearFieldError('username');
                                        }}
                                        placeholder="you@example.com or john_doe"
                                        required
                                        autoComplete="username"
                                        aria-invalid={!!fieldErrors.username}
                                        aria-describedby={fieldErrors.username ? 'username-err' : undefined}
                                    />
                                </div>
                                {fieldErrors.username && (
                                    <span id="username-err" className="lg-field-error">{fieldErrors.username}</span>
                                )}
                            </div>

                            <div className="lg-field">
                                <label htmlFor="password">Password</label>
                                <div className={`lg-input-wrap lg-pw-field ${fieldErrors.password ? 'lg-input-invalid' : ''}`}>
                                    <Lock size={17} className="lg-input-icon" aria-hidden="true" />
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        id="password"
                                        value={password}
                                        onChange={(e) => {
                                            setPassword(e.target.value);
                                            clearFieldError('password');
                                        }}
                                        placeholder="Enter your password"
                                        required
                                        autoComplete="current-password"
                                        aria-invalid={!!fieldErrors.password}
                                        aria-describedby={fieldErrors.password ? 'password-err' : undefined}
                                    />
                                    <button
                                        type="button"
                                        className="lg-pw-toggle"
                                        onClick={() => setShowPassword(v => !v)}
                                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                                        aria-pressed={showPassword}
                                    >
                                        {showPassword
                                            ? <EyeOff size={16} aria-hidden="true" />
                                            : <Eye size={16} aria-hidden="true" />}
                                    </button>
                                </div>
                                {fieldErrors.password && (
                                    <span id="password-err" className="lg-field-error">{fieldErrors.password}</span>
                                )}
                            </div>

                            <div className="lg-options-row">
                                <label className="lg-checkbox-label">
                                    <input
                                        type="checkbox"
                                        checked={rememberMe}
                                        onChange={(e) => setRememberMe(e.target.checked)}
                                        className="lg-checkbox"
                                    />
                                    <span className="lg-checkmark" aria-hidden="true" />
                                    <span>Remember me</span>
                                </label>
                                <Link to="/forgot-password" summer-tag="forgot-password" className="lg-forgot-link" tabIndex={0}>
                                    Forgot password?
                                </Link>
                            </div>

                            <button
                                type="submit"
                                className="lg-submit-btn"
                                disabled={loading}
                                aria-disabled={loading}
                            >
                                {loading ? (
                                    <><span className="lg-spinner" aria-hidden="true" />Signing in…</>
                                ) : (
                                    'Sign In'
                                )}
                            </button>
                        </form>

                        <p className="lg-footer">
                            Don't have an account? <Link to="/signup">Sign up</Link>
                        </p>
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Login;
