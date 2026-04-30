import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../../api/client';
import { ArrowLeft, Settings, FileText, Pencil } from 'lucide-react';
import KBConfig from './KBConfig';
import KBDocuments from './KBDocuments';
import './KB.css';

interface KnowledgeBase {
    id: string;
    name: string;
    description: string;
    created_at: string;
    updated_at: string | null;
}

type TabKey = 'details' | 'config' | 'documents';

const TABS: { key: TabKey; label: string; icon: typeof Pencil }[] = [
    { key: 'details', label: 'Details', icon: Pencil },
    { key: 'config', label: 'Configuration', icon: Settings },
    { key: 'documents', label: 'Documents', icon: FileText },
];

const KBDetails = () => {
    const { id } = useParams<{ id: string }>();
    const [kb, setKb] = useState<KnowledgeBase | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [activeTab, setActiveTab] = useState<TabKey>('details');
    const navigate = useNavigate();
    const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

    useEffect(() => {
        fetchKB();
    }, [id]);

    const fetchKB = async () => {
        try {
            const response = await client.get(`/knowledgebases/${id}`);
            setKb(response.data);
        } catch (err) {
            console.error(err);
            setError('Failed to load knowledge base details');
        } finally {
            setLoading(false);
        }
    };

    const handleTabKeyDown = (e: React.KeyboardEvent, idx: number) => {
        let next = idx;
        if (e.key === 'ArrowRight') next = (idx + 1) % TABS.length;
        else if (e.key === 'ArrowLeft') next = (idx - 1 + TABS.length) % TABS.length;
        else if (e.key === 'Home') next = 0;
        else if (e.key === 'End') next = TABS.length - 1;
        else return;

        e.preventDefault();
        setActiveTab(TABS[next].key);
        tabRefs.current[next]?.focus();
    };

    if (loading) {
        return (
            <div className="page-container">
                <div className="kb-loading" role="status" aria-live="polite">
                    <div className="kb-loading-spinner" aria-hidden="true" />
                    <span>Loading knowledge base...</span>
                </div>
            </div>
        );
    }
    if (error) return <div className="page-container"><div className="error-message" role="alert">{error}</div></div>;
    if (!kb) return <div className="page-container"><div className="error-message" role="alert">Knowledge Base not found</div></div>;

    return (
        <div className="page-container">
            <div className="page-header">
                <div className="header-left">
                    <button
                        onClick={() => navigate('/knowledge-bases')}
                        className="btn-icon"
                        aria-label="Back to knowledge bases"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1>{kb.name}</h1>
                        <p>{kb.description || 'No description'}</p>
                    </div>
                </div>
            </div>

            <div className="tabs" role="tablist" aria-label="Knowledge base sections">
                {TABS.map((tab, idx) => {
                    const Icon = tab.icon;
                    const selected = activeTab === tab.key;
                    return (
                        <button
                            key={tab.key}
                            ref={(el) => { tabRefs.current[idx] = el; }}
                            role="tab"
                            id={`tab-${tab.key}`}
                            aria-selected={selected}
                            aria-controls={`panel-${tab.key}`}
                            tabIndex={selected ? 0 : -1}
                            className={`tab ${selected ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab.key)}
                            onKeyDown={(e) => handleTabKeyDown(e, idx)}
                        >
                            <Icon size={18} aria-hidden="true" />
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            <div
                className="tab-content"
                role="tabpanel"
                id={`panel-${activeTab}`}
                aria-labelledby={`tab-${activeTab}`}
            >
                {activeTab === 'details' && <KBEdit kb={kb} onUpdate={fetchKB} />}
                {activeTab === 'config' && <KBConfig kb={kb} onUpdate={fetchKB} />}
                {activeTab === 'documents' && <KBDocuments kbId={kb.id} />}
            </div>
        </div>
    );
};

interface KBEditProps {
    kb: KnowledgeBase;
    onUpdate: () => void;
}

const KBEdit = ({ kb, onUpdate }: KBEditProps) => {
    const [name, setName] = useState(kb.name);
    const [description, setDescription] = useState(kb.description || '');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const hasChanges = name !== kb.name || description !== (kb.description || '');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) {
            setError('Name is required');
            return;
        }
        setSaving(true);
        setError('');
        setSuccess('');

        try {
            await client.put(`/knowledgebases/${kb.id}`, {
                name: name.trim(),
                description: description.trim() || null,
            });
            setSuccess('Knowledge base updated successfully');
            onUpdate();
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to update knowledge base');
        } finally {
            setSaving(false);
        }
    };

    const handleReset = () => {
        setName(kb.name);
        setDescription(kb.description || '');
        setError('');
        setSuccess('');
    };

    return (
        <div className="config-container">
            <h2>Edit Details</h2>
            <p>Update your knowledge base name and description.</p>

            {error && <div className="error-message" role="alert">{error}</div>}
            {success && <div className="success-message" role="status">{success}</div>}

            <form onSubmit={handleSubmit} className="kb-form" aria-busy={saving}>
                <div className="form-group">
                    <label htmlFor="kb-name">Name</label>
                    <input
                        type="text"
                        id="kb-name"
                        value={name}
                        onChange={(e) => { setName(e.target.value); setSuccess(''); }}
                        placeholder="Knowledge base name"
                        maxLength={100}
                        required
                        aria-required="true"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="kb-description">Description</label>
                    <textarea
                        id="kb-description"
                        value={description}
                        onChange={(e) => { setDescription(e.target.value); setSuccess(''); }}
                        placeholder="What is this knowledge base about?"
                        rows={4}
                        maxLength={500}
                    />
                </div>

                <div className="form-actions">
                    {hasChanges && (
                        <button type="button" className="btn btn-outline" onClick={handleReset}>
                            Reset
                        </button>
                    )}
                    <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={saving || !hasChanges}
                        aria-disabled={saving || !hasChanges}
                    >
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default KBDetails;
