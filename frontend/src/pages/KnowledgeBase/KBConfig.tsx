import { useState, useEffect } from 'react';
import client from '../../api/client';
import { Save, AlertCircle, HelpCircle } from 'lucide-react';
import Select, { SelectOption } from '../../components/UI/Select';
import KBTestChunking from './KBTestChunking';

export type StrategyName = 'fixed_size' | 'sentence_based' | 'semantic_based' |
    'sliding_window' | 'token_based' | 'hybrid' | 'recursive';

interface ChunkingStrategy {
    strategy: StrategyName;
    parameters: Record<string, any>;
}

interface EmbeddingModelConfig {
    dense: string;
    sparse: string;
    multi_vector: string;
}

interface ConfigFormState {
    chunking_strategy: ChunkingStrategy;
    embedding_model: EmbeddingModelConfig;
}

interface ModelsResponse {
    models_embedding: {
        Dense: string[];
        Sparse: string[];
        Multi_vector: string[];
    };
    models_semantic_splitting: {
        sentence_transformers: string[];
        fastembed: string[];
    };
    models_token_splitting: {
        TIKTOKEN_MODELS: Record<string, string>;
        HUGGINGFACE_MODELS: Record<string, string>;
    };
}

const STRATEGY_DEFAULTS: Record<StrategyName, Record<string, any>> = {
    fixed_size: { chunk_size: 1000, chunk_overlap: 100 },
    sentence_based: { max_chunk_size: 1024 },
    semantic_based: { embedding_model: 'all-MiniLM-L6-v2', backend: 'sentence_transformers', breakpoint_percentile: 90, buffer_size: 1 },
    sliding_window: { window_size: 1000, step_size: 500, unit: 'char' },
    token_based: { token_size: 500, token_overlap: 50, model_name: 'cl100k_base', tokenizer_backend: 'tiktoken' },
    recursive: { chunk_size: 1000, chunk_overlap: 100, separators: ['\n\n', '\n', '. ', ' ', ''] },
    hybrid: { embedding_model: 'all-MiniLM-L6-v2', backend: 'sentence_transformers', breakpoint_percentile: 90, buffer_size: 1, token_size: 512, token_overlap: 50, model_name: 'cl100k_base', tokenizer_backend: 'tiktoken' },
};

export const STRATEGY_INFO: Record<StrategyName, { label: string; description: string }> = {
    fixed_size: { label: 'Fixed Size', description: 'Splits text into chunks of a fixed character length with configurable overlap.' },
    sentence_based: { label: 'Sentence Based', description: 'Splits text along sentence boundaries, optionally capping chunk size.' },
    semantic_based: { label: 'Semantic', description: 'Uses an embedding model to detect topic shifts and split at semantic boundaries.' },
    sliding_window: { label: 'Sliding Window', description: 'Moves a window of fixed size across the text with a configurable step size.' },
    token_based: { label: 'Token Based', description: 'Splits text based on token count using a specific tokenizer model.' },
    recursive: { label: 'Recursive', description: 'Recursively splits text using a hierarchy of separators, from paragraphs down to characters.' },
    hybrid: { label: 'Hybrid', description: 'Combines semantic splitting with token-based fallback for robust chunking.' },
};

const PARAM_HELP: Record<string, string> = {
    chunk_size: 'Maximum number of characters per chunk.',
    chunk_overlap: 'Number of overlapping characters between consecutive chunks.',
    max_chunk_size: 'Maximum chunk size in characters. Leave empty for no limit.',
    embedding_model: 'Model used to compute embeddings for semantic boundary detection.',
    backend: 'Library used to run the embedding model.',
    breakpoint_percentile: 'Percentile threshold (0–100) for detecting semantic breakpoints. Higher = fewer, larger chunks.',
    buffer_size: 'Number of sentences to include as context buffer around each split point.',
    window_size: 'Size of the sliding window in the selected unit.',
    step_size: 'Number of units to advance the window each step. Smaller = more overlap.',
    unit: 'Unit of measurement for window and step size.',
    token_size: 'Maximum number of tokens per chunk.',
    token_overlap: 'Number of overlapping tokens between consecutive chunks.',
    model_name: 'Tokenizer model used to count tokens.',
    tokenizer_backend: 'Backend library for the tokenizer.',
    separators: 'Ordered list of separators to try when splitting. One per line.',
    dense: 'Model for dense vector embeddings.',
    sparse: 'Model for sparse vector embeddings (SPLADE).',
    multi_vector: 'Model for multi-vector embeddings (ColBERT).',
};

const FieldLabel = ({ htmlFor, text, helpKey }: { htmlFor: string; text: string; helpKey?: string }) => (
    <label htmlFor={htmlFor} className="label-with-help">
        <span>{text}</span>
        {helpKey && PARAM_HELP[helpKey] && (
            <HelpCircle size={14} title={PARAM_HELP[helpKey]} aria-label={PARAM_HELP[helpKey]} />
        )}
    </label>
);

const separatorsToText = (seps: string[]): string =>
    seps.map(s => s.replace(/\n/g, '\\n')).join('\n');

export const textToSeparators = (text: string): string[] =>
    text.split('\n').map(s => s.replace(/\\n/g, '\n'));

interface KBConfigProps {
    kb: any;
    onUpdate: () => void;
}

const KBConfig = ({ kb, onUpdate }: KBConfigProps) => {
    const [formData, setFormData] = useState<ConfigFormState | null>(null);
    const [models, setModels] = useState<ModelsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        Promise.all([
            client.get('/config/models'),
            client.get(`/knowledgebases/${kb.id}/config`),
        ]).then(([modelsRes, configRes]) => {
            setModels(modelsRes.data);
            setFormData({
                chunking_strategy: configRes.data.chunking_strategy,
                embedding_model: configRes.data.embedding_model,
            });
        }).catch((err) => {
            console.error(err);
            setError('Failed to load configuration');
        }).finally(() => setLoading(false));
    }, [kb.id]);

    if (loading || !formData || !models) {
        return (
            <div className="kb-loading" role="status" aria-live="polite">
                <div className="kb-loading-spinner" aria-hidden="true" />
                <span>Loading configuration...</span>
            </div>
        );
    }

    const strategy = formData.chunking_strategy.strategy;
    const params = formData.chunking_strategy.parameters;

    const updateParam = (key: string, value: any) => {
        setFormData(prev => ({
            ...prev!,
            chunking_strategy: {
                ...prev!.chunking_strategy,
                parameters: { ...prev!.chunking_strategy.parameters, [key]: value },
            },
        }));
        setSuccess('');
    };

    const updateEmbedding = (type: 'dense' | 'sparse' | 'multi_vector', value: string) => {
        setFormData(prev => ({
            ...prev!,
            embedding_model: { ...prev!.embedding_model, [type]: value },
        }));
        setSuccess('');
    };

    const handleStrategyChange = (newStrategy: StrategyName) => {
        setFormData(prev => ({
            ...prev!,
            chunking_strategy: {
                strategy: newStrategy,
                parameters: { ...STRATEGY_DEFAULTS[newStrategy] },
            },
        }));
        setSuccess('');
    };

    const handleSemanticModelChange = (compoundValue: string) => {
        const [backend, model] = compoundValue.split('::');
        setFormData(prev => ({
            ...prev!,
            chunking_strategy: {
                ...prev!.chunking_strategy,
                parameters: { ...prev!.chunking_strategy.parameters, embedding_model: model, backend },
            },
        }));
        setSuccess('');
    };

    const handleTokenModelChange = (compoundValue: string) => {
        const [backend, model] = compoundValue.split('::');
        setFormData(prev => ({
            ...prev!,
            chunking_strategy: {
                ...prev!.chunking_strategy,
                parameters: { ...prev!.chunking_strategy.parameters, model_name: model, tokenizer_backend: backend },
            },
        }));
        setSuccess('');
    };

    const getSemanticCompoundValue = (p: Record<string, any>) =>
        `${p.backend || 'sentence_transformers'}::${p.embedding_model || ''}`;

    const getTokenCompoundValue = (p: Record<string, any>) =>
        `${p.tokenizer_backend || 'tiktoken'}::${p.model_name || ''}`;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setError('');
        setSuccess('');

        const payload: any = {
            chunking_strategy: { ...formData.chunking_strategy },
            embedding_model: { ...formData.embedding_model },
        };

        if (strategy === 'recursive') {
            const sepsText = params.separators;
            payload.chunking_strategy.parameters = {
                ...params,
                separators: Array.isArray(sepsText) ? sepsText : textToSeparators(sepsText),
            };
        }

        if (strategy === 'sentence_based' && params.max_chunk_size === '') {
            payload.chunking_strategy.parameters = { ...params, max_chunk_size: null };
        }

        try {
            await client.put(`/knowledgebases/${kb.id}/config`, payload);
            setSuccess('Configuration saved successfully');
            onUpdate();
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to save configuration');
        } finally {
            setSaving(false);
        }
    };

    const semanticModelOptions: SelectOption[] = [
        ...models.models_semantic_splitting.sentence_transformers.map(m => ({
            value: `sentence_transformers::${m}`, label: m, group: 'Sentence Transformers',
        })),
        ...models.models_semantic_splitting.fastembed.map(m => ({
            value: `fastembed::${m}`, label: m, group: 'FastEmbed',
        })),
    ];

    const renderSemanticFields = (prefix?: string) => {
        const p = params;
        return (
            <>
                <div className="form-group">
                    <FieldLabel htmlFor={`${prefix || ''}sem-model`} text="Embedding Model" helpKey="embedding_model" />
                    <Select
                        id={`${prefix || ''}sem-model`}
                        value={getSemanticCompoundValue(p)}
                        options={semanticModelOptions}
                        onChange={handleSemanticModelChange}
                    />
                </div>
                <div className="config-param-row">
                    <div className="form-group">
                        <FieldLabel htmlFor={`${prefix || ''}bp`} text="Breakpoint Percentile" helpKey="breakpoint_percentile" />
                        <input
                            type="number"
                            id={`${prefix || ''}bp`}
                            value={p.breakpoint_percentile ?? 90}
                            onChange={(e) => updateParam('breakpoint_percentile', parseInt(e.target.value) || 0)}
                            min={0}
                            max={100}
                        />
                    </div>
                    <div className="form-group">
                        <FieldLabel htmlFor={`${prefix || ''}buf`} text="Buffer Size" helpKey="buffer_size" />
                        <input
                            type="number"
                            id={`${prefix || ''}buf`}
                            value={p.buffer_size ?? 1}
                            onChange={(e) => updateParam('buffer_size', parseInt(e.target.value) || 0)}
                            min={0}
                        />
                    </div>
                </div>
            </>
        );
    };

    const tokenModelOptions: SelectOption[] = [
        ...Object.entries(models.models_token_splitting.TIKTOKEN_MODELS).map(([key, val]) => ({
            value: `tiktoken::${val}`, label: key, group: 'Tiktoken',
        })),
        ...Object.entries(models.models_token_splitting.HUGGINGFACE_MODELS).map(([key, val]) => ({
            value: `huggingface::${val}`, label: key, group: 'HuggingFace',
        })),
    ];

    const renderTokenFields = (prefix?: string) => {
        const p = params;
        return (
            <>
                <div className="form-group">
                    <FieldLabel htmlFor={`${prefix || ''}tok-model`} text="Tokenizer Model" helpKey="model_name" />
                    <Select
                        id={`${prefix || ''}tok-model`}
                        value={getTokenCompoundValue(p)}
                        options={tokenModelOptions}
                        onChange={handleTokenModelChange}
                    />
                </div>
                <div className="config-param-row">
                    <div className="form-group">
                        <FieldLabel htmlFor={`${prefix || ''}tsize`} text="Token Size" helpKey="token_size" />
                        <input
                            type="number"
                            id={`${prefix || ''}tsize`}
                            value={p.token_size ?? 500}
                            onChange={(e) => updateParam('token_size', parseInt(e.target.value) || 0)}
                            min={1}
                        />
                    </div>
                    <div className="form-group">
                        <FieldLabel htmlFor={`${prefix || ''}toverlap`} text="Token Overlap" helpKey="token_overlap" />
                        <input
                            type="number"
                            id={`${prefix || ''}toverlap`}
                            value={p.token_overlap ?? 50}
                            onChange={(e) => updateParam('token_overlap', parseInt(e.target.value) || 0)}
                            min={0}
                        />
                    </div>
                </div>
            </>
        );
    };

    const renderStrategyParams = () => {
        switch (strategy) {
            case 'fixed_size':
                return (
                    <div className="config-param-row">
                        <div className="form-group">
                            <FieldLabel htmlFor="chunk_size" text="Chunk Size" helpKey="chunk_size" />
                            <input
                                type="number"
                                id="chunk_size"
                                value={params.chunk_size ?? 1000}
                                onChange={(e) => updateParam('chunk_size', parseInt(e.target.value) || 0)}
                                min={1}
                            />
                        </div>
                        <div className="form-group">
                            <FieldLabel htmlFor="chunk_overlap" text="Chunk Overlap" helpKey="chunk_overlap" />
                            <input
                                type="number"
                                id="chunk_overlap"
                                value={params.chunk_overlap ?? 100}
                                onChange={(e) => updateParam('chunk_overlap', parseInt(e.target.value) || 0)}
                                min={0}
                            />
                        </div>
                    </div>
                );

            case 'sentence_based':
                return (
                    <div className="form-group">
                        <FieldLabel htmlFor="max_chunk_size" text="Max Chunk Size" helpKey="max_chunk_size" />
                        <input
                            type="number"
                            id="max_chunk_size"
                            value={params.max_chunk_size ?? ''}
                            onChange={(e) => updateParam('max_chunk_size', e.target.value === '' ? '' : parseInt(e.target.value) || 0)}
                            min={1}
                            placeholder="Leave empty for no limit"
                        />
                    </div>
                );

            case 'semantic_based':
                return renderSemanticFields();

            case 'sliding_window':
                return (
                    <>
                        <div className="config-param-row">
                            <div className="form-group">
                                <FieldLabel htmlFor="window_size" text="Window Size" helpKey="window_size" />
                                <input
                                    type="number"
                                    id="window_size"
                                    value={params.window_size ?? 1000}
                                    onChange={(e) => updateParam('window_size', parseInt(e.target.value) || 0)}
                                    min={1}
                                />
                            </div>
                            <div className="form-group">
                                <FieldLabel htmlFor="step_size" text="Step Size" helpKey="step_size" />
                                <input
                                    type="number"
                                    id="step_size"
                                    value={params.step_size ?? 500}
                                    onChange={(e) => updateParam('step_size', parseInt(e.target.value) || 0)}
                                    min={1}
                                />
                            </div>
                        </div>
                        <div className="form-group">
                            <FieldLabel htmlFor="unit" text="Unit" helpKey="unit" />
                            <Select
                                id="unit"
                                value={params.unit ?? 'char'}
                                options={[
                                    { value: 'char', label: 'Character' },
                                    { value: 'word', label: 'Word' },
                                    { value: 'sentence', label: 'Sentence' },
                                ]}
                                onChange={(v) => updateParam('unit', v)}
                            />
                        </div>
                    </>
                );

            case 'token_based':
                return renderTokenFields();

            case 'recursive':
                return (
                    <>
                        <div className="config-param-row">
                            <div className="form-group">
                                <FieldLabel htmlFor="r_chunk_size" text="Chunk Size" helpKey="chunk_size" />
                                <input
                                    type="number"
                                    id="r_chunk_size"
                                    value={params.chunk_size ?? 1000}
                                    onChange={(e) => updateParam('chunk_size', parseInt(e.target.value) || 0)}
                                    min={1}
                                />
                            </div>
                            <div className="form-group">
                                <FieldLabel htmlFor="r_chunk_overlap" text="Chunk Overlap" helpKey="chunk_overlap" />
                                <input
                                    type="number"
                                    id="r_chunk_overlap"
                                    value={params.chunk_overlap ?? 100}
                                    onChange={(e) => updateParam('chunk_overlap', parseInt(e.target.value) || 0)}
                                    min={0}
                                />
                            </div>
                        </div>
                        <div className="form-group">
                            <FieldLabel htmlFor="separators" text="Separators" helpKey="separators" />
                            <textarea
                                id="separators"
                                value={Array.isArray(params.separators) ? separatorsToText(params.separators) : (params.separators ?? '')}
                                onChange={(e) => updateParam('separators', e.target.value)}
                                rows={5}
                                placeholder={'\\n\\n\n\\n\n. \n \n(empty line for empty string)'}
                            />
                        </div>
                    </>
                );

            case 'hybrid':
                return (
                    <>
                        <fieldset className="config-fieldset">
                            <legend>Semantic Parameters</legend>
                            {renderSemanticFields('h-')}
                        </fieldset>
                        <fieldset className="config-fieldset">
                            <legend>Token Parameters</legend>
                            {renderTokenFields('h-')}
                        </fieldset>
                    </>
                );

            default:
                return null;
        }
    };

    return (
        <div className="config-container">
            {error && (
                <div className="error-message" role="alert">
                    <AlertCircle size={16} aria-hidden="true" />
                    {error}
                </div>
            )}
            {success && <div className="success-message" role="status">{success}</div>}

            <form onSubmit={handleSubmit} className="kb-form" aria-busy={saving}>
                <div className="config-section">
                    <h3 className="config-section-title">
                        Chunking Strategy
                        <HelpCircle size={15} title="Controls how your documents are split into smaller pieces for retrieval." />
                    </h3>

                    <div className="form-group">
                        <FieldLabel htmlFor="strategy" text="Strategy" />
                        <Select
                            id="strategy"
                            value={strategy}
                            options={(Object.keys(STRATEGY_INFO) as StrategyName[]).map(key => ({
                                value: key, label: STRATEGY_INFO[key].label,
                            }))}
                            onChange={(v) => handleStrategyChange(v as StrategyName)}
                        />
                    </div>

                    <p className="strategy-description">{STRATEGY_INFO[strategy].description}</p>

                    <div className="config-params">
                        {renderStrategyParams()}
                    </div>
                </div>

                <div className="config-section">
                    <h3 className="config-section-title">
                        Embedding Models
                        <HelpCircle size={15} title="Models used to convert text chunks into vector representations for search." />
                    </h3>

                    <div className="config-params">
                        <div className="form-group">
                            <FieldLabel htmlFor="emb-dense" text="Dense Model" helpKey="dense" />
                            <Select
                                id="emb-dense"
                                value={formData.embedding_model.dense}
                                options={models.models_embedding.Dense.map(m => ({ value: m, label: m }))}
                                onChange={(v) => updateEmbedding('dense', v)}
                            />
                        </div>

                        <div className="form-group">
                            <FieldLabel htmlFor="emb-sparse" text="Sparse Model" helpKey="sparse" />
                            <Select
                                id="emb-sparse"
                                value={formData.embedding_model.sparse}
                                options={models.models_embedding.Sparse.map(m => ({ value: m, label: m }))}
                                onChange={(v) => updateEmbedding('sparse', v)}
                            />
                        </div>

                        <div className="form-group">
                            <FieldLabel htmlFor="emb-multi" text="Multi-Vector Model" helpKey="multi_vector" />
                            <Select
                                id="emb-multi"
                                value={formData.embedding_model.multi_vector}
                                options={models.models_embedding.Multi_vector.map(m => ({ value: m, label: m }))}
                                onChange={(v) => updateEmbedding('multi_vector', v)}
                            />
                        </div>
                    </div>
                </div>

                <div className="form-actions">
                    <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={saving}
                        aria-disabled={saving}
                    >
                        <Save size={18} aria-hidden="true" />
                        {saving ? 'Saving...' : 'Save Configuration'}
                    </button>
                </div>
            </form>

            <KBTestChunking
                strategy={formData.chunking_strategy.strategy}
                parameters={formData.chunking_strategy.parameters}
            />
        </div>
    );
};

export default KBConfig;
