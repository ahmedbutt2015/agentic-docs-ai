import { useEffect, useMemo, useRef, useState } from 'react';
import {
  BookOpenIcon,
  MessageCircleIcon,
  SendIcon,
} from './Icons';

const STORAGE_KEY = 'regulus-chat-state';
const MAX_HISTORY_FOR_SERVER = 6;

function loadInitialState(defaultJobId) {
  if (defaultJobId) {
    return { messages: [], scopeJobId: defaultJobId };
  }
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && Array.isArray(parsed.messages)) {
        return {
          messages: parsed.messages,
          scopeJobId: parsed.scopeJobId || '',
        };
      }
    }
  } catch {
    // ignore
  }
  return { messages: [], scopeJobId: '' };
}

function Chat({ apiBase, backendOnline, defaultJobId, onClearDefaultJobId }) {
  const initialStateRef = useRef(loadInitialState(defaultJobId));
  const lastAppliedDefaultJobIdRef = useRef(defaultJobId || '');
  const [messages, setMessages] = useState(initialStateRef.current.messages);
  const [scopeJobId, setScopeJobId] = useState(initialStateRef.current.scopeJobId);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [jobs, setJobs] = useState(null);
  const messagesEndRef = useRef(null);

  // Consume one-time document handoffs from the Results page without making them sticky.
  useEffect(() => {
    if (!defaultJobId) {
      return;
    }

    if (lastAppliedDefaultJobIdRef.current !== defaultJobId) {
      lastAppliedDefaultJobIdRef.current = defaultJobId;
      setScopeJobId(defaultJobId);
      setMessages([]);
      setError('');
    }

    onClearDefaultJobId?.();
  }, [defaultJobId, onClearDefaultJobId]);

  // Persist conversation across navigation
  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ messages, scopeJobId }));
    } catch {
      // ignore quota errors
    }
  }, [messages, scopeJobId]);

  // Fetch document list for the scope dropdown — lazy on chat page mount
  useEffect(() => {
    if (!backendOnline) return;
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch(`${apiBase}/jobs?status=completed&limit=50`);
        if (!response.ok) return;
        const data = await response.json();
        if (!cancelled) {
          setJobs(Array.isArray(data) ? data : []);
        }
      } catch {
        if (!cancelled) setJobs([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBase, backendOnline]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, sending]);

  const scopeLabel = useMemo(() => {
    if (!scopeJobId) return 'All documents';
    const match = (jobs || []).find((job) => job.id === scopeJobId);
    return match ? match.filename : `Document ${scopeJobId.slice(0, 8)}…`;
  }, [scopeJobId, jobs]);

  const handleSend = async (event) => {
    event?.preventDefault?.();
    const trimmed = draft.trim();
    if (!trimmed || sending) return;

    const userMessage = { role: 'user', content: trimmed };
    const next = [...messages, userMessage];
    setMessages(next);
    setDraft('');
    setSending(true);
    setError('');

    try {
      const response = await fetch(`${apiBase}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: trimmed,
          job_id: scopeJobId || null,
          history: messages.slice(-MAX_HISTORY_FOR_SERVER).map((message) => ({
            role: message.role,
            content: message.content,
          })),
        }),
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail?.detail || `Chat failed (${response.status})`);
      }

      const data = await response.json();
      setMessages([
        ...next,
        {
          role: 'assistant',
          content: data.answer || '',
          citations: Array.isArray(data.citations) ? data.citations : [],
        },
      ]);
    } catch (err) {
      setError(err.message || 'Could not send message');
    } finally {
      setSending(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    setError('');
  };

  return (
    <div className="chat-shell">
      <div className="page-header">
        <div>
          <div className="page-title">Document Chat</div>
          <div className="page-subtitle">
            Ask questions across your indexed documents — answers cite specific pages.
          </div>
        </div>
        <div className="page-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleClear}
            disabled={messages.length === 0}
          >
            Clear Conversation
          </button>
        </div>
      </div>

      <div className="card chat-card">
        <div className="card-header chat-header">
          <div className="card-title">
            <MessageCircleIcon color="var(--cyan-bright)" />
            Chat
            <span className="badge badge-muted">{scopeLabel}</span>
          </div>
          <label className="chat-scope-control">
            <span className="form-label">Scope</span>
            <select
              className="form-input chat-scope-select"
              value={scopeJobId}
              onChange={(event) => setScopeJobId(event.target.value)}
            >
              <option value="">All documents</option>
              {(jobs || []).map((job) => (
                <option key={job.id} value={job.id}>
                  {job.filename}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <MessageCircleIcon width={28} height={28} color="var(--text-muted)" />
              <p>Ask a question about your documents.</p>
              <p className="chat-empty-hint">
                Try: "What does this contract say about termination?" or "List the data-handling
                obligations across all documents."
              </p>
            </div>
          ) : null}

          {messages.map((message, index) => (
            <ChatMessageBubble key={`msg-${index}`} message={message} />
          ))}

          {sending ? (
            <div className="chat-bubble chat-bubble-assistant">
              <div className="chat-bubble-author">Assistant</div>
              <div className="chat-bubble-body chat-typing">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            </div>
          ) : null}

          <div ref={messagesEndRef} />
        </div>

        {error ? <p className="error-text chat-error">{error}</p> : null}

        <form className="chat-composer" onSubmit={handleSend}>
          <textarea
            className="form-input chat-input"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                void handleSend();
              }
            }}
            placeholder={
              backendOnline
                ? 'Ask about your documents…'
                : 'Backend offline — chat is unavailable'
            }
            rows={2}
            disabled={!backendOnline || sending}
          />
          <button
            type="submit"
            className="btn btn-primary chat-send"
            disabled={!backendOnline || sending || !draft.trim()}
          >
            <SendIcon width={14} height={14} />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

function ChatMessageBubble({ message }) {
  const [showCitations, setShowCitations] = useState(false);
  const isUser = message.role === 'user';
  const citations = message.citations || [];

  return (
    <div className={`chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'}`}>
      <div className="chat-bubble-author">{isUser ? 'You' : 'Assistant'}</div>
      <div className="chat-bubble-body">{message.content}</div>
      {!isUser && citations.length > 0 ? (
        <>
          <button
            type="button"
            className="chat-citations-toggle"
            onClick={() => setShowCitations((current) => !current)}
          >
            <BookOpenIcon width={12} height={12} />
            {showCitations ? 'Hide' : 'View'} {citations.length} reference{citations.length === 1 ? '' : 's'}
          </button>
          {showCitations ? (
            <div className="chat-citations">
              {citations.map((citation, index) => (
                <div key={citation.chunk_id} className="chat-citation">
                  <div className="chat-citation-header">
                    <span className="chat-citation-index">Source {index + 1}</span>
                    <span className="chat-citation-meta">
                      {citation.source_filename || 'document'} · page {citation.page_number} ·{' '}
                      similarity {citation.score.toFixed(2)}
                    </span>
                  </div>
                  <div className="chat-citation-preview">"{citation.preview}…"</div>
                </div>
              ))}
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

export default Chat;
