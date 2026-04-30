import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Pencil, AlertTriangle, Play, FileText, HardDrive, Activity } from 'lucide-react';
import client from '../../api/client';
import './DocumentDetails.css';

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

interface Chunk {
  id: string;
  doc_id: string;
  chunk_num: number;
  chunk_content: string;
}

const DocumentDetails = () => {
  const { kbId, docId } = useParams<{ kbId: string; docId: string }>();
  const navigate = useNavigate();
  const [doc, setDoc] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Editing state
  const [editingName, setEditingName] = useState(false);
  const [editNameValue, setEditNameValue] = useState('');
  const editInputRef = useRef<HTMLInputElement>(null);

  // Processing state
  const [processing, setProcessing] = useState(false);

  const [docContent, setDocContent] = useState<string | null>(null);
  const [docBlobUrl, setDocBlobUrl] = useState<string | null>(null);
  const [docLoading, setDocLoading] = useState(false);
  const [docContentError, setDocContentError] = useState('');

  // Chunks state
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [chunksLoading, setChunksLoading] = useState(true);
  const [chunksError, setChunksError] = useState('');

  // Add Chunk state
  const [isAddingChunk, setIsAddingChunk] = useState(false);
  const [newChunkContent, setNewChunkContent] = useState('');
  const [isSubmittingChunk, setIsSubmittingChunk] = useState(false);
  const [chunkAddError, setChunkAddError] = useState('');

  // Testing Interface state
  type LeftPanelTab = 'chunks' | 'testing';
  const [activeLeftTab, setActiveLeftTab] = useState<LeftPanelTab>('chunks');
  const [testQuery, setTestQuery] = useState('');
  const [testSearchType, setTestSearchType] = useState('full_rrf');
  const [testResults, setTestResults] = useState<any[]>([]);
  const [isTesting, setIsTesting] = useState(false);
  const [testError, setTestError] = useState('');

  useEffect(() => {
    fetchDocument();
    fetchChunks();
    
    // Cleanup blob URL on unmount
    return () => {
      if (docBlobUrl) {
        URL.revokeObjectURL(docBlobUrl);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kbId, docId]);

  useEffect(() => {
    if (editingName && editInputRef.current) {
      editInputRef.current.focus();
    }
  }, [editingName]);

  // Smart Polling: Automatically refresh if the document is processing or pending
  useEffect(() => {
    if (!doc) return;

    const isTransient = doc.processing_status === 'PROCESSING' || doc.processing_status === 'PENDING';

    if (!isTransient) return;

    const timer = setTimeout(async () => {
      try {
        const response = await client.get(`/knowledgebases/${kbId}/documents/${docId}`);
        const updatedDoc = response.data;
        
        // If it just finished, fetch chunks to show the new data
        if (updatedDoc.processing_status === 'COMPLETED' && doc.processing_status !== 'COMPLETED') {
          fetchChunks();
        }
        
        setDoc(updatedDoc);
      } catch (err) {
        console.error('Polling failed', err);
      }
    }, 3000);

    return () => clearTimeout(timer);
  }, [doc, kbId, docId]);

  const fetchDocumentContent = async (documentData: Document) => {
    try {
      setDocLoading(true);
      setDocContentError('');
      
      const response = await client.get(
        `/knowledgebases/${kbId}/documents/${docId}/download`,
        { responseType: 'blob' }
      );
      
      let blob = response.data;
      const ext = documentData.file_extension.toLowerCase().replace(/^\./, '');
      
      // Force PDF MIME type to ensure the browser previews it inline instead of downloading
      if (ext === 'pdf') {
        blob = new Blob([blob], { type: 'application/pdf' });
      }

      const url = URL.createObjectURL(blob);
      setDocBlobUrl(url);

      const textExtensions = ['txt', 'md', 'csv', 'json', 'log', 'yaml', 'yml', 'py', 'js', 'ts', 'css', 'html'];
      
      if (textExtensions.includes(ext)) {
        const text = await blob.text();
        setDocContent(text);
      }
    } catch (err: any) {
      console.error('Failed to load document content', err);
      setDocContentError('Failed to load document content for viewing.');
    } finally {
      setDocLoading(false);
    }
  };

  const fetchChunks = async () => {
    try {
      setChunksLoading(true);
      setChunksError('');
      const response = await client.get(`/knowledgebases/${kbId}/documents/${docId}/chunks`);
      // Sort chunks by chunk_num for correct ordering
      const sortedChunks = response.data.sort((a: Chunk, b: Chunk) => a.chunk_num - b.chunk_num);
      setChunks(sortedChunks);
    } catch (err: any) {
      console.error('Failed to load chunks', err);
      setChunksError('Failed to load document chunks.');
    } finally {
      setChunksLoading(false);
    }
  };

  const fetchDocument = async (skipLoadingState = false) => {
    try {
      if (!skipLoadingState) {
        setLoading(true);
        setError('');
      }
      const response = await client.get(`/knowledgebases/${kbId}/documents/${docId}`);
      setDoc(response.data);
      setEditNameValue(response.data.name);
      
      // Fetch content only on initial load or full refresh
      if (!skipLoadingState) {
        fetchDocumentContent(response.data);
      }
    } catch (err: any) {
      console.error('Failed to load document details', err);
      if (!skipLoadingState) {
        setError(err.response?.data?.detail || 'Failed to load document details.');
      }
    } finally {
      if (!skipLoadingState) {
        setLoading(false);
      }
    }
  };

  const goBack = () => {
    navigate(`/knowledge-bases/${kbId}`);
  };

  const startEditing = () => {
    setEditNameValue(doc?.name || '');
    setEditingName(true);
  };

  const handleRename = async () => {
    if (!doc) return;
    const trimmed = editNameValue.trim();
    if (!trimmed || trimmed === doc.name) {
      setEditingName(false);
      return;
    }
    
    try {
      await client.put(`/knowledgebases/${kbId}/documents/${docId}`, { name: trimmed });
      setDoc({ ...doc, name: trimmed });
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to rename document.');
      setEditNameValue(doc.name); // Reset on error
    } finally {
      setEditingName(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleRename();
    } else if (e.key === 'Escape') {
      setEditingName(false);
      setEditNameValue(doc?.name || '');
    }
  };

  const handleProcess = async () => {
    try {
      setProcessing(true);
      await client.post(`/knowledgebases/${kbId}/documents/${docId}/process`);
      // Refresh to see updated status
      await fetchDocument();
      await fetchChunks();
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to start processing.');
    } finally {
      setProcessing(false);
    }
  };

  const handleAddChunk = async () => {
    if (!newChunkContent.trim()) return;
    
    try {
      setIsSubmittingChunk(true);
      setChunkAddError('');
      
      await client.post(`/knowledgebases/${kbId}/documents/${docId}/chunks`, {
        content: newChunkContent.trim()
      });
      
      setNewChunkContent('');
      setIsAddingChunk(false);
      await fetchChunks(); // Refresh chunks
      
    } catch (err: any) {
      console.error('Failed to add chunk', err);
      setChunkAddError(err.response?.data?.detail || 'Failed to add chunk.');
    } finally {
      setIsSubmittingChunk(false);
    }
  };

  const handleTestRetrieval = async () => {
    if (!testQuery.trim() || !doc) return;
    
    try {
      setIsTesting(true);
      setTestError('');
      setTestResults([]);
      
      const payload = {
        query: testQuery.trim(),
        search_type: testSearchType,
        knowledge_base_ids: [kbId]
      };
      
      const response = await client.post('/testing/retrieval', payload);
      
      // The API returns retrieved_chunks for the entire KB. Filter for this document only.
      const docHits = response.data.retrieved_chunks.filter(
        (c: any) => c.source_document_name === doc.name
      );
      
      // Sort hits by score descending, safely handling undefined scores
      const sortedHits = docHits.sort((a: any, b: any) => (b.retrieval_score || 0) - (a.retrieval_score || 0));
      setTestResults(sortedHits);
    } catch (err: any) {
      console.error('Testing retrieval failed', err);
      setTestError(err.response?.data?.detail || 'Retrieval test failed.');
    } finally {
      setIsTesting(false);
    }
  };

  const needsParsing = doc && (doc.num_chunks === 0 || doc.processing_status.toLowerCase() === 'failed');

  return (
    <div className="doc-page" data-theme="dark">
      {/* Animated Background */}
      <div className="doc-bg" aria-hidden="true">
        <div className="doc-orb doc-orb-1" />
        <div className="doc-orb doc-orb-2" />
        <div className="doc-orb doc-orb-3" />
        <div className="doc-grid-overlay" />
      </div>

      <div className="doc-content-wrapper">
        {/* Header Section */}
        <header className="doc-header">
          <button onClick={goBack} className="doc-back-btn" aria-label="Back to Knowledge Base">
            <ArrowLeft size={20} />
            <span>Back to KB</span>
          </button>
        </header>

        {/* Content Area */}
        <main className="doc-main">
          {loading ? (
            <div className="doc-loading">
              <div className="doc-spinner" />
              <p>Loading document details...</p>
            </div>
          ) : error ? (
            <div className="doc-error-card">
              <p>{error}</p>
              <button onClick={fetchDocument} className="doc-retry-btn">Retry</button>
            </div>
          ) : doc ? (
            <div className="doc-layout">
              {/* Document Metadata Panel */}
              <div className="doc-metadata-panel">
                <div className="doc-metadata-header">
                  <div className="doc-title-group">
                    {editingName ? (
                      <input
                        ref={editInputRef}
                        type="text"
                        className="doc-name-input"
                        value={editNameValue}
                        onChange={(e) => setEditNameValue(e.target.value)}
                        onBlur={handleRename}
                        onKeyDown={handleKeyDown}
                        maxLength={255}
                        aria-label="Rename document"
                      />
                    ) : (
                      <>
                        <h1 className="doc-title" title={doc.name}>{doc.name}</h1>
                        <button 
                          className="doc-edit-btn" 
                          onClick={startEditing}
                          aria-label="Rename document"
                          title="Rename Document"
                        >
                          <Pencil size={16} />
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* Status Pills */}
                <div className="doc-pills">
                  <div className="doc-pill" title="File Extension">
                    <FileText size={14} />
                    <span>{doc.file_extension.toUpperCase()}</span>
                  </div>
                  <div className="doc-pill" title="File Size">
                    <HardDrive size={14} />
                    <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                  </div>
                  <div className={`doc-pill status-${doc.processing_status.toLowerCase()}`} title="Processing Status">
                    <Activity size={14} />
                    <span>{doc.processing_status}</span>
                  </div>
                </div>

                {/* Unparsed CTA Warning */}
                {needsParsing && (
                  <div className="doc-warning-banner">
                    <div className="doc-warning-content">
                      <AlertTriangle size={24} className="doc-warning-icon" />
                      <div>
                        <h3>Document Not Parsed</h3>
                        <p>This document has not been chunked into the vector database yet. It cannot be retrieved by assistants.</p>
                      </div>
                    </div>
                    <button 
                      className="doc-btn-primary" 
                      onClick={handleProcess}
                      disabled={processing}
                    >
                      {processing ? (
                        <>
                          <div className="doc-spinner-small" />
                          <span>Processing...</span>
                        </>
                      ) : (
                        <>
                          <Play size={18} />
                          <span>Trigger Parsing</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>

              {/* Main Layout: Split Screen */}
              <div className="doc-split-layout">
                {/* Left Panel: Chunks & Testing Placeholder */}
                <div className="doc-left-panel">
                  <div className="doc-panel-tabs">
                    <button 
                      className={`doc-panel-tab ${activeLeftTab === 'chunks' ? 'active' : ''}`}
                      onClick={() => setActiveLeftTab('chunks')}
                    >
                      Document Chunks
                    </button>
                    <button 
                      className={`doc-panel-tab ${activeLeftTab === 'testing' ? 'active' : ''}`}
                      onClick={() => setActiveLeftTab('testing')}
                    >
                      Test Retrieval
                    </button>
                  </div>

                  {activeLeftTab === 'chunks' && (
                    <>
                      <div className="doc-viewer-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h3>Chunks ({chunks.length})</h3>
                        <button 
                          className="doc-btn-primary" 
                          style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                          onClick={() => {
                            setIsAddingChunk(!isAddingChunk);
                            setChunkAddError('');
                          }}
                        >
                          {isAddingChunk ? 'Cancel' : '+ Add Chunk'}
                        </button>
                      </div>
                      
                      {isAddingChunk && (
                        <div className="doc-add-chunk-form">
                          <h4>Add New Chunk</h4>
                          {chunkAddError && (
                            <div className="doc-error-card" style={{ padding: '0.75rem', marginBottom: '1rem', fontSize: '0.85rem' }}>
                              {chunkAddError}
                            </div>
                          )}
                          <textarea
                            value={newChunkContent}
                            onChange={(e) => setNewChunkContent(e.target.value)}
                            placeholder="Enter the raw text content for this new chunk..."
                            rows={4}
                            className="doc-textarea"
                          />
                          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.75rem' }}>
                            <button 
                              className="doc-btn-primary"
                              onClick={handleAddChunk}
                              disabled={isSubmittingChunk || !newChunkContent.trim()}
                            >
                              {isSubmittingChunk ? (
                                <>
                                  <div className="doc-spinner-small" />
                                  <span>Adding...</span>
                                </>
                              ) : (
                                'Save Chunk'
                              )}
                            </button>
                          </div>
                        </div>
                      )}

                      <div className="doc-viewer-body">
                        {chunksLoading ? (
                          <div className="doc-loading">
                            <div className="doc-spinner-small" />
                            <span>Loading chunks...</span>
                          </div>
                        ) : chunksError ? (
                          <div className="doc-error-card">
                            <p>{chunksError}</p>
                            <button onClick={fetchChunks} className="doc-retry-btn">Retry Chunks</button>
                          </div>
                        ) : chunks.length === 0 ? (
                          <div className="doc-unsupported">
                            <FileText size={48} />
                            <p>This document has not been parsed yet.</p>
                          </div>
                        ) : (
                          <div className="doc-chunks-list">
                            {chunks.map(chunk => (
                              <div key={chunk.id} className="doc-chunk-card">
                                <div className="doc-chunk-header">
                                  <span className="doc-chunk-num">Chunk #{chunk.chunk_num}</span>
                                  <div className="doc-chunk-meta">
                                    <span className="doc-chunk-id" title={chunk.id}>
                                      ID: {chunk.id.substring(0, 8)}...
                                    </span>
                                    <span className="doc-chunk-size">{chunk.chunk_content.length} chars</span>
                                  </div>
                                </div>
                                <div className="doc-chunk-content">
                                  {chunk.chunk_content}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </>
                  )}

                  {activeLeftTab === 'testing' && (
                    <div className="doc-testing-container">
                      <div className="doc-testing-controls">
                        <div className="doc-testing-search-bar">
                           <input 
                             type="text" 
                             className="doc-test-input" 
                             placeholder="Enter test query..." 
                             value={testQuery}
                             onChange={(e) => setTestQuery(e.target.value)}
                             onKeyDown={(e) => e.key === 'Enter' && handleTestRetrieval()}
                           />
                           <select 
                             className="doc-test-select"
                             value={testSearchType}
                             onChange={(e) => setTestSearchType(e.target.value)}
                           >
                             <option value="dense">Dense (Vector)</option>
                             <option value="sparse">Sparse (BM25)</option>
                             <option value="multi_vector">Multi Vector</option>
                             <option value="hybrid_dense_sparse">Hybrid (Dense + Sparse)</option>
                             <option value="dense_rerank_multi">Dense + Rerank (Multi)</option>
                             <option value="sparse_rerank_multi">Sparse + Rerank (Multi)</option>
                             <option value="rrf">RRF (Dense + Sparse)</option>
                             <option value="full_rrf">Full RRF (All Vectors)</option>
                           </select>
                           <button 
                             className="doc-btn-primary"
                             onClick={handleTestRetrieval}
                             disabled={isTesting || !testQuery.trim()}
                           >
                             {isTesting ? <div className="doc-spinner-small"/> : 'Test'}
                           </button>
                        </div>
                        {testError && <div className="doc-error-card" style={{padding: '0.75rem', marginTop: '1rem', fontSize: '0.85rem'}}>{testError}</div>}
                      </div>

                      <div className="doc-viewer-body" style={{borderTop: '1px solid rgba(255,255,255,0.05)'}}>
                        {isTesting ? (
                           <div className="doc-loading">
                             <div className="doc-spinner-small" />
                             <span>Running retrieval test...</span>
                           </div>
                        ) : testResults.length > 0 ? (
                           <div className="doc-chunks-list">
                             <p style={{fontSize: '0.85rem', color: '#94a3b8', margin: '0 0 0.5rem 0', padding: '0 0.5rem'}}>
                               Found {testResults.length} relevant chunk(s) in this document.
                             </p>
                             {testResults.map((hit: any, idx: number) => (
                               <div key={hit.chunk_id} className="doc-chunk-card">
                                 <div className="doc-chunk-header" style={{background: 'rgba(99, 102, 241, 0.1)'}}>
                                   <span className="doc-chunk-num">Hit #{idx + 1}</span>
                                   <div className="doc-chunk-meta">
                                     <span className="doc-chunk-id" title={hit.chunk_id}>
                                       ID: {hit.chunk_id.substring(0, 8)}...
                                     </span>
                                     <span className="doc-chunk-size" style={{color: '#818cf8', fontWeight: 600}}>
                                       Score: {hit.retrieval_score != null ? Number(hit.retrieval_score).toFixed(4) : "N/A"}
                                     </span>
                                   </div>
                                 </div>
                                 <div className="doc-chunk-content">
                                   {hit.content}
                                 </div>
                               </div>
                             ))}
                           </div>
                        ) : testQuery && !isTesting ? (
                           <div className="doc-unsupported">
                             <FileText size={48} />
                             <p>No relevant chunks found in this document for the given query.</p>
                           </div>
                        ) : (
                           <div className="doc-unsupported">
                             <p>Enter a query above to test retrieval against this document's chunks.</p>
                           </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Right Panel: Document Viewer */}
                <div className="doc-right-panel">
                  <div className="doc-viewer-header">
                    <h3>Document Viewer</h3>
                  </div>
                  <div className="doc-viewer-body">
                    {docLoading ? (
                      <div className="doc-loading">
                        <div className="doc-spinner-small" />
                        <span>Loading document...</span>
                      </div>
                    ) : docContentError ? (
                      <div className="doc-error-card">
                        <p>{docContentError}</p>
                        <button onClick={() => fetchDocumentContent(doc)} className="doc-retry-btn">Retry Content</button>
                      </div>
                    ) : docBlobUrl ? (
                      doc.file_extension.toLowerCase().replace(/^\./, '') === 'pdf' ? (
                        <object 
                          data={docBlobUrl} 
                          type="application/pdf"
                          className="doc-pdf-viewer"
                        >
                          <div className="doc-unsupported">
                            <FileText size={48} />
                            <p>Your browser does not support inline PDF viewing.</p>
                            <a href={docBlobUrl} download={doc.name} className="doc-btn-primary">
                              Download PDF
                            </a>
                          </div>
                        </object>
                      ) : docContent !== null ? (
                        <pre className="doc-text-viewer">{docContent}</pre>
                      ) : (
                        <div className="doc-unsupported">
                          <FileText size={48} />
                          <p>Preview not supported for this file type.</p>
                          <a href={docBlobUrl} download={doc.name} className="doc-btn-primary">
                            Download File
                          </a>
                        </div>
                      )
                    ) : null}
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </main>
      </div>
    </div>
  );
};

export default DocumentDetails;
