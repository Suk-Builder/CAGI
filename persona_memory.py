"""
CCAGI v0.2 — Project 工坊核心创新: 每人小数据库 (PersonaMemory)
- 每 persona 独立维护: 自己的回答 + 印象最深的他人发言
- cosine 相似度选 top-k 注入 prompt
- 自己回答: 必入档 (无条件)
- 他人发言: 用 LLM 自己评分 "印象分" (1-5) 决定是否入档
- 真跑用 sentence-transformers, 现在用 char-bag 占位
"""

import re
import math
from collections import Counter
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class MemoryEntry:
    """单条记忆"""
    text: str
    author: str  # 谁说的
    round_num: int
    embedding: List[float] = field(default_factory=list)
    impression: float = 1.0  # 印象分 (1-5, 默认 1)
    type: str = "OTHER"  # SELF / NOTABLE_OTHER
    note: str = ""  # 备注


def char_bag_embed(text: str) -> List[float]:
    """字符袋 embedding (占位, 真跑换 sentence-transformers)"""
    text = re.sub(r"[\s\W]+", "", text.lower())
    # 用 256 维 ASCII 袋
    vec = [0.0] * 256
    for c in text:
        v = ord(c) % 256
        if v < 256:
            vec[v] += 1.0
    # L2 归一
    norm = math.sqrt(sum(x*x for x in vec)) or 1.0
    return [x / norm for x in vec]


def cosine(a: List[float], b: List[float]) -> float:
    """cosine 相似度"""
    if not a or not b:
        return 0.0
    return sum(x*y for x, y in zip(a, b))


class PersonaMemory:
    """每个 persona 独立维护的小数据库
    
    关键设计 (Project 11:18 拍):
    - 自己的回答: 必入档
    - 他人发言: 选印象最深的 (LLM 评 1-5 分入档)
    - 跑下轮时: Top-N SELF + Top-N NOTABLE 注入 prompt
    """
    
    def __init__(self, persona_id: int, persona_name: str,
                 max_self: int = 3, max_notable: int = 5):
        self.persona_id = persona_id
        self.persona_name = persona_name
        self.max_self = max_self
        self.max_notable = max_notable
        
        # 数据库
        self.self_answers: List[MemoryEntry] = []  # 自己的回答
        self.notable_others: List[MemoryEntry] = []  # 印象最深的他人
    
    def add_self_answer(self, text: str, round_num: int, note: str = ""):
        """入档: 自己的回答 (无条件)"""
        entry = MemoryEntry(
            text=text, author=self.persona_name, round_num=round_num,
            embedding=char_bag_embed(text), impression=5.0,
            type="SELF", note=note
        )
        self.self_answers.append(entry)
        # 超过上限: 保留最新的 + 印象最深的
        if len(self.self_answers) > self.max_self:
            # 按 impression 排序保留 top max_self
            self.self_answers.sort(key=lambda e: (e.impression, e.round_num), reverse=True)
            self.self_answers = self.self_answers[:self.max_self]
    
    def add_notable_other(self, text, author, round_num,
                          impression=1.0, note=""):
        """入档: 他人发言 (impression >= 3 才入)"""
        impression = impression or 1.0
        if impression < 3.0:
            return  # 不入档
        
        entry = MemoryEntry(
            text=text, author=author, round_num=round_num,
            embedding=char_bag_embed(text), impression=impression,
            type="NOTABLE_OTHER", note=note
        )
        self.notable_others.append(entry)
        
        # 超过上限: 按 impression 排序保留 top
        if len(self.notable_others) > self.max_notable:
            self.notable_others.sort(key=lambda e: e.impression, reverse=True)
            self.notable_others = self.notable_others[:self.max_notable]
    
    def select_top_k_for_prompt(self, query_text: str, 
                                  n_self: int = 2, n_notable: int = 3) -> Dict:
        """选最相关的 top-k 注入 prompt
        
        用 cosine 相似度 (query vs memory) 排序
        """
        query_emb = char_bag_embed(query_text)
        
        # 自己回答: 取最新 N 条
        self_sorted = sorted(self.self_answers, key=lambda e: e.round_num, reverse=True)
        top_self = self_sorted[:n_self]
        
        # 他人: 按 (impression × cosine) 排序
        notable_scored = []
        for e in self.notable_others:
            sim = cosine(query_emb, e.embedding)
            score = e.impression * 0.6 + sim * 0.4
            notable_scored.append((score, e))
        notable_scored.sort(key=lambda x: x[0], reverse=True)
        top_notable = [e for _, e in notable_scored[:n_notable]]
        
        return {
            "self": top_self,
            "notable": top_notable
        }
    
    def format_for_prompt(self, selected: Dict) -> str:
        """格式化成 prompt 文本"""
        lines = ["【你的小数据库 — 这是你记得的事】\n"]
        
        if selected["self"]:
            lines.append("### 你之前说过的话 (你必须保持一致):")
            for e in selected["self"]:
                lines.append(f"  R{e.round_num} 你说: {e.text[:300]}")
            lines.append("")
        
        if selected["notable"]:
            lines.append("### 你印象最深的他人发言 (可以回应):")
            for e in selected["notable"]:
                lines.append(f"  R{e.round_num} [{e.author} 印象{e.impression:.1f}]: {e.text[:300]}")
            lines.append("")
        
        return "\n".join(lines)
    
    def stats(self) -> Dict:
        """统计"""
        return {
            "persona": self.persona_name,
            "self_count": len(self.self_answers),
            "notable_count": len(self.notable_others),
            "avg_impression": (sum(e.impression for e in self.notable_others) / 
                                len(self.notable_others)) if self.notable_others else 0
        }
