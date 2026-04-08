import { useState, useRef } from 'react';
import './index.css';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import StatusPanel from './components/StatusPanel';

export default function App() {
  const [agentStates, setAgentStates] = useState({
    scheduler: { status: 'idle', result: '' },
    taskmaster: { status: 'idle', result: '' },
    librarian: { status: 'idle', result: '' },
  });
  const [thoughts, setThoughts] = useState([]);
  const chatRef = useRef(null);

  const handleStreamEvent = (event) => {
    setThoughts(prev => [...prev, event]);
  };

  const handleQuickAction = (query) => {
    // We'll trigger the chat to submit this query
    // by storing it and using a ref approach
    if (chatRef.current) {
      chatRef.current.submitQuery(query);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar onQuickAction={handleQuickAction} />
      <ChatInterface
        ref={chatRef}
        onStreamEvent={handleStreamEvent}
        agentStates={agentStates}
        setAgentStates={setAgentStates}
      />
      <StatusPanel agentStates={agentStates} thoughts={thoughts} />
    </div>
  );
}
