// Scene manager and app boot.
class SceneManager {
  constructor() {
    this.current = null;
    this.root = document.getElementById('app');
  }

  async switchTo(SceneClass, data = {}) {
    if (this.current && this.current.destroy) this.current.destroy();
    this.root.innerHTML = '';
    this.current = new SceneClass(this.root, data);
    await this.current.enter();
  }
}

const App = {
  scene: new SceneManager(),
};

window.addEventListener('DOMContentLoaded', async () => {
  // Start at the main menu
  await App.scene.switchTo(MainMenuScene);
});
