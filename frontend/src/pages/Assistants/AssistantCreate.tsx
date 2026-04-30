import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import client from '../../api/client';
import { Save, AlertCircle, ChevronDown, ChevronUp, Settings, Database, Sliders, FileText, ArrowLeft } from 'lucide-react';
import './Assistants.css';
import { AssistantCreate as AssistantCreateType, LLMConfig, EmbeddingModelConfig, SearchMethod } from '../../types/assistant';

interface KnowledgeBase {
    id: string;
    name: string;
}

interface ModelsResponse {
    models_embedding: {
        Dense: string[];
        Sparse: string[];
        Multi_vector: string[];
    };
}

const AssistantCreate = () => {
    const { id } = useParams<{ id: string }>();
    const isEditMode = !!id;
    const navigate = useNavigate();

    const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
    const [models, setModels] = useState<ModelsResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [initialLoading, setInitialLoading] = useState(isEditMode);
    const [error, setError] = useState('');
    
    // Collapsible state
    const [showAdvanced, setShowAdvanced] = useState(false);

    // Form State mapped exactly to Pydantic Schema
    const [formData, setFormData] = useState<AssistantCreateType>({
        name: '',
        knowledge_base_ids: [],
        llm_config: {
            provider: 'groq',
            model: 'llama-3.3-70b-versatile',
            temperature: 0.7,
            top_p: 1.0,
            system_prompt: "You are a helpful assistant. Use the provided context to answer the user's query accurately. If the context does not contain the answer, state that you don't have enough information.",
            search_type: 'full_rrf'
        },
        embedding_config: {
            dense: 'BAAI/bge-base-en-v1.5',
            sparse: 'prithivida/Splade_PP_en_v1',
            multi_vector: 'colbert-ir/colbertv2.0'
        }
    });

    useEffect(() => {
        fetchKBs();
        fetchModels();
        if (isEditMode) {
            fetchAssistant();
        }
    }, [id]);

    const fetchModels = async () => {
        try {
            const response = await client.get('/config/models');
            setModels(response.data);
        } catch (err) {
            console.error('Failed to load embedding models', err);
        }
    };

    const fetchKBs = async () => {
        try {
            const response = await client.get('/knowledgebases/');
            setKbs(response.data);
        } catch (err) {
            console.error('Failed to load KBs', err);
        }
    };

    const fetchAssistant = async () => {
        try {
            const response = await client.get(`/assistants/${id}`);
            const data = response.data;
            setFormData({
                name: data.name,
                knowledge_base_ids: data.knowledge_bases.map((kb: any) => kb.id),
                llm_config: data.llm_config,
                embedding_config: data.embedding_config,
            });
        } catch (err) {
            console.error(err);
            setError('Failed to load assistant details');
        } finally {
            setInitialLoading(false);
        }
    };

    // Generic handler for root properties
    const handleRootChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    // Handler for KB multi-select
    const toggleKB = (kbId: string) => {
        setFormData(prev => {
            const ids = prev.knowledge_base_ids;
            if (ids.includes(kbId)) {
                return { ...prev, knowledge_base_ids: ids.filter(id => id !== kbId) };
            } else {
                return { ...prev, knowledge_base_ids: [...ids, kbId] };
            }
        });
    };

    // Handler for nested LLM Config
    const handleLLMChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value, type } = e.target;
        let parsedValue: string | number = value;
        
        if (type === 'range' || type === 'number') {
            parsedValue = parseFloat(value);
        }

        setFormData(prev => ({
            ...prev,
            llm_config: {
                ...prev.llm_config!,
                [name]: parsedValue
            }
        }));
    };

    // Handler for nested Embedding Config
    const handleEmbeddingChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            embedding_config: {
                ...prev.embedding_config!,
                [name]: value
            }
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (formData.knowledge_base_ids.length === 0) {
            setError('Please select at least one Knowledge Base.');
            return;
        }

        setLoading(true);
        setError('');

        try {
            if (isEditMode) {
                await client.put(`/assistants/${id}`, formData);
            } else {
                await client.post('/assistants/', formData);
            }
            navigate('/assistants');
        } catch (err: any) {
            console.error('Failed to save assistant:', err.response?.data || err);
            let errorMsg = 'Failed to save assistant';
            if (err.response?.data?.detail) {
                if (Array.isArray(err.response.data.detail)) {
                    errorMsg = err.response.data.detail.map((e: any) => {
                        const loc = e.loc[e.loc.length - 1];
                        return `${loc}: ${e.msg}`;
                    }).join(', ');
                } else {
                    errorMsg = err.response.data.detail;
                }
            }
            setError(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    if (initialLoading) {
        return <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading configuration...</div>;
    }

    return (
        <div className="ast-form-container">
            <div className="ast-form-header" style={{ position: 'relative' }}>
                <button 
                    type="button"
                    onClick={() => navigate('/assistants')} 
                    style={{ position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                    className="mobile-back-btn"
                >
                    <ArrowLeft size={24} />
                </button>
                <h1>{isEditMode ? 'Edit Assistant' : 'Create Assistant'}</h1>
                <p>Configure knowledge boundaries, retrieval parameters, and personality.</p>
            </div>

            {error && (
                <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', color: '#fca5a5', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <AlertCircle size={20} />
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit}>
                {/* Section 1: Basic Info */}
                <div className="ast-form-section">
                    <div className="ast-form-group">
                        <label className="ast-form-label" htmlFor="name">Assistant Name</label>
                        <input
                            className="ast-input"
                            type="text"
                            id="name"
                            name="name"
                            value={formData.name}
                            onChange={handleRootChange}
                            placeholder="e.g., Codebase Oracle, HR Assistant..."
                            required
                        />
                    </div>
                </div>

                {/* Section 2: Knowledge Bases */}
                <div className="ast-form-section">
                    <div className="ast-form-group">
                        <label className="ast-form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                            <Database size={16} /> Knowledge Sources
                        </label>
                        <span className="ast-form-hint" style={{ marginBottom: '1rem' }}>
                            Select the vector databases this assistant can query during conversation.
                        </span>
                        
                        {kbs.length === 0 ? (
                            <div style={{ padding: '1rem', textAlign: 'center', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', color: '#94a3b8' }}>
                                No Knowledge Bases found. Create one first.
                            </div>
                        ) : (
                            <div className="ast-kb-list">
                                {kbs.map(kb => (
                                    <label key={kb.id} className={`ast-kb-item ${formData.knowledge_base_ids.includes(kb.id) ? 'selected' : ''}`}>
                                        <input
                                            type="checkbox"
                                            className="ast-checkbox"
                                            checked={formData.knowledge_base_ids.includes(kb.id)}
                                            onChange={() => toggleKB(kb.id)}
                                        />
                                        <span style={{ fontSize: '0.9rem', color: '#f8fafc' }}>{kb.name}</span>
                                    </label>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Section 3: Advanced Settings (Collapsible) */}
                <div className="ast-form-section" style={{ paddingBottom: showAdvanced ? '1.5rem' : '0' }}>
                    <div className="ast-advanced-header" onClick={() => setShowAdvanced(!showAdvanced)}>
                        <div className="ast-advanced-title">
                            <Settings size={18} /> Advanced Configuration
                        </div>
                        <div style={{ color: '#818cf8' }}>
                            {showAdvanced ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </div>
                    </div>

                    {showAdvanced && (
                        <div className="ast-advanced-content">
                            {/* System Prompt */}
                            <div className="ast-form-group">
                                <label className="ast-form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                    <FileText size={16} /> System Prompt
                                </label>
                                <textarea
                                    className="ast-textarea"
                                    name="system_prompt"
                                    value={formData.llm_config?.system_prompt}
                                    onChange={handleLLMChange}
                                    placeholder="You are an AI..."
                                />
                                <span className="ast-form-hint">Defines the core personality and constraint rules.</span>
                            </div>

                            {/* LLM & Provider */}
                            <div className="ast-grid-2">
                                <div className="ast-form-group">
                                    <label className="ast-form-label">Provider</label>
                                    <select className="ast-select" name="provider" value={formData.llm_config?.provider} onChange={handleLLMChange}>
                                        <option value="groq">Groq</option>
                                        <option value="openai">OpenAI</option>
                                    </select>
                                </div>
                                <div className="ast-form-group">
                                    <label className="ast-form-label">Model</label>
                                    <select className="ast-select" name="model" value={formData.llm_config?.model} onChange={handleLLMChange}>
                                        {formData.llm_config?.provider === 'groq' ? (
                                            <>
                                                <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
                                                <option value="mixtral-8x7b-32768">mixtral-8x7b-32768</option>
                                            </>
                                        ) : (
                                            <>
                                                <option value="gpt-4o">gpt-4o</option>
                                                <option value="gpt-4-turbo">gpt-4-turbo</option>
                                                <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
                                            </>
                                        )}
                                    </select>
                                </div>
                            </div>

                            {/* Sliders */}
                            <div className="ast-grid-2">
                                <div className="ast-form-group">
                                    <div className="ast-range-header">
                                        <label className="ast-form-label" style={{marginBottom: 0}}>Temperature</label>
                                        <span className="ast-range-val">{formData.llm_config?.temperature.toFixed(2)}</span>
                                    </div>
                                    <input
                                        type="range"
                                        className="ast-range-input"
                                        name="temperature"
                                        min="0"
                                        max="2"
                                        step="0.1"
                                        value={formData.llm_config?.temperature}
                                        onChange={handleLLMChange}
                                    />
                                    <span className="ast-form-hint">Controls randomness. 0 is strict, 2 is maximum creativity.</span>
                                </div>
                                <div className="ast-form-group">
                                    <div className="ast-range-header">
                                        <label className="ast-form-label" style={{marginBottom: 0}}>Top P</label>
                                        <span className="ast-range-val">{formData.llm_config?.top_p.toFixed(2)}</span>
                                    </div>
                                    <input
                                        type="range"
                                        className="ast-range-input"
                                        name="top_p"
                                        min="0"
                                        max="1"
                                        step="0.05"
                                        value={formData.llm_config?.top_p}
                                        onChange={handleLLMChange}
                                    />
                                    <span className="ast-form-hint">Nucleus sampling threshold.</span>
                                </div>
                            </div>

                            <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.05)', margin: '0.5rem 0' }} />

                            {/* Search Method */}
                            <div className="ast-form-group">
                                <label className="ast-form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                    <Sliders size={16} /> Retrieval Search Method
                                </label>
                                <select className="ast-select" name="search_type" value={formData.llm_config?.search_type} onChange={handleLLMChange}>
                                    <option value="dense">Dense (Vector)</option>
                                    <option value="sparse">Sparse (BM25)</option>
                                    <option value="multi_vector">Multi Vector</option>
                                    <option value="hybrid_dense_sparse">Hybrid (Dense + Sparse)</option>
                                    <option value="dense_rerank_multi">Dense + Rerank (Multi)</option>
                                    <option value="sparse_rerank_multi">Sparse + Rerank (Multi)</option>
                                    <option value="rrf">RRF (Dense + Sparse)</option>
                                    <option value="full_rrf">Full RRF (All Vectors)</option>
                                </select>
                                <span className="ast-form-hint">The specific algorithm used to query the vector database.</span>
                            </div>

                            {/* Embedding Models */}
                            <div className="ast-grid-3">
                                <div className="ast-form-group">
                                    <label className="ast-form-label">Dense Model</label>
                                    {models ? (
                                        <select className="ast-select" name="dense" value={formData.embedding_config?.dense} onChange={handleEmbeddingChange}>
                                            {models.models_embedding.Dense.map((m: string) => <option key={m} value={m}>{m}</option>)}
                                        </select>
                                    ) : (
                                        <input className="ast-input" type="text" name="dense" value={formData.embedding_config?.dense} readOnly style={{ opacity: 0.7 }} />
                                    )}
                                </div>
                                <div className="ast-form-group">
                                    <label className="ast-form-label">Sparse Model</label>
                                    {models ? (
                                        <select className="ast-select" name="sparse" value={formData.embedding_config?.sparse} onChange={handleEmbeddingChange}>
                                            {models.models_embedding.Sparse.map((m: string) => <option key={m} value={m}>{m}</option>)}
                                        </select>
                                    ) : (
                                        <input className="ast-input" type="text" name="sparse" value={formData.embedding_config?.sparse} readOnly style={{ opacity: 0.7 }} />
                                    )}
                                </div>
                                <div className="ast-form-group">
                                    <label className="ast-form-label">Multi-Vector Model</label>
                                    {models ? (
                                        <select className="ast-select" name="multi_vector" value={formData.embedding_config?.multi_vector} onChange={handleEmbeddingChange}>
                                            {models.models_embedding.Multi_vector.map((m: string) => <option key={m} value={m}>{m}</option>)}
                                        </select>
                                    ) : (
                                        <input className="ast-input" type="text" name="multi_vector" value={formData.embedding_config?.multi_vector} readOnly style={{ opacity: 0.7 }} />
                                    )}
                                </div>
                            </div>

                        </div>
                    )}
                </div>

                <div className="ast-form-actions">
                    <button type="button" className="ast-btn-outline" onClick={() => navigate('/assistants')}>
                        Cancel
                    </button>
                    <button type="submit" className="ast-btn-primary" disabled={loading}>
                        {loading ? 'Saving...' : (
                            <>
                                <Save size={18} />
                                {isEditMode ? 'Update Assistant' : 'Create Assistant'}
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default AssistantCreate;
