"""
Dashboard API — Knowledge Panel

Endpoint: /dashboard_knowledge (POST)
Actions:
  - stats: Get knowledge base statistics
  - domains: List memory domains with counts
  - recent: Get recently ingested items
  - search: Search knowledge with temporal decay
  - triples: Get knowledge graph triples for a subject
"""

import os
import json
from flask import Request
from python.helpers.api import ApiHandler, Input, Output


class DashboardKnowledge(ApiHandler):

    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "stats")

        if action == "stats":
            return await self._stats()
        elif action == "domains":
            return await self._domains()
        elif action == "recent":
            return await self._recent(input)
        elif action == "search":
            return await self._search(input)
        elif action == "triples":
            return await self._triples(input)
        else:
            return {"error": f"Unknown action: {action}", "available": ["stats", "domains", "recent", "search", "triples"]}

    async def _stats(self) -> Output:
        """Get overall knowledge base statistics."""
        stats = {
            "total_fragments": 0,
            "total_triples": 0,
            "total_ingested_files": 0,
            "domains": {},
            "temporal_coverage": {"earliest": None, "latest": None},
        }

        # Count TKGM triples
        tkgm_dir = "memory"
        if os.path.exists(tkgm_dir):
            for root, dirs, files in os.walk(tkgm_dir):
                for fname in files:
                    if fname == "tkgm_triples.json":
                        try:
                            with open(os.path.join(root, fname), "r") as f:
                                triples = json.load(f)
                                stats["total_triples"] += len(triples)
                        except Exception:
                            pass
                    elif fname == "tkgm_temporal.json":
                        try:
                            with open(os.path.join(root, fname), "r") as f:
                                temporal = json.load(f)
                                stats["total_fragments"] += len(temporal)
                                for key, meta in temporal.items():
                                    domain = meta.get("domain", "unknown")
                                    stats["domains"][domain] = stats["domains"].get(domain, 0) + 1
                                    created = meta.get("created_at", "")
                                    if created:
                                        if not stats["temporal_coverage"]["earliest"] or created < stats["temporal_coverage"]["earliest"]:
                                            stats["temporal_coverage"]["earliest"] = created
                                        if not stats["temporal_coverage"]["latest"] or created > stats["temporal_coverage"]["latest"]:
                                            stats["temporal_coverage"]["latest"] = created
                        except Exception:
                            pass

        # Count ingested files
        ingestion_status = "tmp/knowledge_ingestion/status.json"
        if os.path.exists(ingestion_status):
            try:
                with open(ingestion_status, "r") as f:
                    records = json.load(f)
                    stats["total_ingested_files"] = len(records)
            except Exception:
                pass

        return {"ok": True, "stats": stats}

    async def _domains(self) -> Output:
        """List all memory domains with item counts."""
        domains = {}
        tkgm_dir = "memory"
        if os.path.exists(tkgm_dir):
            for root, dirs, files in os.walk(tkgm_dir):
                for fname in files:
                    if fname == "tkgm_temporal.json":
                        try:
                            with open(os.path.join(root, fname), "r") as f:
                                temporal = json.load(f)
                                for key, meta in temporal.items():
                                    domain = meta.get("domain", "unknown")
                                    if domain not in domains:
                                        domains[domain] = {"count": 0, "latest": ""}
                                    domains[domain]["count"] += 1
                                    created = meta.get("created_at", "")
                                    if created > domains[domain]["latest"]:
                                        domains[domain]["latest"] = created
                        except Exception:
                            pass

        return {"ok": True, "domains": domains}

    async def _recent(self, input: Input) -> Output:
        """Get recently ingested items."""
        limit = int(input.get("limit", 20))
        ingestion_status = "tmp/knowledge_ingestion/status.json"
        records = []
        if os.path.exists(ingestion_status):
            try:
                with open(ingestion_status, "r") as f:
                    all_records = json.load(f)
                    # Sort by timestamp descending
                    sorted_records = sorted(all_records, key=lambda r: r.get("ingested_at", ""), reverse=True)
                    records = sorted_records[:limit]
            except Exception:
                pass

        return {"ok": True, "recent": records, "total": len(records)}

    async def _search(self, input: Input) -> Output:
        """Search knowledge with temporal decay scoring."""
        query = input.get("query", "")
        limit = int(input.get("limit", 10))
        if not query:
            return {"error": "Provide 'query' parameter"}

        # This would integrate with TKGM memory search
        # For now, return a structured search interface
        return {
            "ok": True,
            "query": query,
            "note": "Use the TKGM memory system via agent for full temporal-decay search",
            "hint": "POST to the agent with: search my knowledge for '{query}'",
        }

    async def _triples(self, input: Input) -> Output:
        """Get knowledge graph triples for a subject."""
        subject = input.get("subject", "")
        if not subject:
            return {"error": "Provide 'subject' parameter"}

        results = []
        tkgm_dir = "memory"
        if os.path.exists(tkgm_dir):
            for root, dirs, files in os.walk(tkgm_dir):
                for fname in files:
                    if fname == "tkgm_triples.json":
                        try:
                            with open(os.path.join(root, fname), "r") as f:
                                triples = json.load(f)
                                for t in triples:
                                    if subject.lower() in t.get("subject", "").lower():
                                        results.append(t)
                        except Exception:
                            pass

        return {"ok": True, "subject": subject, "triples": results[:50]}
