"""
积分系统 Backend — FastAPI
API v1: /api/v1/points
"""

import os
import threading
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
    insert_guoxue_metric,
    get_guoxue_metrics,
)

try:
    from git_sync import ensure_git_initialized, git_pull, git_push
    _GIT_SYNC = True
except ImportError:
    _GIT_SYNC = False

# -------------------------------------------------------------------
# App 初始化
# -------------------------------------------------------------------

app = FastAPI(title="积分系统 API", version="1.0.0")

@app.on_event("startup")
def startup_event():
    if _GIT_SYNC:
        ensure_git_initialized()

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

ALLOWED_BRANCHES = {"dev", "fin", "guo", "main", "des_ui", "backend", "frontend", "doc", "test", "eng", "req"}

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
    points: int = Field(..., description="分值档位：-10/-5/-3/-1/1/3/5/10/20/50/60")
    created_by: str

class GuoxueMetricCreate(BaseModel):
    metric_type: Literal["inspection", "ci_build", "content_output"]
    meta: dict
    week: Optional[str] = Field(None, description="YYYY-Www，不传则自动用当前周")

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

    if body.points not in (-10, -5, -3, -1, 1, 3, 5, 10, 20, 50, 60):
        raise HTTPException(status_code=400, detail="points must be one of -10/-5/-3/-1/1/3/5/10/20/50/60")

    record_id = insert_record(
        proposer=body.proposer,
        target=body.target,
        reason=body.reason,
        points=body.points,
        created_by=body.created_by,
    )
    if _GIT_SYNC:
        threading.Thread(target=git_push, daemon=True).start()

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
    if _GIT_SYNC:
        threading.Thread(target=git_push, daemon=True).start()
    return ok(result)

# -------------------------------------------------------------------
# 国学平台运行数据 API（供 fin/guo 录入）
# -------------------------------------------------------------------

@app.post("/api/v1/guoxue/metrics")
def create_guoxue_metric(
    body: GuoxueMetricCreate,
    branch: str = Header(..., alias="X-Agent-Branch"),
):
    """写入国学平台运行数据（inspection/ci_build/content_output）"""
    check_branch(branch)

    record_id = insert_guoxue_metric(
        metric_type=body.metric_type,
        meta=body.meta,
        week=body.week,
    )
    if _GIT_SYNC:
        threading.Thread(target=git_push, daemon=True).start()
    return ok({"id": record_id, "week_num": body.week or get_current_week_num()})

@app.get("/api/v1/guoxue/metrics")
def list_guoxue_metrics(
    metric_type: Optional[str] = Query(None, description="inspection/ci_build/content_output"),
    week: Optional[str] = Query(None, description="YYYY-Www"),
):
    """查询国学平台运行数据"""
    rows = get_guoxue_metrics(metric_type=metric_type, week=week)
    return ok(rows)

# -------------------------------------------------------------------
# 启动
# -------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
