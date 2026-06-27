// Thin wrapper around fetch. All routes return {ok, ...data} or {ok: false, error}.
const API = {
  async get(path) {
    const r = await fetch(path);
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'API error');
    return d;
  },
  async post(path, body = {}) {
    const r = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'API error');
    return d;
  },
  async del(path) {
    const r = await fetch(path, { method: 'DELETE' });
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'API error');
    return d;
  },
};
