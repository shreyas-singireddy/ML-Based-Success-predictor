import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Send, Loader2, Info, ShieldCheck } from 'lucide-react';
import { AppPageHeader } from '../../components/layout/AppPageHeader';
import { ChatMessageBubble } from '../../components/assistant/ChatMessageBubble';
import { SuggestedPrompts } from '../../components/assistant/SuggestedPrompts';
import { LoadingPanel } from '../../components/ui/Skeleton';
import { ErrorState } from '../../components/ui/ErrorState';
import { EmptyState } from '../../components/ui/EmptyState';
import { useStudentData } from '../../contexts/StudentDataContext';
import { assistantApi } from '../../services/assistantApi';
import type {
  AssistantSuggestion,
  ChatMessageInput,
  ChatTurn,
  EvidenceSourceRef,
} from '../../types';

const MAX_HISTORY = 20;

const DISCLAIMER_NOTE =
  'This assistant is a decision-support translator built on your verified academic record and production ML outputs. It does not compute or alter any predictions, grades, or records, and is not a substitute for institutional academic advising.';

let turnCounter = 0;
function nextTurnId(): string {
  turnCounter += 1;
  return `turn-${Date.now()}-${turnCounter}`;
}

export const AssistantPage: React.FC = () => {
  const { student, loading: studentLoading, error: studentError, refresh: refreshStudent } = useStudentData();

  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  const [suggestions, setSuggestions] = useState<AssistantSuggestion[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(true);

  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    assistantApi
      .getSuggestions()
      .then((res) => {
        if (!cancelled) setSuggestions(res.items ?? []);
      })
      .catch(() => {
        if (!cancelled) setSuggestions([]);
      })
      .finally(() => {
        if (!cancelled) setSuggestionsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const historyForRequest = useMemo<ChatMessageInput[]>(() => {
    return messages
      .slice(-MAX_HISTORY)
      .map((turn) => ({ role: turn.role, content: turn.content, timestamp: turn.timestamp }));
  }, [messages]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, isSending]);

  const handleSend = async (rawPrompt?: string) => {
    const text = (rawPrompt ?? input).trim();
    if (!text || isSending) return;

    setInput('');
    const userTurn: ChatTurn = {
      id: nextTurnId(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userTurn]);
    setIsSending(true);

    try {
      const history = [...historyForRequest, { role: 'user' as const, content: text }];
      const resp = await assistantApi.chat(text, history);
      const assistantTurn: ChatTurn = {
        id: nextTurnId(),
        role: 'assistant',
        content: resp.message,
        timestamp: resp.generated_at || new Date().toISOString(),
        intent: resp.intent,
        sourcesUsed: resp.sources_used,
        evidenceReferences: resp.evidence_references as EvidenceSourceRef[],
        suggestedPrompts: resp.suggested_prompts,
        disclaimer: resp.disclaimer,
        status: resp.status,
      };
      setMessages((prev) => [...prev, assistantTurn]);
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        'The assistant could not answer right now. Please try again.';
      const errorTurn: ChatTurn = {
        id: nextTurnId(),
        role: 'assistant',
        content: String(detail),
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorTurn]);
    } finally {
      setIsSending(false);
    }
  };

  const handleComposerKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (studentLoading) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="GENAI ACADEMIC ASSISTANT" title="Connecting to your academic profile…" />
        <LoadingPanel message="Loading your verified academic context…" />
      </div>
    );
  }

  if (studentError) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="GENAI ACADEMIC ASSISTANT" title="Profile unavailable" />
        <ErrorState title="COULD NOT LOAD STUDENT PROFILE" message={studentError} onRetry={refreshStudent} />
      </div>
    );
  }

  if (!student) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="GENAI ACADEMIC ASSISTANT" title="No profile linked" />
        <EmptyState
          title="NO STUDENT PROFILE"
          body="Your user account is not linked to an active student record. Please contact administration."
        />
      </div>
    );
  }

  const emptyChat = messages.length === 0;

  return (
    <div className="app-page">
      <AppPageHeader
        eyebrow={`GENAI ACADEMIC ASSISTANT // ${student.student_number}`}
        title="ASK YOUR ACADEMIC ASSISTANT"
        description="Grounded answers over your verified academic record — every figure is drawn from the production Phase 2–8 engines, never invented by the model."
      />

      <div className="chat-shell panel">
        <div className="chat-window">
          <div className="chat-scroll" ref={scrollRef} role="log" aria-live="polite" aria-relevant="additions">
            {emptyChat ? (
              <div className="chat-welcome">
                <div className="chat-welcome-icon" aria-hidden="true">
                  <ShieldCheck size={22} />
                </div>
                <h2 className="chat-welcome-title">HOW CAN I HELP?</h2>
                <p className="chat-welcome-body">
                  Ask about your predicted CGPA, academic risk, what drives your score, what-if
                  scenarios, or what to work on first. Answers cite the exact phase-based source
                  they are grounded in.
                </p>

                {suggestionsLoading ? (
                  <LoadingPanel message="Preparing personalized starter prompts…" />
                ) : (
                  <SuggestedPrompts suggestions={suggestions} onSelect={handleSend} disabled={isSending} />
                )}

                <p className="chat-welcome-privacy">
                  <Info size={13} /> Your questions stay in the current session and are never saved.
                </p>
              </div>
            ) : (
              <>
                {messages.map((turn) => (
                  <ChatMessageBubble key={turn.id} turn={turn} onSuggestionClick={handleSend} />
                ))}

                {isSending && (
                  <div className="chat-row chat-row--assistant">
                    <div className="chat-avatar" aria-hidden="true">
                      <Loader2 size={16} className="animate-spin" />
                    </div>
                    <div className="chat-bubble chat-bubble--assistant chat-typing" role="status">
                      <span className="chat-typing-label">
                        <span className="dot" /> <span className="dot" /> <span className="dot" />
                      </span>
                      <span className="mono-label">GROUNDING ANSWER…</span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        <form className="chat-composer" onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
          <textarea
            className="chat-input"
            placeholder="Ask about your CGPA, risk, explanations, what-if scenarios…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleComposerKeyDown}
            rows={2}
            maxLength={1000}
            disabled={isSending}
            aria-label="Your question"
          />
          <button
            type="submit"
            className="btn btn-primary chat-send"
            disabled={isSending || !input.trim()}
            aria-label="Send question"
          >
            <Send size={16} />
            <span className="chat-send-label">SEND</span>
          </button>
        </form>

        <div className="chat-disclaimer-bar">
          <Info size={13} />
          <span>{DISCLAIMER_NOTE}</span>
        </div>
      </div>
    </div>
  );
};

export default AssistantPage;