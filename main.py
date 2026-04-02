"""
积分系统 Backend — FastAPI
API v1: /api/v1/points
"""

import os
from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal

from database import (
    init_db,
    insert_record,
    get_weekly_leaderboard,
    get_records,
    get_history,
    reset_weekly,
    get_current_week_num,
)

# -------------------------------------------------------------------
# App 初始化
# -------------------------------------------------------------------

app = FastAPI(title="积分系统 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时初始化数据库
init_db()

# -------------------------------------------------------------------
# 工具
# -------------------------------------------------------------------

ALLOWED_BRANCHES = {"dev", "main"}

def check_branch(x_agent_branch: Optional[str] = Header(None)) -> str:
    """校验分支权限，返回分支名"""
    if x_agent_branch is None:
        raise HTTPException(status_code=403, detail="Missing X-Agent-Branch header")
    if x_agent_branch not in ALLOWED_BRANCHES:
        raise HTTPException(status_code=403, detail=f"Branch '{x_agent_branch}' not allowed")
    return x_agent_branch

def ok(data):
    return {"code": 0, "message": "ok", "data": data}

# -------------------------------------------------------------------
# 请求模型
# -------------------------------------------------------------------

class RecordCreate(BaseModel):
    proposer: str
    target: str
    reason: str
    points: int = Field(..., description="分值档位：-5/-3/-1/1/3/5")
    created_by: str

# -------------------------------------------------------------------
# API 路由
# -------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}

# 3.1 录入积分 — dev 分支
@app.post("/api/v1/points/record")
def create_record(body: RecordCreate, branch: str = Header(..., alias="X-Agent-Branch")):
    check_branch(branch)

    if body.points not in (-5, -3, -1, 1, 3, 5):
        raise HTTPException(status_code=400, detail="points must be one of -5/-3/-1/1/3/5")

    record_id = insert_record(
        proposer=body.proposer,
        target=body.target,
        reason=body.reason,
        points=body.points,
        created_by=body.created_by,
    )

    return ok({"id": record_id, "week_num": get_current_week_num()})

# 3.2 查询当周看板 — 全员
@app.get("/api/v1/points/weekly")
def weekly_leaderboard(week: Optional[str] = Query(None)):
    return ok(get_weekly_leaderboard(week))

# 3.3 查询积分明细 — 全员
@app.get("/api/v1/points/records")
def list_records(
    target: Optional[str] = Query(None),
    week: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return ok(get_records(target=target, week=week, page=page, page_size=page_size))

# 3.4 查询历史归档 — 全员
@app.get("/api/v1/points/history")
def list_history(week: Optional[str] = Query(None)):
    return ok(get_history(week))

# 3.5 清零+归档 — main 分支（内部）
@app.post("/api/v1/points/reset")
def reset_points(branch: str = Header(..., alias="X-Agent-Branch")):
    if branch != "main":
        raise HTTPException(status_code=403, detail="Only main branch can trigger reset")
    result = reset_weekly()
    return ok(result)

# -------------------------------------------------------------------
# 启动
# -------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
