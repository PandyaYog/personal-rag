import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../../api/client';
import { Send, ArrowLeft, User, Bot, ThumbsUp, ThumbsDown, RefreshCw, FileText } from 'lucide-react';
import './Chat.css';
import { Message, ChatWithHistory } from '../../types/chat';

const ChatPage = () => {
    const { assistantId, chatId } = useParams<{ assistantId: string, chatId: string }>();
    const navigate = useNavigate();

    const [chatDetails, setChatDetails] = useState<ChatWithHistory | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [loadingHistory, setLoadingHistory] = useState(true);
    const [regeneratingId, setRegeneratingId] = useState<string | null>(null);
    
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (assistantId && chatId) {
            fetchChatHistory();
        }
    }, [assistantId, chatId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages, loading]);

    const fetchChatHistory = async () => {
        try {
            setLoadingHistory(true);
            const response = await client.get(`/assistants/${assistantId}/chats/${chatId}`);
            const data: ChatWithHistory = response.data;
            setChatDetails(data);
            setMessages(data.messages || []);
        } catch (err) {
            console.error('Failed to load chat history:', err);
        } finally {
            setLoadingHistory(false);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const queryText = input.trim();
        setInput('');
        
        // Optimistic UI for user message
        const optimisticUserMessage: Message = {
            id: `temp-${Date.now()}`,
            role: 'user',
            text: queryText,
            content: { versions: [{ text: queryText }] },
            is_good: null,
            created_at: new Date().toISOString()
        };
        setMessages(prev => [...prev, optimisticUserMessage]);
        setLoading(true);

        try {
            const response = await client.post(`/assistants/${assistantId}/chats/${chatId}/query`, { query: queryText });
            const assistantMessage: Message = response.data;
            
            // To ensure we get the real user message ID back (since query endpoint usually returns the latest message or we need to re-fetch)
            // If the endpoint only returns the assistant's message, we might want to just fetch chat history again to sync
            // For now, we'll append the assistant message. Wait, ideally we fetch history to get both DB IDs safely.
            await fetchChatHistory(); 
            
        } catch (err: any) {
            console.error('Error sending query:', err);
            // Append a temporary error message
            const errMsg = err.response?.data?.detail || 'Sorry, I encountered an error while processing your request.';
            setMessages(prev => [...prev, {
                id: `err-${Date.now()}`,
                role: 'assistant',
                text: typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg),
                content: { versions: [{ text: 'Error' }] },
                is_good: null,
                created_at: new Date().toISOString()
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleFeedback = async (messageId: string, isGood: boolean) => {
        try {
            // Optimistic update
            setMessages(prev => prev.map(msg => 
                msg.id === messageId ? { ...msg, is_good: isGood } : msg
            ));
            await client.post(`/chats/${chatId}/messages/${messageId}/feedback`, { is_good: isGood });
        } catch (err) {
            console.error('Failed to submit feedback:', err);
            // Revert on failure
            await fetchChatHistory();
        }
    };

    const handleRegenerate = async (messageId: string) => {
        if (loading || regeneratingId) return;
        setRegeneratingId(messageId);
        
        try {
            await client.post(`/chats/${chatId}/messages/${messageId}/regenerate`);
            // Fetch updated history to show the new version
            await fetchChatHistory();
        } catch (err: any) {
            console.error('Failed to regenerate response:', err);
            const errMsg = err.response?.data?.detail || 'Failed to regenerate response.';
            alert(errMsg);
        } finally {
            setRegeneratingId(null);
        }
    };

    if (loadingHistory && messages.length === 0) {
        return (
            <div className="chat-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
                <div className="typing-container">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="chat-container">
            {/* Header */}
            <div className="chat-header">
                <div className="chat-header-info">
                    <button onClick={() => navigate('/assistants')} className="btn-icon" style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                        <ArrowLeft size={20} />
                    </button>
                    <div className="chat-title">
                        <h2>{chatDetails?.name || 'Active Session'}</h2>
                        <span className="status-indicator">Connected</span>
                    </div>
                </div>
            </div>

            {/* Messages Area */}
            <div className="messages-area">
                {messages.length === 0 ? (
                    <div className="chat-empty">
                        <Bot size={64} />
                        <h3>How can I assist you?</h3>
                        <p>Ask a question about your connected knowledge bases.</p>
                    </div>
                ) : (
                    messages.map((msg) => (
                        <div key={msg.id} className={`message ${msg.role}`}>
                            <div className="message-avatar">
                                {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                            </div>
                            <div className="message-wrapper">
                                <div className="message-content">
                                    {msg.text || (msg.content?.versions?.[msg.content.versions.length - 1]?.text)}
                                    
                                    {/* Reference Docs (if any) */}
                                    {msg.reference_docs && msg.reference_docs.length > 0 && (
                                        <div className="message-refs">
                                            <div className="message-refs-title">References</div>
                                            <div>
                                                {msg.reference_docs.map((ref, i) => (
                                                    <span key={i} className="message-ref-badge" title={ref}>
                                                        <FileText size={12} /> {ref}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                                
                                {/* Assistant Actions */}
                                {msg.role === 'assistant' && !msg.id.startsWith('err-') && (
                                    <div className="message-actions">
                                        <button 
                                            className={`msg-action-btn ${msg.is_good === true ? 'active good' : ''}`}
                                            onClick={() => handleFeedback(msg.id, true)}
                                            title="Helpful"
                                        >
                                            <ThumbsUp size={14} />
                                        </button>
                                        <button 
                                            className={`msg-action-btn ${msg.is_good === false ? 'active bad' : ''}`}
                                            onClick={() => handleFeedback(msg.id, false)}
                                            title="Not Helpful"
                                        >
                                            <ThumbsDown size={14} />
                                        </button>
                                        <button 
                                            className="msg-action-btn"
                                            onClick={() => handleRegenerate(msg.id)}
                                            disabled={loading || regeneratingId === msg.id}
                                            title="Regenerate Response"
                                        >
                                            <RefreshCw size={14} className={regeneratingId === msg.id ? 'spin' : ''} />
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
                
                {loading && (
                    <div className="message assistant">
                        <div className="message-avatar"><Bot size={18} /></div>
                        <div className="message-wrapper">
                            <div className="message-content" style={{ padding: '1rem' }}>
                                <div className="typing-container">
                                    <div className="typing-dot"></div>
                                    <div className="typing-dot"></div>
                                    <div className="typing-dot"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
                
                {/* Invisible element to scroll to */}
                <div ref={messagesEndRef} style={{ height: '1px' }} />
            </div>

            {/* Input Area */}
            <div className="chat-input-wrapper">
                <form onSubmit={handleSend} className="chat-form">
                    <input
                        type="text"
                        className="chat-input"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your message..."
                        disabled={loading || loadingHistory}
                        autoFocus
                    />
                    <button type="submit" className="chat-submit" disabled={loading || loadingHistory || !input.trim()}>
                        <Send size={18} />
                    </button>
                </form>
            </div>
            
            <style>{`
                .spin { animation: spin 1s linear infinite; }
                @keyframes spin { 100% { transform: rotate(360deg); } }
            `}</style>
        </div>
    );
};

export default ChatPage;
