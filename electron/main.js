const { app, BrowserWindow, shell, dialog } = require('electron');
const path  = require('path');
const http  = require('http');
const { spawn, execFile } = require('child_process');
const ollama = require('./ollama');

const FLASK_PORT = 5000;
const PING_URL   = `http://localhost:${FLASK_PORT}/api/ping`;
const GAME_URL   = `http://localhost:${FLASK_PORT}/`;

let flaskProcess = null;
let mainWindow   = null;

// ── Flask process ─────────────────────────────────────────────────────────────

function launchFlask() {
  // In development: run python run_server.py from the project root.
  // In packaged build: run the PyInstaller-bundled executable from extraResources.
  const isPackaged = app.isPackaged;
  if (isPackaged) {
    const serverDir = path.join(process.resourcesPath, 'server');
    const exe = process.platform === 'win32' ? 'run_server.exe' : 'run_server';
    flaskProcess = execFile(path.join(serverDir, exe), { cwd: serverDir });
  } else {
    const projectRoot = path.join(__dirname, '..');
    const pythonExe = process.env.PYTHON_EXE || 'python';
    flaskProcess = spawn(pythonExe, ['run_server.py'], {
      cwd: projectRoot,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    flaskProcess.stdout.on('data', d => process.stdout.write(`[flask] ${d}`));
    flaskProcess.stderr.on('data', d => process.stderr.write(`[flask] ${d}`));
  }

  flaskProcess.on('error', err => {
    dialog.showErrorBox('Server Error', `Failed to start game server:\n${err.message}`);
  });
  flaskProcess.on('exit', (code, signal) => {
    if (code !== 0 && code !== null) {
      console.error(`Flask exited with code ${code} (signal ${signal})`);
    }
  });
}

// ── Poll until Flask responds ─────────────────────────────────────────────────

function waitForFlask(retries = 60, delayMs = 500) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const check = () => {
      http.get(PING_URL, res => {
        if (res.statusCode === 200) return resolve();
        tryAgain();
      }).on('error', () => tryAgain());
    };
    const tryAgain = () => {
      if (++attempts >= retries) return reject(new Error('Flask did not start in time.'));
      setTimeout(check, delayMs);
    };
    check();
  });
}

// ── Ollama banner ─────────────────────────────────────────────────────────────
// Injected into the renderer. Keeps a single persistent banner element for
// 'cpu' and 'down' states; shows a brief toast on GPU restore; clears on 'gpu'.

function setOllamaBanner(win, mode, message) {
  if (!win || win.isDestroyed()) return;

  const safeMsg = JSON.stringify(message || '');

  const js = `
    (() => {
      const BANNER_ID = '__ollama_banner__';
      let el = document.getElementById(BANNER_ID);

      if (${JSON.stringify(mode)} === 'gpu') {
        if (el) el.remove();
        if (${safeMsg}) {
          // Brief success toast — auto-dismisses after 5 s
          const toast = document.createElement('div');
          toast.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#0d2a0d;color:#4caf50;border-bottom:1px solid #4caf50;text-align:center;padding:8px 16px;font-size:13px;z-index:9999;font-family:Segoe UI,sans-serif';
          toast.textContent = '✓ ' + ${safeMsg};
          document.body.prepend(toast);
          setTimeout(() => toast.remove(), 5000);
        }
        return;
      }

      if (!el) {
        el = document.createElement('div');
        el.id = BANNER_ID;
        document.body.prepend(el);
      }

      const isCpu = ${JSON.stringify(mode)} === 'cpu';
      el.style.cssText = isCpu
        ? 'position:fixed;top:0;left:0;right:0;background:#1e1800;color:#c8a951;border-bottom:1px solid #c8a951;text-align:center;padding:8px 16px;font-size:13px;z-index:9999;font-family:Segoe UI,sans-serif'
        : 'position:fixed;top:0;left:0;right:0;background:#2a1a1a;color:#e05050;border-bottom:1px solid #e05050;text-align:center;padding:8px 16px;font-size:13px;z-index:9999;font-family:Segoe UI,sans-serif';
      el.textContent = (isCpu ? '⚡ ' : '⚠ ') + ${safeMsg};
    })();
  `;

  win.webContents.executeJavaScript(js).catch(() => {});
}

// ── Window ────────────────────────────────────────────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width:  1280,
    height: 800,
    minWidth:  900,
    minHeight: 600,
    title: 'D&D AI Dungeon Master',
    backgroundColor: '#1a1a2e',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    show: false,
  });

  mainWindow.setMenuBarVisibility(false);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    ollama.initOllama((mode, message) => setOllamaBanner(mainWindow, mode, message));
  });

  mainWindow.on('closed', () => { mainWindow = null; });

  // Open links targeting _blank in the system browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.loadURL(GAME_URL);
}

// ── App lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  launchFlask();

  try {
    await waitForFlask();
  } catch (err) {
    dialog.showErrorBox('Startup Error', err.message);
    app.quit();
    return;
  }

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  ollama.cleanup();
  if (flaskProcess && !flaskProcess.killed) {
    flaskProcess.kill();
  }
});
