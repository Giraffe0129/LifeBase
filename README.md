# My Awesome App 🚀

**多端互通任务 / 出行 / 笔记管理应用**

手机和电脑实时同步，一个后端管所有端。支持 PWA 可安装到手机桌面，体验接近原生 App。

---

## 功能总览

| 功能 | 说明 |
|------|------|
| 📋 **当前任务** | 多端添加/完成/删除任务，WebSocket 实时同步，支持优先级 |
| 🗺️ **出行计划** | 创建出行计划时自动查询目的地天气预报，雨天提醒带伞，提供乘车码跳转 |
| 📝 **值得记录** | Markdown 笔记，分"知识点"和"生活碎片"两大类，支持标签和收藏 |

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | Vue 3 + TypeScript + Vite | 响应式 SPA，组件化开发 |
| **状态管理** | Pinia | 全局数据状态 + WebSocket 实时更新 |
| **后端** | FastAPI + Python 3.12 | 高性能异步 API，自动生成 Swagger 文档 |
| **数据库** | SQLite (开发) / PostgreSQL (生产) | SQLAlchemy ORM，轻松切换 |
| **实时同步** | WebSocket | 多端数据实时推送 |
| **天气** | 和风天气 API | 自动查询目的地天气预报 |
| **PWA** | vite-plugin-pwa | 支持手机桌面安装 |
| **部署** | Docker Compose | 一键启动 |

---

## 快速开始

### 方式一：本地开发

#### 1. 启动后端

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
# source .venv/bin/activate

pip install -r requirements.txt

# 修改 .env 文件中的配置（可选）
# 申请和风天气 API Key: https://dev.qweather.com

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后访问:
- API 接口: http://localhost:8000/
- Swagger 文档: http://localhost:8000/docs

#### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端启动后访问: http://localhost:5173

### 方式二：Docker 部署

```bash
docker-compose up -d
```

访问 http://localhost:8000

---

## API 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| **任务** | | |
| GET | `/api/tasks/` | 获取所有任务 |
| POST | `/api/tasks/` | 创建任务 |
| PUT | `/api/tasks/{id}` | 更新任务 |
| DELETE | `/api/tasks/{id}` | 删除任务 |
| **出行计划** | | |
| GET | `/api/travel-plans/` | 获取所有出行计划 |
| POST | `/api/travel-plans/` | 创建出行计划（自动查天气） |
| PUT | `/api/travel-plans/{id}` | 更新出行计划 |
| DELETE | `/api/travel-plans/{id}` | 删除出行计划 |
| **笔记** | | |
| GET | `/api/notes/` | 获取笔记列表（支持 `?category=life` 过滤） |
| POST | `/api/notes/` | 创建笔记 |
| PUT | `/api/notes/{id}` | 更新笔记 |
| DELETE | `/api/notes/{id}` | 删除笔记 |
| **WebSocket** | | |
| WS | `/ws` | 实时同步连接 |

---

## 项目结构

```
my_awesome_app/
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── api/               # API 客户端 + WebSocket
│   │   ├── assets/            # 全局样式
│   │   ├── pages/             # 三个功能页面
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── App.vue            # 根组件
│   │   └── main.ts            # 入口
│   └── vite.config.ts         # 前端构建配置
│
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # 路由控制器
│   │   │   ├── tasks.py       # 任务 CRUD
│   │   │   ├── travel_plans.py # 出行计划 + 天气
│   │   │   ├── notes.py       # 笔记 CRUD
│   │   │   └── ws.py          # WebSocket 端点
│   │   ├── core/              # 配置、数据库、WS 管理器
│   │   ├── models/            # SQLAlchemy 数据模型
│   │   ├── schemas/           # Pydantic 数据验证
│   │   └── main.py            # FastAPI 入口
│   ├── requirements.txt
│   └── .env                   # 环境变量
│
├── docker-compose.yml          # 一键部署
├── Dockerfile                  # 多阶段构建
└── README.md
```

---

## 扩展指南

### 添加新功能模块

1. **后端**：在 `backend/app/models/` 建新模型 → `backend/app/schemas/` 建验证 → `backend/app/api/` 建路由 → 在 `backend/app/main.py` 注册
2. **前端**：在 `frontend/src/api/` 加 API 方法 → `frontend/src/stores/` 加状态 → `frontend/src/pages/` 建页面 → `frontend/src/router/` 加路由 → 在 `App.vue` 的底部导航加 tab

### 切换到 MySQL/PostgreSQL

修改 `backend/.env` 中的 `DATABASE_URL`:

```env
# MySQL
DATABASE_URL=mysql+asyncmy://user:password@localhost:3306/my_app

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/my_app
```

### 接入 AI 出行建议

FastAPI 天然适配 AI Agent 生态：

- 接入 OpenAI / 本地大模型 API，根据目的地和天气自动生成出行建议
- 在 `travel_plans.py` 中添加一个 `POST /api/travel-plans/ai-suggest` 端点即可

---

## 天气 API 配置

1. 前往 https://dev.qweather.com 注册免费账号
2. 创建应用获取 API Key
3. 将 Key 填入 `backend/.env` 的 `QWEATHER_API_KEY=` 中

> 免费版支持每日 1000 次免费调用，个人使用完全足够。

---

## License

MIT
