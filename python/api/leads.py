"""
Lead Management API — Agent Claw Agency CRM

Endpoint: /leads (POST)
Actions:
  - create: Create a new lead
  - update: Update lead fields
  - note: Add a note to a lead
  - list: List leads with filters
  - pipeline: Get pipeline summary
  - followups: Get due follow-ups
"""

from flask import Request
from python.helpers.api import ApiHandler, Input, Output


class LeadsApi(ApiHandler):

    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "list")

        if action == "create":
            return await self._create(input)
        elif action == "update":
            return await self._update(input)
        elif action == "note":
            return await self._note(input)
        elif action == "list":
            return await self._list(input)
        elif action == "pipeline":
            return await self._pipeline()
        elif action == "followups":
            return await self._followups()
        else:
            return {"error": f"Unknown action: {action}", "available": ["create", "update", "note", "list", "pipeline", "followups"]}

    async def _create(self, input: Input) -> Output:
        from python.helpers.lead_pipeline import create_lead
        name = input.get("name", "")
        if not name:
            return {"error": "Provide 'name' parameter"}
        lead = create_lead(
            name=name,
            channel=input.get("channel", ""),
            email=input.get("email", ""),
            phone=input.get("phone", ""),
            company=input.get("company", ""),
            notes=input.get("notes", ""),
        )
        return {"ok": True, "lead": lead.to_dict()}

    async def _update(self, input: Input) -> Output:
        from python.helpers.lead_pipeline import update_lead
        lead_id = input.get("lead_id", "")
        if not lead_id:
            return {"error": "Provide 'lead_id' parameter"}
        updates = {k: v for k, v in input.items() if k not in ("action", "lead_id")}
        lead = update_lead(lead_id, **updates)
        if lead:
            return {"ok": True, "lead": lead.to_dict()}
        return {"ok": False, "error": f"Lead not found: {lead_id}"}

    async def _note(self, input: Input) -> Output:
        from python.helpers.lead_pipeline import add_note
        lead_id = input.get("lead_id", "")
        note_text = input.get("note", input.get("text", ""))
        if not lead_id or not note_text:
            return {"error": "Provide 'lead_id' and 'note' parameters"}
        lead = add_note(lead_id, note_text)
        if lead:
            return {"ok": True, "lead": lead.to_dict()}
        return {"ok": False, "error": f"Lead not found: {lead_id}"}

    async def _list(self, input: Input) -> Output:
        from python.helpers.lead_pipeline import get_leads
        leads = get_leads(
            status=input.get("status", ""),
            temperature=input.get("temperature", ""),
            limit=int(input.get("limit", 50)),
        )
        return {"ok": True, "leads": [l.to_dict() for l in leads], "total": len(leads)}

    async def _pipeline(self) -> Output:
        from python.helpers.lead_pipeline import get_pipeline_summary
        return {"ok": True, "pipeline": get_pipeline_summary()}

    async def _followups(self) -> Output:
        from python.helpers.lead_pipeline import get_followups_due
        followups = get_followups_due()
        return {"ok": True, "followups": [l.to_dict() for l in followups], "total": len(followups)}
