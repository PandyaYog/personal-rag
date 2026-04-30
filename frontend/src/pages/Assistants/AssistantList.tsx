import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import client from '../../api/client';
import { Plus, MessageSquare, Trash2, Edit } from 'lucide-react';
import './Assistants.css';

interface Assistant {
    id: number;
    name: string;
    instructions: string;
    llm_model: string;
    knowledge_base_id: number;
}

const AssistantList = () => {
    const [assistants, setAssistants] = useState<Assistant[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchAssistants();
    }, []);

    const fetchAssistants = async () => {
        try {
            const response = await client.get('/assistants/');
            setAssistants(response.data);
        } catch (err) {
            console.error(err);
            setError('Failed to load assistants');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!window.confirm('Are you sure you want to delete this assistant?')) return;
        try {
            await client.delete(`/assistants/${id}`);
            setAssistants(assistants.filter((a) => a.id !== id));
        } catch (err) {
            console.error(err);
            alert('Failed to delete assistant');
        }
    };

    if (loading) return <div className="loading">Loading...</div>;

    return (
        <div className="page-container">
            <div className="page-header">
                <div>
                    <h1>AI Assistants</h1>
                    <p>Create and manage your AI chat assistants</p>
                </div>
                <Link to="/assistants/create" className="btn btn-primary">
                    <Plus size={20} />
                    Create New
                </Link>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="assistants-grid">
                {assistants.map((assistant) => (
                    <div key={assistant.id} className="assistant-card">
                        <div className="assistant-icon">
                            <MessageSquare size={24} />
                        </div>
                        <div className="assistant-content">
                            <h3>{assistant.name}</h3>
                            <p className="model-badge">{assistant.llm_model}</p>
                            <p className="assistant-desc">{assistant.instructions}</p>
                        </div>
                        <div className="assistant-actions">
                            <Link to={`/chat/${assistant.id}`} className="btn btn-sm btn-outline">
                                Chat
                            </Link>
                            <Link to={`/assistants/${assistant.id}/edit`} className="btn-icon" title="Edit">
                                <Edit size={18} />
                            </Link>
                            <button onClick={() => handleDelete(assistant.id)} className="btn-icon btn-danger" title="Delete">
                                <Trash2 size={18} />
                            </button>
                        </div>
                    </div>
                ))}
                {assistants.length === 0 && !loading && (
                    <div className="empty-state">
                        <MessageSquare size={48} />
                        <h3>No Assistants Found</h3>
                        <p>Create your first AI assistant to start chatting</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AssistantList;
