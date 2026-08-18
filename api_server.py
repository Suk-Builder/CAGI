#!/usr/env python3
"""CAGI API Server v5 — 统一引擎版

架构: config -> models -> backends -> experts -> topics -> tasks -> core -> engine -> api
依赖解析顺序保证无循环 import；不再硬编码 Linux 路径。
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from config import DEFAULT_BACKEND, CAGI_API_TOKEN
from schemas import (
    DiscussRequest, DiscussResponse, HealthResponse,
    SolvayStartRequest, SolvayStartResponse,
    SolvayStatusResponse, SolvayResultResponse,
    SolvayFreeStartRequest, SolvayFreeStartResponse,
    StreamStartRequest, StreamStartResponse,
)
from backends import get_backend, list_backends
from experts import SOLVAY_EXPERTS, get_expert_dicts
from topics import SOLVAY_TOPICS, get_topic_dicts
from tasks import TASKS
from engine import (
    run_cagi_discussion,
    start_solvay, start_free_debate, start_infinite_stream, sse_generator,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[CAGI] Server starting. Default backend: {DEFAULT_BACKEND}")
    yield
    print("[CAGI] Server shutting down.")


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """写操作端点鉴权：消耗 LLM 额度的端点要求 X-API-Key 匹配。
    未配置 CAGI_API_TOKEN 时放行（本机/内网调试用）。"""
    if CAGI_API_TOKEN and x_api_key != CAGI_API_TOKEN:
        raise HTTPException(status_code=401, detail="invalid or missing API key")


app = FastAPI(title="CAGI API v5",
              description="统一引擎: vote(问答投票) / debate(圆桌) / free(四阶段) / stream(SSE)",
              version="5.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/health", response_model=HealthResponse)
async def health():
    backends = list_backends()
    return HealthResponse(status="ok", version="5.0.0", backend=DEFAULT_BACKEND,
        backend_ready=backends.get(DEFAULT_BACKEND, False),
        n_personas=len(SOLVAY_EXPERTS), backend_status=backends)


@app.get("/personas")
async def list_personas():
    return {"count": len(SOLVAY_EXPERTS), "personas": [
        {"id": e.persona_id, "name": e.name, "domain": e.domain,
         "framework": e.cognitive_framework, "avatar": e.avatar_emoji} for e in SOLVAY_EXPERTS]}


@app.post("/discuss", response_model=DiscussResponse, dependencies=[Depends(require_api_key)])
async def discuss(req: DiscussRequest):
    backend_name = req.backend or DEFAULT_BACKEND
    try:
        backend_caller = get_backend(backend_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    result = await run_cagi_discussion(
        question=req.question, ground_truth=req.ground_truth,
        n_instances=req.n_instances, n_rounds=req.n_rounds, backend_caller=backend_caller)
    result["backend"] = backend_name
    return DiscussResponse(**result)


@app.get("/solvay/topics")
async def solvay_topics():
    return {"topics": get_topic_dicts()}


@app.get("/solvay/experts")
async def solvay_experts():
    return {"count": len(SOLVAY_EXPERTS), "experts": get_expert_dicts()}


@app.post("/solvay/start", response_model=SolvayStartResponse, dependencies=[Depends(require_api_key)])
async def solvay_start(req: SolvayStartRequest):
    if req.topic_key not in SOLVAY_TOPICS:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {req.topic_key}")
    backend_name = req.backend or DEFAULT_BACKEND
    backend_caller = get_backend(backend_name)
    tid = start_solvay(req.topic_key, req.n_rounds, backend_caller)
    task = TASKS.get(tid)
    return SolvayStartResponse(task_id=tid, status="started", topic=task["topic"],
        n_rounds=req.n_rounds,
        message=f"索尔维会议已启动，{len(SOLVAY_EXPERTS)}位专家将围绕「{task['topic']['title']}」进行 {req.n_rounds} 轮辩论。")


@app.get("/solvay/status/{task_id}", response_model=SolvayStatusResponse)
async def solvay_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return SolvayStatusResponse(task_id=task_id, status=task["status"],
        progress=task.get("progress", {}),
        current_round=task.get("progress", {}).get("completed", 0),
        n_speeches=len(task.get("debate_log", [])), topic=task.get("topic", {}))


@app.get("/solvay/result/{task_id}", response_model=SolvayResultResponse)
async def solvay_result(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return SolvayResultResponse(task_id=task_id, status=task["status"],
        result=task.get("result"), debate_log=task.get("debate_log", []),
        n_speeches=len(task.get("debate_log", [])))


@app.get("/solvay/tasks")
async def solvay_tasks():
    return {"tasks": TASKS.list_tasks("solvay_classic")}


@app.post("/solvay/free/start", response_model=SolvayFreeStartResponse, dependencies=[Depends(require_api_key)])
async def solvay_free_start(req: SolvayFreeStartRequest):
    if req.topic_key not in SOLVAY_TOPICS:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {req.topic_key}")
    backend_name = req.backend or DEFAULT_BACKEND
    backend_caller = get_backend(backend_name)
    tid = start_free_debate(req.topic_key, backend_caller)
    task = TASKS.get(tid)
    return SolvayFreeStartResponse(task_id=tid, status="started", topic=task["topic"],
        message=f"自由辩论已启动！议题:「{task['topic']['title']}」。种子->反应->交叉->总结 四阶段。")


@app.get("/solvay/free/status/{task_id}")
async def solvay_free_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": task["status"], "progress": task.get("progress", {}),
            "n_speeches": len(task.get("debate_log", [])), "topic": task.get("topic", {})}


@app.get("/solvay/free/result/{task_id}")
async def solvay_free_result(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": task["status"], "result": task.get("result"),
            "debate_log": task.get("debate_log", [])}


@app.get("/solvay/free/tasks")
async def solvay_free_tasks():
    return {"tasks": TASKS.list_tasks("solvay_free")}


@app.post("/solvay/stream/start", response_model=StreamStartResponse, dependencies=[Depends(require_api_key)])
async def solvay_stream_start(req: StreamStartRequest):
    if req.topic_key not in SOLVAY_TOPICS:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {req.topic_key}")
    backend_name = req.backend or DEFAULT_BACKEND
    backend_caller = get_backend(backend_name)
    tid = start_infinite_stream(req.topic_key, backend_name, backend_caller)
    return StreamStartResponse(task_id=tid, status="started",
        stream_url=f"/solvay/stream/{tid}",
        message=f"无限流式辩论已启动！议题:「{SOLVAY_TOPICS[req.topic_key].title}」\n连接 SSE: /solvay/stream/{tid}")


@app.get("/solvay/stream/{task_id}")
async def solvay_stream(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    backend_caller = get_backend(task.get("backend", DEFAULT_BACKEND))
    return StreamingResponse(sse_generator(task_id, task["topic_key"], backend_caller),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


@app.post("/solvay/stream/{task_id}/stop", dependencies=[Depends(require_api_key)])
async def solvay_stream_stop(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    TASKS.update(task_id, stop_requested=True)
    return {"task_id": task_id, "status": "stop_requested"}


@app.get("/solvay/stream/{task_id}/result")
async def solvay_stream_result(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": task["status"],
            "n_speeches": len(task.get("debate_log", [])), "debate_log": task.get("debate_log", [])}


@app.get("/")
async def root():
    return {"name": "CAGI API v5 (Unified Engine)", "version": "5.0.0", "routes": {
        "GET /health": "健康检查", "GET /personas": "专家列表", "POST /discuss": "CAGI 问答投票",
        "GET /solvay/topics": "议题列表", "GET /solvay/experts": "专家列表",
        "POST /solvay/start": "经典辩论", "GET /solvay/status/{id}": "经典辩论状态",
        "GET /solvay/result/{id}": "经典辩论结果",
        "POST /solvay/free/start": "自由辩论", "GET /solvay/free/status/{id}": "自由辩论状态",
        "POST /solvay/stream/start": "SSE 流式辩论", "GET /solvay/stream/{id}": "SSE 连接",
        "POST /solvay/stream/{id}/stop": "停止流式辩论",
    }}
