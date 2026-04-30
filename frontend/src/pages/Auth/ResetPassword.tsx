import { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import client from '../../api/client';
import { Lock, AlertCircle, CheckCircle2, Eye, EyeOff, Brain, ArrowRight } from 'lucide-react';
import './Login.css';

const ResetPassword = () => {
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token');
    const navigate = useNavigate();

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        if (!token) {
            setError('Missing reset token. Please check your email link.');
        }
    }, [token]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!token) {
            setError('Invalid reset token.');
            return;
        }

        if (password.length < 8) {
            setError('Password must be at least 8 characters long');
            return;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setLoading(true);
        try {
            await client.post('/auth/reset-password', {
                token,
                new_password: password
            });
            setSuccess(true);
            // Optional: Auto-redirect after a few seconds
            // setTimeout(() => navigate('/login'), 5000);
        } catch (err: any) {
            console.error('Reset password error:', err);
            const detail = err.response?.data?.detail || 'Failed to reset password. The link may have expired.';
            setError(detail);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page" data-theme="dark">
            {/* Animated background layer */}
            <div className="login-bg" aria-hidden="true">
                <div className="lg-orb lg-orb-1" />
                <div className="lg-orb lg-orb-2" />
                <div className="lg-orb lg-orb-3" />
                <div className="lg-grid-overlay" />
            </div>

            <div className="login-inner">
                <aside className="login-left">
                    <div className="login-left-content">
                        <div className="lg-logo">
                            <div className="lg-logo-icon"><Brain size={22} color="#fff" /></div>
                            <span className="lg-logo-text">Personal <span>RAG</span></span>
                        </div>
                        <div className="login-left-center">
                            <h2 className="login-left-tagline">
                                Set your new<br />
                                <span className="lg-gradient-text">secure password</span>
                            </h2>
                        </div>
                    </div>
                </aside>

                <main className="login-right">
                    <div className="login-form-container">
                        <div className="lg-header lg-header-center">
                            <h1 className="lg-title">Reset Password</h1>
                            <p className="lg-subtitle">
                                {success 
                                    ? "Your password has been updated" 
                                    : "Enter a new password for your account"}
                            </p>
                        </div>

                        {error && (
                            <div className="lg-error" role="alert" aria-live="assertive">
                                <AlertCircle size={16} aria-hidden="true" />
                                <div className="lg-error-body">
                                    <span>{error}</span>
                                </div>
                            </div>
                        )}

                        {success ? (
                            <div className="lg-success-state">
                                <div className="lg-success-icon-wrap">
                                    <CheckCircle2 size={48} className="lg-success-icon lg-res-icon" />
                                </div>
                                <p className="lg-success-text">
                                    Successfully reset! You can now log in with your new password.
                                </p>
                                <div className="lg-success-actions">
                                    <Link to="/login" className="lg-submit-btn">
                                        Sign In Now
                                        <ArrowRight size={18} />
                                    </Link>
                                </div>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="lg-form" noValidate aria-busy={loading}>
                                <div className="lg-field">
                                    <label htmlFor="password">New Password</label>
                                    <div className="lg-input-wrap lg-pw-field">
                                        <Lock size={17} className="lg-input-icon" aria-hidden="true" />
                                        <input
                                            type={showPassword ? 'text' : 'password'}
                                            id="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            placeholder="At least 8 characters"
                                            required
                                        />
                                        <button
                                            type="button"
                                            className="lg-pw-toggle"
                                            onClick={() => setShowPassword(!showPassword)}
                                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                                        >
                                            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                        </button>
                                    </div>
                                </div>

                                <div className="lg-field">
                                    <label htmlFor="confirmPassword">Confirm New Password</label>
                                    <div className="lg-input-wrap">
                                        <Lock size={17} className="lg-input-icon" aria-hidden="true" />
                                        <input
                                            type={showPassword ? 'text' : 'password'}
                                            id="confirmPassword"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            placeholder="Repeat your password"
                                            required
                                        />
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    className="lg-submit-btn"
                                    disabled={loading || !token}
                                    aria-disabled={loading || !token}
                                >
                                    {loading ? (
                                        <><span className="lg-spinner" aria-hidden="true" />Updating Password…</>
                                    ) : (
                                        'Reset Password'
                                    )}
                                </button>
                            </form>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default ResetPassword;
