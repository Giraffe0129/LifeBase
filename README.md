# My Awesome App 🚀

**多端互通任务 / 出行 / 笔记管理 · 离线可用 · 桌面 EXE + 移动 App**

> 非技术人员也能用！下载即用，云端同步，无需懂代码。

---

## 目录

- [📱 快速使用（非技术人员）](#-快速使用非技术人员)
- [☁️ 部署后端到云服务器](#️-部署后端到云服务器)
- [💻 本地开发](#-本地开发)
- [🏗️ 架构说明](#️-架构说明)
- [📖 用户指南](#-用户指南)
- [🔧 常见问题](#-常见问题)

---

## 📱 快速使用（非技术人员）

### 方式一：Windows 桌面端（推荐）

1. 从发布页面下载 **My Awesome App Setup.exe**
2. 双击安装，一路下一步
3. 打开软件，注册账号
4. 进入 **设置** → 配置和风天气 API Key（[免费申请](https://dev.qweather.com)）
5. 开始使用！

> 桌面端使用 Electron 构建，自动检查更新。

### 方式二：手机端（PWA，无需应用商店）

1. 在手机浏览器中打开部署好的后端地址（如 `https://your-app.railway.app`）
2. 首次加载后，**添加到桌面**（iOS: Safari 分享按钮 → 添加到主屏幕；Android: Chrome 菜单 → 添加到主屏幕）
3. 桌面图标启动后，注册账号即可使用
4. 支持**离线缓存**——没网也能查看和编辑，联网后自动同步

### 首次使用配置

```
1. 注册账号 → 2. 进入设置 → 3. 配置天气 API Key → 4. 开始使用
```

> API Key 配置在**设置页**内完成，无需修改任何代码文件。

---

## ☁️ 部署后端到云服务器

### 选项一：Railway（推荐，最快）

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

1. 点击上方按钮，将 GitHub 仓库连接到 Railway
2. 添加 PostgreSQL 插件（Railway 自动配置）
3. 设置环境变量：
   - `SECRET_KEY`：任意随机字符串（用于 JWT 加密）
   - `QWEATHER_API_KEY`：你的和风天气 API Key（可选，用户也可自行配置）
4. 部署完成后，Railway 会提供一个 `https://xxx.up.railway.app` 地址
5. 手机和电脑端都使用这个地址访问

### 选项二：Docker + VPS

```bash
# 1. 安装 Docker 和 docker-compose

# 2. 克隆项目
git clone https://github.com/your-username/my-awesome-app.git
cd my-awesome-app

# 3. 创建 .env 文件
echo "SECRET_KEY=your_random_secret_here" > .env
echo "DB_PASSWORD=your_db_password" >> .env
echo "QWEATHER_API_KEY=your_qweather_key" >> .env

# 4. 启动（自动运行 PostgreSQL + 应用）
docker-compose up -d

# 5. 访问 http://your-server-ip:8000
```

### 选项三：Render

1. 在 [Render](https://render.com) 创建新的 **Web Service**
2. 连接 GitHub 仓库
3. 选择 **Docker** 环境
4. 添加 PostgreSQL 数据库（Render 内置）
5. 设置环境变量同上
6. 部署后获得 `https://your-app.onrender.com` 地址

---

## 💻 本地开发

###  prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL（可选，开发时可用 SQLite 替代）

### 1. 启动后端（SQLite，零配置）

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
# source .venv/bin/activate

pip install -r requirements.txt

# 修改 .env 中的 SECRET_KEY（随便填一个随机字符串）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档：http://localhost:8000/docs

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：http://localhost:5173

### 3. 构建桌面 EXE

```bash
cd frontend
npm run build:electron
# 输出在 frontend/dist-electron/
```

---

## 🏗️ 架构说明

### v2.0 新增特性

| 特性 | 说明 |
|------|------|
| **云端部署** | 后端 + PostgreSQL 部署到云，7x24h 在线 |
| **离线缓存** | IndexedDB + Service Worker，无网可读写，有网自动同步 |
| **桌面 EXE** | Electron 打包，Windows 安装包，Claude 风格界面 |
| **移动 App** | PWA 安装到手机桌面，体验接近原生 |
| **用户系统** | 注册/登录，数据隔离，每个用户独立空间 |
| **API Key 配置** | 用户在 App 内配置天气 API Key，无需碰代码 |
| **Claude 风格 UI** | 桌面端侧边栏 + 响应式适配移动端 |

### 架构图

```
┌──────────────────────────────────────────────┐
│               Cloud Backend                   │
│   FastAPI + PostgreSQL (Railway / Render)     │
│   - 用户认证 / JWT                            │
│   - 任务 / 出行 / 笔记 CRUD                    │
│   - 天气 API 代理                             │
│   - WebSocket 实时推送                        │
└───────────┬──────────────────────┬──────────┘
            │ REST + WS            │ REST + WS
       ┌────┴────┐           ┌────┴────┐
       │ Desktop │           │ Mobile  │
       │ (EXE)   │           │ (PWA)   │
       │ Electron│           │         │
       │ + Vue 3 │           │ Vue 3   │
       │ + Dexie │           │ + Dexie │
       │ (离线)   │           │ (离线)   │
       └─────────┘           └─────────┘
```

### 离线同步原理

```
在线:  操作 → API 请求 → 服务器 → IndexedDB 缓存 → 界面更新
                                          ↑
离线:  操作 → IndexedDB 存储 + 同步队列  ───┘
         ↓ (恢复网络时)
         自动推送队列 → API 请求 → 全量数据拉取 → 刷新本地
```

---

## 📖 用户指南

### 当前任务（📋）

- 点击圆形复选框切换完成状态
- 支持三级优先级：普通 / 重要 / 紧急
- 已完成任务折叠在底部，可展开查看
- 任意端操作后，其他端实时同步

### 出行计划（🗺️）

- 创建计划时填写目的地，**自动查询天气预报**
- 雨天自动标记 🌂 带伞提醒
- 填写日期和时间后按时间排序
- 点击底部 **🚇 乘车码** 按钮（手机端）跳转支付宝乘车码

### 值得记录（📝）

- 分"知识点"和"生活碎片"两类
- 支持 **Markdown** 格式编辑
- 支持标签和收藏
- 点击卡片查看详情（Markdown 渲染）

### 设置（⚙️）

- 配置和风天气 API Key（每个用户独立）
- 查看版本信息和用户信息
- 退出登录

---

## 🔧 常见问题

**Q: 电脑关机后手机端还能用吗？**
A: 如果后端部署到了云服务器（Railway/Render），则**可以**。后端 7x24h 运行，电脑关机不影响手机端使用。

**Q: 离线时操作的数据会丢失吗？**
A: **不会**。离线时数据保存在浏览器 IndexedDB 中，恢复网络时自动同步到服务器。

**Q: 手机端怎么下载？**
A: 不需要应用商店。在浏览器中打开 App 地址，使用"添加到主屏幕"功能即可。

**Q: 和风天气 API Key 怎么获取？**
A: 前往 https://dev.qweather.com 注册 → 创建应用 → 免费版每日 1000 次调用，个人使用完全足够。

**Q: 数据安全吗？**
A: 用户数据通过 JWT 认证隔离，每个人只能看到自己的数据。密码使用 bcrypt 加密存储。

---

## License

MIT
