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
        <div class="char-list">${listHtml}</div>
        ${!isResume ? '<div style="font-size:12px;color:var(--dim);margin-bottom:12px;">To create a character, run: python views/desktop/character_builder/character_builder_app.py</div>' : ''}
        <div class="menu-btn-row">
          <button class="menu-btn" id="btn-back">← Back</button>
          <button class="menu-btn primary" id="btn-select" disabled>
            ${isResume ? 'Resume →' : 'Select →'}
          </button>
        </div>
        <div id="menu-error" class="menu-error"></div>
      </div>
    `;

    this.root.querySelectorAll('.char-item').forEach(el => {
      el.onclick = () => {
        this.root.querySelectorAll('.char-item').forEach(e => e.classList.remove('selected'));
        el.classList.add('selected');
        this.selected = el.dataset.name;
        this.root.querySelector('#btn-select').disabled = false;
      };
    });

    this.root.querySelector('#btn-back').onclick   = () => App.scene.switchTo(MainMenuScene);
    this.root.querySelector('#btn-select').onclick = () => this._proceed();
  }

  _proceed() {
    if (!this.selected) return;
    if (this.mode === 'resume') {
      App.scene.switchTo(GameScene, { mode: 'resume', sessionName: this.selected });
    } else {
      App.scene.switchTo(PresetScene, { mode: this.mode, charName: this.selected });
    }
  }

  destroy() {}
}
