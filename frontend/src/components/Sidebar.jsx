const QUICK_ACTIONS = [
  { icon: '📅', label: "What's on my calendar today?", query: "List all my events for today" },
  { icon: '✅', label: 'Show pending tasks', query: "Show me all pending tasks sorted by priority" },
  { icon: '📝', label: 'Search my notes', query: "Search my notes for meeting prep" },
  { icon: '🔄', label: 'Reschedule today to tomorrow', query: "Move all pending tasks from today to tomorrow" },
  { icon: '🕐', label: 'Find free time', query: "Find all free time slots for tomorrow" },
];

export default function Sidebar({ onQuickAction }) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">⚡</div>
        <div>
          <h1>AETHER</h1>
          <span>Multi-Agent Assistant</span>
        </div>
      </div>

      {/* Navigation */}
      <div>
        <div className="sidebar-section-title">Navigation</div>
        <nav className="sidebar-nav">
          <button className="sidebar-nav-item active">
            <span className="icon">💬</span>
            Chat
          </button>
          <button className="sidebar-nav-item">
            <span className="icon">📊</span>
            Dashboard
          </button>
          <button className="sidebar-nav-item">
            <span className="icon">📜</span>
            History
          </button>
          <button className="sidebar-nav-item">
            <span className="icon">⚙️</span>
            Settings
          </button>
        </nav>
      </div>

      {/* Quick Actions */}
      <div>
        <div className="sidebar-section-title">Quick Actions</div>
        <div className="quick-actions">
          {QUICK_ACTIONS.map((action, i) => (
            <button
              key={i}
              className="quick-action-btn"
              onClick={() => onQuickAction(action.query)}
            >
              <span className="icon">{action.icon}</span>
              {action.label}
            </button>
          ))}
        </div>
      </div>

      {/* Agent Status */}
      <div>
        <div className="sidebar-section-title">Agents</div>
        <div className="agent-status-list">
          <div className="agent-status-row">
            <div className="agent-dot idle scheduler" />
            <span style={{ color: 'var(--scheduler-color)', fontWeight: 600, fontSize: '0.8rem' }}>Scheduler</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginLeft: 'auto' }}>Calendar</span>
          </div>
          <div className="agent-status-row">
            <div className="agent-dot idle taskmaster" />
            <span style={{ color: 'var(--taskmaster-color)', fontWeight: 600, fontSize: '0.8rem' }}>Taskmaster</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginLeft: 'auto' }}>Tasks</span>
          </div>
          <div className="agent-status-row">
            <div className="agent-dot idle librarian" />
            <span style={{ color: 'var(--librarian-color)', fontWeight: 600, fontSize: '0.8rem' }}>Librarian</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginLeft: 'auto' }}>Knowledge</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ marginTop: 'auto', padding: '0 12px' }}>
        <div style={{
          fontSize: '0.65rem',
          color: 'var(--text-muted)',
          lineHeight: 1.5
        }}>
          Powered by <strong style={{ color: 'var(--gold-400)' }}>Gemini 2.0 Flash</strong>
          <br />
          MCP Protocol • Hub-and-Spoke Architecture
        </div>
      </div>
    </aside>
  );
}
