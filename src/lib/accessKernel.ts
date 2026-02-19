export type GrantDecision = {
  grant_id?: string;
  status: "approved" | "pending_approval" | "denied" | string;
};

const ACCESS_KERNEL_BASE = process.env.ACCESS_KERNEL_BASE_URL || "http://localhost:8090";

export async function requestExternalAccess(workItemId: string, principal = "agent-zero"): Promise<GrantDecision> {
  const response = await fetch(`${ACCESS_KERNEL_BASE}/v1/grants/request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      principal,
      principal_type: "agent",
      work_item_id: workItemId,
      resource: "external_api",
      action: "write",
      duration_minutes: 15,
    }),
  });

  if (!response.ok) {
    throw new Error(`Access Kernel request failed with ${response.status}`);
  }

  return (await response.json()) as GrantDecision;
}
