# My Awesome App - Build & Deploy Guide

## 技术栈
- **前端**: Vue 3 + TypeScript + Vite + Pinia
- **后端**: Python FastAPI + SQLite
- **桌面端**: Electron (Windows/Mac)
- **移动端**: Capacitor (Android/iOS)
- **离线同步**: Dexie.js (IndexedDB) + 自定义同步引擎

---

## 快速开始

### 1. 后端启动
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. 前端开发
```bash
cd frontend
npm install
npm run dev          # Web 端 (http://localhost:5173)
```

### 3. Electron 桌面端
```bash
cd frontend
npm run dev:electron  # 启动桌面应用（含热更新）
npm run build:electron # 打包为安装包 (dist-electron/)
```

### 4. 移动端构建 (Capacitor)
```bash
cd frontend
npm run build         # 先构建 Web 端
npm run build:mobile  # 同步到 Capacitor

# Android
npm run build:android
# 然后在 Android Studio 中打包 APK:
npm run cap:open:android

# iOS (仅 macOS)
npm run cap:open:ios
# 然后在 Xcode 中打包 IPA
```

---

## 功能特性

### v3.0.0 新功能
1. **🎨 UI 全面重设计**
   - 极简现代风格 (Minimalist Modern)
   - Bento Grid 布局影响
   - 玻璃拟态 (Glassmorphism) 弹窗
   - 平滑的渐入渐出动画
   - 统一的 Indigo 主题色系统

2. **📌 桌面便签模式 (Electron)**
   - 系统托盘运行
   - 一键切换为始终置顶的小窗口
   - 快捷键: `Ctrl/Cmd + Shift + S`

3. **🔄 任务拖拽排序**
   - 原生拖拽 API 实现
   - 自动同步到服务器
   - 动画过渡效果

4. **📂 自定义笔记分类**
   - 内置"生活碎片"、"知识点"分类
   - 支持添加/编辑/删除自定义分类
   - 每个分类可设置图标和颜色
   - 右键快速编辑分类

5. **🌤️ 天气可视化**
   - 动画天气图标 (动画浮动效果)
   - 渐变天气背景
   - 设置中可开关

6. **⏰ 自定义时间选择器**
   - iOS 风格滚轮选择
   - 年/月/日/时/分 独立滚轮
   - scroll-snap 对齐

7. **📱 移动端原生打包**
   - Capacitor 支持 (Android + iOS)
   - 原生启动屏
   - 状态栏适配

---

## 部署

### 生产部署 (后端)
```bash
cd backend
# 使用生产级 ASGI 服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### PWA 部署
```bash
cd frontend
npm run build
# 将 dist/ 目录部署到任意静态服务器
```
