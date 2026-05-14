/**
 * Electron 主进程 v3
 * 系统托盘 + 便签模式 + 快捷键 (Ctrl+Shift+S 切换 / Ctrl+Shift+X 关闭)
 */
const { app, BrowserWindow, shell, Tray, Menu, nativeImage, globalShortcut } = require('electron')
const path = require('path')

const isDev = !app.isPackaged
let mainWindow = null
let stickyWindow = null
let tray = null
let isStickyMode = false

// ===== ① ⑤ 托盘图标：内嵌 16x16 PNG base64 =====
// 一个简单的 Moss Green 圆角方块图标
function createTrayIcon() {
  // 16x16 PNG: 4 bytes per pixel RGBA, 简单单色图标
  // 使用 nativeImage.createFromBuffer 创建
  const size = 16
  const buf = Buffer.alloc(size * size * 4)
  const mossGreen = [93, 112, 82, 255]    // #5D7052
  const darkGreen = [79, 98, 68, 255]     // #4F6244
  const transparent = [0, 0, 0, 0]

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const idx = (y * size + x) * 4
      // 绘制一个简单的任务方块图标
      if (x >= 2 && x <= 6 && y >= 2 && y <= 6) {       // 左上
        buf[idx] = mossGreen[0]; buf[idx+1] = mossGreen[1]; buf[idx+2] = mossGreen[2]; buf[idx+3] = mossGreen[3]
      } else if (x >= 9 && x <= 13 && y >= 2 && y <= 6) { // 右上
        buf[idx] = darkGreen[0]; buf[idx+1] = darkGreen[1]; buf[idx+2] = darkGreen[2]; buf[idx+3] = darkGreen[3]
      } else if (x >= 2 && x <= 6 && y >= 9 && y <= 13) { // 左下
        buf[idx] = darkGreen[0]; buf[idx+1] = darkGreen[1]; buf[idx+2] = darkGreen[2]; buf[idx+3] = darkGreen[3]
      } else if (x >= 9 && x <= 13 && y >= 9 && y <= 13) { // 右下
        buf[idx] = mossGreen[0]; buf[idx+1] = mossGreen[1]; buf[idx+2] = mossGreen[2]; buf[idx+3] = mossGreen[3]
      } else {
        buf[idx] = transparent[0]; buf[idx+1] = transparent[1]; buf[idx+2] = transparent[2]; buf[idx+3] = transparent[3]
      }
    }
  }

  return nativeImage.createFromBuffer(buf, { width: size, height: size })
}

// ===== 主窗口 =====
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 960,
    height: 680,
    minWidth: 680,
    minHeight: 520,
    title: 'My Awesome App',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    ...(process.platform === 'darwin' ? { titleBarStyle: 'hiddenInset' } : {}),
  })

  if (process.platform === 'win32') mainWindow.setBackgroundColor('#1A1A14')

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  mainWindow.webContents.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: 'deny' } })
  mainWindow.on('close', (event) => { if (!app.isQuitting) { event.preventDefault(); mainWindow.hide() } })
}

// ===== 便签窗口 =====
function createStickyWindow() {
  if (stickyWindow && !stickyWindow.isDestroyed()) { stickyWindow.show(); stickyWindow.focus(); return }

  stickyWindow = new BrowserWindow({
    width: 360, height: 560,
    resizable: false, alwaysOnTop: true, skipTaskbar: true,
    frame: false, transparent: false,
    title: 'My App - 便签',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true, nodeIntegration: false,
    },
  })

  const { screen } = require('electron')
  const displays = screen.getPrimaryDisplay()
  const { width, height } = displays.workAreaSize
  stickyWindow.setPosition(width - 380, height - 600)

  if (isDev) stickyWindow.loadURL('http://localhost:5173/#/sticky')
  else stickyWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'), { hash: '/sticky' })

  stickyWindow.on('closed', () => { stickyWindow = null })
}

function closeStickyWindow() {
  if (stickyWindow && !stickyWindow.isDestroyed()) stickyWindow.close()
  stickyWindow = null
  if (mainWindow) mainWindow.show()
}

// ===== 系统托盘 =====
function createTray() {
  const trayIcon = createTrayIcon()
  tray = new Tray(trayIcon)
  tray.setToolTip('My Awesome App\n右键菜单 | 双击主窗口')

  const buildMenu = () => Menu.buildFromTemplate([
    {
      label: isStickyMode ? '● 便签模式 (开启)' : '○ 便签模式',
      click: () => { toggleStickyMode() },
    },
    { type: 'separator' },
    {
      label: '打开主窗口',
      click: () => { if (mainWindow) { mainWindow.show(); mainWindow.focus() } else createMainWindow() },
    },
    {
      label: '关闭便签',
      click: () => { closeStickyWindow(); isStickyMode = false; tray.setContextMenu(buildMenu()) },
    },
    { type: 'separator' },
    {
      label: '退出',
      click: () => { app.isQuitting = true; app.quit() },
    },
  ])

  tray.setContextMenu(buildMenu())
  tray.on('double-click', () => { if (mainWindow) { mainWindow.show(); mainWindow.focus() } })
}

// ===== ① 切换便签（供快捷键和托盘共用）=====
function toggleStickyMode() {
  isStickyMode = !isStickyMode
  if (isStickyMode) { createStickyWindow(); if (mainWindow) mainWindow.hide() }
  else { closeStickyWindow() }
}

// ===== 快捷键 =====
function registerShortcuts() {
  // ① Ctrl+Shift+S: 切换主窗口/便签
  globalShortcut.register('CommandOrControl+Shift+S', () => { toggleStickyMode() })
  // ⑥ Ctrl+Shift+X / Esc: 关闭便签
  globalShortcut.register('CommandOrControl+Shift+X', () => {
    if (stickyWindow && !stickyWindow.isDestroyed()) { closeStickyWindow(); isStickyMode = false }
  })
}

// ===== App Lifecycle =====
app.whenReady().then(() => { createMainWindow(); createTray(); registerShortcuts() })

app.on('window-all-closed', () => {})
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createMainWindow(); else if (mainWindow) mainWindow.show() })
app.on('will-quit', () => { globalShortcut.unregisterAll() })

const gotLock = app.requestSingleInstanceLock()
if (!gotLock) { app.quit() } else {
  app.on('second-instance', () => {
    if (mainWindow) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.show(); mainWindow.focus() }
  })
}
