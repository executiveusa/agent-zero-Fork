"""
Knowledge Ingestion API

API endpoint for ingesting knowledge from various sources.
Auto-registered at /knowledge_ingest by run_ui.py.

Actions:
  - ingest_file:           Ingest a single file (path on disk)
  - ingest_url:            Ingest from URL (future: Firecrawl)
  - ingest_chatgpt_export: Ingest ChatGPT export JSON
  - ingest_claude_export:  Ingest Claude export JSON
  - list_ingested:         List all ingestion records
  - status:                Get current pipeline status

Created: 2026-02-09
"""

from python.helpers.api import ApiHandler, Input, Output
from flask import Request


class KnowledgeIngestHandler(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: Input, request: Request) -> Output:
        from python.helpers.knowledge_ingestion import (
            ingest_file,
            ingest_directory,
            get_ingestion_history,
            detect_source_type,
        )
        from python.helpers.tkgm_memory import MemoryDomain
        from python.helpers.memory import Memory

        action = input.get("action", "status")

        if action == "ingest_file":
            filepath = input.get("filepath", "")
            source_type = input.get("source_type", "auto")
            area = input.get("area", Memory.Area.MAIN.value)
            domain_str = input.get("domain", "agent_zero")
            
            try:
                domain = MemoryDomain(domain_str)
            except ValueError:
                domain = MemoryDomain.AGENT_ZERO
            
            if not filepath:
                return {"error": "filepath is required"}
            
            # Get agent context for Memory access
            ctx = self.use_context(input.get("ctxid", ""))
            agent = ctx.agent0
            
            record = await ingest_file(filepath, agent, source_type, area, domain)
            return {
                "status": record.status,
                "source_path": record.source_path,
                "source_type": record.source_type,
                "chunk_count": record.chunk_count,
                "error": record.error,
            }
        
        elif action == "ingest_directory":
            dirpath = input.get("dirpath", "")
            recursive = input.get("recursive", True)
            area = input.get("area", Memory.Area.MAIN.value)
            domain_str = input.get("domain", "agent_zero")
            
            try:
                domain = MemoryDomain(domain_str)
            except ValueError:
                domain = MemoryDomain.AGENT_ZERO
            
            if not dirpath:
                return {"error": "dirpath is required"}
            
            ctx = self.use_context(input.get("ctxid", ""))
            agent = ctx.agent0
            
            records = await ingest_directory(dirpath, agent, recursive, area, domain)
            return {
                "total": len(records),
                "completed": sum(1 for r in records if r.status == "completed"),
                "failed": sum(1 for r in records if r.status == "failed"),
                "skipped": sum(1 for r in records if r.status == "skipped"),
                "total_chunks": sum(r.chunk_count for r in records),
            }
        
        elif action == "ingest_chatgpt_export":
            filepath = input.get("filepath", "")
            if not filepath:
                return {"error": "filepath is required"}
            
            ctx = self.use_context(input.get("ctxid", ""))
            agent = ctx.agent0
            
            record = await ingest_file(filepath, agent, "chatgpt")
            return {
                "status": record.status,
                "chunk_count": record.chunk_count,
                "error": record.error,
            }
        
        elif action == "ingest_claude_export":
            filepath = input.get("filepath", "")
            if not filepath:
                return {"error": "filepath is required"}
            
            ctx = self.use_context(input.get("ctxid", ""))
            agent = ctx.agent0
            
            record = await ingest_file(filepath, agent, "claude")
            return {
                "status": record.status,
                "chunk_count": record.chunk_count,
                "error": record.error,
            }
        
        elif action == "list_ingested":
            records = get_ingestion_history()
            return {"records": records, "total": len(records)}
        
        elif action == "status":
            records = get_ingestion_history()
            return {
                "total_ingested": len(records),
                "total_completed": sum(1 for r in records if r.get("status") == "completed"),
                "total_failed": sum(1 for r in records if r.get("status") == "failed"),
                "total_chunks": sum(r.get("chunk_count", 0) for r in records),
            }
        
        else:
            return {"error": f"Unknown action: {action}. Use: ingest_file, ingest_directory, ingest_chatgpt_export, ingest_claude_export, list_ingested, status"}
