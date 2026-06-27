class MainMenuScene {
  constructor(root) { this.root = root; }

  async enter() {
    this.root.innerHTML = `
      <div class="menu-screen">
        <div class="menu-title">⚔ D&D AI DUNGEON MASTER</div>
        <div class="menu-subtitle">Powered by Ollama · Local · Fully Offline</div>
        <div class="menu-card-grid">
          <div class="menu-card" id="btn-new">
            <div class="menu-card-icon">🌅</div>
            <div class="menu-card-title">New Adventure</div>
            <div class="menu-card-desc">Start fresh at level 1 with a brand new story</div>
          </div>
          <div class="menu-card" id="btn-next">
            <div class="menu-card-icon">⚡</div>
            <div class="menu-card-title">Next Adventure</div>
            <div class="menu-card-desc">Keep your character's progress, get a new story</div>
          </div>
          <div class="menu-card" id="btn-resume">
            <div class="menu-card-icon">📖</div>
            <div class="menu-card-title">Resume Session</div>
            <div class="menu-card-desc">Continue exactly where you left off</div>
          </div>
        </div>
        <div id="menu-error" class="menu-error"></div>
      </div>
    `;

    this.root.querySelector('#btn-new').onclick    = () => App.scene.switchTo(CharacterSelectScene, { mode: 'new' });
    this.root.querySelector('#btn-next').onclick   = () => App.scene.switchTo(CharacterSelectScene, { mode: 'next' });
    this.root.querySelector('#btn-resume').onclick = () => App.scene.switchTo(CharacterSelectScene, { mode: 'resume' });
  }

  destroy() {}
}
