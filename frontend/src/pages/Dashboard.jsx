import { useState } from 'react';
import Header from '../components/Header.jsx';
import ChatPanel from '../components/ChatPanel.jsx';
import RoadmapPanel from '../components/RoadmapPanel.jsx';
import { sendChatMessage } from '../services/chatApi.js';

const welcome = {
  id: 'welcome',
  role: 'assistant',
  content: 'Hi! Share your career or skill goal, timeline, current level, and daily study time. I’ll create a practical learning roadmap for you.',
};

export default function Dashboard() {
  const [messages, setMessages] = useState([welcome]);
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const handleSend = async (content) => {
    const userMessage = { id: crypto.randomUUID(), role: 'user', content };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError('');
    try {
      const data = await sendChatMessage(content);
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: data.response }]);
      if (data.roadmap) setRoadmap(data.roadmap);
    } catch (err) {
      setError(err.message);
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: 'Sorry, I could not generate a roadmap right now. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };
  return (
    <>
      <Header />
      <main className="dashboard">
        <ChatPanel
          messages={messages}
          onSend={handleSend}
          onClear={() => {
            setMessages([welcome]);
            setRoadmap(null);
            setError('');
          }}
          loading={loading}
          error={error}
        />
        <RoadmapPanel roadmap={roadmap} />
      </main>
    </>
  );
}
