/**
 * Electron 预加载脚本
 * 安全地暴露部分 Node.js API 给渲染进程。
 */
const { contextBridge } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  isElectron: true,
  platform: process.platform,
})
