// Stand-in for the future C11 hand-rolled WebSocket engine, for testing the
// Next.js relay (src/app/api/engine/stream/route.ts) without real hardware.
// Speaks exactly the schema in ../../engine-contract/WS_PROTOCOL.md.
//
// Usage:
//   node scripts/fake_engine.js
//   ENGINE_WS_URL=ws://localhost:8765 npm run dev   # in another terminal
//   curl -N http://localhost:3000/api/engine/stream # in a third
const { WebSocketServer } = require("ws");

const PORT = process.env.FAKE_ENGINE_PORT ? Number(process.env.FAKE_ENGINE_PORT) : 8765;
const wss = new WebSocketServer({ port: PORT });
console.log(`fake engine listening on ws://localhost:${PORT}`);

wss.on("connection", (socket) => {
  console.log("relay connected");
  socket.send(
    JSON.stringify({
      type: "hello",
      model: { d_model: 64, n_heads: 2, block_size: 128, vocab_size: 50257 },
      engine_version: "0.0.0-fake",
    }),
  );

  let step = 0;
  const timer = setInterval(() => {
    socket.send(
      JSON.stringify({
        type: "token",
        step,
        token_id: 1917 + step,
        text: ` tok${step}`,
        loss: 3.2 - step * 0.01,
      }),
    );
    socket.send(
      JSON.stringify({
        type: "attn",
        step,
        heads: [
          [0.1, 0.2, 0.3],
          [0.4, 0.5, 0.6],
        ],
      }),
    );
    step += 1;
    if (step >= 5) {
      clearInterval(timer);
      socket.close(); // exercises the relay's reconnect/backoff path
    }
  }, 200);

  socket.on("close", () => console.log("relay disconnected"));
});
