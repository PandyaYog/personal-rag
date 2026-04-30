import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import client from '../../api/client';
import { Upload, FileText, Trash2, RefreshCw, Search, Download, Pencil } from 'lucide-react';
import ConfirmModal from '../../components/UI/ConfirmModal';

interface Document {
    id: string;
    name: string;
    file_extension: string;
    file_size: number;
    created_at: string;
    num_chunks: number;
    processing_status: string;
    is_active: boolean;
}

interface KBDocumentsProps {
    kbId: string;
}

const KBDocuments = ({ kbId }: KBDocumentsProps) => {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [search, setSearch] = useState('');
    const [deleteTarget, setDeleteTarget] = useState<Document | null>(null);
    const [deleting, setDeleting] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editName, setEditName] = useState('');
    const [dragOver, setDragOver] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const editInputRef = useRef<HTMLInputElement>(null);
    const dragCounter = useRef(0);

    useEffect(() => {
        fetchDocuments();
    }, [kbId]);

    useEffect(() => {
        if (editingId && editInputRef.current) {
            editInputRef.current.focus();
            editInputRef.current.select();
        }
    }, [editingId]);

    // Smart Polling: Automatically refresh if any document is processing or pending
    useEffect(() => {
        const needsPolling = documents.some(
            (doc) => doc.processing_status === 'PROCESSING' || doc.processing_status === 'PENDING'
        );

        if (!needsPolling) return;

        const timer = setTimeout(() => {
            fetchDocuments();
        }, 3000);

        return () => clearTimeout(timer);
    }, [documents]);

    const fetchDocuments = async () => {
        try {
            const response = await client.get(`/knowledgebases/${kbId}/documents?limit=100`);
            setDocuments(response.data);
        } catch (err) {
            console.error('Failed to fetch documents', err);
            setError('Failed to load documents');
        } finally {
            setLoading(false);
        }
    };

    const uploadFile = async (file: File) => {
        setUploading(true);
        setError('');
        setSuccess('');
        const formData = new FormData();
        formData.append('file', file);

        try {
            await client.post(`/knowledgebases/${kbId}/documents/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setSuccess(`"${file.name}" uploaded successfully`);
            fetchDocuments();
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to upload document');
        } finally {
            setUploading(false);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return;
        await uploadFile(e.target.files[0]);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const handleDelete = async () => {
        if (!deleteTarget) return;
        setDeleting(true);
        try {
            await client.delete(`/knowledgebases/${kbId}/documents/${deleteTarget.id}`);
            setDocuments(documents.filter((d) => d.id !== deleteTarget.id));
            setSuccess(`"${deleteTarget.name}" deleted`);
            setDeleteTarget(null);
        } catch (err) {
            console.error(err);
            setError('Failed to delete document');
            setDeleteTarget(null);
        } finally {
            setDeleting(false);
        }
    };

    const handleReprocess = async (doc: Document) => {
        setError('');
        setSuccess('');
        try {
            await client.post(`/knowledgebases/${kbId}/documents/${doc.id}/process`);
            setSuccess(`Reprocessing "${doc.name}" started`);
            fetchDocuments();
        } catch (err) {
            console.error(err);
            setError('Failed to reprocess document');
        }
    };

    const handleToggleActive = async (doc: Document) => {
        try {
            await client.put(`/knowledgebases/${kbId}/documents/${doc.id}`, {
                is_active: !doc.is_active,
            });
            setDocuments(prev =>
                prev.map(d => d.id === doc.id ? { ...d, is_active: !d.is_active } : d)
            );
        } catch (err) {
            console.error(err);
            setError('Failed to update document status');
        }
    };

    const handleDownload = async (doc: Document) => {
        try {
            const response = await client.get(
                `/knowledgebases/${kbId}/documents/${doc.id}/download`,
                { responseType: 'blob' }
            );
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const a = document.createElement('a');
            a.href = url;
            a.download = doc.name;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error(err);
            setError('Failed to download document');
        }
    };

    const startEditing = (doc: Document) => {
        setEditingId(doc.id);
        setEditName(doc.name);
    };

    const cancelEditing = () => {
        setEditingId(null);
        setEditName('');
    };

    const saveRename = async (doc: Document) => {
        const trimmed = editName.trim();
        if (!trimmed || trimmed === doc.name) {
            cancelEditing();
            return;
        }
        try {
            await client.put(`/knowledgebases/${kbId}/documents/${doc.id}`, { name: trimmed });
            setDocuments(prev =>
                prev.map(d => d.id === doc.id ? { ...d, name: trimmed } : d)
            );
            setSuccess(`Renamed to "${trimmed}"`);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to rename document');
        } finally {
            cancelEditing();
        }
    };

    const handleEditKeyDown = (e: React.KeyboardEvent, doc: Document) => {
        if (e.key === 'Enter') saveRename(doc);
        else if (e.key === 'Escape') cancelEditing();
    };

    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        dragCounter.current++;
        if (dragCounter.current === 1) setDragOver(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        dragCounter.current--;
        if (dragCounter.current === 0) setDragOver(false);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
    };

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        dragCounter.current = 0;
        setDragOver(false);
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            await uploadFile(files[0]);
        }
    };

    const filtered = search
        ? documents.filter(d => d.name.toLowerCase().includes(search.toLowerCase()))
        : documents;

    if (loading) {
        return (
            <div className="kb-loading" role="status" aria-live="polite">
                <div className="kb-loading-spinner" aria-hidden="true" />
                <span>Loading documents...</span>
            </div>
        );
    }

    return (
        <div
            className={`documents-container ${dragOver ? 'doc-drop-active' : ''}`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
        >
            <div className="documents-header">
                <h2>Documents</h2>
                <label className="btn btn-primary doc-upload-label">
                    <Upload size={18} aria-hidden="true" />
                    {uploading ? 'Uploading...' : 'Upload Document'}
                    <input
                        ref={fileInputRef}
                        type="file"
                        onChange={handleFileUpload}
                        disabled={uploading}
                        className="sr-only"
                        aria-label="Choose file to upload"
                    />
                </label>
            </div>

            {documents.length > 0 && (
                <div className="doc-search-wrap">
                    <Search size={16} className="doc-search-icon" aria-hidden="true" />
                    <input
                        type="search"
                        className="doc-search-input"
                        placeholder="Search documents..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        aria-label="Search documents"
                    />
                    {search && (
                        <span className="sr-only" aria-live="polite">
                            {filtered.length} document{filtered.length !== 1 ? 's' : ''} found
                        </span>
                    )}
                </div>
            )}

            {error && <div className="error-message" role="alert">{error}</div>}
            {success && <div className="success-message" role="status">{success}</div>}

            {dragOver && (
                <div className="doc-drop-overlay" aria-hidden="true">
                    <Upload size={32} />
                    <span>Drop file to upload</span>
                </div>
            )}

            <div className="documents-list">
                {documents.length === 0 ? (
                    <div className="empty-state">
                        <FileText size={48} aria-hidden="true" />
                        <h3>No Documents</h3>
                        <p>Drag & drop files here to upload</p>
                    </div>
                ) : (
                    <div className="doc-table-wrap" role="region" aria-label="Documents table">
                        <table className="documents-table">
                            <thead>
                                <tr>
                                    <th scope="col">Name</th>
                                    <th scope="col">Type</th>
                                    <th scope="col">Size</th>
                                    <th scope="col">Chunks</th>
                                    <th scope="col">Status</th>
                                    <th scope="col">Active</th>
                                    <th scope="col">Uploaded</th>
                                    <th scope="col"><span className="sr-only">Actions</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map((doc) => (
                                    <tr key={doc.id} className={!doc.is_active ? 'doc-row-inactive' : ''}>
                                        <td className="doc-name-cell">
                                            {editingId === doc.id ? (
                                                <input
                                                    ref={editInputRef}
                                                    type="text"
                                                    className="doc-name-input"
                                                    value={editName}
                                                    onChange={(e) => setEditName(e.target.value)}
                                                    onBlur={() => saveRename(doc)}
                                                    onKeyDown={(e) => handleEditKeyDown(e, doc)}
                                                    maxLength={255}
                                                    aria-label="Rename document"
                                                />
                                            ) : (
                                                <div className="doc-name-row">
                                                    <Link
                                                        to={`/knowledge-bases/${kbId}/documents/${doc.id}`}
                                                        className="doc-name-link"
                                                    >
                                                        {doc.name}
                                                    </Link>
                                                    <button
                                                        className="doc-rename-btn"
                                                        onClick={() => startEditing(doc)}
                                                        aria-label={`Rename ${doc.name}`}
                                                        title="Rename"
                                                    >
                                                        <Pencil size={13} />
                                                    </button>
                                                </div>
                                            )}
                                        </td>
                                        <td>{doc.file_extension}</td>
                                        <td>{(doc.file_size / 1024).toFixed(1)} KB</td>
                                        <td>{doc.num_chunks}</td>
                                        <td>
                                            <span className={`status-badge ${doc.processing_status.toLowerCase()}`}>
                                                {doc.processing_status}
                                            </span>
                                        </td>
                                        <td>
                                            <label className="toggle-switch" title={doc.is_active ? 'Active' : 'Inactive'}>
                                                <input
                                                    type="checkbox"
                                                    role="switch"
                                                    checked={doc.is_active}
                                                    onChange={() => handleToggleActive(doc)}
                                                    aria-label={`${doc.is_active ? 'Disable' : 'Enable'} ${doc.name}`}
                                                />
                                                <span className="toggle-track" />
                                            </label>
                                        </td>
                                        <td>
                                            <time dateTime={doc.created_at}>
                                                {new Date(doc.created_at).toLocaleDateString()}
                                            </time>
                                        </td>
                                        <td>
                                            <div className="action-buttons">
                                                <button
                                                    onClick={() => handleDownload(doc)}
                                                    className="btn-icon"
                                                    aria-label={`Download ${doc.name}`}
                                                    title="Download"
                                                >
                                                    <Download size={18} />
                                                </button>
                                                <button
                                                    onClick={() => handleReprocess(doc)}
                                                    className="btn-icon"
                                                    aria-label={`Reprocess ${doc.name}`}
                                                    title="Reprocess"
                                                >
                                                    <RefreshCw size={18} />
                                                </button>
                                                <button
                                                    onClick={() => setDeleteTarget(doc)}
                                                    className="btn-icon btn-danger"
                                                    aria-label={`Delete ${doc.name}`}
                                                    title="Delete"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            <ConfirmModal
                open={!!deleteTarget}
                title="Delete Document"
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

export default KBDocuments;
