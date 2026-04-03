"""
积分系统 — GitHub 持久化层
每次写入后自动 commit + push，读取前先 pull 保证最新
"""

import os
import sqlite3
import fcntl
import subprocess
import time
from pathlib import Path

REPO_DIR = Path(__file__).parent.parent
DB_FILE = "points.db"
GIT_LOCK = REPO_DIR / ".git-sync.lock"


def run_git(*args, retry=2):
    """执行 git 命令，失败重试"""
    for attempt in range(retry):
        try:
            result = subprocess.run(
                ["git", "-C", str(REPO_DIR)] + list(args),
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                return result.stdout.strip()
            # 如果是"没有变更"不算错误
            if "nothing to commit" in result.stdout or "up to date" in result.stdout:
                return result.stdout.strip()
        except subprocess.TimeoutExpired:
            time.sleep(1)
    return None


def git_pull():
    """启动时拉取最新数据库"""
    run_git("config", "user.email", "dev@agent.local")
    run_git("config", "user.name", "DevAgent")
    run_git("pull", "--rebase", "origin", "master")
    # 确保本地 db 文件是最新的
    result = run_git("ls-files", DB_FILE)
    if result != DB_FILE:
        # db 文件还没加入 repo，先提交一次
        Path(REPO_DIR / DB_FILE).touch()
        run_git("add", DB_FILE)
        run_git("commit", "-m", "chore: init points.db")


def git_push():
    """每次写入后提交数据库"""
    lock_path = Path("/tmp/points-git-sync.lock")
    with open(lock_path, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            # 先 pull 避免落后
            run_git("pull", "--rebase", "origin", "master")
            # 添加 db 变更
            run_git("add", DB_FILE)
            # 检查是否有变更要提交
            status = run_git("status", "--porcelain")
            if status:
                run_git("commit", "-m", f"data: points update {int(time.time())}")
                run_git("push", "origin", "master")
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def ensure_git_initialized():
    """确保 repo 有 git 并初始化"""
    git_dir = REPO_DIR / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init"], cwd=REPO_DIR, capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:guoxue-platform/points-system.git"],
            cwd=REPO_DIR, capture_output=True
        )
    git_pull()
