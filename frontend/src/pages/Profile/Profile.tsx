import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import client from '../../api/client';
import { User, Mail, Lock, Save, AlertCircle } from 'lucide-react';
import './Profile.css';

const Profile = () => {
    const { user, fetchUser } = useAuth();
    const [formData, setFormData] = useState({
        full_name: user?.full_name || '',
        email: user?.email || '',
    });
    const [passwordData, setPasswordData] = useState({
        current_password: '',
        new_password: '',
        confirm_password: '',
    });
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    const handleInfoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.id]: e.target.value });
    };

    const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setPasswordData({ ...passwordData, [e.target.id]: e.target.value });
    };

    const updateProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage({ type: '', text: '' });

        try {
            await client.put('/users/me', formData);
            await fetchUser();
            setMessage({ type: 'success', text: 'Profile updated successfully' });
        } catch (err: any) {
            console.error(err);
            setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to update profile' });
        } finally {
            setLoading(false);
        }
    };

    const updatePassword = async (e: React.FormEvent) => {
        e.preventDefault();
        if (passwordData.new_password !== passwordData.confirm_password) {
            setMessage({ type: 'error', text: 'New passwords do not match' });
            return;
        }

        setLoading(true);
        setMessage({ type: '', text: '' });

        try {
            await client.put('/users/me/change-password', {
                current_password: passwordData.current_password,
                new_password: passwordData.new_password,
            });
            setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
            setMessage({ type: 'success', text: 'Password changed successfully' });
        } catch (err: any) {
            console.error(err);
            setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to change password' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1>Profile Settings</h1>
            </div>

            {message.text && (
                <div className={`message-banner ${message.type}`}>
                    {message.type === 'error' && <AlertCircle size={20} />}
                    {message.text}
                </div>
            )}

            <div className="profile-grid">
                <div className="profile-card">
                    <div className="card-header">
                        <User size={24} />
                        <h2>Personal Information</h2>
                    </div>
                    <form onSubmit={updateProfile} className="profile-form">
                        <div className="form-group">
                            <label htmlFor="full_name">Full Name</label>
                            <input
                                type="text"
                                id="full_name"
                                value={formData.full_name}
                                onChange={handleInfoChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="email">Email</label>
                            <div className="input-wrapper">
                                <Mail size={18} className="input-icon" />
                                <input
                                    type="email"
                                    id="email"
                                    value={formData.email}
                                    onChange={handleInfoChange}
                                    disabled // Email change might require verification flow
                                />
                            </div>
                            <small className="form-hint">Email cannot be changed directly.</small>
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            <Save size={18} style={{ marginRight: '0.5rem' }} />
                            Save Changes
                        </button>
                    </form>
                </div>

                <div className="profile-card">
                    <div className="card-header">
                        <Lock size={24} />
                        <h2>Change Password</h2>
                    </div>
                    <form onSubmit={updatePassword} className="profile-form">
                        <div className="form-group">
                            <label htmlFor="current_password">Current Password</label>
                            <input
                                type="password"
                                id="current_password"
                                value={passwordData.current_password}
                                onChange={handlePasswordChange}
                                required
                            />
                            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.25rem' }}>
                                <Link 
                                    to="/forgot-password" 
                                    style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textDecoration: 'none' }}
                                >
                                    Forgot current password?
                                </Link>
                            </div>
                        </div>
                        <div className="form-group">
                            <label htmlFor="new_password">New Password</label>
                            <input
                                type="password"
                                id="new_password"
                                value={passwordData.new_password}
                                onChange={handlePasswordChange}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="confirm_password">Confirm New Password</label>
                            <input
                                type="password"
                                id="confirm_password"
                                value={passwordData.confirm_password}
                                onChange={handlePasswordChange}
                                required
                            />
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            Update Password
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Profile;
