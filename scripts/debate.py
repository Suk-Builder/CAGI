#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entities-150 v2.0 裂缝辩论赛客户端"""
import sys
import json
import requests
import argparse
from datetime import datetime

BASE_URL = "http://127.0.0.1:3009"

def call_entity(entity_id, question, context_history=None):
    payload = {"entityId": entity_id, "customQuestion": question}
    if context_history:
        context_str = "\n\n【之前的辩论记录】\n"
        for entry in context_history:
            context_str += f"\n[{entry['name']}]: {entry['content'][:500]}"
        payload["customQuestion"] = question + context_str + "\n\n请基于以上发言，点名回应你认为最有问题的观点，或提出你的反驳/补充。"

    try:
        r = requests.post(f"{BASE_URL}/api/dialogue", headers={"Content-Type": "application/json"},
                          json=payload, timeout=120)
        data = r.json()
        if data.get("success"):
            return {
                "id": entity_id,
                "name": data["data"]["entity"]["nameCn"],
                "bdi": data["data"]["entity"].get("bdiAi", "?"),
                "content": data["data"]["content"],
                "timestamp": datetime.now().isoformat()
            }
        return {"id": entity_id, "name": entity_id, "bdi": "?", "content": f"[错误: {data.get('message', 'unknown')}]", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"id": entity_id, "name": entity_id, "bdi": "?", "content": f"[异常: {str(e)}]", "timestamp": datetime.now().isoformat()}

def run_debate(topic, entities, rounds=3):
    print(f"\n{'='*70}\n  Entities-150 裂缝辩论赛\n  主题: {topic}\n  参与实体: {', '.join(entities)}\n  轮数: {rounds}\n{'='*70}")

    history = []
    for round_num in range(1, rounds + 1):
        print(f"\n{'─'*70}\n  第 {round_num} 轮\n{'─'*70}")
        for entity_id in entities:
            context = history if round_num > 1 else None
            print(f"\n  >>> [{entity_id}] 正在发言...", end=" ", flush=True)
            result = call_entity(entity_id, topic, context)
            print(f"完成 (BDI={result['bdi']})")
            history.append(result)
            print(f"\n  [{result['name']}] (BDI={result['bdi']})")
            print(f"  {'─'*50}")
            for line in result['content'].split('\n'):
                if line.strip():
                    print(f"  {line.strip()}")
            print()

    output = {"topic": topic, "entities": entities, "rounds": rounds, "history": history, "timestamp": datetime.now().isoformat()}
    filename = f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  辩论记录已保存: {filename}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Entities-150 裂缝辩论赛')
    parser.add_argument('topic', help='辩论主题')
    parser.add_argument('--entities', '-e', help='参与实体，逗号分隔')
    parser.add_argument('--rounds', '-r', type=int, default=3, help='辩论轮数')
    args = parser.parse_args()

    entities = [e.strip() for e in args.entities.split(',')] if args.entities else ['zero', 'paradox', 'contradiction']
    run_debate(args.topic, entities, args.rounds)
