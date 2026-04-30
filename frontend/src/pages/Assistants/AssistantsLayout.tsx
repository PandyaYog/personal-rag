import { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom';
import client from '../../api/client';
import { Plus, MessageSquare, Edit2, Trash2, ChevronDown, ChevronRight, Bot } from 'lucide-react';
import ConfirmModal from '../../components/UI/ConfirmModal';
import './AssistantsLayout.css';
import { Assistant } from '../../types/assistant';
import { Chat } from '../../types/chat';

// Define a local type to hold an assistant and its loaded chats
interface AssistantWithChats extends Assistant {
  isExpanded?: boolean;
  chats?: Chat[];
  chatsLoading?: boolean;
}

const AssistantsLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [assistants, setAssistants] = useState<AssistantWithChats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Deletion state
  const [assistantToDelete, setAssistantToDelete] = useState<Assistant | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [prevPath, setPrevPath] = useState(location.pathname);

  // Initial fetch
  useEffect(() => {
    fetchAssistants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-fetch when returning to root (e.g. after updating/creating)
  useEffect(() => {
    if (prevPath !== location.pathname) {
      if (location.pathname === '/assistants' || location.pathname === '/assistants/') {
        fetchAssistants();
      }
      setPrevPath(location.pathname);
    }
  }, [location.pathname, prevPath]);

  const fetchAssistants = async () => {
    try {
      setLoading(true);
      const response = await client.get('/assistants/');
      // Initialize with collapsed state and empty chats
      const asts = response.data.map((ast: Assistant) => ({
        ...ast,
        isExpanded: false,
        chats: [],
        chatsLoading: false
      }));
      setAssistants(asts);
    } catch (err) {
      console.error(err);
      setError('Failed to load assistants.');
    } finally {
      setLoading(false);
    }
  };

  const fetchChatsForAssistant = async (assistantId: string) => {
    try {
      setAssistants(prev => prev.map(a => 
        a.id === assistantId ? { ...a, chatsLoading: true } : a
      ));
      
      const response = await client.get(`/assistants/${assistantId}/chats`);
      
      setAssistants(prev => prev.map(a => 
        a.id === assistantId ? { ...a, chats: response.data, chatsLoading: false, isExpanded: true } : a
      ));
    } catch (err) {
      console.error('Failed to fetch chats', err);
      setAssistants(prev => prev.map(a => 
        a.id === assistantId ? { ...a, chatsLoading: false } : a
      ));
    }
  };

  const toggleAccordion = (assistantId: string) => {
    setAssistants(prev => prev.map(ast => {
      if (ast.id === assistantId) {
        const willExpand = !ast.isExpanded;
        // Fetch chats if we are expanding and haven't fetched yet
        if (willExpand && (!ast.chats || ast.chats.length === 0)) {
          fetchChatsForAssistant(assistantId);
        }
        return { ...ast, isExpanded: willExpand };
      }
      return ast;
    }));
  };

  const handleDeleteAssistant = async () => {
    if (!assistantToDelete) return;
    try {
      setIsDeleting(true);
      await client.delete(`/assistants/${assistantToDelete.id}`);
      setAssistants(prev => prev.filter(a => a.id !== assistantToDelete.id));
      
      // If we are currently viewing the deleted assistant, navigate away
      if (location.pathname.includes(`/assistants/${assistantToDelete.id}`)) {
        navigate('/assistants');
      }
      setAssistantToDelete(null);
    } catch (err) {
      console.error(err);
      alert('Failed to delete assistant.');
    } finally {
      setIsDeleting(false);
    }
  };

  const createNewChat = async (assistantId: string) => {
    try {
      const response = await client.post(`/assistants/${assistantId}/chats`, { name: "New Chat" });
      const newChat = response.data;
      
      // Update local state to include the new chat
      setAssistants(prev => prev.map(ast => {
        if (ast.id === assistantId) {
          return {
            ...ast,
            chats: [newChat, ...(ast.chats || [])],
            isExpanded: true
          };
        }
        return ast;
      }));
      
      // Navigate to the new chat
      navigate(`/assistants/${assistantId}/chat/${newChat.id}`);
    } catch (err) {
      console.error('Failed to create chat', err);
      alert('Failed to create new chat.');
    }
  };

  const isRoot = location.pathname === '/assistants' || location.pathname === '/assistants/';

  return (
    <div className="assistants-page">
      {/* Animated Background */}
      <div className="ast-bg" aria-hidden="true">
        <div className="ast-orb ast-orb-1" />
        <div className="ast-orb ast-orb-2" />
        <div className="ast-grid-overlay" />
      </div>

      <div className={`ast-split-layout ${isRoot ? 'is-root' : 'is-detail'}`}>
        
        {/* LEFT PANEL: Assistant List */}
        <div className="ast-left-panel">
          <div className="ast-sidebar-header">
            <h2>Assistants</h2>
            <button 
              className="ast-new-btn"
              onClick={() => navigate('/assistants/create')}
            >
              <Plus size={16} />
              New
            </button>
          </div>
          
          <div className="ast-sidebar-body">
            {loading ? (
              <div className="ast-loading">
                <div className="ast-spinner" />
                <span>Loading...</span>
              </div>
            ) : error ? (
              <div style={{ color: '#fca5a5', padding: '1rem', textAlign: 'center' }}>{error}</div>
            ) : assistants.length === 0 ? (
              <div style={{ color: '#94a3b8', padding: '2rem 1rem', textAlign: 'center', fontSize: '0.9rem' }}>
                No assistants found. Create one to start chatting!
              </div>
            ) : (
              assistants.map((ast) => (
                <div key={ast.id} className="ast-accordion-item">
                  <button 
                    className="ast-accordion-header"
                    onClick={() => toggleAccordion(ast.id)}
                  >
                    <div className="ast-accordion-title">
                      <Bot size={18} className="ast-accordion-icon" />
                      {ast.name}
                    </div>
                    <div className="ast-assistant-actions">
                      <div 
                        className="ast-action-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/assistants/${ast.id}/edit`);
                        }}
                        title="Edit Assistant"
                      >
                        <Edit2 size={14} />
                      </div>
                      <div 
                        className="ast-action-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          setAssistantToDelete(ast);
                        }}
                        title="Delete Assistant"
                      >
                        <Trash2 size={14} />
                      </div>
                      <div className="ast-action-btn" style={{ marginLeft: '0.25rem' }}>
                        {ast.isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </div>
                    </div>
                  </button>
                  
                  {ast.isExpanded && (
                    <div className="ast-accordion-content">
                      <button 
                        className="ast-new-chat-btn"
                        onClick={() => createNewChat(ast.id)}
                      >
                        <Plus size={14} /> New Chat
                      </button>
                      
                      {ast.chatsLoading ? (
                        <div style={{ padding: '0.5rem', color: '#64748b', fontSize: '0.8rem', textAlign: 'center' }}>
                          Loading chats...
                        </div>
                      ) : ast.chats && ast.chats.length > 0 ? (
                        ast.chats.map(chat => {
                          const isActive = location.pathname === `/assistants/${ast.id}/chat/${chat.id}`;
                          return (
                            <Link 
                              key={chat.id} 
                              to={`/assistants/${ast.id}/chat/${chat.id}`}
                              className={`ast-chat-link ${isActive ? 'active' : ''}`}
                              title={chat.name}
                            >
                              <MessageSquare size={14} style={{ marginRight: '0.4rem', verticalAlign: 'text-bottom' }} />
                              {chat.name || "Untitled Chat"}
                            </Link>
                          );
                        })
                      ) : (
                        <div style={{ padding: '0.5rem', color: '#64748b', fontSize: '0.8rem', textAlign: 'center' }}>
                          No chats yet.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* RIGHT PANEL: Dynamic Content (Outlet) */}
        <div className="ast-right-panel">
          {isRoot ? (
            <div className="ast-empty-state">
              <Bot size={64} />
              <h3>AI Assistants</h3>
              <p>Select a chat from the sidebar or create a new assistant to start interacting with your knowledge bases.</p>
            </div>
          ) : (
            <Outlet />
          )}
        </div>
        
      </div>

      <ConfirmModal
        open={!!assistantToDelete}
        title="Delete Assistant"
        message={`Are you sure you want to delete "${assistantToDelete?.name}"? All associated chats will be permanently removed.`}
        confirmLabel="Delete"
        variant="danger"
        loading={isDeleting}
        onConfirm={handleDeleteAssistant}
        onCancel={() => setAssistantToDelete(null)}
      />
    </div>
  );
};

export default AssistantsLayout;
