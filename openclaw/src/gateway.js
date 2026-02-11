/**
 * OpenClaw Gateway v2.0 — Multi-App Deployment Hub
 * =================================================
 * 16-channel messaging + app registry + deploy streaming + queue.
 *
 * Ports:
 *   WS   :18789 — WebSocket (messaging + deploy streaming)
 *   HTTP  :18790 — REST API (webhooks + app management)
 */

const http = require("http");
const crypto = require("crypto");
const { WebSocketServer } = require("ws");

const { AppRegistry } = require("./registry");
const { DeployStream } = require("./deploy-stream");
const { DeployQueue } = require("./queue");

// ── Config ──────────────────────────────────────────────────
const WS_PORT = parseInt(process.env.WS_PORT || "18789", 10);
const HTTP_PORT = parseInt(process.env.HTTP_PORT || "18790", 10);
const AGENT_ZERO_URL = process.env.AGENT_ZERO_URL || "http://agent-zero:5000";

// ── Initialize Modules ─────────────────────────────────────
const registry = new AppRegistry();
const queue = new DeployQueue();

const connections = new Map(); // ws id → { ws, channel, metadata }
const channels = new Map(); // channel → connection count

// ── WebSocket Server ────────────────────────────────────────
const wss = new WebSocketServer({ port: WS_PORT }, () => {
  console.log(`[OpenClaw] WebSocket server on :${WS_PORT}`);
});

const deployStream = new DeployStream(wss);

wss.on("connection", (ws, req) => {
  const id = crypto.randomUUID();
  const rawPath = req.url?.replace("/", "") || "default";

  // Deploy stream subscription: /deploy/{app-name}
  if (rawPath.startsWith("deploy/")) {
    const appName = rawPath.replace("deploy/", "");
    deployStream.subscribe(appName, ws);
    ws.send(
      JSON.stringify({
        type: "subscribed",
        channel: `deploy/${appName}`,
        id,
      })
    );
    return;
  }

  // Standard messaging channel
  const channel = rawPath;
  connections.set(id, {
    ws,
    channel,
    connectedAt: new Date().toISOString(),
  });
  channels.set(channel, (channels.get(channel) || 0) + 1);

  console.log(`[OpenClaw] Connected: ${id} on channel: ${channel}`);

  ws.on("message", async (raw) => {
    try {
      const msg = JSON.parse(raw.toString());

      if (msg.type === "agent_message" || msg.type === "command") {
        const response = await forwardToAgent(msg);
        ws.send(
          JSON.stringify({
            type: "agent_response",
            data: response,
            id: msg.id,
          })
        );
      }

      if (msg.type === "broadcast") {
        broadcastToChannel(
          channel,
          { type: "broadcast", from: id, data: msg.data },
          id
        );
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
  });

  ws.send(JSON.stringify({ type: "connected", id, channel }));
});

// ── HTTP Server ─────────────────────────────────────────────
const httpServer = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${HTTP_PORT}`);
  const method = req.method;

  // ── Health / Status ─────────────────────────────────────
  if (url.pathname === "/health" || url.pathname === "/ok") {
    return json(res, 200, {
      status: "healthy",
      version: "2.0.0",
      channels: Object.fromEntries(channels),
      connections: connections.size,
      apps: registry.list().length,
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
    });
  }

  if (url.pathname === "/status") {
    return json(res, 200, {
      channels: Object.fromEntries(channels),
      connections: connections.size,
      apps: registry.list().length,
      activeStreams: deployStream.activeChannels(),
      deployQueue: queue.status(),
      uptime_hours: (process.uptime() / 3600).toFixed(2),
    });
  }

  // ── App Registry API ────────────────────────────────────

  // GET /apps — list all apps
  if (url.pathname === "/apps" && method === "GET") {
    return json(res, 200, { apps: registry.list() });
  }

  // POST /apps — register a new app
  if (url.pathname === "/apps" && method === "POST") {
    const body = await readBody(req);
    try {
      const data = JSON.parse(body);
      if (!data.name) return json(res, 400, { error: "name is required" });
      const entry = registry.register(data.name, data);
      return json(res, 201, entry);
    } catch (e) {
      return json(res, 400, { error: e.message });
    }
  }

  // GET /apps/:name — get app details
  const appMatch = url.pathname.match(/^\/apps\/([^/]+)$/);
  if (appMatch && method === "GET") {
    const app = registry.get(appMatch[1]);
    if (!app) return json(res, 404, { error: "App not found" });
    return json(res, 200, app);
  }

  // GET /apps/:name/status — detailed status with queue
  const statusMatch = url.pathname.match(/^\/apps\/([^/]+)\/status$/);
  if (statusMatch && method === "GET") {
    const name = statusMatch[1];
    const app = registry.get(name);
    if (!app) return json(res, 404, { error: "App not found" });
    return json(res, 200, {
      ...app,
      queue: queue.getState(name),
      streamSubscribers: deployStream.subscriberCount(name),
    });
  }

  // DELETE /apps/:name — remove app from registry
  const delMatch = url.pathname.match(/^\/apps\/([^/]+)$/);
  if (delMatch && method === "DELETE") {
    const removed = registry.remove(delMatch[1]);
    return json(res, removed ? 200 : 404, {
      removed,
      name: delMatch[1],
    });
  }

  // ── Deploy API ──────────────────────────────────────────

  // POST /deploy/:name — trigger deployment
  const deployMatch = url.pathname.match(/^\/deploy\/([^/]+)$/);
  if (deployMatch && method === "POST") {
    const name = deployMatch[1];
    const app = registry.get(name);
    if (!app)
      return json(res, 404, {
        error: `App '${name}' not registered. POST /apps first.`,
      });

    const body = await readBody(req);
    let jobData = {};
    try {
      jobData = body ? JSON.parse(body) : {};
    } catch {
      /* empty body is fine */
    }

    const queueResult = queue.enqueue(name, {
      appName: name,
      trigger: jobData.trigger || "api",
      ...jobData,
    });

    if (queueResult.immediate) {
      // Start deploy — forward to Agent Zero
      registry.recordDeploy(name, { trigger: jobData.trigger || "api" });
      deployStream.status(name, "started", { trigger: jobData.trigger });

      // Fire-and-forget deploy request to Agent Zero
      forwardToAgent({
        type: "deploy",
        appName: name,
        data: { ...app, ...jobData },
      }).then((result) => {
        const status = result.error ? "failed" : "finished";
        queue.complete(name, status);
        registry.finishDeploy(name, null, status, null);
        deployStream.status(name, status, result);
      });

      return json(res, 202, {
        message: `Deployment started for '${name}'`,
        position: 0,
      });
    } else {
      return json(res, 202, {
        message: `Deployment queued for '${name}'`,
        position: queueResult.position,
      });
    }
  }

  // POST /apps/:name/rollback — trigger rollback
  const rollbackMatch = url.pathname.match(/^\/apps\/([^/]+)\/rollback$/);
  if (rollbackMatch && method === "POST") {
    const name = rollbackMatch[1];
    const app = registry.get(name);
    if (!app) return json(res, 404, { error: "App not found" });

    deployStream.status(name, "rolling_back");
    forwardToAgent({
      type: "rollback",
      appName: name,
      data: app,
    });

    return json(res, 202, { message: `Rollback triggered for '${name}'` });
  }

  // ── Webhooks (16-channel) ─────────────────────────────────

  if (url.pathname === "/webhook/telegram") {
    const body = await readBody(req);
    try {
      const update = JSON.parse(body);
      await forwardToAgent({ type: "telegram", data: update });
      return text(res, 200, "ok");
    } catch (e) {
      return json(res, 400, { error: e.message });
    }
  }

  if (url.pathname === "/webhook/twilio") {
    const body = await readBody(req);
    await forwardToAgent({ type: "twilio", data: body });
    res.writeHead(200, { "Content-Type": "text/xml" });
    return res.end("<Response><Say>Message received.</Say></Response>");
  }

  if (url.pathname.startsWith("/webhook/")) {
    const channel = url.pathname.replace("/webhook/", "");
    const body = await readBody(req);
    try {
      const data = JSON.parse(body);
      await forwardToAgent({ type: channel, data });
      broadcastToChannel(channel, { type: "webhook", channel, data });
      return json(res, 200, { received: true });
    } catch (e) {
      return json(res, 400, { error: e.message });
    }
  }

  // ── 404 ─────────────────────────────────────────────────
  return json(res, 404, {
    error: "Not found",
    endpoints: [
      "GET  /health",
      "GET  /status",
      "GET  /apps",
      "POST /apps",
      "GET  /apps/:name",
      "GET  /apps/:name/status",
      "DEL  /apps/:name",
      "POST /deploy/:name",
      "POST /apps/:name/rollback",
      "POST /webhook/:channel",
    ],
  });
});

httpServer.listen(HTTP_PORT, () => {
  console.log(`[OpenClaw] HTTP server on :${HTTP_PORT}`);
});

// Start health polling
registry.startHealthPolling();

// ── Helpers ─────────────────────────────────────────────────

function json(res, status, data) {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(data));
}

function text(res, status, body) {
  res.writeHead(status, { "Content-Type": "text/plain" });
  res.end(body);
}

async function forwardToAgent(message) {
  return new Promise((resolve) => {
    const postData = JSON.stringify(message);
    const url = new URL(AGENT_ZERO_URL + "/message");
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(postData),
      },
      timeout: 30000,
    };

    const req = http.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve({ raw: data });
        }
      });
    });
    req.on("error", () => resolve({ error: "Agent unreachable" }));
    req.on("timeout", () => {
      req.destroy();
      resolve({ error: "timeout" });
    });
    req.write(postData);
    req.end();
  });
}

function broadcastToChannel(channel, message, excludeId) {
  const payload = JSON.stringify(message);
  for (const [id, conn] of connections) {
    if (
      conn.channel === channel &&
      id !== excludeId &&
      conn.ws.readyState === 1
    ) {
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
  registry.stopHealthPolling();
  wss.close();
  httpServer.close();
  process.exit(0);
});

console.log("[OpenClaw] Gateway v2.0 initialized — multi-app hub ready");
