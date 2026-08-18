#!/usr/bin/env python3
"""CAGI 核心抽象 — 所有引擎共享的单一数据源

合并自原 engine_cagi / ccagi_v02 / engine_solvay / engine_free / engine_stream 中
复制粘贴的部分：专长锁死、讨论池、答案归一化、投票汇总、专家 prompt、专家记忆、共识分析。
重写后这些只此一份，四种引擎模式（vote/debate/free/stream）都 import 这里。
"""

import asyncio
import re
from typing import List, Dict, Any, Optional, Callable
from collections import Counter
from datetime import datetime

from models import Expert


# ───────────────────────── 并发限制 ─────────────────────────

class ConcurrentLimiter:
    """信号量控并发，避免打爆后端 API。"""
    def __init__(self, max_concurrent: int = 30):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def run(self, coro):
        async with self.semaphore:
            return await coro


# ───────────────────────── 讨论池 ─────────────────────────

class DiscussionPool:
    """所有专家发言按次序写入同一个公共池，是'公共池 + 精英票权'的物理载体。"""
    def __init__(self, max_view: int = 50):
        self._lock = asyncio.Lock()
        self._entries: List[Dict[str, Any]] = []
        self.max_view = max_view

    async def append(self, persona_id: int, round_num: int, content: str,
                     duplicated: bool = False) -> None:
        async with self._lock:
            self._entries.append({
                "persona_id": persona_id,
                "round": round_num,
                "content": content,
                "duplicated": duplicated,
                "timestamp": datetime.now().isoformat(),
            })

    def snapshot(self) -> List[Dict[str, Any]]:
        return list(self._entries)

    def view(self, round_num: int, persona_id: int) -> str:
        """当前专家本轮可见的池视图（同步辩论语义）：只看已完成轮次（round < round_num），
        第 r 轮必然看到第 1..r-1 轮全体发言，无并发竞态。取最近 max_view 条截断防 token 爆炸。"""
        recent = [e for e in self._entries if e["round"] < round_num][-self.max_view:]
        if not recent:
            return "（暂无发言）"
        lines = [f"【R{e['round']}·#{e['persona_id']}】{e['content'][:200]}" for e in recent]
        return "\n\n".join(lines)

    def __len__(self) -> int:
        return len(self._entries)


# ───────────────────────── 观点数据库（池子脱敏）─────────────────────────

class OpinionDB:
    """第三方记录员维护的观点数据库：只存结构化观点摘要，不存原文措辞。

    专家之间的"真隔离"：每人看到的不是彼此的发言原文，而是记录员转述的
    观点卡片（摘要 + 反驳关系）。转述改变了措辞，从根上消除跨专家抄写。
    """
    def __init__(self, max_view: int = 40):
        self._opinions: List[Dict[str, Any]] = []
        self.max_view = max_view

    def append(self, expert_id: int, expert_name: str, round_num: int,
               summary: str, attacks: Optional[List[int]] = None) -> None:
        self._opinions.append({
            "expert_id": expert_id, "expert_name": expert_name, "round": round_num,
            "summary": summary, "attacks": attacks or [],
        })

    def view_for(self, round_num: int) -> str:
        """给专家看的观点卡片视图：只看已完成轮次（round < round_num），
        每条 = 记录员转述的摘要 + 反驳关系。不含原文措辞。"""
        cards = []
        for o in self._opinions:
            if o["round"] >= round_num:
                continue
            atk = f"（反驳了 #{', #'.join(str(a) for a in o['attacks'])}）" if o["attacks"] else ""
            cards.append(f"【R{o['round']}·{o['expert_name']}】{atk}{o['summary']}")
        recent = cards[-self.max_view:]
        return "\n\n".join(recent) if recent else "（暂无发言）"

    def snapshot(self) -> List[Dict[str, Any]]:
        return list(self._opinions)

    def __len__(self) -> int:
        return len(self._opinions)


# ───────────────────────── 答案归一化 ─────────────────────────

def normalize_answer(text: str) -> str:
    """提取核心答案，用于投票归一化。"""
    import re as _re
    text = (text or "").strip().lower()
    # 剥离 qwen3 等模型的 <think>...</think> 思维链，否则推理污染答案
    text = _re.sub(r"<think>.*?</think>", "", text, flags=_re.DOTALL).strip()

    # 1. 数字（数学问题）
    numbers = _re.findall(r"[-+]?\d+\.?\d*", text)
    if numbers:
        return numbers[-1]  # 取最后一个数字（通常是结论）

    # 2. LaTeX 等式结果
    latex_result = _re.findall(r"=\s*([\w\d]+)", text)
    if latex_result:
        return latex_result[-1]

    # 3. 中文实体（地名、人名等）：取最后一句话，去修饰前缀
    sentences = _re.split(r"[。！？\n]", text)
    for s in reversed(sentences):
        s = s.strip()
        if s:
            s = _re.sub(r"从\s*\w+\s*看[:：]", "", s).strip()
            s = _re.sub(r"答案是[:：]?\s*", "", s).strip()
            s = _re.sub(r"结果是[:：]?\s*", "", s).strip()
            if s:
                return s
    return text


# ───────────────────────── 投票汇总 ─────────────────────────

def vote_from_pool(pool: DiscussionPool) -> Dict[str, Any]:
    """原语义：仅消费首轮（R1）发言做投票。"""
    entries = [e for e in pool.snapshot() if e["round"] == 1]
    if not entries:
        entries = pool.snapshot()
    return _tally(entries, pool)


def vote_from_full_pool(pool: DiscussionPool) -> Dict[str, Any]:
    """修复语义：消费全池 R1..RN 所有轮次发言做投票。"""
    entries = pool.snapshot()
    return _tally(entries, pool)


def vote_from_round(pool: DiscussionPool, round_num: int) -> Dict[str, Any]:
    """辩论语义：只消费最终轮（RN）发言做投票——吵架后存活的立场。"""
    entries = [e for e in pool.snapshot() if e["round"] == round_num]
    if not entries:
        entries = pool.snapshot()
    return _tally(entries, pool)


def _tally(entries: List[Dict[str, Any]], pool: DiscussionPool) -> Dict[str, Any]:
    all_content = [e["content"] for e in entries]
    normalized = [normalize_answer(c) for c in all_content]
    counter = Counter(normalized)
    winner_norm, count = counter.most_common(1)[0]
    winner_original = None
    for orig, norm in zip(all_content, normalized):
        if norm == winner_norm:
            winner_original = orig
            break
    return {
        "answer": winner_original or winner_norm,
        "normalized_answer": winner_norm,
        "confidence": count / len(all_content) if all_content else 0,
        "vote_distribution": dict(counter),
        "n_unique_answers": len(counter),
        "total_pool_size": len(pool),
        "rounds_considered": sorted({e["round"] for e in entries}),
    }


# ───────────────────────── 专家 prompt 构建 ─────────────────────────

def build_expert_system_prompt(expert: Expert, extra: str = "") -> str:
    """专长锁死：把专家身份冻结进 system prompt（等价原 PersonaLock.to_system_prompt）。"""
    constraints_text = "\n".join(f"  - {c}" for c in expert.constraints)
    return (
        f"你是{expert.name}（{expert.name_en}），{expert.domain}领域的奠基人。\n"
        f"你的认知风格: {expert.style}\n"
        f"你的核心立场: {expert.stance}\n"
        f"你的认知框架: {expert.cognitive_framework}\n"
        f"约束:\n{constraints_text}\n"
        f"重要规则:\n"
        f"1. 以{expert.name}本人的方式发言：像在学术会议或期刊审稿中那样，严谨、克制、专业。不要表演、不要夸张、不要戏剧化。\n"
        f"2. 语言: 以中文为主；若你是德语区学者（德国/奥地利），说话可自然带德语短句（例如 Wir müssen wissen.），"
        f"但只在自然处出现，不要为了名言而名言、不要复读套话。\n"
        f"3. 你的标志性语言是「{expert.signature_phrase}」：最多在真正适合的地方用一次，禁止反复出现，也禁止借用其他专家的名言。\n"
        f"4. 坚持你的认知框架和立场，但用具体的专业论证说话（公式、数值、实验、思想实验、反例）；"
        f"禁止只喊立场口号、禁止哲学空转（如只重复'实在先于测量''公理非定理'）。"
        + (f"\n\n{extra}" if extra else "")
    )


def build_expert_user_prompt(topic_title: str, topic_desc: str, pool_view: str,
                             round_num: int, expert_name: str, instruction: str = "") -> str:
    return (
        f"议题: {topic_title}\n"
        f"议题描述: {topic_desc}\n"
        f"前面的讨论:\n{pool_view}\n"
        f"现在是第{round_num}轮，轮到你发言。{instruction}\n"
        f"记住：你是{expert_name}。"
    )


# ───────────────────────── 专家记忆 ─────────────────────────

class ExpertMemory:
    """每个专家独立维护的小数据库：自己的发言 + 印象最深的他人发言。

    合并原 engine_free.ExpertMemory 与 engine_stream.StreamExpertMemory（两者完全相同）。
    """
    def __init__(self, expert: Dict[str, Any]):
        self.expert = expert
        self.speeches: List[Dict[str, Any]] = []
        self.rebuttal_targets: List[str] = []
        self.rebutted_by: List[str] = []

    def add_speech(self, phase: str, content: str, targets: List[str] = None):
        self.speeches.append({"phase": phase, "content": content, "targets": targets or []})
        if targets:
            self.rebuttal_targets.extend(targets)

    def add_rebuttal(self, source: str, content: str):
        self.rebutted_by.append(source)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expert_name": self.expert["name"],
            "speeches_count": len(self.speeches),
            "rebuttal_targets": list(set(self.rebuttal_targets)),
            "rebutted_by": list(set(self.rebutted_by)),
        }


# ───────────────────────── 共识分析 ─────────────────────────

# 单一数据源：认知框架 → 实在论倾向分（原 solvay/free/stream 各抄一份，现合并）
STANCE_REALISM: Dict[str, float] = {
    "形式主义": 0.3, "互补性原理": 0.2, "定域实在论": 0.9,
    "操作主义": 0.4, "连续实在论": 0.8, "导波理论": 0.85,
    "统计诠释": 0.5, "对称性优先": 0.6,
    "不完备性原理": 0.35, "数学直觉主义": 0.75,
    "经典决定论": 0.95, "圆环之理": 0.5,
}


def analyze_consensus(experts: List[Dict[str, Any]],
                      speeches: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """按认知框架的实在论分做方差→共识度，并划分阵营。speeches 可选，用于按阶段细分。"""
    scores = [STANCE_REALISM.get(e.get("cognitive_framework", ""), 0.5) for e in experts]
    variance = (sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(scores)
                if len(scores) > 1 else 0)
    consensus_score = round(max(0.0, 1 - variance * 4), 2)

    camps = {"实在论阵营": [], "反实在论阵营": [], "中间/工具主义": []}
    for e in experts:
        sc = STANCE_REALISM.get(e.get("cognitive_framework", ""), 0.5)
        if sc >= 0.7:
            camps["实在论阵营"].append(e["name"])
        elif sc <= 0.3:
            camps["反实在论阵营"].append(e["name"])
        else:
            camps["中间/工具主义"].append(e["name"])

    result = {
        "consensus_score": consensus_score,
        "camps": {k: v for k, v in camps.items() if v},
        "stance_spectrum": {
            "min_realism": min(STANCE_REALISM.values()),
            "max_realism": max(STANCE_REALISM.values()),
            "avg_realism": round(sum(STANCE_REALISM.values()) / len(STANCE_REALISM), 2),
        },
    }
    if speeches:
        result["n_speeches"] = len(speeches)
    return result
