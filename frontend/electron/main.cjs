/**
 * Electron 主进程 v3
 * - 主窗口: 加载 Vue 前端
 * - 便签模式: 最小化到系统托盘，显示为小窗口悬浮在屏幕上
 */
const { app, BrowserWindow, shell, Tray, Menu, nativeImage, globalShortcut } = require('electron')
const path = require('path')

const isDev = !app.isPackaged
let mainWindow = null
let stickyWindow = null
let tray = null
let isStickyMode = false

// ===== 主窗口 =====
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 960,
    height: 680,
    minWidth: 680,
    minHeight: 520,
    title: 'My Awesome App',
    icon: path.join(__dirname, '..', 'public', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    ...(process.platform === 'darwin' ? { titleBarStyle: 'hiddenInset' } : {}),
  })

  if (process.platform === 'win32') {
    mainWindow.setBackgroundColor('#1a1a2e')
  }

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  // 窗口关闭时隐藏而非退出（保留托盘）
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault()
      mainWindow.hide()
    }
  })
}

// ===== 便签窗口 (Sticky Note Mode) =====
function createStickyWindow() {
  if (stickyWindow && !stickyWindow.isDestroyed()) {
    stickyWindow.show()
    stickyWindow.focus()
    return
  }

  // 创建一个始终置顶的小窗口，显示当前任务
  stickyWindow = new BrowserWindow({
    width: 320,
    height: 420,
    resizable: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    frame: false,
    transparent: false,
    title: 'My App - 便签',
    icon: path.join(__dirname, '..', 'public', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  // 设置窗口位置（屏幕右下角）
  const { screen } = require('electron')
  const displays = screen.getPrimaryDisplay()
  const { width, height } = displays.workAreaSize
  stickyWindow.setPosition(width - 340, height - 460)

  // 加载便签视图（小窗口专用 HTML）
  if (isDev) {
    stickyWindow.loadURL('http://localhost:5173/#/sticky')
  } else {
    stickyWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'), {
      hash: '/sticky',
    })
  }

  stickyWindow.on('closed', () => {
    stickyWindow = null
  })
}

// ===== 系统托盘 =====
function createTray() {
  // 使用原生图像或 16x16 图标
  const iconPath = path.join(__dirname, '..', 'public', 'icon.png')
  const trayIcon = nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 })

  tray = new Tray(trayIcon)
  tray.setToolTip('My Awesome App')

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '打开主窗口',
      click: () => {
        if (mainWindow) {
          mainWindow.show()
          mainWindow.focus()
        } else {
          createMainWindow()
        }
      },
    },
    {
      label: '📌 便签模式',
      type: 'checkbox',
      checked: false,
      click: (menuItem) => {
        isStickyMode = menuItem.checked
        if (isStickyMode) {
          createStickyWindow()
          if (mainWindow) mainWindow.hide()
        } else {
          if (stickyWindow && !stickyWindow.isDestroyed()) {
            stickyWindow.close()
          }
        }
      },
    },
    { type: 'separator' },
    {
      label: '退出',
      click: () => {
        app.isQuitting = true
        app.quit()
      },
    },
  ])

  tray.setContextMenu(contextMenu)

  // 双击托盘打开主窗口
  tray.on('double-click', () => {
    if (mainWindow) {
      mainWindow.show()
      mainWindow.focus()
    }
  })
}

// ===== 快捷键 =====
function registerShortcuts() {
  // Cmd/Ctrl+Shift+S: 切换便签模式
  globalShortcut.register('CommandOrControl+Shift+S', () => {
    isStickyMode = !isStickyMode
    if (isStickyMode) {
      createStickyWindow()
      if (mainWindow) mainWindow.hide()
    } else {
      if (stickyWindow && !stickyWindow.isDestroyed()) {
        stickyWindow.close()
      }
      if (mainWindow) mainWindow.show()
    }
  })
}

// ===== App Lifecycle =====
app.whenReady().then(() => {
  createMainWindow()
  createTray()
  registerShortcuts()
})

app.on('window-all-closed', () => {
  // 保留托盘运行
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow()
  } else if (mainWindow) {
    mainWindow.show()
  }
})

app.on('will-quit', () => {
  globalShortcut.unregisterAll()
})

// 防止多个实例
const gotLock = app.requestSingleInstanceLock()
if (!gotLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.show()
      mainWindow.focus()
    }
  })
}
