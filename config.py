#!/usr/bin/env python3
"""CAGI 全局配置 — 环境变量、常量、路径"""

import os

# 密钥仅从环境变量读取，不加载本地文件
# 密钥仅从环境变量读取，不加载本地文件
# 密钥仅从环境变量读取，不加载本地文件
# 密钥仅从环境变量读取，不加载本地文件
# 密钥仅从环境变量读取，不加载本地文件
# 密钥仅从环境变量读取，不加载本地文件
# ─── 后端密钥 ───
DEEPSEEK_API_KEY   = os.environ.get("DEEPSEEK_API_KEY", "")
GLM_API_KEY        = os.environ.get("GLM_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
NVIDIA_API_KEY     = os.environ.get("NVIDIA_API_KEY", "")
SILICONFLOW_API_KEY= os.environ.get("SILICONFLOW_API_KEY", "")
MODELSCOPE_API_KEY = os.environ.get("MODELSCOPE_API_KEY", "")
OLLAMA_HOST        = os.environ.get("OLLAMA_HOST", "http://[::1]:11434")  # 本机 ollama 在 IPv6；IPv4 11434 被占返回空，勿用 localhost
OLLAMA_MODEL       = os.environ.get("OLLAMA_MODEL", "qwen3-8b-chat")  # 本机已装；原默认 qwen2.5:7b 不存在
CUSTOM_API_URL     = os.environ.get("CUSTOM_API_URL", "")
CUSTOM_API_KEY     = os.environ.get("CUSTOM_API_KEY", "")
CUSTOM_MODEL       = os.environ.get("CUSTOM_MODEL", "")

# ─── API 鉴权 ───
# 写操作端点（/discuss、/solvay/*/start 等，会消耗 LLM 额度）要求 X-API-Key。
# 为空 = 不启用鉴权（仅限本机/内网调试用）。
CAGI_API_TOKEN = os.environ.get("CAGI_API_TOKEN", "")

# ─── 默认后端 ───
DEFAULT_BACKEND = os.environ.get("CAGI_BACKEND", "mock").lower()

# ─── CAGI 核心参数 ───
N_INSTANCES         = 150
N_DISCUSSION_ROUNDS = 10
TEMPERATURE         = 0.7
MAX_CONCURRENT      = 5
POOL_MAX_VIEW       = 50

# ─── Solvay 参数 ───
SOLVAY_MAX_ROUNDS   = 5
SOLVAY_MAX_SPEECH_LEN = 800
SOLVAY_SUMMARY_LEN    = 600

# ─── 流式参数 ───
STREAM_MAX_HISTORY  = 15
STREAM_CONSENSUS_THRESHOLD = 0.9
STREAM_CONSENSUS_ROUNDS    = 3
