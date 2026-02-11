/**
 * OpenClaw Deploy Queue — Prevents concurrent deploys
 * ====================================================
 * Ensures only one deploy runs per app at a time.
 * Queues sequential deploys across different apps.
 */

class DeployQueue {
  constructor() {
    /** @type {Map<string, {current: object|null, queue: object[]}>} */
    this.slots = new Map();
  }

  /**
   * Enqueue a deploy job. Returns true if it starts immediately,
   * false if it's queued behind another deploy.
   */
  enqueue(appName, job) {
    if (!this.slots.has(appName)) {
      this.slots.set(appName, { current: null, queue: [] });
    }

    const slot = this.slots.get(appName);

    if (slot.current === null) {
      slot.current = {
        ...job,
        startedAt: new Date().toISOString(),
        status: "running",
      };
      return { immediate: true, position: 0 };
    }

    // Queue behind the current deploy
    const position = slot.queue.length + 1;
    slot.queue.push({
      ...job,
      queuedAt: new Date().toISOString(),
      status: "queued",
    });
    return { immediate: false, position };
  }

  /**
   * Mark current deploy as complete and start next in queue.
   * Returns the next job if any, or null.
   */
  complete(appName, status = "finished") {
    const slot = this.slots.get(appName);
    if (!slot) return null;

    if (slot.current) {
      slot.current.status = status;
      slot.current.finishedAt = new Date().toISOString();
    }

    // Start next in queue
    if (slot.queue.length > 0) {
      slot.current = {
        ...slot.queue.shift(),
        startedAt: new Date().toISOString(),
        status: "running",
      };
      return slot.current;
    }

    slot.current = null;
    return null;
  }

  /**
   * Get current deploy state for an app.
   */
  getState(appName) {
    const slot = this.slots.get(appName);
    if (!slot) return { current: null, queued: 0 };
    return {
      current: slot.current,
      queued: slot.queue.length,
    };
  }

  /**
   * Check if an app is currently deploying.
   */
  isDeploying(appName) {
    const slot = this.slots.get(appName);
    return slot?.current?.status === "running";
  }

  /**
   * Get all active deploys across all apps.
   */
  activeCount() {
    let count = 0;
    for (const slot of this.slots.values()) {
      if (slot.current?.status === "running") count++;
    }
    return count;
  }

  /**
   * Get full queue status for all apps.
   */
  status() {
    const result = {};
    for (const [app, slot] of this.slots) {
      result[app] = {
        deploying: slot.current?.status === "running",
        queued: slot.queue.length,
        current: slot.current,
      };
    }
    return result;
  }
}

module.exports = { DeployQueue };
