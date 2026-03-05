'use strict';

const { app, BrowserWindow, ipcMain, shell, dialog, nativeTheme, protocol, net: electronNet } = require('electron');
const { autoUpdater } = require('electron-updater');
const log = require('electron-log');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const net = require('net');
const treeKill = require('tree-kill');

// ============================================================
// CUSTOM PROTOCOL — serve frontend_out/ via app:// scheme
// ============================================================
protocol.registerSchemesAsPrivileged([
  {
    scheme: 'app',
    privileges: {
      standard: true,
      secure: true,
      supportFetchAPI: true,
      corsEnabled: true,
    },
  },
]);

// ============================================================
// LOGGING SETUP
// ============================================================
log.transports.file.level = 'info';
log.transports.console.level = 'debug';
autoUpdater.logger = log;

// ============================================================
// GLOBALS
// ============================================================
let mainWindow = null;
let splashWindow = null;
let backendProcess = null;
let backendReady = false;
const BACKEND_PORT = 8000;
const isDev = process.argv.includes('--dev') || !app.isPackaged;

// ============================================================
// PATH RESOLUTION
// ============================================================
function getResourcePath(...segments) {
  if (isDev) {
    return path.join(__dirname, '..', '..', ...segments);
  }
  return path.join(process.resourcesPath, ...segments);
}

function getBackendExePath() {
  if (isDev) {
    // In dev mode: run python directly
    return null;
  }
  return path.join(process.resourcesPath, 'backend_dist', 'server', 'server.exe');
}

function getFrontendUrl() {
  if (isDev) {
    return 'http://localhost:3000';
  }
  // Packaged: serve via custom app:// scheme (registered below in app.whenReady)
  return 'app://frontend/index.html';
}

// ============================================================
// BACKEND PROCESS MANAGEMENT
// ============================================================
function checkPort(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => resolve(false)); // port in use = backend alive
    server.once('listening', () => { server.close(); resolve(true); }); // port free
    server.listen(port, '127.0.0.1');
  });
}

async function waitForBackend(maxWaitMs = 60000) {
  const start = Date.now();
  while (Date.now() - start < maxWaitMs) {
    const isFree = await checkPort(BACKEND_PORT);
    if (!isFree) return true; // port occupied = backend is up
    await new Promise(r => setTimeout(r, 500));
  }
  return false;
}

function startBackend() {
  return new Promise(async (resolve, reject) => {
    if (isDev) {
      // Dev mode: assume python server is already running or start it
      log.info('[Backend] Dev mode — checking if backend is already up...');
      const alreadyUp = !(await checkPort(BACKEND_PORT));
      if (alreadyUp) {
        log.info('[Backend] Dev backend already running.');
        return resolve();
      }

      const runPy = path.join(__dirname, '..', '..', 'run.py');
      log.info(`[Backend] Starting dev backend: python ${runPy}`);
      backendProcess = spawn('python', [runPy], {
        cwd: path.join(__dirname, '..', '..'),
        env: {
          ...process.env,
          FLAGS_enable_pir_api: '0',
          FLAGS_enable_pir_in_executor: '0',
          FLAGS_enable_pir: '0',
          FLAGS_use_mkldnn: '0',
          PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK: 'True',
          FLAGS_enable_new_executor: '0',
        },
        stdio: ['ignore', 'pipe', 'pipe'],
      });
    } else {
      // Packaged mode: use bundled .exe
      const exePath = getBackendExePath();
      log.info(`[Backend] Starting packaged backend: ${exePath}`);

      // Create writable temp/output dirs next to the exe (userData)
      const userDataPath = app.getPath('userData');
      const tempDir = path.join(userDataPath, 'temp');
      const outputDir = path.join(userDataPath, 'output');
      const { mkdirSync } = require('fs');
      mkdirSync(tempDir, { recursive: true });
      mkdirSync(outputDir, { recursive: true });

      backendProcess = spawn(exePath, [], {
        cwd: userDataPath,
        env: {
          ...process.env,
          FLAGS_enable_pir_api: '0',
          FLAGS_enable_pir_in_executor: '0',
          FLAGS_enable_pir: '0',
          FLAGS_use_mkldnn: '0',
          PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK: 'True',
          FLAGS_enable_new_executor: '0',
          USERDATA_PATH: userDataPath,
        },
        stdio: ['ignore', 'pipe', 'pipe'],
      });
    }

    if (backendProcess) {
      backendProcess.stdout.on('data', (d) => log.info('[Backend]', d.toString().trim()));
      backendProcess.stderr.on('data', (d) => log.warn('[Backend-ERR]', d.toString().trim()));
      backendProcess.on('close', (code) => log.info(`[Backend] Process exited with code ${code}`));
      backendProcess.on('error', (err) => {
        log.error('[Backend] Failed to start:', err);
        reject(err);
      });
    }

    log.info('[Backend] Waiting for backend to be ready...');
    const ready = await waitForBackend(90000);
    if (ready) {
      log.info('[Backend] ✅ Backend is ready!');
      backendReady = true;
      resolve();
    } else {
      reject(new Error('Backend failed to start within 90 seconds.'));
    }
  });
}

function stopBackend() {
  if (backendProcess && backendProcess.pid) {
    log.info('[Backend] Stopping backend process...');
    treeKill(backendProcess.pid, 'SIGTERM', (err) => {
      if (err) treeKill(backendProcess.pid, 'SIGKILL');
    });
    backendProcess = null;
  }
}

// ============================================================
// SPLASH SCREEN
// ============================================================
function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 480,
    height: 300,
    frame: false,
    transparent: true,
    resizable: false,
    center: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });
  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
  splashWindow.on('closed', () => { splashWindow = null; });
}

// ============================================================
// MAIN WINDOW
// ============================================================
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    frame: false,          // Custom title bar like Discord
    titleBarStyle: 'hidden',
    backgroundColor: '#1e1f22', // Discord-like dark background
    show: false,
    icon: path.join(__dirname, '..', 'assets', 'icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false,  // allow localhost cross-origin for API
    },
  });

  mainWindow.loadURL(getFrontendUrl());

  mainWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
    }
    mainWindow.show();
    setupUpdater();
  });

  mainWindow.on('closed', () => { mainWindow = null; });

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// ============================================================
// IPC HANDLERS — Custom Title Bar Controls
// ============================================================
ipcMain.on('window:minimize', () => mainWindow?.minimize());
ipcMain.on('window:maximize', () => {
  if (!mainWindow) return;
  mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize();
});
ipcMain.on('window:close', () => mainWindow?.close());
ipcMain.handle('window:isMaximized', () => mainWindow?.isMaximized() ?? false);
ipcMain.handle('app:getVersion', () => app.getVersion());

// Update controls
ipcMain.on('updater:install', () => autoUpdater.quitAndInstall());

// ============================================================
// AUTO-UPDATER SETUP
// ============================================================
function setupUpdater() {
  if (isDev) {
    log.info('[Updater] Dev mode — skipping auto-updater.');
    return;
  }

  autoUpdater.autoDownload = true;
  autoUpdater.autoInstallOnAppQuit = true;

  // For private GitHub repos: set token so electron-updater can access releases API
  // Token is bundled via electron-builder's publish config — no need to hardcode here.
  // If repo is private, add GH_TOKEN to updater's requestHeaders:
  autoUpdater.setFeedURL({
    provider: 'github',
    owner: 'LevIlla76',
    repo: 'report_automation_ma',
    private: false,  // set true if repo is private + token needed
  });

  log.info(`[Updater] App version: ${app.getVersion()}`);
  log.info('[Updater] Checking GitHub releases for updates...');

  autoUpdater.on('checking-for-update', () => {
    log.info('[Updater] Checking for updates...');
    mainWindow?.webContents.send('updater:checking');
  });

  autoUpdater.on('update-available', (info) => {
    log.info('[Updater] Update available:', info.version);
    mainWindow?.webContents.send('updater:available', { version: info.version });
  });

  autoUpdater.on('update-not-available', () => {
    log.info('[Updater] App is up to date.');
    mainWindow?.webContents.send('updater:not-available');
  });

  autoUpdater.on('download-progress', (progress) => {
    log.info(`[Updater] Download progress: ${Math.round(progress.percent)}%`);
    mainWindow?.webContents.send('updater:progress', {
      percent: Math.round(progress.percent),
      transferred: progress.transferred,
      total: progress.total,
      speed: progress.bytesPerSecond,
    });
  });

  autoUpdater.on('update-downloaded', (info) => {
    log.info('[Updater] Update downloaded:', info.version);
    mainWindow?.webContents.send('updater:downloaded', { version: info.version });
  });

  autoUpdater.on('error', (err) => {
    log.error('[Updater] Error:', err.message);
    mainWindow?.webContents.send('updater:error', { message: err.message });
  });

  // Check for updates every 4 hours + on startup (after 3s delay)
  setTimeout(() => autoUpdater.checkForUpdates(), 3000);
  setInterval(() => autoUpdater.checkForUpdates(), 4 * 60 * 60 * 1000);
}

// ============================================================
// APP LIFECYCLE
// ============================================================
app.whenReady().then(async () => {
  nativeTheme.themeSource = 'dark';

  // Register app:// protocol to serve static frontend files
  if (!isDev) {
    const frontendDir = path.join(process.resourcesPath, 'frontend_out');
    protocol.handle('app', (request) => {
      // Strip scheme: "app://frontend/index.html" -> "/index.html"
      let urlPath = request.url.replace(/^app:\/\/frontend/, '');
      // Decode URI and strip query/hash
      urlPath = decodeURIComponent(urlPath.split('?')[0].split('#')[0]);
      // Default to index.html
      if (urlPath === '' || urlPath === '/') urlPath = '/index.html';
      const filePath = path.join(frontendDir, urlPath);
      log.info('[Protocol] Serving:', filePath);
      return electronNet.fetch(`file://${filePath}`);
    });
  }

  // Show splash immediately
  createSplashWindow();

  try {
    await startBackend();
  } catch (err) {
    log.error('Fatal: Backend failed to start.', err);
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    dialog.showErrorBox(
      'Backend Failed to Start',
      `The OCR backend could not be started.\n\n${err.message}\n\nPlease check the logs.`
    );
    app.quit();
    return;
  }

  createMainWindow();
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  stopBackend();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
});
