import { useEffect, useState, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import client from '../../api/client';
import { CheckCircle2, XCircle, Loader2, ArrowRight, ShieldCheck, Brain } from 'lucide-react';
import './Login.css';

type Status = 'loading' | 'success' | 'already' | 'error';

const ConfirmEmail = () => {
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token');

    const [status, setStatus] = useState<Status>('loading');
    const [message, setMessage] = useState('');
    const headingRef = useRef<HTMLHeadingElement>(null);

    useEffect(() => {
        if (!token) {
            setStatus('error');
            setMessage('No verification token found. Please check your email link.');
            return;
        }

        let cancelled = false;

        const verify = async () => {
            try {
                const res = await client.get('/auth/confirm-email', { params: { token } });
                if (cancelled) return;
                
                const msg: string = res.data?.message ?? '';
                if (msg.toLowerCase().includes('already verified')) {
                    setStatus('already');
                    setMessage('Your email has already been verified.');
                } else {
                    setStatus('success');
                    setMessage('Your email has been verified successfully.');
                }
            } catch (err: any) {
                if (cancelled) return;
                const detail: string = err.response?.data?.detail || 'Verification failed. The link may be invalid or expired.';
                setStatus('error');
                setMessage(detail);
            }
        };

        verify();
        return () => { cancelled = true; };
    }, [token]);

    useEffect(() => {
        if (status !== 'loading' && headingRef.current) {
            headingRef.current.focus();
        }
    }, [status]);

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
                {/* Left panel — branding */}
                <aside className="login-left">
                    <div className="login-left-content">
                        <div className="lg-logo">
                            <div className="lg-logo-icon"><Brain size={22} color="#fff" /></div>
                            <span className="lg-logo-text">Personal <span>RAG</span></span>
                        </div>
                        <div className="login-left-center">
                            <h2 className="login-left-tagline">
                                Verify your<br />
                                <span className="lg-gradient-text">account access</span>
                            </h2>
                        </div>
                    </div>
                </aside>

                {/* Right panel — status */}
                <main className="login-right">
                    <div className="login-form-container">
                        <div className="lg-header lg-header-center">
                            <h1 className="lg-title">Email Verification</h1>
                            <p className="lg-subtitle">
                                {status === 'loading' ? 'Confirming your identity...' : 'Status of your verification request'}
                            </p>
                        </div>

                        <div className="lg-success-state">
                            {status === 'loading' && (
                                <>
                                    <div className="lg-success-icon-wrap" style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent-1)' }}>
                                        <Loader2 size={36} className="lg-spinner" />
                                    </div>
                                    <p className="lg-success-text">Verifying your email address, please wait...</p>
                                </>
                            )}

                            {status === 'success' && (
                                <>
                                    <div className="lg-success-icon-wrap">
                                        <CheckCircle2 size={48} className="lg-success-icon lg-res-icon" />
                                    </div>
                                    <h2 className="lg-field-label" ref={headingRef} tabIndex={-1} style={{ fontSize: '1.2rem', fontWeight: 700 }}>Verification Successful!</h2>
                                    <p className="lg-success-text">{message}</p>
                                    <div className="lg-success-actions">
                                        <Link to="/login" className="lg-submit-btn">
                                            Continue to Login
                                            <ArrowRight size={18} />
                                        </Link>
                                    </div>
                                </>
                            )}

                            {status === 'already' && (
                                <>
                                    <div className="lg-success-icon-wrap" style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent-1)' }}>
                                        <ShieldCheck size={48} className="lg-res-icon" />
                                    </div>
                                    <h2 className="lg-field-label" ref={headingRef} tabIndex={-1} style={{ fontSize: '1.2rem', fontWeight: 700 }}>Already Verified</h2>
                                    <p className="lg-success-text">{message}</p>
                                    <div className="lg-success-actions">
                                        <Link to="/login" className="lg-submit-btn">
                                            Go to Sign In
                                            <ArrowRight size={18} />
                                        </Link>
                                    </div>
                                </>
                            )}

                            {status === 'error' && (
                                <>
                                    <div className="lg-success-icon-wrap" style={{ background: 'rgba(248, 113, 113, 0.1)', color: '#f87171' }}>
                                        <XCircle size={48} className="lg-res-icon" />
                                    </div>
                                    <h2 className="lg-field-label" ref={headingRef} tabIndex={-1} style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f87171' }}>Verification Failed</h2>
                                    <p className="lg-success-text">{message}</p>
                                    <div className="lg-success-actions" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                        <Link to="/signup" className="lg-submit-btn" style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)' }}>
                                            Back to Sign Up
                                        </Link>
                                        <Link to="/login" className="lg-back-link" style={{ marginTop: 0 }}>
                                            Go to Sign In
                                        </Link>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
};

export default ConfirmEmail;
