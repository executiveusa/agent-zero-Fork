/**
 * OpenClaw Gateway — Legacy Entry Point
 * 
 * v2.0 moved to src/gateway.js with multi-app support.
 * This file remains for backward compatibility.
 * To use v2.0: node src/gateway.js
 */

// Redirect to v2.0 gateway
require("./src/gateway");

// Everything below is the original v1 code, kept as reference.
// It will NOT execute because src/gateway.js takes over the ports.
if (false) {

const http = require("http");
const { WebSocketServer } = require("ws");
const crypto = require("crypto");

// ── Config ──────────────────────────────────────────────────
const WS_PORT = parseInt(process.env.WS_PORT || "18789", 10);
const HTTP_PORT = parseInt(process.env.HTTP_PORT || "18790", 10);
const AGENT_ZERO_URL = process.env.AGENT_ZERO_URL || "http://agent-zero:5000";

// ── Channel Registry ────────────────────────────────────────
const channels = new Map();
const connections = new Map(); // ws id -> { ws, channel, metadata }

// ── WebSocket Server ────────────────────────────────────────
const wss = new WebSocketServer({ port: WS_PORT }, () => {
  console.log(`[OpenClaw] WebSocket server listening on port ${WS_PORT}`);
});

wss.on("connection", (ws, req) => {
  const id = crypto.randomUUID();
  const channel = req.url?.replace("/", "") || "default";

  connections.set(id, { ws, channel, connectedAt: new Date().toISOString() });
  channels.set(channel, (channels.get(channel) || 0) + 1);

  console.log(`[OpenClaw] Client connected: ${id} on channel: ${channel}`);

  ws.on("message", async (raw) => {
    try {
      const msg = JSON.parse(raw.toString());
      console.log(`[OpenClaw] Message from ${channel}:`, msg.type || "unknown");

      // Forward to Agent Zero
      if (msg.type === "agent_message" || msg.type === "command") {
        const response = await forwardToAgent(msg);
        ws.send(JSON.stringify({ type: "agent_response", data: response, id: msg.id }));
      }

      // Broadcast to channel
      if (msg.type === "broadcast") {
        broadcastToChannel(channel, { type: "broadcast", from: id, data: msg.data }, id);
      }
    } catch (err) {
      ws.send(JSON.stringify({ type: "error", message: err.message }));
    }
  });

  ws.on("close", () => {
    connections.delete(id);
    const count = (channels.get(channel) || 1) - 1;
    if (count <= 0) channels.delete(channel);
    else channels.set(channel, count);
    console.log(`[OpenClaw] Client disconnected: ${id}`);
  });

  ws.send(JSON.stringify({ type: "connected", id, channel }));
});

// ── HTTP Webhook Server ─────────────────────────────────────
const httpServer = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${HTTP_PORT}`);

  // Health check
  if (url.pathname === "/health" || url.pathname === "/ok") {
    res.writeHead(200, { "Content-Type": "application/json" });
    return res.end(JSON.stringify({
      status: "healthy",
      channels: Object.fromEntries(channels),
      connections: connections.size,
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
    }));
  }

  // Channel status
  if (url.pathname === "/status") {
    res.writeHead(200, { "Content-Type": "application/json" });
    return res.end(JSON.stringify({
      channels: Object.fromEntries(channels),
      connections: connections.size,
      uptime_hours: (process.uptime() / 3600).toFixed(2),
    }));
  }

  // Telegram webhook
  if (url.pathname === "/webhook/telegram") {
    const body = await readBody(req);
    try {
      const update = JSON.parse(body);
      await forwardToAgent({ type: "telegram", data: update });
      res.writeHead(200);
      return res.end("ok");
    } catch (e) {
      res.writeHead(400);
      return res.end(JSON.stringify({ error: e.message }));
    }
  }

  // Twilio webhook
  if (url.pathname === "/webhook/twilio") {
    const body = await readBody(req);
    await forwardToAgent({ type: "twilio", data: body });
    res.writeHead(200, { "Content-Type": "text/xml" });
    return res.end("<Response><Say>Message received.</Say></Response>");
  }

  // Generic webhook
  if (url.pathname.startsWith("/webhook/")) {
    const channel = url.pathname.replace("/webhook/", "");
    const body = await readBody(req);
    try {
      const data = JSON.parse(body);
      await forwardToAgent({ type: channel, data });
      broadcastToChannel(channel, { type: "webhook", channel, data });
      res.writeHead(200);
      return res.end(JSON.stringify({ received: true }));
    } catch (e) {
      res.writeHead(400);
      return res.end(JSON.stringify({ error: e.message }));
    }
  }

  // 404
  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "Not found", endpoints: ["/health", "/status", "/webhook/:channel"] }));
});

httpServer.listen(HTTP_PORT, () => {
  console.log(`[OpenClaw] HTTP webhook server listening on port ${HTTP_PORT}`);
});

// ── Helpers ─────────────────────────────────────────────────

async function forwardToAgent(message) {
  return new Promise((resolve) => {
    const postData = JSON.stringify(message);
    const url = new URL(AGENT_ZERO_URL + "/message");
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(postData) },
      timeout: 30000,
    };

    const req = http.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try { resolve(JSON.parse(data)); }
        catch { resolve({ raw: data }); }
      });
    });
    req.on("error", () => resolve({ error: "Agent unreachable" }));
    req.on("timeout", () => { req.destroy(); resolve({ error: "timeout" }); });
    req.write(postData);
    req.end();
  });
}

function broadcastToChannel(channel, message, excludeId) {
  const payload = JSON.stringify(message);
  for (const [id, conn] of connections) {
    if (conn.channel === channel && id !== excludeId && conn.ws.readyState === 1) {
      conn.ws.send(payload);
    }
  }
}

function readBody(req) {
  return new Promise((resolve) => {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", () => resolve(body));
  });
}

// ── Graceful shutdown ───────────────────────────────────────
process.on("SIGTERM", () => {
  console.log("[OpenClaw] Shutting down...");
  wss.close();
  httpServer.close();
  process.exit(0);
});

console.log("[OpenClaw] Gateway initialized — 16-channel messaging hub ready");

} // end of v1 dead code block
