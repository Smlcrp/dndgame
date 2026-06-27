const { app, BrowserWindow, shell, dialog } = require('electron');
const path  = require('path');
const http  = require('http');
const { spawn, execFile } = require('child_process');

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
    flaskProcess = spawn('python', ['run_server.py'], {
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

function waitForFlask(retries = 30, delayMs = 500) {
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

// ── Ollama check (dev only) ───────────────────────────────────────────────────

function checkOllamaAsync(win) {
  http.get('http://localhost:11434/api/tags', res => {
    // Ollama is running
  }).on('error', () => {
    // Ollama not detected — show a gentle notice in the game window
    if (win && !win.isDestroyed()) {
      win.webContents.executeJavaScript(`
        if (typeof App !== 'undefined') {
          const notice = document.createElement('div');
          notice.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#2a1a1a;color:#e05050;text-align:center;padding:8px;font-size:13px;z-index:9999;font-family:Segoe UI,sans-serif';
          notice.innerHTML = '⚠ Ollama not detected at localhost:11434. <a href="#" onclick="require(\\'electron\\').shell.openExternal(\\'https://ollama.com\\');return false" style="color:#c8a951">Download Ollama</a> to enable the AI Dungeon Master.';
          document.body.prepend(notice);
        }
      `).catch(() => {});
    }
  });
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
    checkOllamaAsync(mainWindow);
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
  if (flaskProcess && !flaskProcess.killed) {
    flaskProcess.kill();
  }
});
