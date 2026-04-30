import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import client from '../../api/client';
import { Plus, Search, Database, Trash2, ChevronRight, Calendar, AlertCircle } from 'lucide-react';
import ConfirmModal from '../../components/UI/ConfirmModal';
import './KB.css';

interface KnowledgeBase {
    id: number;
    name: string;
    description: string;
    created_at: string;
    updated_at: string;
}

const KBList = () => {
    const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [deleteTarget, setDeleteTarget] = useState<KnowledgeBase | null>(null);
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        fetchKBs();
    }, []);

    const fetchKBs = async () => {
        try {
            const response = await client.get('/knowledgebases/');
            setKbs(response.data);
        } catch (err) {
            console.error(err);
            setError('Failed to load knowledge bases');
        } finally {
            setLoading(false);
        }
    };

    const openDeleteModal = (e: React.MouseEvent, kb: KnowledgeBase) => {
        e.preventDefault();
        e.stopPropagation();
        setDeleteTarget(kb);
    };

    const handleDelete = async () => {
        if (!deleteTarget) return;
        setDeleting(true);
        try {
            await client.delete(`/knowledgebases/${deleteTarget.id}`);
            setKbs(kbs.filter((kb) => kb.id !== deleteTarget.id));
            setDeleteTarget(null);
        } catch (err) {
            console.error(err);
            setError('Failed to delete knowledge base');
            setDeleteTarget(null);
        } finally {
            setDeleting(false);
        }
    };

    const filteredKBs = kbs.filter((kb) =>
        kb.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <div className="kb-page">
                <div className="kb-loading" role="status" aria-live="polite">
                    <div className="kb-loading-spinner" aria-hidden="true" />
                    <span>Loading knowledge bases...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="kb-page">
            <div className="kb-page-header">
                <div className="kb-page-header-left">
                    <h1 className="kb-page-title">Knowledge Bases</h1>
                    <p className="kb-page-subtitle">Manage your document collections</p>
                </div>
                <Link to="/knowledge-bases/create" className="kb-create-btn">
                    <Plus size={18} aria-hidden="true" />
                    <span>Create New</span>
                </Link>
            </div>

            <div className="kb-search-wrap">
                <Search size={17} className="kb-search-icon" aria-hidden="true" />
                <input
                    type="search"
                    className="kb-search-input"
                    placeholder="Search knowledge bases..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    aria-label="Search knowledge bases"
                />
            </div>

            {searchQuery && (
                <div className="sr-only" aria-live="polite" role="status">
                    {filteredKBs.length} result{filteredKBs.length !== 1 ? 's' : ''} found
                </div>
            )}

            {error && (
                <div className="kb-error-banner" role="alert" aria-live="assertive">
                    <AlertCircle size={16} aria-hidden="true" />
                    <span>{error}</span>
                </div>
            )}

            {filteredKBs.length > 0 ? (
                <div className="kb-grid" role="list" aria-label="Knowledge bases">
                    {filteredKBs.map((kb) => (
                        <div key={kb.id} className="kb-card" role="listitem">
                            <div className="kb-card-header">
                                <div className="kb-card-icon" aria-hidden="true">
                                    <Database size={20} />
                                </div>
                                <button
                                    onClick={(e) => openDeleteModal(e, kb)}
                                    className="kb-card-delete"
                                    aria-label={`Delete ${kb.name}`}
                                    title="Delete"
                                >
                                    <Trash2 size={15} />
                                </button>
                            </div>
                            <Link
                                to={`/knowledge-bases/${kb.id}`}
                                className="kb-card-link"
                                aria-label={`Open ${kb.name}`}
                            >
                                <div className="kb-card-body">
                                    <h3 className="kb-card-name">{kb.name}</h3>
                                    <p className="kb-card-desc">
                                        {kb.description || 'No description provided'}
                                    </p>
                                </div>
                                <div className="kb-card-footer">
                                    <span className="kb-card-date">
                                        <Calendar size={13} aria-hidden="true" />
                                        <time dateTime={kb.created_at}>
                                            {new Date(kb.created_at).toLocaleDateString()}
                                        </time>
                                    </span>
                                    <span className="kb-card-arrow" aria-hidden="true">
                                        <ChevronRight size={16} />
                                    </span>
                                </div>
                            </Link>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="kb-empty" role="status">
                    <div className="kb-empty-icon" aria-hidden="true">
                        <Database size={40} />
                    </div>
                    <h3 className="kb-empty-title">
                        {searchQuery ? 'No matching knowledge bases' : 'No Knowledge Bases Yet'}
                    </h3>
                    <p className="kb-empty-text">
                        {searchQuery
                            ? 'Try adjusting your search terms'
                            : 'Create your first knowledge base to get started'}
                    </p>
                    {!searchQuery && (
                        <Link to="/knowledge-bases/create" className="kb-create-btn kb-empty-btn">
                            <Plus size={18} aria-hidden="true" />
                            <span>Create Knowledge Base</span>
                        </Link>
                    )}
                </div>
            )}

            <ConfirmModal
                open={!!deleteTarget}
                title="Delete Knowledge Base"
                message={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
                confirmLabel="Delete"
                variant="danger"
                loading={deleting}
                onConfirm={handleDelete}
                onCancel={() => setDeleteTarget(null)}
            />
        </div>
    );
};

export default KBList;
