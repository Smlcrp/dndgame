class GameScene {
  constructor(root, data) {
    this.root = root;
    this.data = data;
    this._state = data.state || {};
    this._busy = false;           // true while awaiting DM or dice
    this._combatTarget = null;    // current combat target name
    this._pendingAction = null;   // {attack?, spell?, feature?, etc} from [ACTION:] event
    this._rollBtn = null;         // active roll button in narration (disabled after use)
  }

  async enter() {
    // Resume mode: fetch session from server (blocking recap call is fine here)
    if (this.data.mode === 'resume') {
      try {
        const d = await API.post('/api/game/resume', { session_name: this.data.sessionName });
        this._state = d.state;
        this._build();
        this._appendNarration(d.narration, 'dm');
        this._updateSidebar();
      } catch (e) {
        this._build();
        this._appendNarration(`Error resuming session: ${e.message}`, 'error');
      }
      return;
    }

    this._build();
    this._updateSidebar();
    // New / next: stream the opening DM narration immediately
    await this._autoStart();
  }

  _build() {
    const char = this._state.character || {};
    this.root.innerHTML = `
      <div class="game-layout">
        <div class="game-header">
          <div class="game-header-title" id="hdr-char">${char.name || 'Adventure'}</div>
          <div class="game-header-loc" id="hdr-loc"></div>
          <div id="hdr-badges"></div>
          <button class="menu-btn" id="btn-save" style="font-size:11px;padding:4px 10px">Save</button>
          <button class="menu-btn" id="btn-menu" style="font-size:11px;padding:4px 10px">Menu</button>
        </div>
        <div class="game-body">
          <div class="game-main">
            <div class="narration" id="narration"></div>
            <div class="input-area">
              <input id="player-input" type="text" placeholder="What do you do? You can also ask questions." autocomplete="off">
              <button class="send-btn" id="send-btn">Send →</button>
            </div>
          </div>
          <div class="sidebar" id="sidebar"></div>
        </div>
      </div>
    `;

    this.root.querySelector('#send-btn').onclick = () => this._send();
    this.root.querySelector('#player-input').addEventListener('keydown', e => {
      if (e.key === 'Enter') this._send();
    });
    this.root.querySelector('#btn-save').onclick = async () => {
      try { await API.post('/api/game/save'); this._flash('Saved.'); } catch (e) { this._flash(e.message, true); }
    };
    this.root.querySelector('#btn-menu').onclick = () => App.scene.switchTo(MainMenuScene);
  }

  // ── Narration helpers ───────────────────────────────────────────────────

  _appendNarration(text, type = 'dm') {
    const narr = document.getElementById('narration');
    if (!narr) return;
    const entry = document.createElement('div');
    entry.className = `narration-entry ${type}`;
    const p = document.createElement('div');
    p.className = 'narration-text';
    p.textContent = text;
    entry.appendChild(p);
    narr.appendChild(entry);
    narr.scrollTop = narr.scrollHeight;
    return entry;
  }

  _appendThinking() {
    const narr = document.getElementById('narration');
    if (!narr) return null;
    const entry = document.createElement('div');
    entry.className = 'narration-entry system';
    entry.innerHTML = `<div class="narration-text thinking-indicator">DM is thinking<span class="thinking-dot">.</span><span class="thinking-dot">.</span><span class="thinking-dot">.</span></div>`;
    narr.appendChild(entry);
    narr.scrollTop = narr.scrollHeight;
    return entry;
  }

  _appendRollButton(label, onConfirm) {
    const narr = document.getElementById('narration');
    if (!narr) return;
    const btn = document.createElement('button');
    btn.className = 'narration-roll-btn';
    btn.textContent = `🎲 ${label}`;
    btn.onclick = async () => {
      if (btn.disabled) return;
      btn.disabled = true;
      await onConfirm();
    };
    narr.appendChild(btn);
    narr.scrollTop = narr.scrollHeight;
    return btn;
  }

  _flash(msg, isError = false) {
    const el = this._appendNarration(msg, isError ? 'error' : 'system');
    if (el) setTimeout(() => el.remove(), 3000);
  }

  _setBusy(busy) {
    this._busy = busy;
    const input = document.getElementById('player-input');
    const btn   = document.getElementById('send-btn');
    if (input) input.disabled = busy;
    if (btn)   btn.disabled   = busy;
  }

  // ── Send player action ──────────────────────────────────────────────────

  async _send() {
    if (this._busy) return;
    const input = document.getElementById('player-input');
    const text  = input.value.trim();
    if (!text) return;
    input.value = '';
    await this._sendStreaming(text, true);
  }

  // Called automatically after new/next game to stream the opening narration.
  async _autoStart() {
    await this._sendStreaming('[START] Begin the adventure. Open with the hook.', false);
  }

  // Core streaming method used by _send() and _autoStart().
  // showPlayerText: whether to display `text` in the narration panel as a player message.
  async _sendStreaming(text, showPlayerText = true) {
    this._setBusy(true);
    if (showPlayerText) this._appendNarration(text, 'player');

    // Create the DM entry upfront with an animated thinking indicator
    const narr    = document.getElementById('narration');
    const dmEntry = document.createElement('div');
    dmEntry.className = 'narration-entry dm';
    const dmText = document.createElement('div');
    dmText.className = 'narration-text';
    dmText.innerHTML = '<span class="thinking-dot">.</span><span class="thinking-dot">.</span><span class="thinking-dot">.</span>';
    dmEntry.appendChild(dmText);
    narr.appendChild(dmEntry);
    narr.scrollTop = narr.scrollHeight;

    // Live tag filter — suppresses [TAG: ...] sequences from the visible stream
    let inTag       = false;
    let tagBuf      = '';
    let visibleText = '';
    let firstToken  = true;

    function filterToken(token) {
      let visible = '';
      for (const ch of token) {
        if (inTag) {
          tagBuf += ch;
          if (ch === ']') { inTag = false; tagBuf = ''; }
        } else if (ch === '[') {
          inTag = true;
          tagBuf = '[';
          // Drop the newline that typically precedes a tag
          if (visible.endsWith('\n'))      visible      = visible.slice(0, -1);
          if (visibleText.endsWith('\n'))  visibleText  = visibleText.slice(0, -1);
        } else {
          visible += ch;
        }
      }
      return visible;
    }

    let events = [];
    try {
      const response = await fetch('/api/action/stream', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ text }),
      });
      if (!response.ok) throw new Error(`Server error ${response.status}`);

      const reader  = response.body.getReader();
      const decoder = new TextDecoder();
      let   buf     = '';

      outer: while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });

        const parts = buf.split('\n\n');
        buf = parts.pop(); // keep the last incomplete chunk

        for (const part of parts) {
          if (!part.startsWith('data: ')) continue;
          const data = JSON.parse(part.slice(6));

          if (data.error) throw new Error(data.error);

          if (data.token) {
            const visible = filterToken(data.token);
            if (visible) {
              if (firstToken) {
                dmText.textContent = '';
                firstToken = false;
              }
              visibleText += visible;
              dmText.textContent = visibleText;
              narr.scrollTop = narr.scrollHeight;
            }
          }

          if (data.done) {
            // Replace live-filtered text with the server's clean narration
            dmText.textContent = data.narration;
            this._state = data.state;
            events = data.events || [];
            this._appendPlayButton(dmEntry, data.narration);
            narr.scrollTop = narr.scrollHeight;
            break outer;
          }
        }
      }

      this._updateSidebar();
      await this._handleEvents(events);
    } catch (e) {
      dmEntry.remove();
      this._appendNarration(`Error: ${e.message}`, 'error');
    } finally {
      this._setBusy(false);
    }
  }

  // ── Narrator ────────────────────────────────────────────────────────────

  _appendPlayButton(entry, text) {
    const btn = document.createElement('button');
    btn.className = 'narration-play-btn';
    btn.textContent = '⏳ Preparing…';
    btn.disabled = true;

    let audioBlob = null;
    let audio     = null;

    // Pre-generate TTS immediately while the player reads the text.
    // By the time they click Play the audio is already in memory.
    fetch('/api/narrate', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ text }),
    })
      .then(r => { if (!r.ok) throw new Error(r.status); return r.blob(); })
      .then(blob => {
        audioBlob = blob;
        btn.textContent = '▶ Play';
        btn.disabled    = false;
      })
      .catch(e => {
        console.error('[narrator] pre-generate failed:', e.message);
        btn.remove();
      });

    btn.onclick = () => {
      if (!audioBlob) return;

      if (audio && !audio.paused) {
        audio.pause();
        audio.currentTime = 0;
        URL.revokeObjectURL(audio.src);
        audio = null;
        btn.textContent = '▶ Play';
        btn.classList.remove('playing');
        return;
      }

      const url = URL.createObjectURL(audioBlob);
      audio = new Audio(url);
      audio.onended = () => {
        btn.textContent = '▶ Play';
        btn.classList.remove('playing');
        URL.revokeObjectURL(url);
        audio = null;
      };
      audio.play();
      btn.textContent = '⏹ Stop';
      btn.classList.add('playing');
    };

    entry.appendChild(btn);
  }

  // ── Event handler ───────────────────────────────────────────────────────

  async _handleEvents(events) {
    for (const ev of events) {
      await this._handleEvent(ev);
    }
  }

  async _handleEvent(ev) {
    switch (ev.type) {
      case 'combat_start':
        await this._startCombat(ev.enemies || []);
        break;

      case 'skill_check':
        await this._handleSkillCheck(ev.skill, ev.dc);
        break;

      case 'action_taken':
        await this._handleActionTaken(ev.action || {});
        break;

      case 'xp_award':
        await this._handleXP(ev.amount);
        break;

      case 'gold_award':
        await this._handleGold(ev.amount);
        break;

      case 'item_award':
        await this._handleItem(ev.name, ev.slot, ev.bonus);
        break;

      case 'beat_complete':
        await this._handleBeat();
        break;

      case 'climax_reached':
        this._appendNarration('⚔  THE CLIMAX — final confrontation!', 'banner');
        await this._handleBeat();
        break;

      case 'break_suggested':
        this._appendNarration('─── Natural session break point ───', 'system');
        break;

      case 'scene_change':
        if (ev.location) {
          this._state.session = this._state.session || {};
          this._state.session.location = ev.location;
          const loc = document.getElementById('hdr-loc');
          if (loc) loc.textContent = ev.location;
        }
        break;
    }
  }

  // ── Combat ──────────────────────────────────────────────────────────────

  async _startCombat(enemies) {
    this._appendNarration('⚔ Combat begins! Roll for initiative.', 'banner');
    this._setBusy(true);
    try {
      const total = await DiceRoller.rollInitiative();
      const result = await API.post('/api/combat/setup', {
        enemies: enemies,
        d20_initiative: total,
      });
      this._state = result.state;
      this._appendNarration(result.display, 'system');
      this._updateSidebar();
      await this._checkEnemyTurn();
    } catch (e) {
      this._appendNarration(`Combat setup error: ${e.message}`, 'error');
    } finally {
      this._setBusy(false);
    }
  }

  async _checkEnemyTurn() {
    const session = this._state.session || {};
    if (!session.in_combat) return;
    const order = session.initiative_order || [];
    const current = order[session.current_turn || 0];
    if (current && !current.is_player && !current.is_companion) {
      await this._doEnemyTurn();
    }
  }

  async _doEnemyTurn() {
    try {
      const result = await API.post('/api/combat/end-turn');
      this._state = result.state;
      if (result.enemy_result && !result.enemy_result.skip) {
        const er = result.enemy_result;
        if (er.hit && er.damage) {
          this._appendNarration(
            `${er.attacker} attacks! Hit for ${er.damage.total} ${er.damage.damage_type || ''} damage.`,
            'system'
          );
        } else if (!er.hit) {
          this._appendNarration(`${er.attacker} attacks and misses.`, 'system');
        }
        if (result.state.session.current_hp <= 0) {
          this._appendNarration('You have fallen to 0 HP!', 'banner');
          await this._handleDeathSave();
          return;
        }
      }
      this._updateSidebar();
    } catch (e) {
      this._appendNarration(`Error: ${e.message}`, 'error');
    }
  }

  async _handleActionTaken(action) {
    if (action.attack) {
      await this._doAttack(action.attack, action.mode);
    } else if (action.spell) {
      await this._doSpell(action.spell, action.slot);
    } else if (action.feature) {
      await this._doFeature(action.feature);
    }
    // dodge/dash/disengage/hide — DM already narrated, no mechanical action
  }

  async _doAttack(weaponName, mode) {
    // Find the current enemy target
    const session = this._state.session || {};
    const enemies = (session.initiative_order || []).filter(c => !c.is_player && c.hp > 0);
    const target = enemies[0];
    if (!target) return;

    this._setBusy(true);
    try {
      const d20 = await DiceRoller.roll(20, `Roll to Attack with ${weaponName}`);
      const result = await API.post('/api/combat/attack', {
        weapon: weaponName,
        target: target.name,
        d20,
      });
      this._state = result.state;

      if (result.hit) {
        const dmg = result.damage;
        const critText = result.critical ? ' CRITICAL HIT!' : '';
        this._appendNarration(
          `${weaponName}: Hit!${critText} ${dmg ? `${dmg.total} damage (${dmg.notation})` : ''}`, 'system'
        );
        if (result.killed) {
          this._appendNarration(`${target.name} is defeated!`, 'system');
          if (!(this._state.session || {}).enemies_alive) {
            await this._endCombat();
            return;
          }
        }
      } else {
        this._appendNarration(`${weaponName}: Miss (rolled ${d20}).`, 'system');
      }

      this._updateSidebar();
      // Show End Turn button
      this._appendRollButton('End Turn', async () => { await this._endPlayerTurn(); });
    } catch (e) {
      this._appendNarration(`Attack error: ${e.message}`, 'error');
    } finally {
      this._setBusy(false);
    }
  }

  async _doSpell(spellName, slotLevel) {
    const session = this._state.session || {};
    const enemies = (session.initiative_order || []).filter(c => !c.is_player && c.hp > 0);
    const target = enemies[0];
    if (!target) return;

    this._setBusy(true);
    try {
      let d20 = null;
      // Attack-roll spells need a d20
      d20 = await DiceRoller.roll(20, `Cast ${spellName}`);
      const result = await API.post('/api/combat/spell', {
        spell: spellName,
        target: target.name,
        slot_level: slotLevel || 1,
        d20,
      });
      this._state = result.state;
      const dmg = result.damage;
      this._appendNarration(
        `${spellName}: ${result.hit ? `Hit! ${dmg ? `${dmg.total} damage` : ''}` : 'Miss.'}`, 'system'
      );
      if (result.killed) {
        this._appendNarration(`${target.name} is defeated!`, 'system');
        if (!(this._state.session || {}).enemies_alive) {
          await this._endCombat();
          return;
        }
      }
      this._updateSidebar();
      this._appendRollButton('End Turn', async () => { await this._endPlayerTurn(); });
    } catch (e) {
      this._appendNarration(`Spell error: ${e.message}`, 'error');
    } finally {
      this._setBusy(false);
    }
  }

  async _doFeature(featureName) {
    this._appendNarration(`Used: ${featureName}`, 'system');
    this._appendRollButton('End Turn', async () => { await this._endPlayerTurn(); });
  }

  async _endPlayerTurn() {
    this._setBusy(true);
    try {
      const result = await API.post('/api/combat/end-turn');
      this._state = result.state;
      this._updateSidebar();
      if (result.enemy_result && !result.enemy_result.skip) {
        const er = result.enemy_result;
        if (er.hit && er.damage) {
          this._appendNarration(`${er.attacker} hits for ${er.damage.total} damage!`, 'system');
          if (this._state.session.current_hp <= 0) {
            this._appendNarration('You fall to 0 HP!', 'banner');
            await this._handleDeathSave();
            return;
          }
        } else if (!er.error && !er.skip) {
          this._appendNarration(`${er.attacker || 'Enemy'} misses.`, 'system');
        }
      }
      const session = this._state.session || {};
      if (!session.enemies_alive) {
        await this._endCombat();
      }
    } catch (e) {
      this._appendNarration(`Error: ${e.message}`, 'error');
    } finally {
      this._setBusy(false);
    }
  }

  async _endCombat() {
    try {
      const result = await API.post('/api/combat/end');
      this._state = result.state;
      this._appendNarration('All enemies defeated! Combat ends.', 'banner');
      if (result.xp_result) {
        await this._handleXPResult(result.xp_result);
      }
      this._updateSidebar();
    } catch (e) {
      this._appendNarration(`Error ending combat: ${e.message}`, 'error');
    }
  }

  async _handleDeathSave() {
    this._setBusy(true);
    try {
      const d20 = await DiceRoller.roll(20, 'Death Saving Throw');
      const result = await API.post('/api/combat/death-save');
      this._state = result.state;
      const ds = result.death_saves || {};
      if (result.outcome === 'revived') {
        this._appendNarration('Natural 20! You revive at 1 HP!', 'banner');
      } else if (result.outcome === 'stable') {
        this._appendNarration('3 successes — you stabilize.', 'system');
      } else if (result.outcome === 'dead') {
        this._appendNarration('3 failures — your character has died.', 'error');
      } else {
        this._appendNarration(
          `Death save: ${result.success ? 'Success' : 'Failure'} (${ds.successes || 0} successes, ${ds.failures || 0} failures)`, 'system'
        );
        // Continue letting player save-roll
        if (result.outcome === 'ongoing') {
          this._appendRollButton('Roll Death Save', async () => { await this._handleDeathSave(); });
        }
      }
      this._updateSidebar();
    } catch (e) {
      this._appendNarration(`Error: ${e.message}`, 'error');
    } finally {
      this._setBusy(false);
    }
  }

  // ── Non-combat events ───────────────────────────────────────────────────

  async _handleSkillCheck(skill, dc) {
    this._setBusy(true);
    const d20 = await DiceRoller.roll(20, `${skill} Check (DC ${dc})`);
    try {
      const result = await API.post('/api/skill-check', { skill, dc, d20 });
      const tier = d20 === 20 ? 'CRITICAL SUCCESS'
        : result.success && (result.total - dc) >= 5 ? 'SOLID SUCCESS'
        : result.success ? 'BARE SUCCESS'
        : (dc - result.total) <= 4 ? 'BARE FAILURE'
        : 'CRITICAL FAILURE';
      const label = result.success ? '✓' : '✗';
      this._appendNarration(
        `${label} ${skill} check: ${result.total} vs DC ${dc} — ${tier}`, 'system'
      );
      // Send result back to DM so it can narrate accordingly (streaming)
      const outcomeText = `[SKILL_RESULT] ${skill} check: d20=${d20}, total=${result.total}, DC=${dc}, margin=${result.total - dc}, tier=${tier}`;
      await this._sendStreaming(outcomeText, false);
    } catch (e) {
      this._appendNarration(`Skill check error: ${e.message}`, 'error');
    } finally {
      this._setBusy(false);
    }
  }

  async _handleXP(amount) {
    try {
      const result = await API.post('/api/award/xp', { amount });
      this._state = result.state;
      this._appendNarration(`+${amount} XP gained (Total: ${result.total_xp} XP)`, 'system');
      if (result.leveled_up) {
        this._appendNarration(`Level up! You are now level ${result.new_level}.`, 'banner');
        await LevelUpScene.show(this._state);
        // Refresh state after level-up
        const fresh = await API.get('/api/game/state');
        this._state = { session: fresh.session, character: fresh.character };
        this._updateSidebar();
      }
    } catch (e) {
      this._appendNarration(`XP error: ${e.message}`, 'error');
    }
  }

  async _handleXPResult(xpResult) {
    if (!xpResult) return;
    this._appendNarration(`+${xpResult.xp_gained} XP gained (Total: ${xpResult.total_xp} XP)`, 'system');
    if (xpResult.leveled_up) {
      this._appendNarration(`Level up! You are now level ${xpResult.new_level}.`, 'banner');
      const fresh = await API.get('/api/game/state');
      this._state = { session: fresh.session, character: fresh.character };
      await LevelUpScene.show(this._state);
      const fresh2 = await API.get('/api/game/state');
      this._state = { session: fresh2.session, character: fresh2.character };
    }
  }

  async _handleGold(amount) {
    try {
      const result = await API.post('/api/award/gold', { amount });
      this._state = result.state;
      this._appendNarration(`+${amount} gp (Total: ${result.new_total} gp)`, 'system');
      this._updateSidebar();
    } catch(e) {}
  }

  async _handleItem(name, slot, bonus) {
    try {
      const result = await API.post('/api/award/item', { name, slot: slot || 'misc', bonus: bonus || 0 });
      this._state = result.state;
      this._appendNarration(`You received: ${name}${bonus ? ` (+${bonus})` : ''}`, 'system');
      this._updateSidebar();
    } catch(e) {}
  }

  async _handleBeat() {
    try {
      const result = await API.post('/api/adventure/beat');
      this._state = result.state;
      if (result.xp > 0) {
        this._appendNarration(`Beat complete! +${result.xp} XP`, 'system');
        if (result.xp_result && result.xp_result.leveled_up) {
          await this._handleXPResult(result.xp_result);
        }
      }
      this._updateSidebar();
    } catch(e) {}
  }

  // ── Sidebar ─────────────────────────────────────────────────────────────

  _updateSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    const s = this._state.session   || {};
    const c = this._state.character || {};

    const maxHp  = c.hp?.max     || 1;
    const curHp  = s.current_hp  ?? c.hp?.current ?? maxHp;
    const tempHp = s.temp_hp     || 0;
    const pct    = Math.max(0, Math.min(100, (curHp / maxHp) * 100));
    const hpClass = pct <= 25 ? 'low' : pct <= 50 ? 'mid' : '';

    const xp       = c.experience || 0;
    const level    = c.level      || 1;
    const nextXp   = [0,300,900,2700,6500,14000,23000,34000,48000,64000,85000,
                       100000,120000,140000,165000,195000,225000,265000,305000,355000][level] || 355000;
    const curXp    = [0,300,900,2700,6500,14000,23000,34000,48000,64000,85000,
                       100000,120000,140000,165000,195000,225000,265000,305000,355000][level-1] || 0;
    const xpPct    = nextXp > curXp ? Math.min(100, ((xp - curXp) / (nextXp - curXp)) * 100) : 100;

    const ac       = (c.armor_class || 10) + (c.magic_armor_bonus || 0);
    const speed    = c.speed   || 30;
    const conds    = s.conditions || [];

    // Feature charges
    const features  = c.feature_uses || {};
    const featureHtml = Object.entries(features).map(([name, data]) => {
      const pips = Array.from({ length: data.max || 0 }, (_, i) =>
        `<div class="pip ${i < (data.current || 0) ? 'filled' : ''}"></div>`).join('');
      return `<div class="feature-row"><span class="feature-name">${name}</span>
        <div class="feature-pips">${pips}</div></div>`;
    }).join('') || '<div style="color:var(--dim);font-size:12px">—</div>';

    // Attacks
    const attacks = (c.attacks || []).map(a =>
      `<div class="attack-row">${a.name}
        <span class="attack-bonus"> +${a.attack_bonus || 0}</span>
        <span class="attack-damage"> ${a.damage || '—'}</span>
      </div>`).join('') || '<div style="color:var(--dim);font-size:12px">—</div>';

    // Combat tracker
    let combatHtml = '';
    if (s.in_combat) {
      const order = s.initiative_order || [];
      combatHtml = `
        <div class="sidebar-section">
          <div class="sidebar-section-title">⚔ Combat — Round ${s.round || 1}</div>
          <div class="combat-tracker">
            ${order.map((c2, i) => `
              <div class="combatant-row ${i === (s.current_turn || 0) ? 'active' : ''} ${c2.hp <= 0 ? 'dead' : ''} ${c2.is_player ? 'player' : ''}">
                <span class="combatant-name">${c2.name}</span>
                <span class="combatant-hp">${c2.hp}/${c2.max_hp}</span>
              </div>`).join('')}
          </div>
        </div>`;
    }

    // Inventory
    const currency = c.currency || {};
    const gp = currency.gp || 0;
    const sp = currency.sp || 0;
    const items = c.magic_items || [];
    const invHtml = `
      <div class="inventory-row">Gold <span class="val">${gp} gp${sp ? ` / ${sp} sp` : ''}</span></div>
      ${items.map(i => `<div class="magic-item">${i.name}${i.bonus ? ` +${i.bonus}` : ''}</div>`).join('')}
    `;

    // Death save display
    const ds = s.death_saves || { successes: 0, failures: 0 };
    const deathHtml = curHp <= 0 && !s.stable
      ? `<div class="sidebar-section" style="border-color:var(--red)">
           <div class="sidebar-section-title" style="color:var(--red)">DEATH SAVES</div>
           <div style="font-size:12px">Successes: ${'●'.repeat(ds.successes)}${'○'.repeat(3 - ds.successes)}</div>
           <div style="font-size:12px">Failures: ${'●'.repeat(ds.failures)}${'○'.repeat(3 - ds.failures)}</div>
         </div>` : '';

    // Inspiration
    const insp = c.inspiration ? `<span class="game-header-badge" style="color:var(--accent)">★ Inspired</span>` : '';

    sidebar.innerHTML = `
      <!-- VITALS -->
      <div class="sidebar-section">
        <div class="sidebar-section-title">Vitals — ${c.name || ''} Lv ${level} ${c.class || ''}</div>
        <div class="hp-numbers">
          <span class="current ${hpClass}">${curHp}</span>
          <span class="sep">/</span>
          <span class="max">${maxHp}</span>
        </div>
        ${tempHp > 0 ? `<div class="hp-temp">+${tempHp} temp HP</div>` : ''}
        <div class="hp-bar-wrap"><div class="hp-bar-fill ${hpClass}" style="width:${pct}%"></div></div>
        <div class="xp-bar-wrap"><div class="xp-bar-fill" style="width:${xpPct}%"></div></div>
        <div class="xp-label">XP ${xp.toLocaleString()} / ${nextXp.toLocaleString()}</div>
        <div class="sidebar-stat-row"><span>AC</span><span>${ac}</span></div>
        <div class="sidebar-stat-row"><span>Speed</span><span>${speed} ft</span></div>
        ${insp}
        ${conds.length ? `<div class="conditions-row">${conds.map(c2 => `<div class="condition-chip">${c2}</div>`).join('')}</div>` : ''}
      </div>
      ${deathHtml}
      ${combatHtml}
      <!-- FEATURES -->
      <div class="sidebar-section">
        <div class="sidebar-section-title">Features</div>
        ${featureHtml}
      </div>
      <!-- ATTACKS -->
      <div class="sidebar-section">
        <div class="sidebar-section-title">Attacks</div>
        ${attacks}
      </div>
      <!-- INVENTORY -->
      <div class="sidebar-section">
        <div class="sidebar-section-title">Inventory</div>
        ${invHtml}
      </div>
    `;

    // Update header
    const loc = document.getElementById('hdr-loc');
    if (loc && s.location) loc.textContent = s.location;
  }

  destroy() {}
}
