'use strict';

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Window controls
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
  isMaximized: () => ipcRenderer.invoke('window:isMaximized'),

  // Auto-updater
  installUpdate: () => ipcRenderer.send('updater:install'),
  onUpdaterEvent: (event, callback) => {
    const validEvents = [
      'updater:checking',
      'updater:available',
      'updater:not-available',
      'updater:progress',
      'updater:downloaded',
      'updater:error',
    ];
    if (!validEvents.includes(event)) return;
    const handler = (_evt, ...args) => callback(...args);
    ipcRenderer.on(event, handler);
    // Return cleanup function
    return () => ipcRenderer.removeListener(event, handler);
  },
});
