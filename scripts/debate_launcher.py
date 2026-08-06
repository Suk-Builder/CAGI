#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entities-150 v2.0 辩论启动器"""
import requests
import json
import random

BASE_URL = "http://127.0.0.1:3009"

def get_entities():
    r = requests.get(f"{BASE_URL}/api/entities/list", timeout=10)
    return r.json()["data"]["entities"]

def classify_entities(entities):
    abstract_keywords = ['paradox', 'contradiction', 'zero', 'boundary', 'observer', 'emergence',
                         'chaos', 'infinity', 'void', 'light_entity', 'darkness', 'time_entity']
    abstract, real_people = [], []
    for e in entities:
        if any(kw in e['id'].lower() for kw in abstract_keywords):
            abstract.append(e)
        else:
            real_people.append(e)
    return abstract, real_people

def main():
    print("=" * 70)
    print("  Entities-150 v2.0 裂缝辩论赛 - 自动启动器")
    print("=" * 70)

    print("\n[1/3] 获取实体列表...")
    entities = get_entities()
    print(f"  共 {len(entities)} 个实体")

    print("\n[2/3] 分类实体...")
    abstract, real_people = classify_entities(entities)
    print(f"  抽象实体: {len(abstract)} 个")
    print(f"  真人实体: {len(real_people)} 个")

    print("\n[3/3] 选择辩论参与者...")
    selected_abstract = random.sample(abstract, min(1, len(abstract))) if abstract else []
    selected_real = random.sample(real_people, min(9, len(real_people))) if real_people else []
    selected = [e['id'] for e in selected_abstract] + [e['id'] for e in selected_real]

    for i, eid in enumerate(selected, 1):
        entity = next(e for e in entities if e['id'] == eid)
        etype = "【抽象】" if eid in [a['id'] for a in abstract] else "【真人】"
        print(f"    {i}. {entity['nameCn']} {etype} BDI={entity.get('bdiAi', '?')}")

    print("\n[4/4] 发起10轮自由辩论...")
    payload = {
        "name": f"自由辩论_{json.dumps(selected, ensure_ascii=False)}",
        "topic": "自由辩论",
        "entities": selected,
        "rounds": 10,
        "mode": "free"
    }
    r = requests.post(f"{BASE_URL}/api/debate", headers={"Content-Type": "application/json"},
                      json=payload, timeout=600)
    result = r.json()
    if result.get('success'):
        print(f"\n✓ 辩论已启动! ID: {result['data']['debateId']}")
    else:
        print(f"\n✗ 启动失败: {result.get('message')}")

if __name__ == '__main__':
    main()
