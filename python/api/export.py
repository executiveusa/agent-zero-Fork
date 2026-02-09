"""
Export API — Agent Claw Data Export

Endpoint: /export (POST)
Actions:
  - knowledge: Export knowledge base (triples, temporal metadata)
  - costs: Export cost tracking data
  - audit: Export audit trail
  - backup: Full platform backup
  - list: List available exports
"""

from flask import Request
from python.helpers.api import ApiHandler, Input, Output


class ExportApi(ApiHandler):

    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "list")

        if action == "knowledge":
            return await self._export_knowledge(input)
        elif action == "costs":
            return await self._export_costs(input)
        elif action == "audit":
            return await self._export_audit(input)
        elif action == "backup":
            return await self._export_backup()
        elif action == "list":
            return await self._list()
        else:
            return {"error": f"Unknown action: {action}", "available": ["knowledge", "costs", "audit", "backup", "list"]}

    async def _export_knowledge(self, input: Input) -> Output:
        from python.helpers.export_pipeline import export_knowledge
        format = input.get("format", "json")
        job = export_knowledge(format)
        return {
            "ok": job.status == "completed",
            "job_id": job.job_id,
            "status": job.status,
            "output_path": job.output_path,
            "record_count": job.record_count,
            "error": job.error,
        }

    async def _export_costs(self, input: Input) -> Output:
        from python.helpers.export_pipeline import export_costs
        days = int(input.get("days", 30))
        format = input.get("format", "json")
        job = export_costs(days, format)
        return {
            "ok": job.status == "completed",
            "job_id": job.job_id,
            "status": job.status,
            "output_path": job.output_path,
            "record_count": job.record_count,
            "error": job.error,
        }

    async def _export_audit(self, input: Input) -> Output:
        from python.helpers.export_pipeline import export_audit
        days = int(input.get("days", 7))
        format = input.get("format", "json")
        job = export_audit(days, format)
        return {
            "ok": job.status == "completed",
            "job_id": job.job_id,
            "status": job.status,
            "output_path": job.output_path,
            "record_count": job.record_count,
            "error": job.error,
        }

    async def _export_backup(self) -> Output:
        from python.helpers.export_pipeline import export_full_backup
        job = export_full_backup()
        return {
            "ok": job.status == "completed",
            "job_id": job.job_id,
            "status": job.status,
            "output_path": job.output_path,
            "record_count": job.record_count,
            "error": job.error,
        }

    async def _list(self) -> Output:
        from python.helpers.export_pipeline import list_exports
        exports = list_exports()
        return {"ok": True, "exports": exports, "total": len(exports)}
