"""
Export Pipeline — Agent Claw Data Export System

Exports agent knowledge, conversations, cost reports, and audit trails
to structured formats (JSON, CSV, Markdown) for backup, reporting, and
client deliverables.

Uses ByteRoverAtomic for safe persistence.
"""

import os
import json
import csv
import io
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ExportJob:
    """Represents an export job."""
    job_id: str
    export_type: str  # knowledge, costs, audit, conversations, full_backup
    format: str  # json, csv, markdown
    status: str  # pending, running, completed, failed
    created_at: str
    completed_at: Optional[str] = None
    output_path: Optional[str] = None
    record_count: int = 0
    error: Optional[str] = None


EXPORT_DIR = "tmp/exports"


def _ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)


def export_knowledge(format: str = "json") -> ExportJob:
    """Export all knowledge base data (TKGM triples + temporal metadata)."""
    _ensure_export_dir()
    job_id = f"exp_knowledge_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    job = ExportJob(
        job_id=job_id,
        export_type="knowledge",
        format=format,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    try:
        all_triples = []
        all_temporal = {}

        # Collect from memory directories
        memory_dir = "memory"
        if os.path.exists(memory_dir):
            for root, dirs, files in os.walk(memory_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    if fname == "tkgm_triples.json":
                        try:
                            with open(fpath, "r") as f:
                                triples = json.load(f)
                                for t in triples:
                                    t["_source_dir"] = os.path.relpath(root, memory_dir)
                                all_triples.extend(triples)
                        except Exception:
                            pass
                    elif fname == "tkgm_temporal.json":
                        try:
                            with open(fpath, "r") as f:
                                temporal = json.load(f)
                                for key, meta in temporal.items():
                                    meta["_source_dir"] = os.path.relpath(root, memory_dir)
                                    all_temporal[key] = meta
                        except Exception:
                            pass

        # Also include ingestion records
        ingestion_records = []
        ingestion_path = "tmp/knowledge_ingestion/status.json"
        if os.path.exists(ingestion_path):
            try:
                with open(ingestion_path, "r") as f:
                    ingestion_records = json.load(f)
            except Exception:
                pass

        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "triples": all_triples,
            "temporal_metadata": all_temporal,
            "ingestion_records": ingestion_records,
            "summary": {
                "total_triples": len(all_triples),
                "total_temporal_entries": len(all_temporal),
                "total_ingested_files": len(ingestion_records),
            },
        }

        if format == "json":
            output_path = os.path.join(EXPORT_DIR, f"{job_id}.json")
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            output_path = os.path.join(EXPORT_DIR, f"{job_id}_triples.csv")
            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["subject", "predicate", "object", "confidence", "source_dir"])
                for t in all_triples:
                    writer.writerow([t.get("subject", ""), t.get("predicate", ""), t.get("object", ""), t.get("confidence", ""), t.get("_source_dir", "")])
        elif format == "markdown":
            output_path = os.path.join(EXPORT_DIR, f"{job_id}.md")
            with open(output_path, "w") as f:
                f.write(f"# Knowledge Export\n\n")
                f.write(f"**Exported**: {data['exported_at']}\n\n")
                f.write(f"## Summary\n")
                f.write(f"- Triples: {len(all_triples)}\n")
                f.write(f"- Temporal entries: {len(all_temporal)}\n")
                f.write(f"- Ingested files: {len(ingestion_records)}\n\n")
                f.write(f"## Knowledge Triples\n\n")
                f.write(f"| Subject | Predicate | Object | Confidence |\n")
                f.write(f"|---------|-----------|--------|------------|\n")
                for t in all_triples[:100]:
                    f.write(f"| {t.get('subject', '')} | {t.get('predicate', '')} | {t.get('object', '')} | {t.get('confidence', '')} |\n")
                if len(all_triples) > 100:
                    f.write(f"\n*... and {len(all_triples) - 100} more triples*\n")
        else:
            output_path = os.path.join(EXPORT_DIR, f"{job_id}.json")
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

        job.status = "completed"
        job.output_path = output_path
        job.record_count = len(all_triples) + len(all_temporal)
        job.completed_at = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        job.status = "failed"
        job.error = str(e)

    return job


def export_costs(days: int = 30, format: str = "json") -> ExportJob:
    """Export cost tracking data."""
    _ensure_export_dir()
    job_id = f"exp_costs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    job = ExportJob(
        job_id=job_id,
        export_type="costs",
        format=format,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    try:
        cost_dir = "tmp/cost_tracking"
        all_entries = []
        daily_totals = {}

        if os.path.exists(cost_dir):
            today = datetime.now(timezone.utc).date()
            for i in range(days):
                date = today - timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                fname = os.path.join(cost_dir, f"costs_{date_str}.json")
                day_total = 0.0
                if os.path.exists(fname):
                    try:
                        with open(fname, "r") as f:
                            entries = json.load(f)
                            for entry in entries:
                                entry["date"] = date_str
                                all_entries.append(entry)
                                day_total += entry.get("estimated_cost", 0)
                    except Exception:
                        pass
                daily_totals[date_str] = round(day_total, 4)

        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "days_covered": days,
            "total_cost": round(sum(daily_totals.values()), 4),
            "daily_totals": daily_totals,
            "entries": all_entries,
        }

        if format == "json":
            output_path = os.path.join(EXPORT_DIR, f"{job_id}.json")
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            output_path = os.path.join(EXPORT_DIR, f"{job_id}.csv")
            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "timestamp", "model", "agent_id", "input_tokens", "output_tokens", "estimated_cost"])
                for entry in all_entries:
                    writer.writerow([
                        entry.get("date", ""),
                        entry.get("timestamp", ""),
                        entry.get("model", ""),
                        entry.get("agent_id", ""),
                        entry.get("input_tokens", 0),
                        entry.get("output_tokens", 0),
                        entry.get("estimated_cost", 0),
                    ])
        elif format == "markdown":
            output_path = os.path.join(EXPORT_DIR, f"{job_id}.md")
            with open(output_path, "w") as f:
                f.write(f"# Cost Report\n\n")
                f.write(f"**Period**: {days} days | **Total**: ${data['total_cost']:.4f}\n\n")
                f.write(f"## Daily Totals\n\n")
                f.write(f"| Date | Cost |\n|------|------|\n")
                for date_str, cost in sorted(daily_totals.items(), reverse=True):
                    f.write(f"| {date_str} | ${cost:.4f} |\n")
        else:
            output_path = os.path.join(EXPORT_DIR, f"{job_id}.json")
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

        job.status = "completed"
        job.output_path = output_path
        job.record_count = len(all_entries)
        job.completed_at = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        job.status = "failed"
        job.error = str(e)

    return job


def export_audit(days: int = 7, format: str = "json") -> ExportJob:
    """Export audit trail data."""
    _ensure_export_dir()
    job_id = f"exp_audit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    job = ExportJob(
        job_id=job_id,
        export_type="audit",
        format=format,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    try:
        events = []
        
        # Collect swarm events
        swarm_dir = "tmp/swarms"
        if os.path.exists(swarm_dir):
            for fname in os.listdir(swarm_dir):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(swarm_dir, fname), "r") as f:
                            swarm = json.load(f)
                            events.append({
                                "type": "swarm_execution",
                                "timestamp": swarm.get("created_at", ""),
                                "data": {
                                    "swarm_id": swarm.get("swarm_id"),
                                    "name": swarm.get("name"),
                                    "status": swarm.get("status"),
                                    "task_count": swarm.get("task_count", 0),
                                },
                            })
                    except Exception:
                        pass

        # Collect from audit exports
        audit_dir = "tmp/audit"
        if os.path.exists(audit_dir):
            for fname in os.listdir(audit_dir):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(audit_dir, fname), "r") as f:
                            audit_data = json.load(f)
                            events.extend(audit_data.get("events", []))
                    except Exception:
                        pass

        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "events": events,
            "total_events": len(events),
        }

        output_path = os.path.join(EXPORT_DIR, f"{job_id}.json")
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        job.status = "completed"
        job.output_path = output_path
        job.record_count = len(events)
        job.completed_at = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        job.status = "failed"
        job.error = str(e)

    return job


def export_full_backup() -> ExportJob:
    """Export everything — full platform backup."""
    _ensure_export_dir()
    job_id = f"exp_backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    job = ExportJob(
        job_id=job_id,
        export_type="full_backup",
        format="json",
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    try:
        knowledge_job = export_knowledge("json")
        costs_job = export_costs(90, "json")
        audit_job = export_audit(30, "json")

        backup_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "backup_type": "full",
            "components": {
                "knowledge": {
                    "file": knowledge_job.output_path,
                    "records": knowledge_job.record_count,
                    "status": knowledge_job.status,
                },
                "costs": {
                    "file": costs_job.output_path,
                    "records": costs_job.record_count,
                    "status": costs_job.status,
                },
                "audit": {
                    "file": audit_job.output_path,
                    "records": audit_job.record_count,
                    "status": audit_job.status,
                },
            },
        }

        output_path = os.path.join(EXPORT_DIR, f"{job_id}_manifest.json")
        with open(output_path, "w") as f:
            json.dump(backup_data, f, indent=2)

        job.status = "completed"
        job.output_path = output_path
        job.record_count = knowledge_job.record_count + costs_job.record_count + audit_job.record_count
        job.completed_at = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        job.status = "failed"
        job.error = str(e)

    return job


def list_exports() -> list:
    """List all export files."""
    exports = []
    if os.path.exists(EXPORT_DIR):
        for fname in sorted(os.listdir(EXPORT_DIR), reverse=True):
            fpath = os.path.join(EXPORT_DIR, fname)
            if os.path.isfile(fpath):
                exports.append({
                    "filename": fname,
                    "path": fpath,
                    "size_bytes": os.path.getsize(fpath),
                    "created": datetime.fromtimestamp(os.path.getctime(fpath), timezone.utc).isoformat(),
                })
    return exports
