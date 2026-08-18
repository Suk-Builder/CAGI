#!/usr/bin python3
"""CAGI 领域数据模型 — 不依赖任何 web 框架

Expert / Topic 是核心领域类型，被 core / engine / experts / topics 共享。
API 的 Pydantic schema 在 schemas.py（仅 api_server 依赖）。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


@dataclass
class Expert:
    persona_id: int
    name: str
    name_en: str
    avatar_emoji: str
    domain: str
    style: str
    constraints: List[str]
    stance: str
    signature_phrase: str
    signature_zh: str
    cognitive_framework: str
    attack_style: str
    defense_style: str
    realism_score: float = 0.5
    famous_thought_experiments: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "name": self.name,
            "name_en": self.name_en,
            "avatar_emoji": self.avatar_emoji,
            "domain": self.domain,
            "style": self.style,
            "constraints": self.constraints,
            "stance": self.stance,
            "signature_phrase": self.signature_phrase,
            "signature_zh": self.signature_zh,
            "cognitive_framework": self.cognitive_framework,
            "attack_style": self.attack_style,
            "defense_style": self.defense_style,
            "realism_score": self.realism_score,
            "famous_thought_experiments": self.famous_thought_experiments,
        }


@dataclass
class Topic:
    key: str
    title: str
    title_en: str
    description: str
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "title_en": self.title_en,
            "description": self.description,
            "tags": self.tags,
        }


# ─── SSE 事件类型 ───

class SSEEventType(str, Enum):
    CONNECTED   = "connected"
    ROUND_START = "round_start"
    SPEECH      = "speech"
    CONSENSUS   = "consensus"
    HEARTBEAT   = "heartbeat"
    AUTO_STOP   = "auto_stop"
    COMPLETED   = "completed"
    ERROR       = "error"
    STOPPED     = "stopped"


@dataclass
class SSEEvent:
    event: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def format(self) -> str:
        payload = {"event": self.event, **self.data, "timestamp": self.timestamp}
        import json
        return f"event: {self.event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
