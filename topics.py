#!/usr/bin/env python3
"""CAGI 索尔维会议议题库"""

from typing import List, Dict, Any
from models import Topic

SOLVAY_TOPICS = {
    "wave_function_reality": Topic(
        key="wave_function_reality", title="波函数是否描述了物理实在？",
        title_en="Does the wave function describe physical reality?",
        description="波函数ψ是量子力学的核心数学对象。它描述的是一种真实的物理波动，还是仅仅是我们对系统知识的一种编码？",
        tags=["本体论","实在论","波函数"]),
    "completeness": Topic(
        key="completeness", title="量子力学的数学基础是否完备？",
        title_en="Is the mathematical foundation of quantum mechanics complete?",
        description="量子力学能否被进一步公理化？是否存在隐变量可以补全现有理论？",
        tags=["完备性","公理化","隐变量"]),
    "measurement_problem": Topic(
        key="measurement_problem", title="测量问题：波函数坍缩是物理过程还是知识更新？",
        title_en="The Measurement Problem: Physical process or knowledge update?",
        description="测量时波函数从叠加态到本征态的转变，是真实的物理坍缩，还是观察者信息的更新？",
        tags=["测量问题","坍缩","观察者"]),
    "epr_paradox": Topic(
        key="epr_paradox", title="EPR佯谬：量子力学是否允许定域实在论？",
        title_en="EPR Paradox: Does quantum mechanics allow local realism?",
        description="爱因斯坦-波多尔斯基-罗森佯谬质疑量子力学的完备性。量子纠缠是否意味着非定域性？",
        tags=["EPR","纠缠","定域性"]),
    "determinism": Topic(
        key="determinism", title="量子力学是否从根本上排除了决定论？",
        title_en="Does quantum mechanics fundamentally exclude determinism?",
        description="如果量子力学本质上是概率性的，那么决定论在基础物理层面是否已被证伪？",
        tags=["决定论","概率","因果律"]),
}

def get_topic(key: str) -> Topic:
    if key not in SOLVAY_TOPICS:
        raise ValueError(f"Unknown topic: {key}. Available: {list(SOLVAY_TOPICS.keys())}")
    return SOLVAY_TOPICS[key]

def get_topic_dicts() -> List[Dict[str, Any]]:
    return [t.to_dict() for t in SOLVAY_TOPICS.values()]
