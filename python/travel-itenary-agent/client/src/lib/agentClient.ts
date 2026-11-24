/**
 * Talks to the agent: POST /api/turn, then read the Server-Sent Events stream.
 * (EventSource only supports GET, so we parse the stream from fetch ourselves.)
 */
import type {AgentToRendererMessage as A2uiMessage} from '@a2ui/web_core/v1_0';

export type ClientAction = {
  name: string;
  surfaceId: string;
  sourceComponentId: string;
  timestamp: string;
  context: Record<string, unknown>;
};

export type TurnInput =
  | {type: 'start'}
  | {type: 'text'; text: string}
  | {type: 'action'; action: ClientAction};

export type AgentEvent =
  | {type: 'a2ui'; message: A2uiMessage}
  | {type: 'status'; text: string}
  | {type: 'text'; delta: string}
  | {type: 'error'; message: string}
  | {type: 'done'};

export async function streamTurn(
  sessionId: string,
  input: TurnInput,
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch('/api/turn', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({sessionId, input}),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`Agent request failed: ${res.status} ${await res.text()}`);
  }

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = '';
  for (;;) {
    const {value, done} = await reader.read();
    if (done) break;
    buffer += value;
    // SSE events are separated by a blank line.
    let sep: number;
    while ((sep = buffer.search(/\r?\n\r?\n/)) !== -1) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep).replace(/^\r?\n\r?\n/, '');
      const data = raw
        .split(/\r?\n/)
        .filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).trimStart())
        .join('\n');
      if (data) onEvent(JSON.parse(data) as AgentEvent);
    }
  }
}
