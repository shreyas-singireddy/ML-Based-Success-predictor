import React, { useEffect, useState, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Sparkles,
  Send,
  ShieldCheck,
  Building2,
  RefreshCw,
  Info,
  Layers,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { facultyApi } from '../../services/facultyApi';
import { FacultyAssistantChatResponse } from '../../types/faculty';

interface ChatTurn {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  evidence?: Array<{ source: string; label: string; value: string }>;
  timestamp: string;
}

export const FacultyAssistantPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const targetStudentId = searchParams.get('student_id');

  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    facultyApi.getSuggestions().then(setSuggestions).catch(() => {});
  }, []);

  useEffect(() => {
    // Initial greeting turn
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        text: (
          "Welcome to the Faculty Decision-Support AI Advisor. I have access to authorized student group " +
          "records, Phase 3 CGPA projections, Phase 4 risk classifications, Phase 5 SHAP explanations, " +
          "and Phase 8 intervention recommendations.\n\n" +
          "How can I assist your advising session or cohort review today?"
        ),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  }, []);

  useEffect(() => {
    if (typeof chatEndRef.current?.scrollIntoView === 'function') {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);


  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const userTurn: ChatTurn = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userTurn]);
    setInput('');
    setLoading(true);

    try {
      const res = await facultyApi.askAssistant(query, targetStudentId || undefined);
      const assistantTurn: ChatTurn = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        text: res.reply,
        evidence: res.evidence_references,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantTurn]);
    } catch (err: any) {
      const errMsg = err?.response?.data?.error?.message || err?.message || 'Error processing inquiry.';
      setMessages((prev) => [
        ...prev,
        {
          id: `ai-err-${Date.now()}`,
          role: 'assistant',
          text: `Apologies, I encountered an issue retrieving verified intelligence: ${errMsg}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '2rem 2.5rem', maxWidth: '1200px', width: '100%', margin: '0 auto', display: 'flex', flexDirection: 'column', height: 'calc(100vh - 40px)' }}>
      {/* Header */}
      <div style={{ marginBottom: '1rem', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
          <span style={{ fontSize: '0.7rem', fontFamily: "'JetBrains Mono', monospace", color: '#6366F1', fontWeight: 600, letterSpacing: '0.08em' }}>
            GENAI DECISION SUPPORT
          </span>
          <span style={{ color: 'rgba(255, 255, 255, 0.2)' }}>/</span>
          <span style={{ fontSize: '0.72rem', color: '#A1A1AA' }}>Grounding & Scope Enforced</span>
        </div>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#FFFFFF', margin: 0, letterSpacing: '-0.02em' }}>
          Faculty AI Academic Advisor
        </h1>
        <div style={{ fontSize: '0.78rem', color: '#71717A', marginTop: '0.2rem' }}>
          Grounded conversational decision support translating verified ML risk predictions, SHAP attributions, and action recommendations.
        </div>
      </div>

      {/* Suggestion Starter Buttons */}
      {suggestions.length > 0 && (
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem', flexShrink: 0 }}>
          {suggestions.map((sug, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(sug)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.4rem 0.75rem',
                backgroundColor: '#121216',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                borderRadius: '6px',
                color: '#D4D4D8',
                fontSize: '0.72rem',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(99, 102, 241, 0.15)';
                e.currentTarget.style.color = '#FFFFFF';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#121216';
                e.currentTarget.style.color = '#D4D4D8';
              }}
            >
              <Sparkles size={12} color="#6366F1" />
              <span>{sug}</span>
            </button>
          ))}
        </div>
      )}

      {/* Chat Messages Container */}
      <div
        style={{
          flex: 1,
          backgroundColor: '#0A0A0C',
          border: '1px solid rgba(255, 255, 255, 0.07)',
          borderRadius: '8px',
          padding: '1.5rem',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
          marginBottom: '1rem',
        }}
      >
        {messages.map((turn) => {
          const isUser = turn.role === 'user';
          return (
            <div
              key={turn.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: isUser ? 'flex-end' : 'flex-start',
              }}
            >
              <div
                style={{
                  maxWidth: '85%',
                  padding: '1rem 1.25rem',
                  borderRadius: '8px',
                  backgroundColor: isUser ? '#6366F1' : '#121216',
                  color: '#FFFFFF',
                  border: isUser ? 'none' : '1px solid rgba(255, 255, 255, 0.06)',
                  fontSize: '0.85rem',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {turn.text}

                {/* Evidence Badges if available */}
                {turn.evidence && turn.evidence.length > 0 && (
                  <div
                    style={{
                      marginTop: '0.85rem',
                      paddingTop: '0.75rem',
                      borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.35rem',
                    }}
                  >
                    <div style={{ fontSize: '0.68rem', color: '#71717A', fontFamily: "'JetBrains Mono', monospace", textTransform: 'uppercase' }}>
                      Verified Grounded Evidence Sources
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                      {turn.evidence.map((ev, i) => (
                        <div
                          key={i}
                          style={{
                            fontSize: '0.68rem',
                            padding: '0.2rem 0.5rem',
                            backgroundColor: '#18181B',
                            border: '1px solid rgba(99, 102, 241, 0.3)',
                            borderRadius: '4px',
                            color: '#A5B4FC',
                          }}
                        >
                          <span style={{ fontWeight: 600 }}>{ev.label}:</span> {ev.value}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div style={{ fontSize: '0.65rem', color: '#52525B', marginTop: '0.3rem', padding: '0 0.25rem' }}>
                {turn.timestamp}
              </div>
            </div>
          );
        })}

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#71717A', fontSize: '0.78rem' }}>
            <RefreshCw size={14} className="animate-spin" color="#6366F1" />
            <span>Consulting verified ML intelligence & synthesizing advising response…</span>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Box */}
      <div style={{ display: 'flex', gap: '0.75rem', flexShrink: 0 }}>
        <input
          type="text"
          placeholder="Ask about student group performance, risk factors, or individual advising strategies..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSendMessage();
          }}
          disabled={loading}
          style={{
            flex: 1,
            padding: '0.85rem 1.25rem',
            backgroundColor: '#0F0F12',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            color: '#FFFFFF',
            fontSize: '0.85rem',
            outline: 'none',
          }}
        />
        <button
          onClick={() => handleSendMessage()}
          disabled={loading || !input.trim()}
          style={{
            padding: '0.85rem 1.5rem',
            backgroundColor: loading || !input.trim() ? '#1E1E24' : '#6366F1',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 600,
            fontSize: '0.85rem',
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <span>Ask</span>
          <Send size={15} />
        </button>
      </div>
    </div>
  );
};
