import { Link, useLocation } from 'react-router-dom';
import { Database, MessageSquare, User, LogOut, Brain, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './Sidebar.css';

interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
    const { user, logout } = useAuth();
    const location = useLocation();

    const isActive = (path: string) => location.pathname.startsWith(path);

    const navLinks = [
        { to: '/knowledge-bases', icon: Database, label: 'Knowledge Bases' },
        { to: '/assistants', icon: MessageSquare, label: 'Assistants' },
    ];

    const handleNavClick = () => {
        onClose();
    };

    return (
        <>
            <div
                className={`sb-overlay ${isOpen ? 'sb-overlay-visible' : ''}`}
                onClick={onClose}
                aria-hidden="true"
            />
            <aside className={`sb-sidebar ${isOpen ? 'sb-open' : ''}`}>
                <div className="sb-header">
                    <Link to="/" className="sb-logo" onClick={handleNavClick}>
                        <div className="sb-logo-icon">
                            <Brain size={18} color="#fff" />
                        </div>
                        <span className="sb-logo-text">
                            Personal <span>RAG</span>
                        </span>
                    </Link>
                    <button
                        className="sb-close-btn"
                        onClick={onClose}
                        aria-label="Close sidebar"
                    >
                        <X size={20} />
                    </button>
                </div>

                <nav className="sb-nav" aria-label="Main navigation">
                    {navLinks.map(({ to, icon: Icon, label }) => (
                        <Link
                            key={to}
                            to={to}
                            className={`sb-nav-item ${isActive(to) ? 'sb-active' : ''}`}
                            onClick={handleNavClick}
                        >
                            <Icon size={19} />
                            <span>{label}</span>
                        </Link>
                    ))}
                </nav>

                <div className="sb-footer">
                    <Link
                        to="/profile"
                        className={`sb-nav-item sb-profile-item ${isActive('/profile') ? 'sb-active' : ''}`}
                        onClick={handleNavClick}
                    >
                        <div className="sb-avatar">
                            {user?.full_name?.[0]?.toUpperCase() || user?.username?.[0]?.toUpperCase() || 'U'}
                        </div>
                        <div className="sb-profile-info">
                            <span className="sb-profile-name">
                                {user?.full_name || user?.username || 'User'}
                            </span>
                            <span className="sb-profile-email">{user?.email || ''}</span>
                        </div>
                    </Link>
                    <button onClick={logout} className="sb-nav-item sb-logout-btn">
                        <LogOut size={18} />
                        <span>Logout</span>
                    </button>
                </div>
            </aside>
        </>
    );
};

export default Sidebar;
