const AGENT_META = {
  scheduler: {
    icon: '🗓️',
    color: 'var(--scheduler-color)',
    label: 'Scheduler',
    description: 'Time-blocking, conflict resolution, calendar management',
  },
  taskmaster: {
    icon: '✅',
    color: 'var(--taskmaster-color)',
    label: 'Taskmaster',
    description: 'To-do lists, priority levels, deadline enforcement',
  },
  librarian: {
    icon: '📚',
    color: 'var(--librarian-color)',
    label: 'Librarian',
    description: 'Knowledge base search, note summarization, research',
  },
};

export default function StatusPanel({ agentStates, thoughts }) {
  return (
    <div className="status-panel">
      {/* Agent Cards */}
      <div>
        <div className="status-panel-title">Agent Status</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '8px' }}>
          {Object.entries(AGENT_META).map(([key, meta]) => {
            const state = agentStates[key] || { status: 'idle', result: '' };
            return (
              <div key={key} className={`agent-card ${state.status === 'running' ? 'active' : ''}`}>
                <div className="agent-card-header">
                  <div className="agent-card-name" style={{ color: meta.color }}>
                    <span>{meta.icon}</span>
                    {meta.label}
                  </div>
                  <span className={`agent-card-badge ${state.status}`}>
                    {state.status === 'idle' ? 'Idle' : state.status === 'running' ? 'Running' : 'Done'}
                  </span>
                </div>
                <div className="agent-card-description">{meta.description}</div>
                {state.result && (
                  <div className="agent-card-result">
                    {typeof state.result === 'string' ? state.result.slice(0, 300) : JSON.stringify(state.result).slice(0, 300)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Thought Timeline */}
      {thoughts.length > 0 && (
        <div>
          <div className="status-panel-title">Execution Timeline</div>
          <div className="thought-timeline" style={{ marginTop: '8px' }}>
            {thoughts.map((t, i) => (
              <div key={i} className="thought-item">
                <div className={`thought-dot ${t.agent || 'system'}`}>
                  {t.type === 'plan' ? '📋' : t.type === 'thought' ? '💭' : t.type === 'result' ? '✅' : '⚡'}
                </div>
                <div className="thought-content">
                  <div className="thought-title">
                    {t.agent ? AGENT_META[t.agent]?.label || t.agent : 'Orchestrator'}
                  </div>
                  <div className="thought-detail">
                    {t.message || t.action || 'Processing...'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Architecture Info */}
      <div style={{ marginTop: 'auto' }}>
        <div className="status-panel-title">Architecture</div>
        <div style={{
          marginTop: '8px',
          padding: '14px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--bg-glass)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.72rem',
          color: 'var(--text-muted)',
          lineHeight: 1.6,
        }}>
          <div style={{ marginBottom: '8px' }}>
            <strong style={{ color: 'var(--gold-400)' }}>Hub-and-Spoke Model</strong>
          </div>
          <div>🧠 Orchestrator classifies intent</div>
          <div>🔀 Parallel agent dispatch</div>
          <div>📋 Blackboard state sharing</div>
          <div>🔁 Plan → Validate → Execute → Report</div>
          <div style={{ marginTop: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
            <strong style={{ color: 'var(--text-secondary)' }}>MCP Protocol</strong> for tool decoupling
          </div>
        </div>
      </div>
    </div>
  );
}
