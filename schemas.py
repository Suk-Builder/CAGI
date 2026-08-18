#!/usr/bin python3
"""CAGI API Schemas — Pydantic request/response 模型（仅 api_server 依赖）

领域类型在 models.py；这里只放 HTTP 边界的 schema，避免核心逻辑依赖 web 框架。
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DiscussRequest(BaseModel):
    question: str
    ground_truth: Optional[str] = None
    n_instances: int = 10
    n_rounds: int = 3
    backend: Optional[str] = None


class DiscussResponse(BaseModel):
    question: str
    final_answer: Dict[str, Any]
    conference_summary: Optional[Dict[str, Any]] = None
    pool_size: int
    n_rounds: int
    is_correct: Optional[bool]
    elapsed_seconds: float
    backend: str
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    version: str
    backend: str
    backend_ready: bool
    n_personas: int
    backend_status: Dict[str, bool]


class SolvayStartRequest(BaseModel):
    topic_key: str
    n_rounds: int = 3
    backend: Optional[str] = None


class SolvayStartResponse(BaseModel):
    task_id: str
    status: str
    topic: Dict[str, Any]
    n_rounds: int
    message: str


class SolvayStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Dict[str, Any]
    current_round: int
    n_speeches: int
    topic: Dict[str, Any]


class SolvayResultResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]]
    debate_log: List[Dict[str, Any]]
    n_speeches: int


class SolvayFreeStartRequest(BaseModel):
    topic_key: str
    backend: Optional[str] = None


class SolvayFreeStartResponse(BaseModel):
    task_id: str
    status: str
    topic: Dict[str, Any]
    message: str


class StreamStartRequest(BaseModel):
    topic_key: str
    backend: Optional[str] = None


class StreamStartResponse(BaseModel):
    task_id: str
    status: str
    stream_url: str
    message: str
