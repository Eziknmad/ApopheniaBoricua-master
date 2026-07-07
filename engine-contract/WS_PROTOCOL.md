# PareidoliaBoricua Engine <-> ApopheniaBoricua Frontend Wire Protocol

This is the contract between the C11 engine (built on the other machine) and the
Next.js relay in `my-app/src/app/api/engine/stream/route.ts`. Both sides must
agree on this document before either implementation changes.

## Transport

- The engine is the WebSocket **server** (RFC 6455), hand-rolled in C11.
- The Next.js API route is the WebSocket **client**. It connects once, relays
  every message to the browser as Server-Sent Events, and reconnects with
  backoff on drop.
- Address is not hardcoded: the relay reads it from `ENGINE_WS_URL`
  (e.g. `ws://192.168.1.50:8765`).

### Framing rules the C11 server MUST get right

These are the parts of RFC 6455 that hand-rolled servers most commonly get
wrong. The Node `ws` client used on the relay side enforces them strictly and
will drop the connection on violation:

1. **Server-to-client frames must NOT be masked.** Client-to-server frames
   (there are none in this protocol besides pings/close) MUST be masked by
   the client; a server never masks.
2. Use **text frames** (opcode `0x1`) with a UTF-8 JSON payload — one JSON
   object per frame, no newline-delimited batching.
3. Handle **PING** (opcode `0x9`) by replying with **PONG** (`0xA`) carrying
   the same application data, so the link survives idle periods.
4. Handle continuation frames (`0x0`) if any message exceeds one frame, or
   simply avoid fragmentation by keeping every JSON payload under the
   engine's single send buffer (attention rows here are small, see below).
5. On `Sec-WebSocket-Accept`, use the fixed GUID
   `258EAFA5-E914-47DA-95CA-C5AB0DC85B11`.

## Message schema

Every message is a single JSON object with a `type` discriminant.

### `hello` (sent once, right after handshake)

```json
{
  "type": "hello",
  "model": { "d_model": 64, "n_heads": 2, "block_size": 128, "vocab_size": 50257 },
  "engine_version": "0.1.0"
}
```

### `token` (sent once per generated/audited step)

```json
{
  "type": "token",
  "step": 41,
  "token_id": 1917,
  "text": " Boricua",
  "loss": 3.2185
}
```

- `loss` is the streaming online-log-sum-exp cross-entropy for this step,
  computed row-by-row over the 50257-wide vocab without ever materializing a
  dense `(B,T,vocab)` tensor. It is a single scalar, not a distribution.

### `attn` (sent once per step, immediately after the matching `token`)

Only the current query position's attention row is sent — i.e. how the token
at `step` attends back over its causal history (at most `block_size`
entries). Full `(block_size x block_size)` matrices are never streamed; that
would be `128*128*2 heads` floats per step, which is wasteful on both the
N6000's uplink and the browser.

```json
{
  "type": "attn",
  "step": 41,
  "heads": [
    [0.01, 0.02, "... up to min(step+1, block_size) floats ..."],
    [0.00, 0.05, "... second head, same length ..."]
  ]
}
```

### `error` / `close`

```json
{ "type": "error", "message": "arena OOM guard tripped at step 900" }
```

Followed by a normal WebSocket close frame.

## Non-goals

- No binary frames, no protobuf/msgpack — JSON text keeps the C11 side to
  `snprintf`-able code, no serialization library needed.
- No backpressure protocol yet: the engine is expected to run at a pace the
  N6000 imposes naturally (a handful of tokens/sec), so simple send-and-move-on
  is fine. Revisit if the relay's SSE buffer grows unbounded.
