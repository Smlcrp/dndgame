// Dice roller modal — shows a spinning animation then reveals the result.
// Usage:
//   const value = await DiceRoller.roll(20, 'Roll Initiative');
// Fetches the server-rolled value first, animates, resolves on confirm.
const DiceRoller = {
  // Show animation for a value the caller already fetched.
  // Returns Promise<void> that resolves when the user clicks Confirm.
  show(value, label = 'Roll') {
    return new Promise(resolve => {
      const overlay = document.createElement('div');
      overlay.className = 'dice-overlay';
      overlay.innerHTML = `
        <div class="dice-card">
          <div class="dice-label">${label}</div>
          <div class="dice-face spinning" id="dice-face">?</div>
          <div class="dice-result-label" id="dice-result-label"></div>
          <button class="dice-confirm-btn" id="dice-confirm" disabled>Confirm</button>
        </div>
      `;
      document.body.appendChild(overlay);

      const face    = overlay.querySelector('#dice-face');
      const rlabel  = overlay.querySelector('#dice-result-label');
      const confirm = overlay.querySelector('#dice-confirm');

      // Rapid random-number phase for ~1.5s, then reveal result
      let spinning = true;
      const interval = setInterval(() => {
        if (spinning) face.textContent = Math.floor(Math.random() * 20) + 1;
      }, 60);

      setTimeout(() => {
        clearInterval(interval);
        spinning = false;
        face.classList.remove('spinning');
        face.classList.add('landed');
        face.textContent = value;
        rlabel.textContent = value === 20 ? '✦ Natural 20!' : value === 1 ? '✦ Natural 1' : '';
        rlabel.style.color = value === 20 ? 'var(--accent)' : value === 1 ? 'var(--red)' : 'var(--dim)';
        confirm.disabled = false;
      }, 1500);

      confirm.addEventListener('click', () => {
        document.body.removeChild(overlay);
        resolve();
      });
    });
  },

  // Fetch a roll from the server, animate it, return the value on confirm.
  async roll(sides = 20, label = 'Roll') {
    const data = await API.post('/api/roll', { sides });
    await DiceRoller.show(data.value, label);
    return data.value;
  },

  // Fetch initiative from the server (returns total with DEX mod), animate raw d20.
  async rollInitiative() {
    const data = await API.post('/api/roll/initiative');
    await DiceRoller.show(data.value, `Roll Initiative (DEX ${data.modifier >= 0 ? '+' : ''}${data.modifier})`);
    return data.total;  // pass the total to /api/combat/setup
  },
};
