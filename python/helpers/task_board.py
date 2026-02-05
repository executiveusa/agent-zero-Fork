"""
Task Board -- shared coordination state for the agent swarm.

Thread-safe and file-backed so multiple processes (including Docker containers
sharing a volume mount) can read/write the same board without conflicts.

The board is the single source of truth for "what is each agent doing right now".
The master dashboard polls it via snapshot() on every tick.
"""

import json
import os
import time
import threading
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Optional

# Default path lives inside the shared workspace volume.  Override via env.
TASK_BOARD_PATH = os.environ.get(
    "TASK_BOARD_PATH", "workspace/.task_board.json"
)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class TaskEntry:
    id: str
    title: str
    status: TaskStatus
    owner: str                          # agent_name that owns this task
    result: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


class TaskBoard:
    """Singleton.  Call TaskBoard.get() everywhere."""

    _instance: Optional["TaskBoard"] = None
    _class_lock = threading.Lock()

    def __init__(self):
        self._tasks: dict[str, TaskEntry] = {}
        self._write_lock = threading.Lock()
        self._load()

    # ── singleton ────────────────────────────────────────────────────
    @classmethod
    def get(cls) -> "TaskBoard":
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── public API ───────────────────────────────────────────────────
    def register(self, title: str, owner: str, metadata: Optional[dict] = None) -> str:
        """Create a new PENDING task.  Returns the task_id."""
        task_id = f"{owner}-{int(time.time() * 1000)}"
        entry = TaskEntry(
            id=task_id,
            title=title,
            status=TaskStatus.PENDING,
            owner=owner,
            metadata=metadata or {},
        )
        with self._write_lock:
            self._tasks[task_id] = entry
            self._persist()
        return task_id

    def claim(self, task_id: str, owner: str) -> bool:
        """Transition PENDING → RUNNING.  Returns False if already claimed."""
        with self._write_lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.RUNNING
                task.owner = owner
                task.updated_at = time.time()
                self._persist()
                return True
        return False

    def complete(self, task_id: str, result: str = "") -> bool:
        """Transition → DONE."""
        with self._write_lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.DONE
                task.result = result
                task.updated_at = time.time()
                self._persist()
                return True
        return False

    def fail(self, task_id: str, error: str = "") -> bool:
        """Transition → FAILED."""
        with self._write_lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.FAILED
                task.error = error
                task.updated_at = time.time()
                self._persist()
                return True
        return False

    # ── queries ──────────────────────────────────────────────────────
    def get_by_status(self, status: TaskStatus) -> list[TaskEntry]:
        return [t for t in self._tasks.values() if t.status == status]

    def get_by_owner(self, owner: str) -> list[TaskEntry]:
        return [t for t in self._tasks.values() if t.owner == owner]

    def get(self, task_id: str) -> Optional[TaskEntry]:
        return self._tasks.get(task_id)

    # ── dashboard snapshot ───────────────────────────────────────────
    def snapshot(self) -> dict:
        """Full board state.  Consumed by the master dashboard poll."""
        return {
            "tasks": [
                {**asdict(t), "status": t.status.value}
                for t in self._tasks.values()
            ],
            "summary": {
                "pending": len(self.get_by_status(TaskStatus.PENDING)),
                "running": len(self.get_by_status(TaskStatus.RUNNING)),
                "done":    len(self.get_by_status(TaskStatus.DONE)),
                "failed":  len(self.get_by_status(TaskStatus.FAILED)),
            },
        }

    # ── persistence ──────────────────────────────────────────────────
    def _persist(self):
        """Write board to disk.  Called under _write_lock."""
        os.makedirs(os.path.dirname(TASK_BOARD_PATH) or ".", exist_ok=True)
        with open(TASK_BOARD_PATH, "w") as fh:
            json.dump(
                {tid: {**asdict(e), "status": e.status.value} for tid, e in self._tasks.items()},
                fh,
                indent=2,
            )

    def _load(self):
        """Hydrate from disk if the file exists."""
        if not os.path.exists(TASK_BOARD_PATH):
            return
        try:
            with open(TASK_BOARD_PATH, "r") as fh:
                raw = json.load(fh)
            for tid, data in raw.items():
                self._tasks[tid] = TaskEntry(
                    id=data["id"],
                    title=data["title"],
                    status=TaskStatus(data["status"]),
                    owner=data["owner"],
                    result=data.get("result", ""),
                    error=data.get("error", ""),
                    created_at=data.get("created_at", 0.0),
                    updated_at=data.get("updated_at", 0.0),
                    metadata=data.get("metadata", {}),
                )
        except (json.JSONDecodeError, KeyError):
            pass  # corrupt file -- start fresh
