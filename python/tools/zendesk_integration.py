"""Zendesk integration for Agent Zero.

Actions
-------
create_ticket   – open a new ticket
get_ticket      – fetch a single ticket by ID
list_tickets    – list tickets, optionally filtered by status
search          – full-text search across tickets
update_ticket   – update arbitrary ticket fields
add_comment     – append an internal or public comment
close_ticket    – set status to closed
assign_ticket   – assign to an agent (assignee_id) or group (group_id)
list_agents     – enumerate agents available for assignment
list_groups     – enumerate support groups
bulk_create     – create up to 100 tickets in one call

Environment
-----------
ZENDESK_SUBDOMAIN   your-company (https://<subdomain>.zendesk.com)
ZENDESK_EMAIL       agent email address used for Basic auth
ZENDESK_API_KEY     API key (Settings → Agents → API keys)
"""

import base64
import os
from typing import Dict, List, Optional

import requests


class ZendeskIntegration:
    def __init__(self) -> None:
        self.subdomain = os.getenv("ZENDESK_SUBDOMAIN", "")
        self.email = os.getenv("ZENDESK_EMAIL", "")
        self.api_key = os.getenv("ZENDESK_API_KEY", "")
        self.base_url = f"https://{self.subdomain}.zendesk.com/api/v2"

        credentials = base64.b64encode(f"{self.email}:{self.api_key}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # low-level
    # ------------------------------------------------------------------
    def _request(self, method: str, endpoint: str, data: Optional[dict] = None,
                 params: Optional[dict] = None) -> dict:
        response = requests.request(
            method,
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=data,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json() if response.text else {}

    # ------------------------------------------------------------------
    # tickets
    # ------------------------------------------------------------------
    def create_ticket(self, subject: str, body: str, *,
                      requester_email: Optional[str] = None,
                      priority: str = "normal",
                      tags: Optional[List[str]] = None,
                      assignee_id: Optional[int] = None,
                      group_id: Optional[int] = None) -> dict:
        ticket: Dict = {
            "subject": subject,
            "comment": {"body": body},
            "priority": priority,
        }
        if requester_email:
            ticket["requester"] = {"email": requester_email}
        if tags:
            ticket["tags"] = tags
        if assignee_id is not None:
            ticket["assignee_id"] = assignee_id
        if group_id is not None:
            ticket["group_id"] = group_id

        result = self._request("POST", "/tickets", data={"ticket": ticket})
        t = result["ticket"]
        return {"success": True, "ticket_id": t["id"], "ticket_url": t["html_url"], "status": t["status"]}

    def get_ticket(self, ticket_id: int) -> dict:
        result = self._request("GET", f"/tickets/{ticket_id}")
        t = result["ticket"]
        return {
            "success": True,
            "ticket": {
                "id": t["id"],
                "subject": t["subject"],
                "status": t["status"],
                "priority": t["priority"],
                "tags": t.get("tags", []),
                "requester_id": t.get("requester_id"),
                "assignee_id": t.get("assignee_id"),
                "group_id": t.get("group_id"),
                "created_at": t.get("created_at"),
                "updated_at": t.get("updated_at"),
                "url": t["html_url"],
            },
        }

    def list_tickets(self, status: Optional[str] = None, page_size: int = 25,
                     sort_by: str = "created_at", sort_order: str = "desc") -> dict:
        params: Dict = {"page[size]": page_size, "sort_by": sort_by, "sort_order": sort_order}
        if status:
            params["status"] = status

        result = self._request("GET", "/tickets", params=params)
        tickets = [
            {"id": t["id"], "subject": t["subject"], "status": t["status"],
             "priority": t["priority"], "created_at": t.get("created_at"), "url": t["html_url"]}
            for t in result.get("tickets", [])
        ]
        return {"success": True, "tickets": tickets, "count": len(tickets)}

    def search_tickets(self, query: str, page_size: int = 25) -> dict:
        result = self._request("GET", "/search/export",
                               params={"query": query, "page[size]": page_size})
        tickets = [
            {"id": t["id"], "subject": t["subject"], "status": t["status"],
             "priority": t["priority"], "url": t.get("html_url", "")}
            for t in result.get("results", [])
            if t.get("object_type") == "ticket"
        ]
        return {"success": True, "tickets": tickets, "count": len(tickets)}

    def update_ticket(self, ticket_id: int, updates: dict) -> dict:
        result = self._request("PUT", f"/tickets/{ticket_id}", data={"ticket": updates})
        t = result["ticket"]
        return {"success": True, "ticket_id": t["id"], "status": t["status"], "updated_at": t["updated_at"]}

    def add_comment(self, ticket_id: int, body: str, public: bool = False) -> dict:
        result = self._request("PUT", f"/tickets/{ticket_id}",
                               data={"ticket": {"comment": {"body": body, "public": public}}})
        return {"success": True, "ticket_id": result["ticket"]["id"], "public": public}

    def close_ticket(self, ticket_id: int) -> dict:
        return self.update_ticket(ticket_id, {"status": "closed"})

    def assign_ticket(self, ticket_id: int, assignee_id: Optional[int] = None,
                      group_id: Optional[int] = None) -> dict:
        updates: Dict = {}
        if assignee_id is not None:
            updates["assignee_id"] = assignee_id
        if group_id is not None:
            updates["group_id"] = group_id
        if not updates:
            return {"success": False, "error": "Provide assignee_id or group_id"}
        return self.update_ticket(ticket_id, updates)

    # ------------------------------------------------------------------
    # agents / groups
    # ------------------------------------------------------------------
    def list_agents(self) -> dict:
        result = self._request("GET", "/agents")
        return {
            "success": True,
            "agents": [{"id": a["id"], "name": a["name"], "email": a["email"], "role": a.get("role", "")}
                       for a in result.get("agents", [])],
        }

    def list_groups(self) -> dict:
        result = self._request("GET", "/groups")
        return {
            "success": True,
            "groups": [{"id": g["id"], "name": g["name"]} for g in result.get("groups", [])],
        }

    # ------------------------------------------------------------------
    # bulk
    # ------------------------------------------------------------------
    def bulk_create_tickets(self, tickets: List[dict]) -> dict:
        if len(tickets) > 100:
            return {"success": False, "error": "Bulk create limit is 100 tickets"}

        ticket_list = []
        for t in tickets:
            entry: Dict = {
                "subject": t["subject"],
                "comment": {"body": t.get("body", "")},
                "priority": t.get("priority", "normal"),
            }
            if t.get("tags"):
                entry["tags"] = t["tags"]
            if t.get("assignee_id") is not None:
                entry["assignee_id"] = t["assignee_id"]
            ticket_list.append(entry)

        result = self._request("POST", "/tickets/create_many", data={"tickets": ticket_list})
        return {"success": True, "job_status": result.get("job_status", {}), "count": len(ticket_list)}


# ----------------------------------------------------------------------
# tool entry-point (auto-discovered by Agent Zero)
# ----------------------------------------------------------------------
def process_tool(tool_input: dict) -> dict:
    zendesk = ZendeskIntegration()

    if not all([zendesk.subdomain, zendesk.email, zendesk.api_key]):
        return {
            "success": False,
            "error": "Zendesk credentials missing. Set ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_KEY in .env",
        }

    action = tool_input.get("action", "")

    try:
        if action == "create_ticket":
            return zendesk.create_ticket(
                subject=tool_input["subject"],
                body=tool_input["body"],
                requester_email=tool_input.get("requester_email"),
                priority=tool_input.get("priority", "normal"),
                tags=tool_input.get("tags"),
                assignee_id=tool_input.get("assignee_id"),
                group_id=tool_input.get("group_id"),
            )
        elif action == "get_ticket":
            return zendesk.get_ticket(ticket_id=int(tool_input["ticket_id"]))
        elif action == "list_tickets":
            return zendesk.list_tickets(
                status=tool_input.get("status"),
                page_size=tool_input.get("page_size", 25),
                sort_by=tool_input.get("sort_by", "created_at"),
                sort_order=tool_input.get("sort_order", "desc"),
            )
        elif action == "search":
            return zendesk.search_tickets(
                query=tool_input["query"],
                page_size=tool_input.get("page_size", 25),
            )
        elif action == "update_ticket":
            return zendesk.update_ticket(
                ticket_id=int(tool_input["ticket_id"]),
                updates=tool_input["updates"],
            )
        elif action == "add_comment":
            return zendesk.add_comment(
                ticket_id=int(tool_input["ticket_id"]),
                body=tool_input["body"],
                public=tool_input.get("public", False),
            )
        elif action == "close_ticket":
            return zendesk.close_ticket(ticket_id=int(tool_input["ticket_id"]))
        elif action == "assign_ticket":
            return zendesk.assign_ticket(
                ticket_id=int(tool_input["ticket_id"]),
                assignee_id=tool_input.get("assignee_id"),
                group_id=tool_input.get("group_id"),
            )
        elif action == "list_agents":
            return zendesk.list_agents()
        elif action == "list_groups":
            return zendesk.list_groups()
        elif action == "bulk_create":
            return zendesk.bulk_create_tickets(tickets=tool_input["tickets"])
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "create_ticket", "get_ticket", "list_tickets", "search",
                    "update_ticket", "add_comment", "close_ticket", "assign_ticket",
                    "list_agents", "list_groups", "bulk_create",
                ],
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
