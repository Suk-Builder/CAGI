#!/usr/bin/env python3
"""CAGI 服务入口"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=7788, reload=False)
