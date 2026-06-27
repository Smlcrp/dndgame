// Manages Ollama process health, CPU fallback, and GPU auto-recovery.
//
// Strategy:
//   1. On init: if Ollama is healthy, stay out of its way (GPU assumed).
//   2. If Ollama process exists but port is dead → CUDA crash → kill, restart
//      in CPU mode (CUDA_VISIBLE_DEVICES=-1 + OLLAMA_NUM_GPU=0).
//   3. Every 30 s, check /api/ps. When the model unloads (idle), attempt GPU
//      restart. On success, notify. On failure, back to CPU + 5 min cooldown.

const { execSync, spawn } = require('child_process');
const http = require('http');
const os   = require('os');
const path = require('path');

const OLLAMA_URL           = 'http://127.0.0.1:11434';
const IDLE_POLL_MS         = 30_000;
const GPU_FAIL_COOLDOWN_MS = 5 * 60_000;

let ollamaProc    = null;   // only set when we spawned it
let currentMode   = null;   // 'gpu' | 'cpu' | 'down'
let onModeChange  = null;
let idleTimer     = null;
let lastGpuFail   = 0;

// ── Low-level helpers ─────────────────────────────────────────────────────────

function httpGet(url, timeoutMs = 3000) {
  return new Promise(resolve => {
    const req = http.get(url, { timeout: timeoutMs }, res => {
      let body = '';
      res.on('data', d => body += d);
      res.on('end', () => resolve({ ok: res.statusCode === 200, body }));
    });
    req.on('error',   () => resolve({ ok: false, body: '' }));
    req.on('timeout', () => { req.destroy(); resolve({ ok: false, body: '' }); });
  });
}

async function isHealthy() {
  return (await httpGet(`${OLLAMA_URL}/api/tags`)).ok;
}

async function isIdle() {
  const r = await httpGet(`${OLLAMA_URL}/api/ps`);
  if (!r.ok) return false;
  try { return (JSON.parse(r.body).models || []).length === 0; }
  catch { return false; }
}

function isProcessRunning() {
  if (process.platform !== 'win32') return false;
  try {
    const out = execSync('tasklist /FI "IMAGENAME eq ollama.exe" /NH', { encoding: 'utf8', timeout: 3000 });
    return out.toLowerCase().includes('ollama.exe');
  } catch { return false; }
}

function killAll() {
  if (process.platform === 'win32') {
    for (const name of ['"ollama app.exe"', 'ollama.exe']) {
      try { execSync(`taskkill /F /IM ${name} /T`, { timeout: 3000 }); } catch {}
    }
  }
  if (ollamaProc && !ollamaProc.killed) {
    try { ollamaProc.kill(); } catch {}
  }
  ollamaProc = null;
}

function findExe() {
  const local = process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local');
  const candidates = [path.join(local, 'Programs', 'Ollama', 'ollama.exe')];
  for (const c of candidates) {
    try { execSync(`"${c}" --version`, { timeout: 2000, stdio: 'ignore' }); return c; } catch {}
  }
  try { execSync('ollama --version', { timeout: 2000, stdio: 'ignore' }); return 'ollama'; } catch {}
  return null;
}

function spawnServe(gpu) {
  const exe = findExe();
  if (!exe) return null;
  const env = { ...process.env };
  if (gpu) {
    delete env.CUDA_VISIBLE_DEVICES;
    delete env.OLLAMA_NUM_GPU;
  } else {
    env.CUDA_VISIBLE_DEVICES = '-1';
    env.OLLAMA_NUM_GPU       = '0';
  }
  const proc = spawn(exe, ['serve'], { env, stdio: 'ignore', windowsHide: true });
  proc.on('error', err => console.error('[ollama] spawn error:', err.message));
  return proc;
}

function waitForHealthy(timeoutMs = 15_000) {
  return new Promise(resolve => {
    const deadline = Date.now() + timeoutMs;
    const check = async () => {
      if (await isHealthy()) return resolve(true);
      if (Date.now() >= deadline) return resolve(false);
      setTimeout(check, 500);
    };
    check();
  });
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ── Mode state ────────────────────────────────────────────────────────────────

function setMode(mode, message) {
  currentMode = mode;
  if (onModeChange) onModeChange(mode, message);
}

// ── GPU recovery loop ─────────────────────────────────────────────────────────

function scheduleIdleCheck() {
  if (idleTimer) clearTimeout(idleTimer);
  idleTimer = setTimeout(tryGPUUpgrade, IDLE_POLL_MS);
}

async function tryGPUUpgrade() {
  if (currentMode !== 'cpu') return;

  // Respect cooldown after a failed GPU attempt
  if (Date.now() - lastGpuFail < GPU_FAIL_COOLDOWN_MS) {
    scheduleIdleCheck();
    return;
  }

  // Only switch when the model has fully unloaded — zero disruption
  if (!await isIdle()) {
    scheduleIdleCheck();
    return;
  }

  // Model is unloaded: safe window to attempt GPU restart
  killAll();
  await sleep(1000);
  ollamaProc = spawnServe(true);
  const ok = await waitForHealthy(15_000);

  if (ok) {
    setMode('gpu', 'GPU mode restored — AI responses are back to full speed.');
    return; // no more retries needed
  }

  // GPU still broken — return to CPU
  killAll();
  await sleep(500);
  ollamaProc = spawnServe(false);
  await waitForHealthy(20_000);
  lastGpuFail = Date.now();
  scheduleIdleCheck();
}

// ── Public API ────────────────────────────────────────────────────────────────

async function initOllama(modeChangeCb) {
  onModeChange = modeChangeCb;

  // Fast path: Ollama already healthy (user started it, GPU running)
  if (await isHealthy()) {
    setMode('gpu', null);
    return;
  }

  if (isProcessRunning()) {
    // Process alive, port dead → CUDA crash
    killAll();
    await sleep(1000);
    ollamaProc = spawnServe(false); // CPU mode
    const ok = await waitForHealthy(20_000);
    if (ok) {
      setMode('cpu', 'GPU driver conflict detected — running in CPU mode (slower responses). Restoring GPU mode when idle…');
      scheduleIdleCheck();
    } else {
      setMode('down', 'Ollama failed to start. Please restart it manually.');
    }
  } else {
    setMode('down', 'Ollama not detected at localhost:11434. Download it at ollama.com to enable the AI Dungeon Master.');
  }
}

function cleanup() {
  if (idleTimer) clearTimeout(idleTimer);
  if (ollamaProc && !ollamaProc.killed) killAll();
}

module.exports = { initOllama, cleanup };
