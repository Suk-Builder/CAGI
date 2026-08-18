#!/usr/bin/env python3
"""CAGI 统一任务管理器 — 所有引擎共享"""

import uuid
import threading
from typing import Dict, Any, Optional
from datetime import datetime

class TaskManager:
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self, task_type: str, topic_key: str, backend: str, extra: Optional[Dict] = None) -> str:
        tid = str(uuid.uuid4())[:8]
        task = {
            "task_id": tid, "type": task_type, "status": "pending",
            "topic_key": topic_key, "backend": backend,
            "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
            "progress": {"phase": "等待开始", "completed": 0, "total": 0},
            "debate_log": [], "result": None, "error": None,
        }
        if extra:
            task.update(extra)
        with self._lock:
            self._tasks[tid] = task
        return tid

    def get(self, tid: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._tasks.get(tid)

    def update(self, tid: str, **kwargs):
        with self._lock:
            if tid in self._tasks:
                self._tasks[tid].update(kwargs)

    def set_progress(self, tid: str, phase: str, completed: int, total: int):
        with self._lock:
            if tid in self._tasks:
                self._tasks[tid]["progress"] = {"phase": phase, "completed": completed, "total": total}

    def append_log(self, tid: str, entry: Dict[str, Any]):
        with self._lock:
            if tid in self._tasks:
                self._tasks[tid]["debate_log"].append(entry)
                self._tasks[tid]["progress"]["completed"] = len(self._tasks[tid]["debate_log"])

    def list_tasks(self, task_type: Optional[str] = None) -> list:
        with self._lock:
            tasks = list(self._tasks.values())
        if task_type:
            tasks = [t for t in tasks if t.get("type") == task_type]
        return [
            {"task_id": t["task_id"], "type": t.get("type"), "status": t["status"],
             "topic_key": t.get("topic_key"), "progress": t.get("progress", {}),
             "created_at": t.get("created_at")}
            for t in tasks
        ]

TASKS = TaskManager()
