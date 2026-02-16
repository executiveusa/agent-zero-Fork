const targetUrl = process.env.AGENT_ZERO_URL || "http://localhost:3000";

async function run() {
  try {
    const response = await fetch(targetUrl, { method: "GET" });
    if (!response.ok) {
      console.error(`Smoke check failed: ${response.status} ${response.statusText}`);
      process.exit(1);
    }

    const html = await response.text();
    if (!html || html.length < 50) {
      console.error("Smoke check failed: response body too small");
      process.exit(1);
    }

    console.log(`Smoke check passed: ${targetUrl} -> ${response.status}`);
    process.exit(0);
  } catch (error) {
    console.error("Smoke check failed:", error.message);
    process.exit(1);
  }
}

run();
