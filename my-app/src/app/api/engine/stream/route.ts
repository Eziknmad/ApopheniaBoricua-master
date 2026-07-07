import WebSocket from "ws";
import { parseEngineMessage } from "@/lib/engineProtocol";

// The `ws` package needs real Node sockets, not the Edge runtime.
export const runtime = "nodejs";
// This is a long-lived stream, never statically cache it.
export const dynamic = "force-dynamic";

const MIN_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 15000;
const HEARTBEAT_MS = 20000;

function sseEvent(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

export async function GET(request: Request) {
  const engineUrl = process.env.ENGINE_WS_URL;
  if (!engineUrl) {
    return new Response(
      sseEvent("error", { message: "ENGINE_WS_URL is not configured on the Next.js server" }),
      { status: 500, headers: { "Content-Type": "text/event-stream" } },
    );
  }

  let closed = false;
  let socket: WebSocket | null = null;
  let backoffMs = MIN_BACKOFF_MS;
  let heartbeat: ReturnType<typeof setInterval> | undefined;

  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const encoder = new TextEncoder();
      const enqueue = (chunk: string) => {
        if (closed) return;
        try {
          controller.enqueue(encoder.encode(chunk));
        } catch {
          // Controller already closed (client disconnected); ignore.
        }
      };

      const connect = () => {
        if (closed) return;
        socket = new WebSocket(engineUrl);

        socket.on("open", () => {
          backoffMs = MIN_BACKOFF_MS; // reset backoff on a healthy connection
          enqueue(sseEvent("relay", { status: "connected", engineUrl }));
        });

        socket.on("message", (data, isBinary) => {
          if (isBinary) return; // protocol is text/JSON only, see WS_PROTOCOL.md
          let parsed: unknown;
          try {
            parsed = JSON.parse(data.toString("utf-8"));
          } catch {
            return; // drop malformed frames rather than killing the relay
          }
          const message = parseEngineMessage(parsed);
          if (message) {
            enqueue(sseEvent(message.type, message));
          }
        });

        socket.on("error", () => {
          // 'close' fires right after 'error' on the ws client; let close() own reconnection.
        });

        socket.on("close", () => {
          if (closed) return;
          enqueue(sseEvent("relay", { status: "disconnected", retry_in_ms: backoffMs }));
          setTimeout(connect, backoffMs);
          backoffMs = Math.min(backoffMs * 2, MAX_BACKOFF_MS);
        });
      };

      connect();

      // Keep intermediary proxies from timing out an idle SSE connection.
      heartbeat = setInterval(() => enqueue(": heartbeat\n\n"), HEARTBEAT_MS);

      request.signal.addEventListener("abort", () => {
        closed = true;
        clearInterval(heartbeat);
        socket?.close();
        try {
          controller.close();
        } catch {
          // already closed
        }
      });
    },
    cancel() {
      closed = true;
      clearInterval(heartbeat);
      socket?.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
