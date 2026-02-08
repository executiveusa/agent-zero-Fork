/**
 * MCP Docker Server — Node.js MCP server for Docker & agent orchestration
 *
 * Provides Model Context Protocol (MCP) endpoints for:
 * - Health checks across all containers
 * - Agent discovery and status
 * - Docker container management
 * - OpenClaw gateway status
 *
 * Designed to run as a sidecar container or standalone process.
 * Communicates via stdio MCP protocol.
 */

const { execSync } = require("child_process");
const http = require("http");
const os = require("os");

const PORT = parseInt(process.env.MCP_DOCKER_PORT || "18800", 10);
const AGENT_ZERO_URL = process.env.AGENT_ZERO_URL || "http://127.0.0.1:50001";
const OPENCLAW_WS = process.env.OPENCLAW_GATEWAY_URL || "ws://127.0.0.1:18789";

// Helpers

function runCommand(cmd, timeout) {
  timeout = timeout || 10000;
  try {
    return execSync(cmd, { timeout: timeout, encoding: "utf-8" }).trim();
  } catch (e) {
    return null;
  }
}

function getDockerContainers() {
  var raw = runCommand(
    'docker ps --format "{{.Names}}|{{.Status}}|{{.Image}}|{{.Ports}}" 2>&1'
  );
  if (!raw) return [];

  return raw.split("\n").filter(Boolean).map(function (line) {
    var parts = line.split("|");
    return {
      name: parts[0] || "unknown",
      status: parts[1] || "unknown",
      image: parts[2] || "unknown",
      ports: parts[3] || "",
      healthy: (parts[1] || "").toLowerCase().indexOf("up") >= 0,
    };
  });
}

function httpGet(url, timeout) {
  timeout = timeout || 5000;
  return new Promise(function (resolve) {
    var req = http.get(url, { timeout: timeout }, function (res) {
      var data = "";
      res.on("data", function (chunk) { data += chunk; });
      res.on("end", function () { resolve({ status: res.statusCode, data: data }); });
    });
    req.on("error", function () { resolve(null); });
    req.on("timeout", function () { req.destroy(); resolve(null); });
  });
}

// MCP Tool Definitions

var TOOLS = {
  health_check: {
    description: "Check health of all Agent Claw services",
    inputSchema: { type: "object", properties: {} },
    handler: function () {
      var services = {};
      var containers = getDockerContainers();
      services.docker = {
        available: containers.length > 0,
        containers: containers.map(function (c) {
          return { name: c.name, status: c.status, healthy: c.healthy };
        }),
      };
      services.system = {
        platform: os.platform(),
        memory_free_mb: Math.round(os.freemem() / 1024 / 1024),
        memory_total_mb: Math.round(os.totalmem() / 1024 / 1024),
        cpus: os.cpus().length,
        uptime_hours: Math.round(os.uptime() / 3600),
      };
      return httpGet(AGENT_ZERO_URL + "/ok").then(function (a0) {
        services.agent_zero = {
          available: a0 !== null && a0.status === 200,
          url: AGENT_ZERO_URL,
        };
        var allHealthy = services.agent_zero.available && containers.every(function (c) { return c.healthy; });
        return { healthy: allHealthy, services: services, timestamp: new Date().toISOString() };
      });
    },
  },

  list_containers: {
    description: "List all Docker containers with status",
    inputSchema: { type: "object", properties: {} },
    handler: function () {
      var containers = getDockerContainers();
      return Promise.resolve({ count: containers.length, containers: containers });
    },
  },

  container_logs: {
    description: "Get recent logs from a Docker container",
    inputSchema: {
      type: "object",
      properties: {
        container: { type: "string", description: "Container name" },
        lines: { type: "number", description: "Number of log lines" },
      },
      required: ["container"],
    },
    handler: function (args) {
      var lines = args.lines || 50;
      var logs = runCommand("docker logs --tail " + lines + " " + args.container + " 2>&1", 15000);
      return Promise.resolve({
        container: args.container,
        lines: lines,
        logs: logs || "No logs available or container not found",
      });
    },
  },

  restart_container: {
    description: "Restart a Docker container",
    inputSchema: {
      type: "object",
      properties: {
        container: { type: "string", description: "Container name to restart" },
      },
      required: ["container"],
    },
    handler: function (args) {
      var result = runCommand("docker restart " + args.container + " 2>&1", 30000);
      return Promise.resolve({
        container: args.container,
        result: result || "Restart command sent",
        success: result !== null,
      });
    },
  },

  agent_status: {
    description: "Get Agent Zero status and active contexts",
    inputSchema: { type: "object", properties: {} },
    handler: function () {
      return httpGet(AGENT_ZERO_URL + "/ok").then(function (ok) {
        if (!ok || ok.status !== 200) {
          return { available: false, error: "Agent Zero not responding" };
        }
        return httpGet(AGENT_ZERO_URL + "/chats").then(function (chats) {
          var activeChats = 0;
          if (chats && chats.status === 200) {
            try {
              var data = JSON.parse(chats.data);
              activeChats = Array.isArray(data) ? data.length : 0;
            } catch (e) { activeChats = 0; }
          }
          return {
            available: true,
            url: AGENT_ZERO_URL,
            active_chats: activeChats,
            timestamp: new Date().toISOString(),
          };
        });
      });
    },
  },

  openclaw_status: {
    description: "Check OpenClaw messaging gateway status",
    inputSchema: { type: "object", properties: {} },
    handler: function () {
      var containers = getDockerContainers();
      var openclawContainer = containers.find(function (c) {
        return c.name.indexOf("openclaw") >= 0 || c.name.indexOf("clawbot") >= 0 || c.name.indexOf("whatsapp") >= 0;
      });
      return Promise.resolve({
        container: openclawContainer || null,
        gateway_url: OPENCLAW_WS,
        running: openclawContainer ? openclawContainer.healthy : false,
      });
    },
  },
};

// MCP stdio Protocol Handler

function MCPServer() {
  this.tools = TOOLS;
  this.buffer = "";
}

MCPServer.prototype.start = function () {
  var self = this;
  process.stdin.setEncoding("utf-8");
  process.stdin.on("data", function (chunk) {
    self.buffer += chunk;
    self.processBuffer();
  });
  process.stderr.write("MCP Docker Server started. " + Object.keys(this.tools).length + " tools available.\n");
};

MCPServer.prototype.processBuffer = function () {
  var lines = this.buffer.split("\n");
  this.buffer = lines.pop() || "";
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];
    if (!line.trim()) continue;
    try {
      var message = JSON.parse(line);
      this.handleMessage(message);
    } catch (e) {
      process.stderr.write("Invalid JSON: " + line.substring(0, 100) + "\n");
    }
  }
};

MCPServer.prototype.handleMessage = function (msg) {
  var self = this;
  var id = msg.id;
  var method = msg.method;
  var params = msg.params;

  switch (method) {
    case "initialize":
      self.respond(id, {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: "agent-claw-docker-mcp", version: "1.0.0" },
      });
      break;
    case "tools/list":
      var toolList = Object.keys(self.tools).map(function (name) {
        return { name: name, description: self.tools[name].description, inputSchema: self.tools[name].inputSchema };
      });
      self.respond(id, { tools: toolList });
      break;
    case "tools/call":
      self.handleToolCall(id, params);
      break;
    case "notifications/initialized":
      break;
    default:
      self.respondError(id, -32601, "Unknown method: " + method);
  }
};

MCPServer.prototype.handleToolCall = function (id, params) {
  var self = this;
  var name = (params || {}).name;
  var args = (params || {}).arguments || {};
  var tool = self.tools[name];

  if (!tool) {
    self.respondError(id, -32602, "Unknown tool: " + name);
    return;
  }

  Promise.resolve(tool.handler(args)).then(function (result) {
    self.respond(id, {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    });
  }).catch(function (e) {
    self.respond(id, {
      content: [{ type: "text", text: JSON.stringify({ error: e.message }) }],
      isError: true,
    });
  });
};

MCPServer.prototype.respond = function (id, result) {
  process.stdout.write(JSON.stringify({ jsonrpc: "2.0", id: id, result: result }) + "\n");
};

MCPServer.prototype.respondError = function (id, code, message) {
  process.stdout.write(JSON.stringify({ jsonrpc: "2.0", id: id, error: { code: code, message: message } }) + "\n");
};

// HTTP health endpoint

var httpServer = http.createServer(function (req, res) {
  res.setHeader("Content-Type", "application/json");
  if (req.url === "/health" || req.url === "/ok") {
    TOOLS.health_check.handler({}).then(function (result) {
      res.writeHead(result.healthy ? 200 : 503);
      res.end(JSON.stringify(result));
    });
  } else if (req.url === "/tools") {
    var list = Object.keys(TOOLS).map(function (n) {
      return { name: n, description: TOOLS[n].description };
    });
    res.writeHead(200);
    res.end(JSON.stringify(list));
  } else {
    res.writeHead(404);
    res.end(JSON.stringify({ error: "Not found" }));
  }
});

httpServer.listen(PORT, function () {
  process.stderr.write("MCP Docker HTTP server on port " + PORT + "\n");
});

// Start MCP stdio server
var mcp = new MCPServer();
mcp.start();
