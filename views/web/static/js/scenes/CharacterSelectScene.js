class CharacterSelectScene {
  constructor(root, data) {
    this.root = root;
    this.mode = data.mode; // 'new' | 'next' | 'resume'
    this.selected = null;
    this.sessions = [];
    this.chars = [];
  }

  async enter() {
    const [cData, sData] = await Promise.all([
      API.get('/api/characters'),
      API.get('/api/sessions'),
    ]);
    this.chars    = cData.characters;
    this.sessions = sData.sessions;
    this._build();
  }

  _build() {
    const isResume = this.mode === 'resume';
    const items = isResume ? this.sessions : this.chars;
    const title = { new: 'Choose a Character', next: 'Choose a Character', resume: 'Resume a Session' }[this.mode];
    const hint  = isResume
      ? 'Pick a saved session to continue.'
      : this.mode === 'new'
        ? 'Choose a character to adventure with. They will reset to level 1.'
        : 'Choose a character. Their progress carries forward into the new story.';

    const listHtml = items.length
      ? items.map(n => `
          <div class="char-item" data-name="${n}">
            <span class="char-item-name">${n}</span>
          </div>`).join('')
      : `<div class="char-empty">${isResume ? 'No saved sessions found.' : 'No characters found.'}</div>`;

    this.root.innerHTML = `
      <div class="menu-screen">
        <div class="menu-title">${title}</div>
        <div class="menu-subtitle">${hint}</div>
        <div class="char-list" id="char-list">${listHtml}</div>
        ${!isResume ? `
          <div style="display:flex;gap:10px;align-items:center;margin-bottom:12px;font-size:12px">
            <span style="color:var(--dim)">Or:</span>
            <button class="menu-btn" id="btn-ddb" style="font-size:11px;padding:4px 10px">⬇ Import from D&D Beyond</button>
            <span style="color:var(--dim)">· Builder: <code>python views/desktop/character_builder/character_builder_app.py</code></span>
          </div>` : ''}
        <div class="menu-btn-row">
          <button class="menu-btn" id="btn-back">← Back</button>
          <button class="menu-btn primary" id="btn-select" disabled>
            ${isResume ? 'Resume →' : 'Select →'}
          </button>
        </div>
        <div id="menu-error" class="menu-error"></div>
      </div>
    `;

    this._wireList();

    this.root.querySelector('#btn-back').onclick   = () => App.scene.switchTo(MainMenuScene);
    this.root.querySelector('#btn-select').onclick = () => this._proceed();
    const ddbBtn = this.root.querySelector('#btn-ddb');
    if (ddbBtn) ddbBtn.onclick = () => this._openDdbImport();
  }

  _wireList() {
    this.root.querySelectorAll('.char-item').forEach(el => {
      el.onclick = () => {
        this.root.querySelectorAll('.char-item').forEach(e => e.classList.remove('selected'));
        el.classList.add('selected');
        this.selected = el.dataset.name;
        this.root.querySelector('#btn-select').disabled = false;
      };
    });
  }

  _proceed() {
    if (!this.selected) return;
    if (this.mode === 'resume') {
      App.scene.switchTo(GameScene, { mode: 'resume', sessionName: this.selected });
    } else {
      App.scene.switchTo(PresetScene, { mode: this.mode, charName: this.selected });
    }
  }

  _openDdbImport() {
    const overlay = document.createElement('div');
    overlay.className = 'dev-overlay';
    overlay.innerHTML = `
      <div class="dev-panel" style="width:360px">
        <div class="dev-title">⬇ Import from D&D Beyond</div>
        <p style="font-size:11px;color:var(--dim);margin-bottom:12px">
          Paste a D&D Beyond character URL or ID. Public characters need no token.
          For private characters, paste your CobaltSession cookie value.
        </p>
        <div class="dev-row" style="flex-direction:column;align-items:stretch;gap:4px">
          <label style="font-size:11px;color:var(--dim)">Character URL or ID</label>
          <input class="dev-input" id="ddb-url" type="text" placeholder="https://www.dndbeyond.com/characters/12345678">
        </div>
        <div class="dev-row" style="flex-direction:column;align-items:stretch;gap:4px;margin-top:8px">
          <label style="font-size:11px;color:var(--dim)">CobaltSession token (optional, private characters only)</label>
          <input class="dev-input" id="ddb-token" type="password" placeholder="Leave blank for public characters">
        </div>
        <div class="dev-status" id="ddb-status" style="min-height:18px;margin:10px 0"></div>
        <div style="display:flex;gap:8px;justify-content:flex-end">
          <button class="dev-action-btn" id="ddb-import-btn">Import</button>
          <button class="dev-action-btn" id="ddb-cancel-btn">Cancel</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);

    const status = overlay.querySelector('#ddb-status');
    overlay.querySelector('#ddb-cancel-btn').onclick = () => overlay.remove();
    overlay.querySelector('#ddb-import-btn').onclick = async () => {
      const url   = overlay.querySelector('#ddb-url').value.trim();
      const token = overlay.querySelector('#ddb-token').value.trim();
      if (!url) { status.style.color = 'var(--red)'; status.textContent = 'URL is required.'; return; }
      status.style.color = 'var(--dim)';
      status.textContent = 'Importing…';
      overlay.querySelector('#ddb-import-btn').disabled = true;
      try {
        const r = await API.post('/api/characters/import-ddb', { url, token });
        status.style.color = 'var(--green)';
        status.textContent = `✓ Imported "${r.name}"`;
        // Refresh the character list
        const fresh = await API.get('/api/characters');
        this.chars = fresh.characters;
        const list = this.root.querySelector('#char-list');
        if (list) {
          list.innerHTML = this.chars.map(n =>
            `<div class="char-item" data-name="${n}"><span class="char-item-name">${n}</span></div>`
          ).join('');
          this._wireList();
        }
        setTimeout(() => overlay.remove(), 1500);
      } catch(e) {
        status.style.color = 'var(--red)';
        status.textContent = `Error: ${e.message}`;
        overlay.querySelector('#ddb-import-btn').disabled = false;
      }
    };
  }

  destroy() {}
}
