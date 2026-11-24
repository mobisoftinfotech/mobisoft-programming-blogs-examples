import {useCallback, useEffect, useRef, useState, type FormEvent} from 'react';
import {A2uiSurface} from '@a2ui/react/v0_9';
import {streamTurn, type AgentEvent, type TurnInput} from './lib/agentClient';
import {useA2ui} from './lib/useA2ui';

type ChatEntry = {role: 'user' | 'agent' | 'error'; text: string};

const SESSION_ID = crypto.randomUUID();

/** What to show in the chat when the user clicks something in an agent surface. */
function describeAction(name: string, context: Record<string, unknown>): string {
  switch (name) {
    case 'suggest':
      return String(context.prompt ?? name);
    case 'refine_itinerary':
      return `✏️ ${String(context.change ?? 'Change the plan')}`;
    case 'find_hotels':
      return `🏨 Hotels in ${String(context.city)} for ${String(context.nights)} nights`;
    case 'select_hotel':
      return `✅ Selected ${String(context.hotelId)}`;
    case 'confirm_booking':
      return `🛎️ Confirm booking for ${String(context.guestName)}`;
    case 'cancel_booking':
      return '✖ Cancel booking';
    case 'dismiss_notice':
      return '✖ Dismiss';
    case 'start_over':
      return '✨ Start over';
    case 'plan_trip':
      return `🗺️ Plan my trip to ${String(context.destination)}`;
    default:
      return `▶ ${name}`;
  }
}

export default function App() {
  const [chat, setChat] = useState<ChatEntry[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState('');
  const started = useRef(false);

  // The processor holds all UI state. Actions (e.g. clicking "Plan my trip") go back to the agent.
  // (`send` is defined below; the callback only runs after render.)
  const busyRef = useRef(false);
  const {surfaces, process} = useA2ui(action => {
    if (busyRef.current) return; // one request at a time: ignore clicks while the agent works
    setChat(prev => [...prev, {role: 'user', text: describeAction(action.name, action.context ?? {})}]);
    void send({type: 'action', action});
  });

  // Seconds since the current request started, shown in the "thinking" bubble.
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!busy) return;
    setElapsed(0);
    const started = Date.now();
    const timer = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(timer);
  }, [busy]);

  // Keep the newest message (and the thinking bubble) in view.
  const logRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    logRef.current?.scrollTo({top: logRef.current.scrollHeight, behavior: 'smooth'});
  }, [chat, status, busy]);

  const onEvent = useCallback((ev: AgentEvent) => {
    switch (ev.type) {
      case 'a2ui':
        process(ev.message);
        break;
      case 'status':
        setStatus(ev.text);
        break;
      case 'text':
        setStatus(null);
        setChat(prev => {
          const last = prev.at(-1);
          if (last?.role === 'agent') return [...prev.slice(0, -1), {...last, text: last.text + ev.delta}];
          return [...prev, {role: 'agent', text: ev.delta}];
        });
        break;
      case 'error':
        setChat(prev => [...prev, {role: 'error', text: ev.message}]);
        break;
      case 'done':
        setStatus(null);
        break;
    }
  }, [process]);

  const send = useCallback(
    async (input: TurnInput) => {
      busyRef.current = true;
      setBusy(true);
      try {
        await streamTurn(SESSION_ID, input, onEvent);
      } catch (err) {
        setChat(prev => [...prev, {role: 'error', text: String(err)}]);
      } finally {
        busyRef.current = false;
        setBusy(false);
        setStatus(null);
      }
    },
    [onEvent],
  );

  useEffect(() => {
    if (started.current) return; // StrictMode runs effects twice in dev
    started.current = true;
    void send({type: 'start'});
  }, [send]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    setChat(prev => [...prev, {role: 'user', text}]);
    setDraft('');
    void send({type: 'text', text});
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Wanderly</h1>
        <span className="tag">A2UI v1.0 · Generative UI demo</span>
      </header>

      <main className="layout">
        <section className={`surfaces${busy ? ' is-busy' : ''}`} aria-label="Agent UI" aria-busy={busy}>
          {busy && <div className="progress-bar" role="progressbar" aria-label="Agent is working" />}
          {surfaces.length === 0 && <p className="muted">Waiting for the agent…</p>}
          {/* Newest surface first: what the agent just sent is what the user should see. */}
          {[...surfaces].reverse().map(surface => (
            <div className="surface" key={surface.id} data-surface={surface.id}>
              <A2uiSurface surface={surface} />
            </div>
          ))}
        </section>

        <section className="chat" aria-label="Conversation">
          <div className="chat-log" ref={logRef} aria-live="polite">
            {chat.map((entry, i) => (
              <div key={i} className={`bubble ${entry.role}`}>
                {entry.text}
              </div>
            ))}
            {busy && (
              <div className="bubble agent thinking">
                <span className="dots" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </span>
                <span>{status ?? 'Thinking…'}</span>
                {elapsed >= 3 && <span className="elapsed">{elapsed}s</span>}
              </div>
            )}
          </div>
          <form className="chat-input" onSubmit={submit}>
            <input
              value={draft}
              onChange={e => setDraft(e.target.value)}
              placeholder="Try: 7 nights and 8 days in Thailand · Book a hotel in Lisbon for 2 days"
              aria-label="Message"
              disabled={busy}
            />
            <button type="submit" disabled={busy || !draft.trim()}>
              {busy ? <span className="spinner" aria-label="Working" /> : 'Send'}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}
