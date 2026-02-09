"""
TKGM Memory — Temporal Knowledge Graph Memory

Extends the base Memory system with:
- Temporal tagging: ISO timestamps + exponential decay scoring
- Knowledge triples: (subject, predicate, object) stored as FAISS metadata
- Tenant/agent isolation: Memory keys prefixed with agent_id
- Graph traversal: get_related(), get_timeline(), get_triples_for()
- Byte Rover atomic writes for crash-safe persistence
- Memory domains matching the Agent Claw architecture

Follows the Ralphie 30-second loop pattern:
  Perception → read memory state
  Decision   → score/rank by recency + relevance
  Action     → write with atomic persistence

Created: 2026-02-09
"""

import os
import json
import time
import tempfile
import asyncio
from datetime import datetime, timezone
from typing import Optional, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
from python.helpers.memory import Memory, MyFaiss
from python.helpers.print_style import PrintStyle
from python.helpers import files
from agent import Agent


# ─── Memory Domains (from ralphie-config.json) ─────────────────

class MemoryDomain(Enum):
    AGENT_ZERO = "agent_zero"
    DESIGN_SYSTEM = "design_system"
    CODE_GENERATION = "code_generation"
    DEPLOYMENT_LOGS = "deployment_logs"
    VIDEO_PROJECTS = "video_projects"
    VOICE_SESSIONS = "voice_sessions"
    CLIENT_CONVERSATIONS = "client_conversations"
    SHARED = "shared"


# ─── Knowledge Triple ──────────────────────────────────────────

@dataclass
class KnowledgeTriple:
    subject: str
    predicate: str
    obj: str  # 'object' is reserved in Python
    confidence: float = 1.0
    source_agent: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_text(self) -> str:
        return f"{self.subject} {self.predicate} {self.obj}"
    
    def to_metadata(self) -> dict:
        return {
            "triple_subject": self.subject,
            "triple_predicate": self.predicate,
            "triple_object": self.obj,
            "triple_confidence": self.confidence,
            "source_agent": self.source_agent,
        }


# ─── Temporal Metadata ─────────────────────────────────────────

@dataclass
class TemporalTag:
    created_at: str = ""
    last_accessed: str = ""
    access_count: int = 0
    decay_rate: float = 0.01  # exponential decay per hour
    source_agent: str = ""
    domain: str = MemoryDomain.AGENT_ZERO.value
    
    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.last_accessed:
            self.last_accessed = now
    
    def compute_decay_score(self) -> float:
        """Compute relevance score with exponential time decay."""
        try:
            created = datetime.fromisoformat(self.created_at)
            now = datetime.now(timezone.utc)
            hours_elapsed = (now - created).total_seconds() / 3600
            import math
            base_score = math.exp(-self.decay_rate * hours_elapsed)
            # Boost for frequently accessed memories
            access_boost = min(0.3, self.access_count * 0.02)
            return min(1.0, base_score + access_boost)
        except Exception:
            return 0.5
    
    def to_metadata(self) -> dict:
        return {
            "temporal_created_at": self.created_at,
            "temporal_last_accessed": self.last_accessed,
            "temporal_access_count": self.access_count,
            "temporal_decay_rate": self.decay_rate,
            "temporal_source_agent": self.source_agent,
            "temporal_domain": self.domain,
        }


# ─── Byte Rover Atomic Writes ──────────────────────────────────

class ByteRoverAtomic:
    """
    Crash-safe file persistence using write-to-temp-then-rename.
    Pattern from E:\\...\\byte_rover_atomic.py
    """
    
    @staticmethod
    def write(filepath: str, data: Any) -> bool:
        """Atomic write: write to temp file, then rename."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            content = json.dumps(data, indent=2, default=str)
            
            # Write to temp file in same directory (ensures same filesystem for rename)
            dir_name = os.path.dirname(filepath)
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
            try:
                with os.fdopen(fd, 'w') as f:
                    f.write(content)
                # Atomic rename (on same filesystem)
                os.replace(tmp_path, filepath)
                return True
            except Exception:
                # Clean up temp file on failure
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise
        except Exception as e:
            PrintStyle.error(f"ByteRover atomic write failed: {e}")
            return False
    
    @staticmethod
    def read(filepath: str, default: Any = None) -> Any:
        """Read JSON file with fallback default."""
        try:
            if not os.path.exists(filepath):
                return default
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            PrintStyle.error(f"ByteRover read failed: {e}")
            return default


# ─── TKGM Memory Class ─────────────────────────────────────────

class TKGMMemory:
    """
    Temporal Knowledge Graph Memory wrapper around the base Memory class.
    
    Usage:
        tkgm = await TKGMMemory.get(agent)
        await tkgm.insert_with_temporal("User prefers dark mode", domain=MemoryDomain.CLIENT_CONVERSATIONS)
        await tkgm.insert_triple(KnowledgeTriple("user", "prefers", "dark mode"))
        results = await tkgm.search_with_decay("user preferences", top_k=5)
        timeline = await tkgm.get_timeline(hours=24)
        related = await tkgm.get_related("dark mode")
    """
    
    _instances: dict[str, "TKGMMemory"] = {}
    TRIPLES_FILE = "tkgm_triples.json"
    TEMPORAL_FILE = "tkgm_temporal.json"
    
    def __init__(self, base_memory: MyFaiss, memory_subdir: str, agent_id: str = ""):
        self.db = base_memory
        self.memory_subdir = memory_subdir
        self.agent_id = agent_id
        self._triples: list[dict] = []
        self._temporal_index: dict[str, dict] = {}
        self._load_persistence()
    
    @staticmethod
    async def get(agent: Agent) -> "TKGMMemory":
        """Factory: get or create TKGM instance for an agent."""
        from python.helpers.memory import get_agent_memory_subdir
        memory_subdir = get_agent_memory_subdir(agent)
        agent_id = f"agent_{agent.number}"
        
        cache_key = f"{memory_subdir}:{agent_id}"
        if cache_key not in TKGMMemory._instances:
            base_db = await Memory.get(agent)
            tkgm = TKGMMemory(base_db.db, memory_subdir, agent_id)
            TKGMMemory._instances[cache_key] = tkgm
        return TKGMMemory._instances[cache_key]
    
    def _persistence_dir(self) -> str:
        return os.path.join("memory", self.memory_subdir, "tkgm")
    
    def _load_persistence(self):
        """Load triples and temporal index from disk."""
        pdir = self._persistence_dir()
        self._triples = ByteRoverAtomic.read(
            os.path.join(pdir, self.TRIPLES_FILE), default=[]
        )
        self._temporal_index = ByteRoverAtomic.read(
            os.path.join(pdir, self.TEMPORAL_FILE), default={}
        )
    
    def _save_triples(self):
        ByteRoverAtomic.write(
            os.path.join(self._persistence_dir(), self.TRIPLES_FILE),
            self._triples,
        )
    
    def _save_temporal(self):
        ByteRoverAtomic.write(
            os.path.join(self._persistence_dir(), self.TEMPORAL_FILE),
            self._temporal_index,
        )
    
    # ── Temporal Operations ──────────────────────────────────
    
    async def insert_with_temporal(
        self,
        text: str,
        area: str = Memory.Area.MAIN.value,
        domain: MemoryDomain = MemoryDomain.AGENT_ZERO,
        decay_rate: float = 0.01,
        source_agent: str = "",
        extra_metadata: dict | None = None,
    ) -> str:
        """Insert text with temporal tagging and domain isolation."""
        temporal = TemporalTag(
            decay_rate=decay_rate,
            source_agent=source_agent or self.agent_id,
            domain=domain.value,
        )
        
        metadata = {
            "area": area,
            "agent_id": self.agent_id,
            **temporal.to_metadata(),
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        
        # Insert into FAISS via base Memory
        from langchain_core.documents import Document
        doc = Document(page_content=text, metadata=metadata)
        ids = self.db.add_documents([doc])
        doc_id = ids[0] if ids else ""
        
        # Track in temporal index
        self._temporal_index[doc_id] = asdict(temporal)
        self._save_temporal()
        
        return doc_id
    
    async def search_with_decay(
        self,
        query: str,
        top_k: int = 10,
        area: str | None = None,
        domain: MemoryDomain | None = None,
        min_decay_score: float = 0.1,
    ) -> list[dict]:
        """Search with combined semantic similarity + temporal decay scoring."""
        # Get more results than needed, then re-rank
        fetch_k = top_k * 3
        
        filter_expr = ""
        if area:
            filter_expr = f"area=='{area}'"
        
        results = self.db.similarity_search_with_score(query, k=fetch_k)
        
        scored_results = []
        for doc, similarity_score in results:
            meta = doc.metadata or {}
            
            # Apply area filter
            if area and meta.get("area") != area:
                continue
            
            # Apply domain filter
            if domain and meta.get("temporal_domain") != domain.value:
                continue
            
            # Apply agent isolation
            if meta.get("agent_id") and meta.get("agent_id") != self.agent_id:
                # Allow shared domain
                if meta.get("temporal_domain") != MemoryDomain.SHARED.value:
                    continue
            
            # Compute temporal decay
            temporal_data = self._temporal_index.get("", {})
            # Try to reconstruct TemporalTag
            tag = TemporalTag(
                created_at=meta.get("temporal_created_at", ""),
                last_accessed=meta.get("temporal_last_accessed", ""),
                access_count=meta.get("temporal_access_count", 0),
                decay_rate=meta.get("temporal_decay_rate", 0.01),
            )
            decay_score = tag.compute_decay_score()
            
            if decay_score < min_decay_score:
                continue
            
            # Combined score: 70% similarity + 30% recency
            # Note: FAISS returns distance (lower = more similar), convert to similarity
            sim_score = max(0, 1.0 - similarity_score) if similarity_score < 2 else 0.5
            combined = 0.7 * sim_score + 0.3 * decay_score
            
            scored_results.append({
                "content": doc.page_content,
                "metadata": meta,
                "similarity_score": sim_score,
                "decay_score": decay_score,
                "combined_score": combined,
            })
        
        # Sort by combined score descending
        scored_results.sort(key=lambda x: x["combined_score"], reverse=True)
        return scored_results[:top_k]
    
    async def get_timeline(self, hours: int = 24, domain: MemoryDomain | None = None) -> list[dict]:
        """Get memories created within the last N hours, ordered chronologically."""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        timeline = []
        all_docs = self.db.get_all_docs()
        
        for doc_id, doc in all_docs.items():
            meta = doc.metadata or {}
            created_str = meta.get("temporal_created_at", "")
            if not created_str:
                continue
            
            try:
                created = datetime.fromisoformat(created_str)
                if created < cutoff:
                    continue
                if domain and meta.get("temporal_domain") != domain.value:
                    continue
                
                timeline.append({
                    "doc_id": doc_id,
                    "content": doc.page_content[:200],
                    "created_at": created_str,
                    "domain": meta.get("temporal_domain", ""),
                    "agent": meta.get("temporal_source_agent", ""),
                })
            except Exception:
                continue
        
        timeline.sort(key=lambda x: x["created_at"], reverse=True)
        return timeline
    
    # ── Knowledge Triple Operations ──────────────────────────
    
    async def insert_triple(self, triple: KnowledgeTriple) -> str:
        """Insert a knowledge triple into both FAISS and the triple index."""
        text = triple.to_text()
        metadata = {
            "area": Memory.Area.MAIN.value,
            "is_triple": True,
            "agent_id": self.agent_id,
            **triple.to_metadata(),
            **TemporalTag(source_agent=triple.source_agent or self.agent_id).to_metadata(),
        }
        
        from langchain_core.documents import Document
        doc = Document(page_content=text, metadata=metadata)
        ids = self.db.add_documents([doc])
        doc_id = ids[0] if ids else ""
        
        # Persist triple
        self._triples.append({
            "doc_id": doc_id,
            **asdict(triple),
        })
        self._save_triples()
        
        return doc_id
    
    async def get_triples_for(self, entity: str, limit: int = 20) -> list[dict]:
        """Get all triples where entity appears as subject or object."""
        entity_lower = entity.lower()
        matches = []
        for t in self._triples:
            if (entity_lower in t.get("subject", "").lower() or
                entity_lower in t.get("obj", "").lower()):
                matches.append(t)
        return matches[:limit]
    
    async def get_related(self, entity: str, hops: int = 2, limit: int = 20) -> list[dict]:
        """
        Graph traversal: find entities related to the given entity within N hops.
        Hop 1: direct connections
        Hop 2+: connections of connections
        """
        visited = set()
        results = []
        current_entities = {entity.lower()}
        
        for hop in range(hops):
            next_entities = set()
            for t in self._triples:
                subj = t.get("subject", "").lower()
                obj = t.get("obj", "").lower()
                
                if subj in current_entities and obj not in visited:
                    results.append({**t, "hop": hop + 1, "direction": "outgoing"})
                    next_entities.add(obj)
                    visited.add(obj)
                elif obj in current_entities and subj not in visited:
                    results.append({**t, "hop": hop + 1, "direction": "incoming"})
                    next_entities.add(subj)
                    visited.add(subj)
            
            current_entities = next_entities
            if not current_entities:
                break
        
        return results[:limit]
    
    # ── Bulk Operations ──────────────────────────────────────
    
    async def extract_triples_from_text(self, agent: Agent, text: str) -> list[KnowledgeTriple]:
        """Use LLM to extract knowledge triples from text."""
        system = agent.read_prompt("memory.tkgm_extraction.sys.md")
        if not system:
            system = (
                "Extract knowledge triples from the given text. "
                "Return a JSON array of objects with keys: subject, predicate, obj. "
                "Only extract factual, meaningful relationships. Return [] if none found."
            )
        
        response = await agent.call_utility_model(
            system=system,
            message=text,
            background=True,
        )
        
        triples = []
        try:
            from python.helpers.dirty_json import DirtyJson
            parsed = DirtyJson.parse_string(response)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "subject" in item and "predicate" in item:
                        triples.append(KnowledgeTriple(
                            subject=str(item["subject"]),
                            predicate=str(item["predicate"]),
                            obj=str(item.get("obj", item.get("object", ""))),
                            source_agent=self.agent_id,
                        ))
        except Exception as e:
            PrintStyle.error(f"Triple extraction failed: {e}")
        
        return triples
    
    async def consolidate_domain(self, domain: MemoryDomain, max_age_hours: int = 168) -> dict:
        """
        Consolidation pass for a memory domain.
        Follows Ralphie loop Action phase pattern.
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        expired_ids = []
        all_docs = self.db.get_all_docs()
        
        for doc_id, doc in all_docs.items():
            meta = doc.metadata or {}
            if meta.get("temporal_domain") != domain.value:
                continue
            
            created_str = meta.get("temporal_created_at", "")
            if not created_str:
                continue
            
            try:
                created = datetime.fromisoformat(created_str)
                tag = TemporalTag(
                    created_at=created_str,
                    access_count=meta.get("temporal_access_count", 0),
                    decay_rate=meta.get("temporal_decay_rate", 0.01),
                )
                if tag.compute_decay_score() < 0.05:
                    expired_ids.append(doc_id)
            except Exception:
                continue
        
        if expired_ids:
            self.db.delete(expired_ids)
        
        return {
            "domain": domain.value,
            "expired_removed": len(expired_ids),
            "total_remaining": len(all_docs) - len(expired_ids),
        }
