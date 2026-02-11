/**
 * OpenClaw App Registry — Multi-App Deployment Tracking
 * ======================================================
 * In-memory registry of all deployed applications with
 * status tracking, health polling, and deployment history.
 *
 * Persists to registry.json on disk for restart resilience.
 */

const fs = require("fs");
const path = require("path");
const http = require("http");

const REGISTRY_FILE = path.join(__dirname, "..", "data", "registry.json");
const HEALTH_INTERVAL = 60_000; // 60s between health polls

class AppRegistry {
  constructor() {
    /** @type {Map<string, AppEntry>} */
    this.apps = new Map();
    this._healthTimer = null;
    this._load();
  }

  // ── CRUD ────────────────────────────────────────────────

  register(name, data = {}) {
    const entry = {
      name,
      uuid: data.uuid || null,
      url: data.url || null,
      type: data.type || "unknown",
      port: data.port || 3000,
      status: "registered",
      health: "unknown",
      lastDeploy: null,
      lastHealthCheck: null,
      deployHistory: [],
      createdAt: new Date().toISOString(),
      ...data,
    };
    this.apps.set(name, entry);
    this._save();
    return entry;
  }

  update(name, data) {
    const entry = this.apps.get(name);
    if (!entry) return null;
    Object.assign(entry, data);
    this._save();
    return entry;
  }

  get(name) {
    return this.apps.get(name) || null;
  }

  list() {
    return Array.from(this.apps.values());
  }

  remove(name) {
    const had = this.apps.delete(name);
    if (had) this._save();
    return had;
  }

  // ── Deploy Tracking ───────────────────────────────────────

  recordDeploy(name, deployData) {
    const entry = this.apps.get(name);
    if (!entry) return null;

    const record = {
      deploy_uuid: deployData.deploy_uuid || null,
      status: deployData.status || "started",
      startedAt: new Date().toISOString(),
      finishedAt: null,
      elapsed: null,
      trigger: deployData.trigger || "api",
    };

    entry.deployHistory.push(record);
    entry.lastDeploy = record;
    entry.status = "deploying";

    // Keep last 20 deploys
    if (entry.deployHistory.length > 20) {
      entry.deployHistory = entry.deployHistory.slice(-20);
    }

    this._save();
    return record;
  }

  finishDeploy(name, deployUuid, status, elapsed) {
    const entry = this.apps.get(name);
    if (!entry) return;

    const record = entry.deployHistory.find(
      (d) => d.deploy_uuid === deployUuid
    );
    if (record) {
      record.status = status;
      record.finishedAt = new Date().toISOString();
      record.elapsed = elapsed;
    }

    entry.status = status === "finished" ? "running" : "failed";
    entry.lastDeploy = record || entry.lastDeploy;
    this._save();
  }

  // ── Health Polling ────────────────────────────────────────

  startHealthPolling(intervalMs = HEALTH_INTERVAL) {
    if (this._healthTimer) clearInterval(this._healthTimer);
    this._healthTimer = setInterval(() => this._pollAll(), intervalMs);
    console.log(
      `[Registry] Health polling started (every ${intervalMs / 1000}s)`
    );
  }

  stopHealthPolling() {
    if (this._healthTimer) {
      clearInterval(this._healthTimer);
      this._healthTimer = null;
    }
  }

  async _pollAll() {
    for (const [name, entry] of this.apps) {
      if (!entry.url) continue;
      try {
        const healthy = await this._checkHealth(entry.url);
        entry.health = healthy ? "healthy" : "unhealthy";
        entry.lastHealthCheck = new Date().toISOString();
      } catch {
        entry.health = "unreachable";
        entry.lastHealthCheck = new Date().toISOString();
      }
    }
    this._save();
  }

  _checkHealth(baseUrl) {
    return new Promise((resolve) => {
      const url = new URL("/health", baseUrl);
      const req = http.get(
        url.toString(),
        { timeout: 10_000, headers: { "User-Agent": "OpenClaw/2.0" } },
        (res) => {
          resolve(res.statusCode === 200);
        }
      );
      req.on("error", () => resolve(false));
      req.on("timeout", () => {
        req.destroy();
        resolve(false);
      });
    });
  }

  // ── Persistence ───────────────────────────────────────────

  _save() {
    try {
      const dir = path.dirname(REGISTRY_FILE);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      const data = Object.fromEntries(this.apps);
      fs.writeFileSync(REGISTRY_FILE, JSON.stringify(data, null, 2));
    } catch (err) {
      console.error("[Registry] Save failed:", err.message);
    }
  }

  _load() {
    try {
      if (fs.existsSync(REGISTRY_FILE)) {
        const raw = JSON.parse(fs.readFileSync(REGISTRY_FILE, "utf-8"));
        for (const [name, entry] of Object.entries(raw)) {
          this.apps.set(name, entry);
        }
        console.log(`[Registry] Loaded ${this.apps.size} apps from disk`);
      }
    } catch (err) {
      console.error("[Registry] Load failed:", err.message);
    }
  }
}

module.exports = { AppRegistry };
