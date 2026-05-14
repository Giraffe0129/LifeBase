# My Awesome App

多端互通任务 · 出行 · 笔记管理 | 全栈 Web + 桌面端 + 移动端

---

## 功能特性

### 📋 当前任务
- 创建/编辑/删除任务
- **拖拽排序**（所有列表页均支持）
- **子任务**：大任务拆分为多个小任务，可展开/收起
- 优先级标签（普通 / ⭐重要 / 🔥紧急）
- 已完成任务归档

### 🗺️ 出行计划
- 创建出行计划，填写目的地自动查询**天气预报**
- **iOS 风格滚轮选择器**选择日期和时间
- **天气可视化**：Lucide 天气图标 + 渐变背景（晴/雨/阴/雪）
- 天气显示可在设置页开关

### 📝 值得记录
- Markdown 笔记编辑器
- **自定义分类**（内置"生活碎片""知识点"，可新增/编辑/删除）
- 标签系统，收藏功能
- 笔记详情预览

### ⚙️ 其他
- 用户注册/登录（JWT 认证）
- **离线缓存**（IndexedDB + 自动同步）
- **WebSocket 实时同步**（多端数据实时更新）
- **昼夜模式**（自动日出日落 + 手动切换）
- **桌面便签模式**（Electron 系统托盘 + 始终置顶小窗口）
- **PWA** / **Capacitor** 移动端原生打包

---

## 快速开始

### 前置要求
- Python 3.10+
- Node.js 18+
- npm 9+

### 1. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 填入你的配置

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档。

### 2. 前端启动

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173。

### 3. 桌面端（Electron）

```bash
cd frontend
npm run dev:electron
```

**快捷键：**
- `Ctrl/Cmd + Shift + S` — 切换主窗口/便签模式
- `Ctrl/Cmd + Shift + X` — 关闭便签
- `Esc` — 关闭便签
- `← →` — 便签内切换模块

### 4. 移动端（Capacitor）

```bash
cd frontend
npm run build
npx cap sync

# Android
npx cap open android
# Android Studio 中打包 APK

# iOS（仅 macOS）
npx cap open ios
# Xcode 中打包 IPA
```

---

## 部署到服务器

### 方案一：直接部署（Linux VPS）

```bash
# 1. 后端
cd backend
pip install -r requirements.txt

# 使用生产级 ASGI 服务器
pip install gunicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 推荐使用 supervisor 或 systemd 管理进程
# 或使用 Docker（见下方）
```

### 方案二：Docker 部署

创建后端 `Dockerfile`：

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/ .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```bash
docker build -t my-awesome-app-backend .
docker run -d -p 8000:8000 \
  -e SECRET_KEY="your_random_secret_here" \
  -e DATABASE_URL="sqlite+aiosqlite:///./app.db" \
  my-awesome-app-backend
```

### 方案三：云平台部署

**Render（推荐）**
1. 在 `backend/` 目录放置 `render.yaml`：

```yaml
services:
  - type: web
    name: my-awesome-app
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        value: sqlite+aiosqlite:///./app.db
```

2. 连接 GitHub 仓库，Render 自动部署。

### 部署后的前端配置

构建前端并部署到静态托管（Vercel / Netlify / Cloudflare Pages）：

```bash
cd frontend
npm run build
# 将 dist/ 目录部署
```

在 `frontend/src/api/index.ts` 中，**生产环境**自动使用当前域名（不跨域），无需修改。
如果前后端分离部署，需要设置 `VITE_API_BASE_URL` 环境变量指向后端地址。

---

## 开源到 GitHub — 隐私保护指南

### ✅ 已经保护的内容
以下已在 `.gitignore` 中排除：
- `__pycache__/`, `node_modules/` — 编译缓存
- `.env` — 环境变量（密钥、数据库密码）
- `*.db`, `*.sqlite3` — 数据库文件（含用户数据）
- `.idea/`, `.vscode/` — IDE 配置

### 🔧 上传前请检查

#### 1. 后端配置 (`backend/app/core/config.py`)
SECRET_KEY 使用了默认占位符 `"change_this_to_a_random_secret_key_in_production"`，**无隐私泄露风险**。
用户部署时必须自行修改。

#### 2. 环境变量模板
```bash
# 创建 .env.example（已安全，不含真实密钥）
cp backend/.env backend/.env.example
```

#### 3. 前端 API 地址
`frontend/src/api/index.ts` 中：
```typescript
const BASE_URL = import.meta.env.PROD ? '' : ''
```
生产环境自动使用同域地址，不暴露任何服务器信息。

#### 4. 数据库
`backend/app.db` 已在 `.gitignore` 中排除。
首次部署后会自动创建空数据库，不含任何用户数据。

### 📝 开源步骤

```bash
# 1. 在项目根目录初始化 Git
git init

# 2. 添加所有文件
git add .

# 3. 检查是否有敏感文件
git status
# 确认以下不在列表中：
#   ❌ backend/.env
#   ❌ backend/app.db
#   ❌ frontend/node_modules/
#   ❌ __pycache__/
#   ❌ .claude/

# 4. 首次提交
git commit -m "Initial commit: My Awesome App v3"

# 5. 在 GitHub 创建仓库（不要勾选 Add README）

# 6. 推送到 GitHub
git remote add origin https://github.com/你的用户名/my-awesome-app.git
git branch -M main
git push -u origin main
```

### 🔐 部署生产环境时的安全注意事项

| 项目 | 建议 |
|------|------|
| **SECRET_KEY** | 使用 `openssl rand -hex 32` 生成随机 64 位密钥 |
| **数据库** | 生产环境使用 PostgreSQL，勿用 SQLite |
| **HTTPS** | 必须启用 HTTPS（推荐 Cloudflare / Let's Encrypt） |
| **CORS** | 在 `.env` 中限制为具体的生产域名 |
| **密码** | 用户密码通过 bcrypt 哈希存储（已实现） |
| **JWT** | Token 有效期为 30 天，生产环境可缩短 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端框架** | Vue 3 + TypeScript |
| **状态管理** | Pinia |
| **路由** | Vue Router (Hash History) |
| **构建工具** | Vite 5 |
| **CSS** | 原生 CSS + CSS 变量（Organic/Natural 设计系统） |
| **后端框架** | Python FastAPI |
| **数据库 ORM** | SQLAlchemy 2.0 (Async) |
| **数据库** | SQLite（开发）/ PostgreSQL（生产） |
| **认证** | JWT (python-jose + passlib bcrypt) |
| **实时通信** | WebSocket |
| **离线同步** | Dexie.js (IndexedDB) |
| **桌面端** | Electron |
| **移动端** | Capacitor (Android/iOS) |
| **天气 API** | 和风天气 (QWeather) |
| **设计系统** | Organic/Natural（Fraunces + Nunito, Moss Green） |
| **图标** | Lucide 风格 SVG |

---

## 项目结构

```
my-awesome-app/
├── backend/
│   └── app/
│       ├── api/          # RESTful API 路由
│       │   ├── auth.py        # 用户认证
│       │   ├── tasks.py       # 任务 CRUD + 子任务
│       │   ├── travel_plans.py # 出行计划 + 天气
│       │   ├── notes.py       # 笔记 CRUD + 分类
│       │   ├── categories.py  # 自定义分类 CRUD
│       │   ├── settings.py    # 用户设置
│       │   └── ws.py          # WebSocket
│       ├── core/         # 核心配置
│       │   ├── config.py      # 环境变量配置
│       │   ├── database.py    # 数据库引擎
│       │   ├── auth.py        # JWT + 密码工具
│       │   ├── ws_manager.py  # WebSocket 管理器
│       │   └── migration.py   # 数据库迁移
│       ├── models/       # 数据模型
│       ├── schemas/      # Pydantic 验证
│       └── main.py       # 应用入口
│
├── frontend/
│   ├── src/
│   │   ├── pages/       # 页面组件
│   │   │   ├── LoginPage.vue
│   │   │   ├── TasksPage.vue     # 当前任务
│   │   │   ├── TravelPage.vue    # 出行计划
│   │   │   ├── NotesPage.vue     # 值得记录
│   │   │   ├── SettingsPage.vue  # 设置
│   │   │   └── StickyPage.vue    # 便签模式
│   │   ├── api/         # API 客户端
│   │   ├── stores/      # Pinia 状态管理
│   │   ├── db/          # IndexedDB + 同步引擎
│   │   ├── utils/       # 工具函数、图标
│   │   ├── assets/      # 全局样式
│   │   ├── router/      # 路由配置
│   │   ├── App.vue      # 根组件
│   │   └── main.ts      # 入口
│   ├── electron/        # Electron 主进程
│   ├── capacitor.config.ts
│   └── package.json
│
├── BUILD.md             # 本文件
└── .gitignore
```

---

## API 文档

启动后端后访问 http://localhost:8000/docs 查看交互式 Swagger 文档。

**主要端点：**

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET/POST | `/api/tasks/` | 任务列表/创建 |
| PUT | `/api/tasks/reorder/bulk` | 任务批量排序 |
| GET | `/api/tasks/{id}/subtasks` | 获取子任务 |
| GET/POST | `/api/travel-plans/` | 出行计划列表/创建 |
| PUT | `/api/travel-plans/reorder/bulk` | 出行计划批量排序 |
| GET/POST | `/api/notes/` | 笔记列表/创建 |
| PUT | `/api/notes/reorder/bulk` | 笔记批量排序 |
| GET/POST | `/api/categories/` | 分类列表/创建 |
| GET/PUT | `/api/settings/` | 用户设置 |
| WS | `/ws` | WebSocket 实时同步 |

---

## 版本历史

| 版本 | 说明 |
|------|------|
| v1.0.0 | 基础功能：任务、出行、笔记 CRUD |
| v2.0.0 | 用户认证 + 离线同步 + PWA + WebSocket |
| v3.0.0 | UI 重设计 + 拖拽排序 + 自定义分类 + 子任务 + 便签模式 + Capacitor |
