class PresetScene {
  constructor(root, data) {
    this.root = root;
    this.mode = data.mode;
    this.charName = data.charName;
    this.preset = 'Quest'; // default
  }

  async enter() {
    this.root.innerHTML = `
      <div class="menu-screen">
        <div class="menu-title">Choose Your Adventure Length</div>
        <div class="menu-subtitle">Playing as <strong style="color:var(--accent)">${this.charName}</strong></div>
        <div class="menu-card-grid">
          <div class="menu-card" data-preset="One Shot">
            <div class="menu-card-icon">⚡</div>
            <div class="menu-card-title">One Shot</div>
            <div class="menu-card-desc">~1–2 hours · Straight to the action · Perfect for a quick session</div>
          </div>
          <div class="menu-card selected" data-preset="Quest">
            <div class="menu-card-icon">⚔</div>
            <div class="menu-card-title">Quest</div>
            <div class="menu-card-desc">~3–4 hours · Three acts · The classic adventure structure</div>
          </div>
          <div class="menu-card" data-preset="Epic">
            <div class="menu-card-icon">🐉</div>
            <div class="menu-card-title">Epic</div>
            <div class="menu-card-desc">~5–8 hours · Five acts · Deep story across multiple sessions</div>
          </div>
        </div>
        <div class="menu-btn-row">
          <button class="menu-btn" id="btn-back">← Back</button>
          <button class="menu-btn primary" id="btn-begin">Begin Adventure →</button>
        </div>
        <div id="menu-error" class="menu-error"></div>
      </div>
    `;

    this.root.querySelectorAll('.menu-card').forEach(card => {
      card.onclick = () => {
        this.root.querySelectorAll('.menu-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        this.preset = card.dataset.preset;
      };
    });

    this.root.querySelector('#btn-back').onclick  = () =>
      App.scene.switchTo(CharacterSelectScene, { mode: this.mode });
    this.root.querySelector('#btn-begin').onclick = () => this._begin();
  }

  async _begin() {
    const btn = this.root.querySelector('#btn-begin');
    btn.disabled = true;
    btn.textContent = 'Starting…';
    try {
      const endpoint = this.mode === 'next' ? '/api/game/next' : '/api/game/new';
      const data = await API.post(endpoint, { char_name: this.charName, preset: this.preset });
      await App.scene.switchTo(GameScene, { state: data.state, mode: this.mode });
    } catch (e) {
      this.root.querySelector('#menu-error').textContent = e.message;
      btn.disabled = false;
      btn.textContent = 'Begin Adventure →';
    }
  }

  destroy() {}
}
