"""
积分系统数据库层
SQLite + 四个表：records / weekly_current / weekly_history / guoxue_metrics
"""

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).parent / "points.db"))

# -------------------------------------------------------------------
# 连接管理
# -------------------------------------------------------------------

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

# -------------------------------------------------------------------
# Schema 初始化
# -------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    proposer    TEXT    NOT NULL,
    target      TEXT    NOT NULL,
    reason      TEXT    NOT NULL,
    points      INTEGER NOT NULL,
    week_num    TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    created_by  TEXT    NOT NULL,
    CHECK (points IN (-5,-3,-1,1,3,5))
);

CREATE INDEX IF NOT EXISTS idx_records_week_num  ON records(week_num);
CREATE INDEX IF NOT EXISTS idx_records_target   ON records(target);
CREATE INDEX IF NOT EXISTS idx_records_proposer ON records(proposer);

CREATE TABLE IF NOT EXISTS weekly_current (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    target       TEXT    NOT NULL UNIQUE,
    total_points INTEGER NOT NULL DEFAULT 0,
    week_num     TEXT    NOT NULL,
    updated_at   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_weekly_current_target ON weekly_current(target);

CREATE TABLE IF NOT EXISTS weekly_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    target          TEXT    NOT NULL,
    total_points    INTEGER NOT NULL,
    week_num        TEXT    NOT NULL,
    archived_at     TEXT    NOT NULL,
    archived_by     TEXT    NOT NULL,
    UNIQUE(target, week_num)
);

CREATE INDEX IF NOT EXISTS idx_weekly_history_week   ON weekly_history(week_num);
CREATE INDEX IF NOT EXISTS idx_weekly_history_target ON weekly_history(target);

CREATE TABLE IF NOT EXISTS guoxue_metrics (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type       TEXT NOT NULL,
    week_num          TEXT NOT NULL,
    recorded_at       TEXT NOT NULL,
    meta              TEXT,
    CHECK (metric_type IN ('inspection','ci_build','content_output'))
);

CREATE INDEX IF NOT EXISTS idx_guoxue_metrics_type_week ON guoxue_metrics(metric_type, week_num);
"""

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)

# -------------------------------------------------------------------
# 业务操作
# -------------------------------------------------------------------

def get_current_week_num() -> str:
    """返回当前 ISO 周标识 YYYY-Www"""
    import datetime
    today = datetime.date.today()
    week_num = today.isocalendar()[1]
    return f"{today.year}-W{week_num:02d}"

def insert_record(proposer: str, target: str, reason: str, points: int,
                  created_by: str) -> int:
    """写入 records 表并同步 weekly_current"""
    import datetime
    week_num = get_current_week_num()
    now = datetime.datetime.utcnow().isoformat() + "+00:00"

    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO records (proposer,target,reason,points,week_num,created_at,created_by)
               VALUES (?,?,?,?,?,?,?)""",
            (proposer, target, reason, points, week_num, now, created_by)
        )
        record_id = cur.lastrowid

        # 同步更新 weekly_current
        existing = conn.execute(
            "SELECT total_points FROM weekly_current WHERE target=? AND week_num=?",
            (target, week_num)
        ).fetchone()

        if existing:
            new_total = existing["total_points"] + points
            conn.execute(
                "UPDATE weekly_current SET total_points=?, updated_at=? WHERE target=? AND week_num=?",
                (new_total, now, target, week_num)
            )
        else:
            conn.execute(
                "INSERT INTO weekly_current (target,total_points,week_num,updated_at) VALUES (?,?,?,?)",
                (target, points, week_num, now)
            )

        return record_id

def get_weekly_leaderboard(week: str = None) -> dict:
    """返回指定周或当前周的 leaderboard"""
    if week is None:
        week = get_current_week_num()

    with get_conn() as conn:
        rows = conn.execute(
            """SELECT target, total_points FROM weekly_current
               WHERE week_num=? ORDER BY total_points DESC""",
            (week,)
        ).fetchall()

    leaderboard = [
        {"rank": i+1, "target": row["target"], "total_points": row["total_points"]}
        for i, row in enumerate(rows)
    ]
    return {"week_num": week, "leaderboard": leaderboard}

def get_records(target: str = None, week: str = None,
                page: int = 1, page_size: int = 20) -> dict:
    """查询积分明细，支持分页"""
    conditions = []
    params = []

    if target:
        conditions.append("target=?")
        params.append(target)
    if week:
        conditions.append("week_num=?")
        params.append(week)

    where = " AND ".join(conditions) if conditions else "1=1"

    with get_conn() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM records WHERE {where}", params
        ).fetchone()[0]

        offset = (page - 1) * page_size
        rows = conn.execute(
            f"""SELECT * FROM records WHERE {where}
                ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            [*params, page_size, offset]
        ).fetchall()

    records = [dict(row) for row in rows]
    return {"total": total, "page": page, "page_size": page_size, "records": records}

def get_history(week: str = None) -> dict:
    """查询历史归档"""
    if week:
        where = "WHERE week_num=?"
        params = [week]
    else:
        where = "1=1"
        params = []

    with get_conn() as conn:
        rows = conn.execute(
            f"""SELECT week_num, target, total_points FROM weekly_history
                {where} ORDER BY week_num DESC, total_points DESC""",
            params
        ).fetchall()

    # 按周分组
    weeks_map = {}
    for row in rows:
        w = row["week_num"]
        if w not in weeks_map:
            weeks_map[w] = {"week_num": w, "leaderboard": []}
        weeks_map[w]["leaderboard"].append({
            "target": row["target"],
            "total_points": row["total_points"]
        })

    return {"weeks": list(weeks_map.values())}

def reset_weekly() -> dict:
    """清零 + 归档（由 main 分支 cronjob 调用）"""
    import datetime
    current_week = get_current_week_num()
    now = datetime.datetime.utcnow().isoformat() + "+00:00"

    with get_conn() as conn:
        # 1. 读取当周快照
        snapshot = conn.execute(
            "SELECT target, total_points FROM weekly_current WHERE week_num=?",
            (current_week,)
        ).fetchall()

        # 2. 写入历史归档
        for row in snapshot:
            conn.execute(
                """INSERT OR REPLACE INTO weekly_history
                   (target,total_points,week_num,archived_at,archived_by)
                   VALUES (?,?,?,?,?)""",
                (row["target"], row["total_points"], current_week, now, "main")
            )

        # 3. 清空当周看板（保留表结构）
        conn.execute("DELETE FROM weekly_current WHERE week_num=?", (current_week,))

    return {"archived_week": current_week, "archived_count": len(snapshot)}

# -------------------------------------------------------------------
# 国学平台运行数据
# -------------------------------------------------------------------

def insert_guoxue_metric(metric_type: str, meta: dict, week: str = None) -> int:
    """
    写入国学平台运行数据到 guoxue_metrics 表。

    metric_type: 'inspection' | 'ci_build' | 'content_output'
    meta: 各类型专属字段的字典，会序列化为 JSON
    week: YYYY-Www，不传则自动使用当前周
    """
    import datetime
    import json

    if week is None:
        week = get_current_week_num()
    now = datetime.datetime.utcnow().isoformat() + "+00:00"

    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO guoxue_metrics (metric_type, week_num, recorded_at, meta)
               VALUES (?,?,?,?)""",
            (metric_type, week, now, json.dumps(meta, ensure_ascii=False))
        )
        return cur.lastrowid

def get_guoxue_metrics(metric_type: str = None, week: str = None) -> list:
    """
    查询国学平台运行数据。
    metric_type: 可选过滤 'inspection' | 'ci_build' | 'content_output'
    week: 可选过滤 YYYY-Www
    """
    import json

    conditions = []
    params = []

    if metric_type:
        conditions.append("metric_type=?")
        params.append(metric_type)
    if week:
        conditions.append("week_num=?")
        params.append(week)

    where = " AND ".join(conditions) if conditions else "1=1"

    with get_conn() as conn:
        rows = conn.execute(
            f"""SELECT * FROM guoxue_metrics WHERE {where}
                ORDER BY recorded_at DESC""",
            params
        ).fetchall()

    result = []
    for row in rows:
        d = dict(row)
        d["meta"] = json.loads(d["meta"]) if d["meta"] else {}
        result.append(d)
    return result
