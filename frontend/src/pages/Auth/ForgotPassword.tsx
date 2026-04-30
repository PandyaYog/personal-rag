import { useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../../api/client';
import { Mail, AlertCircle, CheckCircle2, ArrowLeft, Brain } from 'lucide-react';
import './Login.css';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        
        if (!email.trim()) {
            setError('Please enter your email address');
            return;
        }

        setLoading(true);
        try {
            await client.post('/auth/forgot-password', { email: email.trim() });
            setSuccess(true);
        } catch (err: any) {
            console.error('Forgot password error:', err);
            const detail = err.response?.data?.detail || 'Something went wrong. Please try again later.';
            setError(detail);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page" data-theme="dark">
            {/* Animated background - consistent with Login/Signup */}
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
                                Recover your<br />
                                <span className="lg-gradient-text">knowledge access</span>
                            </h2>
                        </div>
                    </div>
                </aside>

                <main className="login-right">
                    <div className="login-form-container">
                        <div className="lg-header lg-header-center">
                            <h1 className="lg-title">Forgot Password</h1>
                            <p className="lg-subtitle">
                                {success 
                                    ? "Check your inbox for a reset link" 
                                    : "Enter your email to receive a password reset link"}
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
                                    If an account exists for <strong>{email}</strong>, you will receive an email with instructions to reset your password shortly.
                                </p>
                                <div className="lg-success-actions">
                                    <Link to="/login" className="lg-submit-btn">
                                        Back to Login
                                    </Link>
                                </div>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="lg-form" noValidate aria-busy={loading}>
                                <div className="lg-field">
                                    <label htmlFor="email">Email Address</label>
                                    <div className={`lg-input-wrap ${error ? 'lg-input-invalid' : ''}`}>
                                        <Mail size={17} className="lg-input-icon" aria-hidden="true" />
                                        <input
                                            type="email"
                                            id="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            placeholder="you@example.com"
                                            required
                                            autoComplete="email"
                                        />
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    className="lg-submit-btn"
                                    disabled={loading}
                                    aria-disabled={loading}
                                >
                                    {loading ? (
                                        <><span className="lg-spinner" aria-hidden="true" />Sending Link…</>
                                    ) : (
                                        'Send Reset Link'
                                    )}
                                </button>

                                <Link to="/login" className="lg-back-link">
                                    <ArrowLeft size={16} aria-hidden="true" />
                                    <span>Back to Login</span>
                                </Link>
                            </form>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default ForgotPassword;
