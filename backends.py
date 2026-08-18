#!/usr/bin/env python3
"""CAGI 后端适配器 — 统一接口，每个后端独立封装

所有适配器共享同一签名:
    async def call_XXX(system_prompt: str, user_prompt: str) -> str

注册表: BACKENDS = {"name": call_fn, ...}
"""

import os
import json
import aiohttp
from typing import Dict, Callable, Optional

from config import (
    DEEPSEEK_API_KEY, GLM_API_KEY, OPENROUTER_API_KEY,
    NVIDIA_API_KEY, SILICONFLOW_API_KEY, MODELSCOPE_API_KEY,
    OLLAMA_HOST, OLLAMA_MODEL, CUSTOM_API_URL, CUSTOM_API_KEY, CUSTOM_MODEL,
    TEMPERATURE,
)

# ─── 统一超时 ───
_TIMEOUT = aiohttp.ClientTimeout(total=120)


async def call_mock(system_prompt: str, user_prompt: str) -> str:
    """Mock 模式 — 本地模拟专家回答"""
    import random
    domain = "通用"
    if "专长" in user_prompt:
        try:
            domain = user_prompt.split("你的专长:")[1].split(",")[0].strip()
        except Exception:
            pass
    question = user_prompt.split("题目:")[1].split("\n")[0].strip() if "题目:" in user_prompt else ""
    known = {"法国的首都": "巴黎", "2+2": "4", "中国首都": "北京", "1+1": "2"}
    answer = None
    for k, v in known.items():
        if k in question:
            answer = v
            break
    if answer and random.random() < 0.6:
        return f"从 {domain} 看: {answer}"
    fake = random.choice(["错误答案1", "错误答案2", "不确定"])
    return f"从 {domain} 看: {fake}"


async def call_deepseek(system_prompt: str, user_prompt: str) -> str:
    key = DEEPSEEK_API_KEY
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": 10000,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        async with session.post("https://api.deepseek.com/v1/chat/completions",
                                json=payload, headers=headers) as resp:
            data = await resp.json()
            if "error" in data:
                raise RuntimeError(f"DeepSeek error: {data['error']}")
            return data["choices"][0]["message"]["content"].strip()


async def call_glm(system_prompt: str, user_prompt: str) -> str:
    key = GLM_API_KEY
    if not key:
        raise RuntimeError("GLM_API_KEY not set")
    payload = {
        "model": "glm-4-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": 10000,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        async with session.post("https://open.bigmodel.cn/api/paas/v4/chat/completions",
                                json=payload, headers=headers) as resp:
            data = await resp.json()
            if "error" in data:
                raise RuntimeError(f"GLM error: {data['error']}")
            msg = data.get("choices", [{}])[0].get("message", {})
            content = msg.get("content", "")
            if not content and msg.get("reasoning_content"):
                reasoning = msg.get("reasoning_content", "")
                lines = [l.strip() for l in reasoning.split("\n") if l.strip()]
                content = lines[-1] if lines else reasoning
            return content.strip()


async def call_openrouter(system_prompt: str, user_prompt: str) -> str:
    key = OPENROUTER_API_KEY
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    payload = {
        "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": 10000,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://cagi.example.com",
        "X-Title": "CAGI",
    }
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        async with session.post("https://openrouter.ai/api/v1/chat/completions",
                                json=payload, headers=headers) as resp:
            data = await resp.json()
            if "error" in data:
                raise RuntimeError(f"OpenRouter error: {data['error']}")
            return data["choices"][0]["message"]["content"].strip()


async def call_nvidia(system_prompt: str, user_prompt: str) -> str:
    key = NVIDIA_API_KEY
    if not key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    payload = {
        "model": "nvidia/nemotron-3-ultra-550b-a55b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": 10000,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        async with session.post("https://integrate.api.nvidia.com/v1/chat/completions",
                                json=payload, headers=headers) as resp:
            data = await resp.json()
            if "error" in data:
                raise RuntimeError(f"NVIDIA error: {data['error']}")
            return data["choices"][0]["message"]["content"].strip()


async def call_siliconflow(system_prompt: str, user_prompt: str) -> str:
    key = SILICONFLOW_API_KEY
    if not key:
        raise RuntimeError("SILICONFLOW_API_KEY not set")
    # 2026年8月: DeepSeek-V2.5 已下架，换用 Qwen2.5-72B-Instruct
    payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": 10000,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        async with session.post("https://api.siliconflow.cn/v1/chat/completions",
                                json=payload, headers=headers) as resp:
            data = await resp.json()
            if "error" in data:
                raise RuntimeError(f"SiliconFlow error: {data['error']}")
            return data["choices"][0]["message"]["content"].strip()


async def call_modelscope(system_prompt: str, user_prompt: str) -> str:
    key = MODELSCOPE_API_KEY
    if not key:
        raise RuntimeError("MODELSCOPE_API_KEY not set")
    payload = {
        "model": "deepseek-ai/DeepSeek-V4-Pro",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": 5000,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        async with session.post("https://api-inference.modelscope.cn/v1/chat/completions",
                                json=payload, headers=headers) as resp:
            data = await resp.json()
            if "error" in data:
                raise RuntimeError(f"ModelScope error: {data['error']}")
            # ModelScope 返回格式可能是 delta 或 message
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})
            content = msg.get("content", "")
            if not content:
                # 尝试 delta 格式
                delta = choice.get("delta", {})
                content = delta.get("content", "")
            if not content and msg.get("reasoning_content"):
                reasoning = msg.get("reasoning_content", "")
                lines = [l.strip() for l in reasoning.split("\n") if l.strip()]
                content = lines[-1] if lines else reasoning
            if not content:
                raise RuntimeError(f"ModelScope empty response: {json.dumps(data)[:200]}")
            return content.strip()


async def call_ollama(system_prompt: str, user_prompt: str) -> str:
    host = OLLAMA_HOST
    model = OLLAMA_MODEL
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": TEMPERATURE},
    }
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        async with session.post(f"{host}/api/chat", json=payload) as resp:
            data = await resp.json()
            # 修复：ollama 出错时返回 {"error": ...} 而非 message，原版静默给空串
            if "error" in data:
                raise RuntimeError(f"Ollama error ({model}): {data['error']}")
            content = data.get("message", {}).get("content", "")
            if not content:
                raise RuntimeError(f"Ollama empty content ({model}); raw={json.dumps(data, ensure_ascii=False)[:160]}")
            return content.strip()


async def call_custom(system_prompt: str, user_prompt: str) -> str:
    if not CUSTOM_API_URL or not CUSTOM_API_KEY or not CUSTOM_MODEL:
        raise RuntimeError("CUSTOM backend not configured")
    payload = {
        "model": CUSTOM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": 10000,
    }
    headers = {"Authorization": f"Bearer {CUSTOM_API_KEY}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        async with session.post(CUSTOM_API_URL, json=payload, headers=headers) as resp:
            data = await resp.json()
            if "error" in data:
                raise RuntimeError(f"Custom error: {data['error']}")
            return data["choices"][0]["message"]["content"].strip()


# ─── 注册表 ───

BACKENDS: Dict[str, Callable] = {
    "mock":        call_mock,
    "deepseek":    call_deepseek,
    "glm":         call_glm,
    "openrouter":  call_openrouter,
    "nvidia":      call_nvidia,
    "siliconflow": call_siliconflow,
    "modelscope":  call_modelscope,
    "ollama":      call_ollama,
    "custom":      call_custom,
}


def get_backend(name: Optional[str] = None) -> Callable:
    """获取后端调用函数，支持 fallback"""
    from config import DEFAULT_BACKEND
    name = (name or DEFAULT_BACKEND).lower()
    if name not in BACKENDS:
        raise ValueError(f"Unknown backend: {name}. Available: {list(BACKENDS.keys())}")
    return BACKENDS[name]


def list_backends() -> Dict[str, bool]:
    """列出所有后端及其就绪状态（有密钥即就绪）"""
    keys = {
        "mock": True,
        "deepseek":    bool(DEEPSEEK_API_KEY),
        "glm":         bool(GLM_API_KEY),
        "openrouter":  bool(OPENROUTER_API_KEY),
        "nvidia":      bool(NVIDIA_API_KEY),
        "siliconflow": bool(SILICONFLOW_API_KEY),
        "modelscope":  bool(MODELSCOPE_API_KEY),
        "ollama":      True,
        "custom":      bool(CUSTOM_API_URL and CUSTOM_API_KEY and CUSTOM_MODEL),
    }
    return keys


async def call_with_fallback(system_prompt: str, user_prompt: str,
                              backend_caller: Callable) -> str:
    """调用后端，带重试和降级链: 主调用 → 重试 → nvidia → modelscope → openrouter → glm → mock"""
    # 1. 主调用
    try:
        return await backend_caller(system_prompt, user_prompt)
    except Exception as e:
        print(f"[Fallback] Primary failed: {e}")

    # 2. 重试
    try:
        return await backend_caller(system_prompt, user_prompt)
    except Exception as e:
        print(f"[Fallback] Retry failed: {e}")

    # 3. 降级 nvidia
    for name, caller in [("nvidia", BACKENDS.get("nvidia")),
                          ("modelscope", BACKENDS.get("modelscope")),
                          ("openrouter", BACKENDS.get("openrouter")),
                          ("glm", BACKENDS.get("glm"))]:
        try:
            if caller:
                print(f"[Fallback] → {name}")
                return await caller(system_prompt, user_prompt)
        except Exception as e:
            print(f"[Fallback] {name} failed: {e}")

    # 4. 降级 mock
    try:
        mock = BACKENDS.get("mock")
        if mock:
            print("[Fallback] → mock")
            return await mock(system_prompt, user_prompt)
    except Exception as e:
        print(f"[Fallback] mock failed: {e}")

    raise RuntimeError("All backends failed")
