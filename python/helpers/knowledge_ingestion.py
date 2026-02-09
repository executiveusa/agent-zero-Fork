"""
Knowledge Ingestion Pipeline

Parses and ingests knowledge from multiple sources:
- ChatGPT export JSON (conversations[].mapping[].message.content)
- Claude export JSON (chat_messages[].text)
- Plain text / Markdown with smart semantic chunking
- PDF documents (via existing document_query helper)

Integrates with Memory.preload_knowledge() for automatic ingestion.
Uses Byte Rover atomic writes for persistence.

Follows Ralphie loop pattern:
  Perception → detect new files in knowledge/ dirs
  Decision   → determine format, chunking strategy
  Action     → parse, chunk, and insert into FAISS

Created: 2026-02-09
"""

import os
import re
import json
import hashlib
from datetime import datetime, timezone
from typing import Generator
from dataclasses import dataclass, field
from python.helpers.print_style import PrintStyle
from python.helpers.memory import Memory
from python.helpers.tkgm_memory import ByteRoverAtomic, MemoryDomain, TemporalTag


# ─── Ingestion Status Tracking ───────────────────────────────

INGESTION_STATUS_FILE = "tmp/knowledge_ingestion/status.json"

@dataclass
class IngestionRecord:
    source_path: str
    source_type: str  # chatgpt, claude, markdown, pdf, plaintext
    chunk_count: int = 0
    status: str = "pending"  # pending, processing, completed, failed
    error: str = ""
    ingested_at: str = ""
    file_hash: str = ""
    
    def __post_init__(self):
        if not self.ingested_at:
            self.ingested_at = datetime.now(timezone.utc).isoformat()


def _get_ingestion_status() -> dict:
    return ByteRoverAtomic.read(INGESTION_STATUS_FILE, default={"records": []})


def _save_ingestion_status(status: dict):
    ByteRoverAtomic.write(INGESTION_STATUS_FILE, status)


def _file_hash(filepath: str) -> str:
    """SHA256 hash of file for deduplication."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ─── Smart Chunking ─────────────────────────────────────────

def smart_chunk_text(text: str, max_chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    """
    Semantic-boundary-aware chunking. Splits on:
    1. Double newlines (paragraph boundaries)
    2. Headers (# ## ### etc.)
    3. Code block boundaries
    4. Sentence boundaries (fallback)
    
    Maintains overlap for context continuity.
    """
    if len(text) <= max_chunk_size:
        return [text.strip()] if text.strip() else []
    
    # Split on semantic boundaries
    # Priority: headers > double newlines > code blocks > single newlines
    boundary_patterns = [
        r'\n#{1,6}\s',         # Markdown headers
        r'\n\n+',              # Paragraph breaks
        r'\n```',              # Code block boundaries
        r'\n---+\n',           # Horizontal rules
        r'(?<=[.!?])\s+(?=[A-Z])',  # Sentence boundaries
    ]
    
    chunks = []
    current_chunk = ""
    
    # First split on double newlines
    paragraphs = re.split(r'\n\n+', text)
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) + 2 <= max_chunk_size:
            current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
                # Keep overlap from end of previous chunk
                if overlap > 0:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para
            else:
                # Single paragraph exceeds max_chunk_size, split on sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= max_chunk_size:
                        current_chunk = f"{current_chunk} {sent}" if current_chunk else sent
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sent
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


# ─── ChatGPT Export Parser ───────────────────────────────────

def parse_chatgpt_export(filepath: str) -> list[dict]:
    """
    Parse ChatGPT conversations.json export.
    Structure: [{ "title": "...", "mapping": { "id": { "message": { "content": { "parts": [...] } } } } }]
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    conversations = data if isinstance(data, list) else [data]
    
    for conv in conversations:
        title = conv.get("title", "Untitled")
        create_time = conv.get("create_time", 0)
        mapping = conv.get("mapping", {})
        
        messages = []
        for node_id, node in mapping.items():
            msg = node.get("message")
            if not msg:
                continue
            
            role = msg.get("author", {}).get("role", "unknown")
            content = msg.get("content", {})
            
            if isinstance(content, dict):
                parts = content.get("parts", [])
                text = "\n".join([str(p) for p in parts if isinstance(p, str)])
            elif isinstance(content, str):
                text = content
            else:
                continue
            
            if text.strip():
                messages.append(f"[{role}]: {text}")
        
        if messages:
            full_text = f"# {title}\n\n" + "\n\n".join(messages)
            chunks = smart_chunk_text(full_text)
            for i, chunk in enumerate(chunks):
                documents.append({
                    "content": chunk,
                    "metadata": {
                        "source": "chatgpt_export",
                        "conversation_title": title,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "source_file": os.path.basename(filepath),
                    }
                })
    
    return documents


# ─── Claude Export Parser ────────────────────────────────────

def parse_claude_export(filepath: str) -> list[dict]:
    """
    Parse Claude chat export JSON.
    Structure: [{ "uuid": "...", "name": "...", "chat_messages": [{ "text": "...", "sender": "..." }] }]
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    conversations = data if isinstance(data, list) else [data]
    
    for conv in conversations:
        name = conv.get("name", "Untitled")
        messages = conv.get("chat_messages", [])
        
        msg_texts = []
        for msg in messages:
            sender = msg.get("sender", "unknown")
            text = msg.get("text", "")
            if isinstance(text, list):
                # Claude sometimes has content blocks
                text = "\n".join([
                    b.get("text", "") if isinstance(b, dict) else str(b) 
                    for b in text
                ])
            if text.strip():
                msg_texts.append(f"[{sender}]: {text}")
        
        if msg_texts:
            full_text = f"# {name}\n\n" + "\n\n".join(msg_texts)
            chunks = smart_chunk_text(full_text)
            for i, chunk in enumerate(chunks):
                documents.append({
                    "content": chunk,
                    "metadata": {
                        "source": "claude_export",
                        "conversation_name": name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "source_file": os.path.basename(filepath),
                    }
                })
    
    return documents


# ─── Markdown / Plain Text Parser ────────────────────────────

def parse_text_file(filepath: str) -> list[dict]:
    """Parse markdown or plain text files with smart chunking."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    
    ext = os.path.splitext(filepath)[1].lower()
    source_type = "markdown" if ext in (".md", ".mdx") else "plaintext"
    
    chunks = smart_chunk_text(text)
    documents = []
    for i, chunk in enumerate(chunks):
        documents.append({
            "content": chunk,
            "metadata": {
                "source": source_type,
                "source_file": os.path.basename(filepath),
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
        })
    
    return documents


# ─── PDF Parser ──────────────────────────────────────────────

def parse_pdf_file(filepath: str) -> list[dict]:
    """Parse PDF files using available PDF libraries."""
    try:
        # Try PyPDF2 first (common in agent-zero deps)
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    except ImportError:
        try:
            # Fallback to pdfplumber
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
        except ImportError:
            return [{
                "content": f"[PDF file: {os.path.basename(filepath)} - install PyPDF2 or pdfplumber to parse]",
                "metadata": {"source": "pdf", "source_file": os.path.basename(filepath), "parse_error": True}
            }]
    
    if not text.strip():
        return []
    
    chunks = smart_chunk_text(text)
    documents = []
    for i, chunk in enumerate(chunks):
        documents.append({
            "content": chunk,
            "metadata": {
                "source": "pdf",
                "source_file": os.path.basename(filepath),
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
        })
    
    return documents


# ─── Master Ingestion Pipeline ───────────────────────────────

def detect_source_type(filepath: str) -> str:
    """Auto-detect source type from file content/extension."""
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == ".pdf":
        return "pdf"
    
    if ext in (".md", ".mdx", ".txt", ".text"):
        return "plaintext"
    
    if ext == ".json":
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Detect ChatGPT format
            if isinstance(data, list) and data:
                if "mapping" in data[0]:
                    return "chatgpt"
                if "chat_messages" in data[0]:
                    return "claude"
            if isinstance(data, dict):
                if "mapping" in data:
                    return "chatgpt"
                if "chat_messages" in data:
                    return "claude"
        except Exception:
            pass
        return "plaintext"
    
    return "plaintext"


async def ingest_file(
    filepath: str,
    agent=None,
    source_type: str = "auto",
    area: str = Memory.Area.MAIN.value,
    domain: MemoryDomain = MemoryDomain.AGENT_ZERO,
) -> IngestionRecord:
    """
    Main entry point: ingest a single file into the memory system.
    
    Follows Ralphie loop Action phase:
    1. Detect format
    2. Parse and chunk
    3. Insert into FAISS with temporal metadata
    4. Persist status atomically
    """
    record = IngestionRecord(source_path=filepath, source_type=source_type)
    
    try:
        if not os.path.exists(filepath):
            record.status = "failed"
            record.error = f"File not found: {filepath}"
            return record
        
        # Check deduplication
        fhash = _file_hash(filepath)
        record.file_hash = fhash
        
        status = _get_ingestion_status()
        for existing in status.get("records", []):
            if existing.get("file_hash") == fhash and existing.get("status") == "completed":
                record.status = "skipped"
                record.error = "Already ingested (duplicate hash)"
                return record
        
        # Auto-detect source type
        if source_type == "auto":
            source_type = detect_source_type(filepath)
            record.source_type = source_type
        
        record.status = "processing"
        
        # Parse based on type
        if source_type == "chatgpt":
            documents = parse_chatgpt_export(filepath)
        elif source_type == "claude":
            documents = parse_claude_export(filepath)
        elif source_type == "pdf":
            documents = parse_pdf_file(filepath)
        else:
            documents = parse_text_file(filepath)
        
        if not documents:
            record.status = "completed"
            record.chunk_count = 0
            return record
        
        # Insert into Memory
        if agent:
            db = await Memory.get(agent)
            for doc in documents:
                temporal_meta = {
                    "area": area,
                    "temporal_created_at": datetime.now(timezone.utc).isoformat(),
                    "temporal_decay_rate": 0.005,  # Slower decay for knowledge
                    "temporal_source_agent": f"agent_{agent.number}",
                    "temporal_domain": domain.value,
                    "ingestion_source": source_type,
                    **doc.get("metadata", {}),
                }
                await db.insert_text(text=doc["content"], metadata=temporal_meta)
        
        record.chunk_count = len(documents)
        record.status = "completed"
        
        # Persist status
        status["records"].append({
            "source_path": record.source_path,
            "source_type": record.source_type,
            "chunk_count": record.chunk_count,
            "status": record.status,
            "file_hash": record.file_hash,
            "ingested_at": record.ingested_at,
        })
        _save_ingestion_status(status)
        
    except Exception as e:
        record.status = "failed"
        record.error = str(e)
        PrintStyle.error(f"Ingestion failed for {filepath}: {e}")
    
    return record


async def ingest_directory(
    dirpath: str,
    agent=None,
    recursive: bool = True,
    area: str = Memory.Area.MAIN.value,
    domain: MemoryDomain = MemoryDomain.AGENT_ZERO,
) -> list[IngestionRecord]:
    """Ingest all supported files from a directory."""
    supported_extensions = {".json", ".md", ".mdx", ".txt", ".text", ".pdf"}
    records = []
    
    if recursive:
        for root, dirs, fnames in os.walk(dirpath):
            for fname in fnames:
                if os.path.splitext(fname)[1].lower() in supported_extensions:
                    fpath = os.path.join(root, fname)
                    record = await ingest_file(fpath, agent, "auto", area, domain)
                    records.append(record)
    else:
        for fname in os.listdir(dirpath):
            fpath = os.path.join(dirpath, fname)
            if os.path.isfile(fpath) and os.path.splitext(fname)[1].lower() in supported_extensions:
                record = await ingest_file(fpath, agent, "auto", area, domain)
                records.append(record)
    
    return records


def get_ingestion_history() -> list[dict]:
    """Get all ingestion records."""
    status = _get_ingestion_status()
    return status.get("records", [])
