# 积分系统 Docker 部署指南

## 架构（方案甲）

| 组件 | 位置 | 端口 |
|------|------|------|
| OpenClaw | Windows 本地（不动） | — |
| 积分系统 backend | Docker 容器 | 8000 |
| 积分系统 frontend | Docker Nginx | 3000 |

## 前置条件

- Docker Desktop for Windows 已安装并运行
- WSL2 backend 已启用

## 部署步骤

### 1. 克隆/更新项目

```bash
cd /path/to/points-system
git pull origin main
```

### 2. 一键启动

```bash
docker-compose up -d --build
```

Docker 会自动：
- 拉取 `python:3.11-slim`、`node:20-alpine`、`nginx:alpine` 镜像
- 构建 backend 和 frontend
- 启动两个容器

### 3. 验证

```bash
# 查看容器状态
docker-compose ps

# 查看 backend 日志
docker-compose logs backend

# 查看 frontend 日志
docker-compose logs frontend
```

### 4. 访问

- 前端：http://localhost:3000
- Backend API：http://localhost:8000/health

## 停止

```bash
docker-compose down
```

## 数据持久化

SQLite 数据库保存在 Docker volume 中，不会因容器重启丢失。

## 常见问题

**Q: docker-compose up 卡住不动**
A: 首次运行需要拉取镜像，等待 5-10 分钟。

**Q: 端口被占用**
A: 修改 `docker-compose.yml` 中的端口映射（把 `8000:8000` 改成 `8080:8000` 等）

**Q: 容器启动失败**
A: 运行 `docker-compose logs backend` 查看错误信息。
