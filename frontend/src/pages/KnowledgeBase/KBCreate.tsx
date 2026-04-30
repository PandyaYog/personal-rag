import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../../api/client';
import { ArrowLeft } from 'lucide-react';
import './KB.css';

const KBCreate = () => {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await client.post('/knowledgebases/', {
                name,
                description,
            });
            navigate(`/knowledge-bases/${response.data.id}`);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to create knowledge base');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <button
                    onClick={() => navigate(-1)}
                    className="btn-icon"
                    aria-label="Go back"
                >
                    <ArrowLeft size={20} />
                    <span>Back</span>
                </button>
            </div>

            <div className="kb-form-container">
                <h1>Create Knowledge Base</h1>
                <p>Start by giving your knowledge base a name and description.</p>

                {error && <div className="error-message" role="alert">{error}</div>}

                <form onSubmit={handleSubmit} className="kb-form" aria-busy={loading}>
                    <div className="form-group">
                        <label htmlFor="name">Name</label>
                        <input
                            type="text"
                            id="name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="e.g., Company Policies"
                            required
                            aria-required="true"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="description">Description</label>
                        <textarea
                            id="description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="What is this knowledge base about?"
                            rows={4}
                        />
                    </div>

                    <div className="form-actions">
                        <button
                            type="button"
                            onClick={() => navigate(-1)}
                            className="btn btn-outline"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading}
                            aria-disabled={loading}
                        >
                            {loading ? 'Creating...' : 'Create Knowledge Base'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default KBCreate;
