import { requestExternalAccess } from "@/lib/accessKernel";

/**
 * API Proxy Route - Agent Zero Backend Integration
 * Handles communication between frontend and Docker MCP server
 */

export async function POST(request: Request) {
  const { message, timestamp, work_item_id } = await request.json();

  if (!work_item_id) {
    return new Response(
      JSON.stringify({ success: false, response: "work_item_id is required", agent: "Access Kernel" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  try {
    const decision = await requestExternalAccess(work_item_id);
    if (decision.status !== "approved" && decision.status !== "pending_approval") {
      return new Response(
        JSON.stringify({ success: false, response: "Access denied by Access Kernel", agent: "Access Kernel" }),
        { status: 403, headers: { "Content-Type": "application/json" } }
      );
    }
  } catch {
    return new Response(
      JSON.stringify({ success: false, response: "Access Kernel unavailable", agent: "Access Kernel" }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }

  try {
    const response = await fetch('http://localhost:3000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, timestamp }),
    });

    if (!response.ok) {
      throw new Error(`MCP Server returned ${response.status}`);
    }

    const data = await response.json();
    return new Response(
      JSON.stringify({
        success: true,
        response: data.response || 'Message processed',
        agent: data.agent || 'Agent Zero',
      }),
      { headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({
        success: false,
        response: 'Backend connection failed. Running in demo mode.',
        agent: 'Agent Zero (Demo)',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

export async function OPTIONS() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}

export async function GET() {
  try {
    const response = await fetch('http://localhost:3000/health');
    const data = await response.json();
    return new Response(JSON.stringify(data), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    return new Response(
      JSON.stringify({ success: false, status: 'offline' }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
