/**
 * OpenClaw Deploy Stream — WebSocket live deployment logs
 * ========================================================
 * Broadcasts Coolify deployment status updates to connected
 * clients via WebSocket channels at /deploy/{app-name}.
 */

class DeployStream {
  constructor(wss) {
    /** @type {Map<string, Set<WebSocket>>} */
    this.subscribers = new Map();
    this.wss = wss;
  }

  /**
   * Subscribe a WebSocket to a deploy channel.
   * @param {string} appName
   * @param {WebSocket} ws
   */
  subscribe(appName, ws) {
    if (!this.subscribers.has(appName)) {
      this.subscribers.set(appName, new Set());
    }
    this.subscribers.get(appName).add(ws);

    ws.on("close", () => {
      const subs = this.subscribers.get(appName);
      if (subs) {
        subs.delete(ws);
        if (subs.size === 0) this.subscribers.delete(appName);
      }
    });
  }

  /**
   * Broadcast a deploy event to all subscribers of an app.
   * @param {string} appName
   * @param {object} event - {type, status, message, timestamp, ...}
   */
  broadcast(appName, event) {
    const subs = this.subscribers.get(appName);
    if (!subs || subs.size === 0) return;

    const payload = JSON.stringify({
      type: "deploy_event",
      app: appName,
      timestamp: new Date().toISOString(),
      ...event,
    });

    for (const ws of subs) {
      if (ws.readyState === 1) {
        // OPEN
        ws.send(payload);
      }
    }
  }

  /**
   * Broadcast a deploy log line.
   */
  log(appName, message, level = "info") {
    this.broadcast(appName, {
      type: "deploy_log",
      level,
      message,
    });
  }

  /**
   * Broadcast a deploy status change.
   */
  status(appName, status, details = {}) {
    this.broadcast(appName, {
      type: "deploy_status",
      status,
      ...details,
    });
  }

  /**
   * Get subscriber count for an app.
   */
  subscriberCount(appName) {
    return this.subscribers.get(appName)?.size || 0;
  }

  /**
   * Get all apps with active subscribers.
   */
  activeChannels() {
    const result = {};
    for (const [app, subs] of this.subscribers) {
      result[app] = subs.size;
    }
    return result;
  }
}

module.exports = { DeployStream };
