#!/usr/bin/env python3
"""CAGI 统一引擎 — 四种讨论模式共享核心

模式:
  vote    — /discuss：三层架构（个人人格/人格记忆/会议总结）同步轮次纯吵架，裁判按最终立场原文判断最后的情况
  debate  — 原 engine_solvay：围绕议题多轮圆桌辩论 + 共识分析
  free    — 原 engine_free：种子→阵营反应→自由交叉→总结 四阶段辩论
  stream  — 原 engine_stream：无限轮 SSE 流式辩论，达共识阈值自动收敛

所有模式共用 core.py 的锁/池/投票/专家prompt/记忆/共识，不再各抄一份。
"""

import asyncio
import json
import re
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from core import (
    ConcurrentLimiter, DiscussionPool, OpinionDB, normalize_answer,
    vote_from_full_pool, vote_from_pool, vote_from_round,
    build_expert_system_prompt, build_expert_user_prompt,
    ExpertMemory, analyze_consensus,
)
from experts import SOLVAY_EXPERTS, get_expert_dicts
from topics import get_topic
from tasks import TASKS
from backends import call_with_fallback
from config import (
    MAX_CONCURRENT, POOL_MAX_VIEW, N_DISCUSSION_ROUNDS,
    SOLVAY_MAX_SPEECH_LEN, SOLVAY_SUMMARY_LEN,
    STREAM_MAX_HISTORY, STREAM_CONSENSUS_THRESHOLD, STREAM_CONSENSUS_ROUNDS,
)
from models import Expert


# ───────────────────────── 公共：并发调用单个专家 ─────────────────────────

async def _call_expert(expert: Expert, user_prompt: str, backend_caller: Callable,
                       limiter: ConcurrentLimiter) -> str:
    system = build_expert_system_prompt(expert)
    try:
        content = await limiter.run(call_with_fallback(system, user_prompt, backend_caller))
        return content.strip()
    except Exception as e:
        return f"[{expert.name}] 发言中断: {str(e)[:80]}"


def _dup_ratio(new_content: str, history: List[str]) -> float:
    """该专家本轮发言与其历史发言的最高相似度（复读检测用）。"""
    from difflib import SequenceMatcher
    best = 0.0
    for h in history:
        if h:
            r = SequenceMatcher(None, h, new_content).ratio()
            if r > best:
                best = r
    return best


# ───────────────────────── 第三方记录员（池子脱敏核心）─────────────────────────

SUMMARIZER_SYSTEM = (
    "你是辩论记录员。你不参与辩论、不表达任何立场、不评价对错。"
    "你的唯一职责：把专家的发言提炼成客观、准确的观点摘要。\n"
    "规则（准确优先，宁可多写不可漏）：\n"
    "1. 必须保留发言中划清界限的限定语：如'非…''但需补充…''我反对/认同X的…'，"
    "不得抹掉该专家与其他专家立场的区别。\n"
    "2. 若发言点名批评或反驳了谁（如 #2、#5），summary 必须体现'他批评/反驳了X的什么观点'，"
    "attacks 记录被批评的专家 id。\n"
    "3. 只基于本轮这条发言的内容总结，禁止使用其他轮次或其他发言的信息（禁止串轮、禁止脑补）。\n"
    "4. 用你自己的话转述，禁止摘抄原文措辞；摘要 60-90 字。\n"
    "严格输出 JSON 数组：[{\"expert_id\": 1, \"summary\": \"...\", \"attacks\": [2, 3]}]"
)


async def summarize_round(entries: List[Dict[str, Any]], round_num: int,
                          backend_caller: Callable, limiter: ConcurrentLimiter) -> Optional[List[Dict[str, Any]]]:
    """第三方记录员：把本轮全体发言总结成观点摘要（一次调用）。失败返回 None。"""
    if not entries:
        return []
    text = "\n\n".join(
        f"专家{e['expert_id']}（{e['expert_name']}）: {e['content']}" for e in entries)
    user = (
        f"以下是第{round_num}轮全体专家的发言原文。请提炼每个人的观点摘要（用你自己的话转述，不抄原文）：\n\n{text}"
    )
    try:
        raw = (await limiter.run(call_with_fallback(SUMMARIZER_SYSTEM, user, backend_caller))).strip()
        start_i, end_i = raw.find("["), raw.rfind("]")
        if start_i < 0 or end_i < start_i:
            return None
        span = raw[start_i:end_i + 1]
        try:
            parsed = json.loads(span)
        except Exception:
            parsed = json.loads(re.sub(r"\\(?![\"\\/bfnrtu])", "", span))
        if not isinstance(parsed, list):
            return None
        out = []
        for s in parsed:
            if isinstance(s, dict) and "expert_id" in s:
                out.append({
                    "expert_id": int(s["expert_id"]),
                    "summary": str(s.get("summary", ""))[:120],
                    "attacks": [int(a) for a in s.get("attacks", []) if str(a).isdigit()],
                })
        return out if out else None
    except Exception as e:
        print(f"[Summarizer] 记录员调用失败: {str(e)[:120]}")
        return None


def _expert_entry(expert: Expert, round_num: int, phase: str, content: str) -> Dict[str, Any]:
    d = expert.to_dict()
    return {
        "round": round_num, "phase": phase,
        "expert_id": d["persona_id"], "expert_name": d["name"],
        "expert_name_en": d["name_en"], "expert_avatar": d["avatar_emoji"],
        "expert_domain": d["domain"], "expert_framework": d["cognitive_framework"],
        "realism_score": d.get("realism_score", 0.5),
        "content": content, "timestamp": datetime.now().isoformat(),
    }


# ───────────────────────── 模式 vote：QA 投票 ─────────────────────────

async def run_cagi_discussion(
    question: str,
    ground_truth: Optional[str] = None,
    n_instances: int = 6,
    n_rounds: int = N_DISCUSSION_ROUNDS,
    backend_caller: Optional[Callable] = None,
    vote_mode: str = "last_round",  # "last_round"=纯吵架：原文为准+裁判判断；"full"/"round1"=旧评分对照
) -> Dict[str, Any]:
    if backend_caller is None:
        from backends import get_backend
        backend_caller = get_backend()

    # 专家池不足则循环复用（统一注册表只有 SOLVAY_EXPERTS 一份）
    base = SOLVAY_EXPERTS
    if n_instances > len(base):
        selected = (base * ((n_instances // len(base)) + 1))[:n_instances]
    else:
        selected = base[:n_instances]

    pool = DiscussionPool(max_view=POOL_MAX_VIEW)
    limiter = ConcurrentLimiter(MAX_CONCURRENT)
    # 池子脱敏：第三方记录员维护的观点数据库（专家只见观点卡片，不见原文）
    opinions = OpinionDB(max_view=POOL_MAX_VIEW)
    # 三层架构·第二层：人格记忆（每专家独立发言史 + 反驳关系）
    memories = {e.persona_id: ExpertMemory(e.to_dict()) for e in selected}
    _target_re = re.compile(r"#(\d+)")

    async def call_persona_round(expert: Expert, round_num: int):
        # 池子脱敏：第2轮起只见记录员转述的观点卡片，不看任何人的发言原文
        pool_view = opinions.view_for(round_num) if round_num > 1 else "（暂无发言）"
        mem = memories[expert.persona_id]
        if round_num == 1:
            instruction = "请给出你的回答和推理（限制100字内）。"
        else:
            mem_lines = []
            if mem.speeches:
                mem_lines.append("你此前的发言（这些你已经说过了，禁止重复）: " + " | ".join(
                    s["content"][:80] for s in mem.speeches[-2:]))
            if mem.rebuttal_targets:
                mem_lines.append("你反驳过: " + "、".join(sorted(set(mem.rebuttal_targets))))
            if mem.rebutted_by:
                mem_lines.append("反驳过你的: " + "、".join(sorted(set(mem.rebutted_by))))
            memory_block = "你的记忆:\n" + "\n".join(mem_lines) if mem_lines else ""
            instruction = (
                "现在进入辩论环节：给出你的论证，并攻击对方论证的要害。\n"
                "质量要求：\n"
                "1. 准确：用你的专业知识说话——具体的技术论证（公式、数值、实验、思想实验、反例），禁止空洞的立场口号。\n"
                "2. 狠：攻击必须打在对方论证的具体缺陷上（逻辑漏洞、反例、自相矛盾、前提错误），"
                "禁止只贴'范畴错误''形而上学'这类标签就完事。\n"
                "3. 禁止哲学打圈圈：不要只重复立场口号（如'实在先于测量''公理非定理'）；"
                "每次发言必须给出新的技术论证，或指出对方论证的一个具体缺陷。\n"
                "4. 不要复述别人的话，不要和稀泥，不要夸张表演。每轮必须推进："
                "没有新论点就明确说'我的立场不变'并只补充一点新的。限制100字内。"
            )
            if memory_block:
                instruction = memory_block + "\n\n" + instruction
        user = (
            f"题目: {question}\n\n"
            f"前面的讨论:\n{pool_view}\n\n"
            f"{instruction}"
        )
        content = await _call_expert(expert, user, backend_caller, limiter)
        duplicated = False
        if round_num > 1 and mem.speeches:
            prev_texts = [s["content"] for s in mem.speeches]
            if _dup_ratio(content, prev_texts) >= 0.80:
                # 复读僵化：重试一次，明示警告
                warn = user + (
                    "\n\n[警告] 你刚才的发言与你此前的发言高度重复（复读）。"
                    "不要复读已说过的内容：给出新的论点、或针对对方最新反驳的深入回应，"
                    "或明确承认立场不变但补充一个此前未说的论证角度。"
                )
                retry = await _call_expert(expert, warn, backend_caller, limiter)
                content = retry
                duplicated = _dup_ratio(content, prev_texts) >= 0.80  # 仍复读则标记（防死循环）
        await pool.append(expert.persona_id, round_num, content, duplicated=duplicated)
        target_ids = [int(t) for t in _target_re.findall(content)
                      if t.isdigit() and int(t) != expert.persona_id]
        mem.add_speech(f"第{round_num}轮", content, [str(t) for t in target_ids])
        for t in target_ids:
            if t in memories:
                memories[t].add_rebuttal(expert.name, content[:100])
        return content

    start = time.time()
    # 纯吵架：同步轮次屏障，每轮全体发言完才进下一轮；第 r 轮必然看到前 r-1 轮全体发言
    for round_num in range(1, n_rounds + 1):
        await asyncio.gather(*[call_persona_round(e, round_num) for e in selected])
        # 第三方记录员：本轮发言总结进观点数据库（专家下轮只见观点卡片，不见原文）
        round_entries = [e for e in pool.snapshot() if e["round"] == round_num]
        r_entries = []
        for e in round_entries:
            ex = next((x for x in selected if x.persona_id == e["persona_id"]), None)
            r_entries.append({
                "expert_id": e["persona_id"],
                "expert_name": ex.name if ex else f"#{e['persona_id']}",
                "content": e["content"],
            })
        id2name = {e["expert_id"]: e["expert_name"] for e in r_entries}
        summaries = await summarize_round(r_entries, round_num, backend_caller, limiter)
        if summaries:
            for s in summaries:
                opinions.append(s["expert_id"], id2name.get(s["expert_id"], "?"),
                                round_num, s["summary"], s["attacks"])
        else:
            # 降级：原文截断入库（保证辩论不中断，措辞仍可被转述性使用）
            for e in r_entries:
                opinions.append(e["expert_id"], e["expert_name"], round_num, e["content"][:80], [])
    elapsed = time.time() - start

    # 三层架构·第三层：会议总结（最终立场原文 + 共识分析 + 裁判判断）
    final_entries = [e for e in pool.snapshot() if e["round"] == n_rounds]
    final_positions = []
    for e in final_entries:
        ex = next((x for x in selected if x.persona_id == e["persona_id"]), None)
        final_positions.append({
            "expert_name": ex.name if ex else f"#{e['persona_id']}",
            "cognitive_framework": ex.cognitive_framework if ex else "",
            "content": e["content"],
        })
    # 第1轮起点（裁判判断早期共识是否被推翻用）
    r1_entries = [e for e in pool.snapshot() if e["round"] == 1]
    round1_positions = []
    for e in r1_entries:
        ex = next((x for x in selected if x.persona_id == e["persona_id"]), None)
        round1_positions.append({
            "expert_name": ex.name if ex else f"#{e['persona_id']}",
            "cognitive_framework": ex.cognitive_framework if ex else "",
            "content": e["content"],
        })
    consensus = analyze_consensus([e.to_dict() for e in selected], pool.snapshot())

    # 全程 trace（人格稳定性审计用）：每轮每人的发言节选
    trace = []
    for e in pool.snapshot():
        ex = next((x for x in selected if x.persona_id == e["persona_id"]), None)
        trace.append({
            "round": e["round"],
            "expert_name": ex.name if ex else f"#{e['persona_id']}",
            "content": e["content"][:150],
            "duplicated": e.get("duplicated", False),
        })

    judge = None
    if vote_mode == "round1":
        vote_result = vote_from_pool(pool)
    elif vote_mode == "full":
        vote_result = vote_from_full_pool(pool)
    else:
        # 默认（原文为准）：裁判只依据最终立场原文判断"最后的情况"
        judge = await _judge_final(question, ground_truth, final_positions,
                                   round1_positions, n_rounds, backend_caller, limiter)
        if judge:
            vote_result = {
                "answer": judge["winner_original"],
                "normalized_answer": judge["judged_answer"],
                "confidence": round(judge["support_count"] / judge["total_positions"], 4)
                              if judge.get("total_positions") else 0.0,
                "vote_distribution": {p["expert_name"]: p["content"] for p in final_positions},
                "n_unique_answers": len(final_positions),
                "total_pool_size": len(pool),
                "rounds_considered": [n_rounds],
                "judgment": judge,
            }
        else:
            vote_result = vote_from_round(pool, n_rounds)  # 裁判调用失败时的规则兜底

    is_correct = None
    if ground_truth:
        if judge and judge.get("is_correct") is not None:
            is_correct = judge["is_correct"]
        else:
            is_correct = normalize_answer(vote_result.get("answer", "")) == normalize_answer(ground_truth)

    return {
        "question": question,
        "final_answer": vote_result,
        "conference_summary": {
            "final_positions": final_positions,
            "consensus": consensus,
            "judgment": judge,
            "opinions": opinions.snapshot(),
            "trace": trace,
        },
        "pool_size": len(pool),
        "n_rounds": n_rounds,
        "vote_mode": vote_mode,
        "is_correct": is_correct,
        "elapsed_seconds": round(elapsed, 2),
        "backend": "injected" if backend_caller else "default",
        "timestamp": datetime.now().isoformat(),
    }


async def _judge_final(question: str, ground_truth: Optional[str],
                       final_positions: List[Dict[str, Any]],
                       round1_positions: List[Dict[str, Any]], n_rounds: int,
                       backend_caller: Callable, limiter: ConcurrentLimiter) -> Optional[Dict[str, Any]]:
    """裁判：只依据专家发言原文判断辩论最后的情况（原文为准，不做数字抽奖）。"""
    if not final_positions:
        return None
    # 给裁判的文本剥掉 LaTeX（原文照旧保留在 conference_summary，避免模型把 \c 之类塞回 JSON 破坏解析）
    def _clean(s: str) -> str:
        return re.sub(r"[\\\\$]", "", s)

    positions_txt = "\n\n".join(
        f"【{p['expert_name']} · {p['cognitive_framework']}】\n{_clean(p['content'])}"
        for p in final_positions)
    r1_txt = "\n\n".join(
        f"【{p['expert_name']}】\n{_clean(p['content'])}" for p in round1_positions) if round1_positions else "（无）"
    system = (
        "你是辩论裁判。只依据专家们发言的原文判断，不预设标准答案、不做数字抽取。"
        "专家发言是历史人物的角色立场，不代表他们本人正确或错误。"
    )
    gt_line = f"参考答案（仅用于判定最终答案是否相符）: {ground_truth}\n\n" if ground_truth else ""
    user = (
        f"题目: {question}\n\n"
        f"辩论起点（第1轮发言）:\n{r1_txt}\n\n"
        f"最终立场原文（第{n_rounds}轮，共{len(final_positions)}位）:\n{positions_txt}\n\n"
        f"{gt_line}"
        "请判断辩论最后的情况：\n"
        "1. 最终立场中，哪些真正回答了题目？\n"
        "2. 综合整场辩论，结论是什么？（用原文支撑）\n"
        "3. 最终答案是什么？注意：若最终轮无人再报具体数值，"
        "检查辩论起点（第1轮）是否已确立数值且未被后续发言推翻——未被推翻则以该数值为最终答案。\n"
        "4. 支持该最终答案的立场有几个（把起点共识与最终轮一致立场都计入）？\n"
        "5. 若给了参考答案，最终答案是否与它一致：数值相等、单位等价、或最终答案比参考答案更精确"
        "（如 99.974°C 与 100°C、差异在 0.1 以内）都算一致？\n"
        "严格只输出 JSON：{\"judged_answer\":\"...\",\"winner_persona\":\"...\","
        "\"support_count\":数字,\"total_positions\":数字,\"is_correct\":true或false,\"reason\":\"...\"}"
    )
    try:
        raw = (await limiter.run(call_with_fallback(system, user, backend_caller))).strip()
        start_i, end_i = raw.find("{"), raw.rfind("}")
        if start_i < 0 or end_i < start_i:
            return None
        span = raw[start_i:end_i + 1]
        try:
            judge = json.loads(span)
        except Exception:
            # 模型可能仍塞了 \c / \text 之类非法转义：清掉反斜杠后重试
            judge = json.loads(re.sub(r"\\(?![\"\\/bfnrtu])", "", span))
        if not isinstance(judge, dict) or "judged_answer" not in judge:
            return None
        w = judge.get("winner_persona")
        if isinstance(w, list):
            winners = [p for p in final_positions if p["expert_name"] in w]
            judge["winner_original"] = winners[0]["content"] if winners else final_positions[0]["content"]
        else:
            winner = next((p for p in final_positions if p["expert_name"] == w), None)
            judge["winner_original"] = winner["content"] if winner else final_positions[0]["content"]
        judge.setdefault("support_count", 0)
        judge.setdefault("total_positions", len(final_positions))
        judge.setdefault("is_correct", None)
        return judge
    except Exception as e:
        print(f"[Judge] 裁判调用失败，回退规则兜底: {str(e)[:120]}")
        return None


# ───────────────────────── 模式 debate：经典圆桌 ─────────────────────────

async def run_solvay_conference(tid: str, topic_key: str, n_rounds: int, backend_caller: Callable):
    topic = get_topic(topic_key).to_dict()
    experts = SOLVAY_EXPERTS
    expert_dicts = [e.to_dict() for e in experts]
    all_speeches: List[Dict[str, Any]] = []
    TASKS.update(tid, status="running", started_at=datetime.now().isoformat())
    TASKS.set_progress(tid, "种子辩论", 0, len(experts) * n_rounds)
    limiter = ConcurrentLimiter(MAX_CONCURRENT)

    for round_num in range(1, n_rounds + 1):
        recent = all_speeches[-20:] if len(all_speeches) > 20 else all_speeches
        pool_view = "\n\n".join(
            [f"【{s['round']}轮·{s['expert_name']}】{s['content'][:100]}..." for s in recent]
        ) if recent else "（暂无发言）"

        async def speak(expert):
            user = build_expert_user_prompt(
                topic["title"], topic["description"], pool_view, round_num, expert.name,
                instruction="请基于你的专长和立场，给出你的观点。")
            return await _call_expert(expert, user, backend_caller, limiter)

        results = await asyncio.gather(*[speak(e) for e in experts], return_exceptions=True)
        for expert, content in zip(experts, results):
            if isinstance(content, Exception):
                content = f"[{expert.name}] 发言中断: {str(content)[:50]}"
            entry = _expert_entry(expert, round_num, "圆桌", content[:SOLVAY_MAX_SPEECH_LEN])
            TASKS.append_log(tid, entry)
            all_speeches.append(entry)
        TASKS.set_progress(tid, f"第{round_num}轮辩论", len(all_speeches), len(experts) * n_rounds)
        await asyncio.sleep(0.5)

    consensus = analyze_consensus(expert_dicts, all_speeches)
    result = {
        "topic": topic, "n_experts": len(experts), "n_rounds": n_rounds,
        "consensus_analysis": consensus, "debate_log": all_speeches,
        "summary": {
            "title": "第五次索尔维会议 — 经典辩论记录",
            "final_consensus": f"共识度: {consensus['consensus_score']*100:.0f}%",
            "total_speeches": len(all_speeches),
        },
    }
    TASKS.update(tid, status="completed", completed_at=datetime.now().isoformat(), result=result)


# ───────────────────────── 模式 free：四阶段辩论 ─────────────────────────

async def run_free_debate(tid: str, topic_key: str, backend_caller: Callable):
    topic = get_topic(topic_key).to_dict()
    experts = SOLVAY_EXPERTS
    expert_dicts = [e.to_dict() for e in experts]
    memories = {e.persona_id: ExpertMemory(e.to_dict()) for e in experts}
    all_speeches: List[Dict[str, Any]] = []
    TASKS.update(tid, status="running", started_at=datetime.now().isoformat())
    limiter = ConcurrentLimiter(MAX_CONCURRENT)

    async def gen(expert, user):
        return await _call_expert(expert, user, backend_caller, limiter)

    # 阶段1 种子辩论：玻尔 + 爱因斯坦
    TASKS.set_progress(tid, "种子辩论", 0, 2)
    seeds = [e for e in experts if e.name in ("尼尔斯·玻尔", "阿尔伯特·爱因斯坦")]
    seed_results = await asyncio.gather(*[
        gen(e, f"议题: {topic['title']}\n议题描述: {topic['description']}\n你是{e.name}，现在轮到你做开篇陈述（300-500字）。")
        for e in seeds], return_exceptions=True)
    for e, c in zip(seeds, seed_results):
        c = c if not isinstance(c, Exception) else f"[{e.name}] 发言中断: {str(c)[:50]}"
        all_speeches.append(_expert_entry(e, 1, "种子辩论", c[:SOLVAY_MAX_SPEECH_LEN]))
        memories[e.persona_id].add_speech("种子辩论", c)

    # 阶段2 阵营反应
    TASKS.set_progress(tid, "阵营反应", len(all_speeches), 12)
    others = [e for e in experts if e.name not in ("尼尔斯·玻尔", "阿尔伯特·爱因斯坦")]
    seed_text = "\n\n".join([f"【{s['expert_name']}】({s['expert_framework']}):\n{s['content']}" for s in all_speeches])
    reaction_results = await asyncio.gather(*[
        gen(e, f"议题: {topic['title']}\n前面的种子辩论:\n{seed_text}\n现在轮到你发言。") for e in others],
        return_exceptions=True)
    for e, c in zip(others, reaction_results):
        c = c if not isinstance(c, Exception) else f"[{e.name}] 发言中断: {str(c)[:50]}"
        all_speeches.append(_expert_entry(e, 2, "阵营反应", c[:SOLVAY_MAX_SPEECH_LEN]))
        memories[e.persona_id].add_speech("阵营反应", c)

    # 阶段3 自由交叉
    TASKS.set_progress(tid, "自由交叉", len(all_speeches), 24)
    free_results = await asyncio.gather(*[
        gen(e, f"议题: {topic['title']}\n当前会议已有的发言:\n{seed_text}\n现在轮到你做自由发言。") for e in experts],
        return_exceptions=True)
    for e, c in zip(experts, free_results):
        c = c if not isinstance(c, Exception) else f"[{e.name}] 发言中断: {str(c)[:50]}"
        all_speeches.append(_expert_entry(e, 3, "自由交叉", c[:SOLVAY_MAX_SPEECH_LEN]))
        targets = [o.name for o in experts if o.name != e.name and o.name in c]
        memories[e.persona_id].add_speech("自由交叉", c, targets)
        for o in experts:
            if o.name in targets:
                memories[o.persona_id].add_rebuttal(e.name, c[:100])

    # 阶段4 总结陈词
    TASKS.set_progress(tid, "总结陈词", len(all_speeches), 36)
    summary_results = await asyncio.gather(*[
        gen(e, f"议题: {topic['title']}\n现在请做你的总结陈词。") for e in experts],
        return_exceptions=True)
    for e, c in zip(experts, summary_results):
        c = c if not isinstance(c, Exception) else f"[{e.name}] 发言中断: {str(c)[:50]}"
        all_speeches.append(_expert_entry(e, 4, "总结陈词", c[:SOLVAY_SUMMARY_LEN]))
        memories[e.persona_id].add_speech("总结陈词", c)

    consensus = analyze_consensus(expert_dicts, all_speeches)
    result = {
        "topic": topic, "n_experts": len(experts), "n_phases": 4,
        "consensus_analysis": consensus,
        "expert_memories": {e.persona_id: memories[e.persona_id].to_dict() for e in experts},
        "debate_log": all_speeches,
        "summary": {
            "title": "第五次索尔维会议 — 自由辩论记录",
            "final_consensus": f"共识度: {consensus['consensus_score']*100:.0f}% — "
                               + ("高度共识" if consensus['consensus_score'] > 0.7
                                  else "部分共识" if consensus['consensus_score'] > 0.4 else "严重分歧"),
            "total_speeches": len(all_speeches),
        },
    }
    TASKS.update(tid, status="completed", completed_at=datetime.now().isoformat(), result=result)


# ───────────────────────── 模式 stream：无限 SSE 流式 ─────────────────────────

async def run_infinite_stream(tid: str, topic_key: str, backend_caller: Callable,
                              event_queue: asyncio.Queue):
    import json
    topic = get_topic(topic_key).to_dict()
    experts = SOLVAY_EXPERTS
    expert_dicts = [e.to_dict() for e in experts]
    memories = {e.persona_id: ExpertMemory(e.to_dict()) for e in experts}
    all_speeches: List[Dict[str, Any]] = []
    round_num = 0
    TASKS.update(tid, status="running", started_at=datetime.now().isoformat(),
                 consensus_history=[])
    limiter = ConcurrentLimiter(MAX_CONCURRENT)

    while True:
        round_num += 1
        task = TASKS.get(tid)
        if not task or task.get("stop_requested"):
            break
        await event_queue.put({"event": "round_start", "round": round_num,
                               "timestamp": datetime.now().isoformat()})

        async def speak(expert):
            recent = all_speeches[-STREAM_MAX_HISTORY:] if len(all_speeches) > STREAM_MAX_HISTORY else all_speeches
            history = "\n\n".join(
                [f"【{s['round']}轮·{s['expert_name']}】{s['content'][:150]}..." for s in recent]
            ) if recent else "（暂无发言）"
            user = (
                f"议题: {topic['title']}\n前面的辩论记录:\n{history}\n"
                f"现在是第{round_num}轮，轮到你发言。请给出你的回应或反击。记住：你是{expert.name}，在索尔维会议上。"
            )
            return await _call_expert(expert, user, backend_caller, limiter)

        speeches = await asyncio.gather(*[speak(e) for e in experts], return_exceptions=True)
        for e, c in zip(experts, speeches):
            c = c if not isinstance(c, Exception) else f"[{e.name}] 发言中断: {str(c)[:50]}"
            c = c[:800]
            entry = _expert_entry(e, round_num, f"第{round_num}轮", c)
            TASKS.append_log(tid, entry)
            all_speeches.append(entry)
            targets = [o.name for o in experts if o.name != e.name and o.name in c]
            memories[e.persona_id].add_speech(f"第{round_num}轮", c, targets)
            for o in experts:
                if o.name in targets:
                    memories[o.persona_id].add_rebuttal(e.name, c[:100])
            await event_queue.put(entry)

        consensus = analyze_consensus(expert_dicts, all_speeches)
        score = consensus.get("consensus_score", 0)
        await event_queue.put({"event": "consensus", "round": round_num,
                               "consensus_score": score, "camps": consensus.get("camps", {}),
                               "timestamp": datetime.now().isoformat()})

        history = list(TASKS.get(tid).get("consensus_history", []))
        history.append(score)
        TASKS.update(tid, consensus_history=history)
        if len(history) >= STREAM_CONSENSUS_ROUNDS and \
           all(s > STREAM_CONSENSUS_THRESHOLD for s in history[-STREAM_CONSENSUS_ROUNDS:]):
            await event_queue.put({"event": "auto_stop",
                                    "reason": f"连续{STREAM_CONSENSUS_ROUNDS}轮共识度超过"
                                              f"{STREAM_CONSENSUS_THRESHOLD*100:.0f}%，辩论自然收敛",
                                    "round": round_num, "timestamp": datetime.now().isoformat()})
            break
        await asyncio.sleep(1)

    TASKS.update(tid, status="completed", completed_at=datetime.now().isoformat())
    await event_queue.put({"event": "completed", "total_rounds": round_num,
                           "total_speeches": len(all_speeches), "timestamp": datetime.now().isoformat()})


# ───────────────────────── 启动包装（供 api_server 调用） ─────────────────────────

def start_solvay(topic_key: str, n_rounds: int, backend_caller: Callable) -> str:
    tid = TASKS.create("solvay_classic", topic_key, "nvidia",
                       extra={"n_rounds": n_rounds, "topic": get_topic(topic_key).to_dict()})
    def run():
        asyncio.run(run_solvay_conference(tid, topic_key, n_rounds, backend_caller))
    import threading
    threading.Thread(target=run, daemon=True).start()
    return tid


def start_free_debate(topic_key: str, backend_caller: Callable) -> str:
    tid = TASKS.create("solvay_free", topic_key, "nvidia",
                       extra={"topic": get_topic(topic_key).to_dict()})
    def run():
        asyncio.run(run_free_debate(tid, topic_key, backend_caller))
    import threading
    threading.Thread(target=run, daemon=True).start()
    return tid


def start_infinite_stream(topic_key: str, backend: str, backend_caller: Callable) -> str:
    tid = TASKS.create("solvay_stream", topic_key, backend,
                       extra={"topic": get_topic(topic_key).to_dict(), "consensus_history": []})
    return tid


async def sse_generator(tid: str, topic_key: str, backend_caller: Callable):
    import json
    event_queue = asyncio.Queue()
    asyncio.create_task(run_infinite_stream(tid, topic_key, backend_caller, event_queue))
    yield f"event: connected\ndata: {json.dumps({'task_id': tid, 'status': 'connected'}, ensure_ascii=False)}\n\n"
    try:
        while True:
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=30)
            except asyncio.TimeoutError:
                yield f"event: heartbeat\ndata: {json.dumps({'time': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
                continue
            data = json.dumps(event, ensure_ascii=False)
            yield f"event: {event.get('event', 'message')}\ndata: {data}\n\n"
            if event.get("event") in ("completed", "auto_stop"):
                break
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    finally:
        task = TASKS.get(tid)
        if task and task.get("status") == "pending":
            TASKS.update(tid, status="completed", completed_at=datetime.now().isoformat())
