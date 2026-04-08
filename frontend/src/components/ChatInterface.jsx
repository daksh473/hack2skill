import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import { executeQuery } from '../api/client';

const SUGGESTIONS = [
  { icon: '🗓️', text: 'I have a meeting at 2 PM, clear my afternoon tasks and summarize my prep notes.' },
  { icon: '✅', text: 'Show me all high-priority tasks due today and reschedule the low-priority ones.' },
  { icon: '📚', text: 'Search my notes for anything related to the product review and summarize the findings.' },
  { icon: '⏰', text: 'Find a free 1-hour slot tomorrow for a design sprint and create the calendar event.' },
];

const ChatInterface = forwardRef(function ChatInterface({ onStreamEvent, agentStates, setAgentStates }, ref) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamEvents, setStreamEvents] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages, streamEvents]);

  useImperativeHandle(ref, () => ({
    submitQuery: (q) => handleSubmit(q),
  }));

  const handleSubmit = async (query) => {
    const q = query || input.trim();
    if (!q || isStreaming) return;

    setMessages(prev => [...prev, { role: 'user', content: q }]);
    setInput('');
    setIsStreaming(true);
    setStreamEvents([]);

    setAgentStates({
      scheduler: { status: 'idle', result: '' },
      taskmaster: { status: 'idle', result: '' },
      librarian: { status: 'idle', result: '' },
    });

    try {
      await executeQuery(q, 'user_123', (event) => {
        onStreamEvent(event);

        if (event.type === 'thought') {
          setAgentStates(prev => ({
            ...prev,
            [event.agent]: {
              status: event.status === 'done' ? 'done' : 'running',
              result: event.result || event.message || '',
              action: event.action || '',
            }
          }));
        }

        if (event.type === 'result') {
          setMessages(prev => [...prev, { role: 'assistant', content: event.summary }]);
          setStreamEvents([]);
        } else {
          setStreamEvents(prev => [...prev, event]);
        }
      });
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error: ${err.message}. Make sure the backend is running on http://localhost:8000`
      }]);
    }

    setIsStreaming(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'plan': return '📋';
      case 'thought': return '💭';
      case 'status': return '⚡';
      case 'result': return '✅';
      case 'error': return '❌';
      default: return '📌';
    }
  };

  const showWelcome = messages.length === 0 && !isStreaming;

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Aether Assistant</h2>
        <span className="badge">● Online</span>
      </div>

      <div className="chat-messages">
        {showWelcome && (
          <div className="welcome-container">
            <div className="welcome-icon">⚡</div>
            <h2 className="welcome-title">Multi-Agent Productivity</h2>
            <p className="welcome-subtitle">
              I orchestrate Scheduler, Taskmaster, and Librarian agents to handle complex
              productivity requests. Try one of these:
            </p>
            <div className="welcome-suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} className="welcome-suggestion" onClick={() => handleSubmit(s.text)}>
                  <span className="suggestion-icon">{s.icon}</span>
                  {s.text}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-label">
              {msg.role === 'user' ? 'You' : 'Aether'}
            </div>
            <div className="message-bubble">
              {msg.content}
            </div>
          </div>
        ))}

        {streamEvents.map((event, i) => (
          <div key={`stream-${i}`} className={`stream-event ${event.type}`}>
            <span className="event-icon">{getEventIcon(event.type)}</span>
            <span className="event-text">{event.message || JSON.stringify(event)}</span>
          </div>
        ))}

        {isStreaming && streamEvents.length === 0 && (
          <div className="stream-event">
            <span className="event-icon">⏳</span>
            <span className="event-text">Connecting to orchestrator...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-wrapper">
        <div className="chat-input-container">
          <input
            ref={inputRef}
            className="chat-input"
            type="text"
            placeholder="Ask me to manage your schedule, tasks, or notes..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            id="chat-input"
          />
          <button
            className="chat-send-btn"
            onClick={() => handleSubmit()}
            disabled={isStreaming || !input.trim()}
            id="send-button"
          >
            ➤
          </button>
        </div>
        <div className="chat-hint">
          Press Enter to send • Powered by Gemini + Multi-Agent Orchestration
        </div>
      </div>
    </div>
  );
});

export default ChatInterface;
