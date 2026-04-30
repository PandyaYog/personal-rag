import { useState, useEffect, useRef } from 'react';
import client from '../../api/client';
import { FlaskConical, Play, ChevronDown } from 'lucide-react';
import { StrategyName, STRATEGY_INFO, textToSeparators } from './KBConfig';

interface TestResult {
    total_chunks: number;
    avg_chunk_length_chars: number;
    avg_chunk_length_tokens: number;
    chunks: string[];
}

interface KBTestChunkingProps {
    strategy: StrategyName;
    parameters: Record<string, any>;
}

const KBTestChunking = ({ strategy, parameters }: KBTestChunkingProps) => {
    const [collapsed, setCollapsed] = useState(true);
    const [testText, setTestText] = useState('');
    const [testing, setTesting] = useState(false);
    const [result, setResult] = useState<TestResult | null>(null);
    const [error, setError] = useState('');
    const strategyRef = useRef(strategy);
    const paramsRef = useRef(parameters);

    useEffect(() => {
        if (strategyRef.current !== strategy || paramsRef.current !== parameters) {
            strategyRef.current = strategy;
            paramsRef.current = parameters;
            setResult(null);
            setError('');
        }
    }, [strategy, parameters]);

    const handleRunTest = async () => {
        if (!testText.trim()) return;
        setTesting(true);
        setError('');
        setResult(null);

        let normalizedParams = { ...parameters };
        if (strategy === 'recursive' && !Array.isArray(normalizedParams.separators)) {
            normalizedParams.separators = textToSeparators(normalizedParams.separators);
        }
        if (strategy === 'sentence_based' && normalizedParams.max_chunk_size === '') {
            normalizedParams.max_chunk_size = null;
        }

        try {
            const response = await client.post('/testing/chunking', {
                text_content: testText,
                strategy,
                parameters: normalizedParams,
            });
            setResult(response.data);
        } catch (err: any) {
            console.error(err);
            const detail = err.response?.data?.detail;
            setError(typeof detail === 'string' ? detail : 'Chunking test failed');
        } finally {
            setTesting(false);
        }
    };

    return (
        <div className="test-chunking-section">
            <button
                type="button"
                className="test-chunking-header"
                onClick={() => setCollapsed(prev => !prev)}
                aria-expanded={!collapsed}
            >
                <FlaskConical size={18} className="test-icon" aria-hidden="true" />
                <h3>Test Chunking</h3>
                <ChevronDown
                    size={16}
                    className={`test-chunking-chevron ${collapsed ? '' : 'expanded'}`}
                    aria-hidden="true"
                />
            </button>

            {!collapsed && (
                <div className="test-chunking-body">
                    <p className="test-strategy-label">
                        Test how <strong>{STRATEGY_INFO[strategy].label}</strong> will chunk your text
                    </p>

                    <div className="form-group">
                        <label htmlFor="test-text">Sample Text</label>
                        <textarea
                            id="test-text"
                            className="test-textarea"
                            value={testText}
                            onChange={(e) => setTestText(e.target.value)}
                            rows={6}
                            placeholder="Paste sample text here to test chunking..."
                            aria-required="true"
                        />
                    </div>

                    <div className="test-actions">
                        <button
                            type="button"
                            className="btn btn-primary"
                            onClick={handleRunTest}
                            disabled={!testText.trim() || testing}
                            aria-disabled={!testText.trim() || testing}
                        >
                            <Play size={16} aria-hidden="true" />
                            {testing ? 'Testing...' : 'Run Test'}
                        </button>
                    </div>

                    {error && <div className="error-message" role="alert">{error}</div>}

                    {result && (
                        <div className="test-results" aria-live="polite" role="status">
                            <div className="test-stats-row">
                                <div className="test-stat-card">
                                    <div className="test-stat-value">{result.total_chunks}</div>
                                    <div className="test-stat-label">Total Chunks</div>
                                </div>
                                <div className="test-stat-card">
                                    <div className="test-stat-value">
                                        {Math.round(result.avg_chunk_length_chars)}
                                    </div>
                                    <div className="test-stat-label">Avg Chars</div>
                                </div>
                                <div className="test-stat-card">
                                    <div className="test-stat-value">
                                        {Math.round(result.avg_chunk_length_tokens)}
                                    </div>
                                    <div className="test-stat-label">Avg Tokens</div>
                                </div>
                            </div>

                            <div className="test-chunks-list">
                                {result.chunks.map((chunk, i) => (
                                    <div key={i} className="test-chunk-card">
                                        <span className="test-chunk-index">#{i + 1}</span>
                                        <pre className="test-chunk-text">{chunk}</pre>
                                        <div className="test-chunk-meta">{chunk.length} chars</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default KBTestChunking;
