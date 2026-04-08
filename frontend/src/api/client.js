/**
 * API client for the Multi-Agent backend.
 * Handles SSE streaming for real-time agent thoughts.
 */

const API_BASE = 'http://localhost:8000';

/**
 * Execute a query via the orchestrator with SSE streaming.
 * @param {string} query - Natural language instruction
 * @param {string} userId - User identifier
 * @param {function} onEvent - Callback for each streamed event
 * @returns {Promise<void>}
 */
export async function executeQuery(query, userId = 'user_123', onEvent) {
  const response = await fetch(`${API_BASE}/v1/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, query }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim();
        if (data === '[DONE]') return;
        try {
          const event = JSON.parse(data);
          onEvent(event);
        } catch (e) {
          // skip malformed
        }
      }
    }
  }
}

/**
 * Execute a query synchronously (non-streaming).
 */
export async function executeQuerySync(query, userId = 'user_123') {
  const response = await fetch(`${API_BASE}/v1/execute/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, query }),
  });
  return response.json();
}

/**
 * Get execution history for a user.
 */
export async function getHistory(userId = 'user_123', limit = 20) {
  const response = await fetch(`${API_BASE}/v1/history/${userId}?limit=${limit}`);
  return response.json();
}

/**
 * Health check.
 */
export async function healthCheck() {
  const response = await fetch(`${API_BASE}/v1/health`);
  return response.json();
}
