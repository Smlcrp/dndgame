class GameScene {
  constructor(root, data) {
    this.root = root;
    this.data = data;
    this._state = data.state || {};
    this._busy = false;
    this._combatTarget = null;
    this._pendingAction = null;
    this._rollBtn = null;
    this._devUnlocked = false;
    this._attackOpts = null; // cached variant list, set on combat start
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
          <button class="menu-btn dev-btn" id="btn-dev" style="font-size:11px;padding:4px 10px">DEV</button>
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
    this.root.querySelector('#btn-dev').onclick  = () => this._openDev();
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
            // NARRATOR DISABLED: this._appendPlayButton(dmEntry, data.narration);
            narr.scrollTop = narr.scrollHeight;
            if (data.ollama_mode === 'cpu') this._showCpuBanner();
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

  // ── Ollama mode banner ───────────────────────────────────────────────────

  _showCpuBanner() {
    if (document.getElementById('cpu-mode-banner')) return; // already shown
    const banner = document.createElement('div');
    banner.id = 'cpu-mode-banner';
    banner.className = 'ollama-cpu-banner';
    banner.textContent = '⚠ Running on CPU — responses will be slower (GPU unavailable)';
    document.body.appendChild(banner);
  }

  // ── Narrator (DISABLED — revisit in a later stage) ──────────────────────
  //
  // _appendPlayButton(entry, text) {
  //   const btn = document.createElement('button');
  //   btn.className = 'narration-play-btn';
  //   btn.textContent = '⏳ Preparing…';
  //   btn.disabled = true;
  //   let audioBlob = null;
  //   let audio     = null;
  //   fetch('/api/narrate', {
  //     method:  'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body:    JSON.stringify({ text }),
  //   })
  //     .then(r => { if (!r.ok) throw new Error(r.status); return r.blob(); })
  //     .then(blob => { audioBlob = blob; btn.textContent = '▶ Play'; btn.disabled = false; })
  //     .catch(e => { console.error('[narrator] pre-generate failed:', e.message); btn.remove(); });
  //   btn.onclick = () => {
  //     if (!audioBlob) return;
  //     if (audio && !audio.paused) {
  //       audio.pause(); audio.currentTime = 0; URL.revokeObjectURL(audio.src);
  //       audio = null; btn.textContent = '▶ Play'; btn.classList.remove('playing'); return;
  //     }
  //     const url = URL.createObjectURL(audioBlob);
  //     audio = new Audio(url);
  //     audio.onended = () => { btn.textContent = '▶ Play'; btn.classList.remove('playing'); URL.revokeObjectURL(url); audio = null; };
  //     audio.play(); btn.textContent = '⏹ Stop'; btn.classList.add('playing');
  //   };
  //   entry.appendChild(btn);
  // }

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

      case 'companion_join':
        this._appendNarration(`${ev.name} has joined the party!`, 'banner');
        this._updateSidebar();
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
      // Pre-fetch attack variants so sidebar and Actions panel are ready
      try {
        const optResult = await API.get('/api/combat/attack-options');
        this._attackOpts = optResult.options || null;
      } catch (_) { this._attackOpts = null; }
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
      const label = mode === 'melee_2h' ? `${weaponName} (two-handed)`
                  : mode === 'thrown'   ? `${weaponName} (thrown)`
                  : mode === 'offhand'  ? `${weaponName} (off-hand)`
                  : weaponName;
      const d20 = await DiceRoller.roll(20, `Roll to Attack — ${label}`);
      const result = await API.post('/api/combat/attack', {
        weapon: weaponName,
        target: target.name,
        d20,
        mode: mode || 'melee',
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
    this._attackOpts = null; // clear variant cache on combat end
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

  _mod(score) {
    return Math.floor(((score || 10) - 10) / 2);
  }
  _modStr(score) {
    const m = this._mod(score);
    return (m >= 0 ? '+' : '') + m;
  }

  _updateSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    const s = this._state.session   || {};
    const c = this._state.character || {};

    // ── Vitals ──
    const maxHp   = c.hp?.max  || 1;
    const curHp   = s.current_hp  ?? c.hp?.current ?? maxHp;
    const tempHp  = s.temp_hp || 0;
    const pct     = Math.max(0, Math.min(100, (curHp / maxHp) * 100));
    const hpClass = pct <= 25 ? 'low' : pct <= 50 ? 'mid' : '';
    const xp      = c.experience || 0;
    const level   = c.level || 1;
    const XP_TABLE = [0,300,900,2700,6500,14000,23000,34000,48000,64000,85000,
                      100000,120000,140000,165000,195000,225000,265000,305000,355000];
    const nextXp  = XP_TABLE[level] || 355000;
    const curXp   = XP_TABLE[level-1] || 0;
    const xpPct   = nextXp > curXp ? Math.min(100, ((xp - curXp) / (nextXp - curXp)) * 100) : 100;
    const ac      = (c.armor_class || 10) + (c.magic_armor_bonus || 0);
    const speed   = c.speed || 30;
    const conds   = s.conditions || [];
    const insp    = c.inspiration ? `<span style="color:var(--accent);font-size:11px">★ Inspired</span>` : '';
    const pb      = level < 5 ? 2 : level < 9 ? 3 : level < 13 ? 4 : level < 17 ? 5 : 6;

    // ── Abilities ──
    const ABILITY_KEYS = ['STR','DEX','CON','INT','WIS','CHA'];
    const ABILITY_LABELS = {STR:'STR',DEX:'DEX',CON:'CON',INT:'INT',WIS:'WIS',CHA:'CHA'};
    const abs = c.abilities || {};
    const abilitiesHtml = ABILITY_KEYS.map(k => {
      const score = abs[k] || 10;
      return `<div class="ability-box">
        <div class="ability-label">${ABILITY_LABELS[k]}</div>
        <div class="ability-mod">${this._modStr(score)}</div>
        <div class="ability-score">${score}</div>
      </div>`;
    }).join('');

    // ── Saving throws ──
    const SAVE_KEYS = {STR:'Strength',DEX:'Dexterity',CON:'Constitution',INT:'Intelligence',WIS:'Wisdom',CHA:'Charisma'};
    const saveProfs = c.saving_throw_proficiencies || [];
    const savesHtml = ABILITY_KEYS.map(k => {
      const prof   = saveProfs.includes(SAVE_KEYS[k]);
      const total  = this._mod(abs[k] || 10) + (prof ? pb : 0);
      const sign   = total >= 0 ? '+' : '';
      return `<div class="save-row">
        <span class="save-pip ${prof ? 'prof' : ''}"></span>
        <span class="save-name">${k}</span>
        <span class="save-val">${sign}${total}</span>
      </div>`;
    }).join('');

    // ── Skills ──
    const SKILLS = [
      ['Acrobatics','DEX'],['Animal Handling','WIS'],['Arcana','INT'],
      ['Athletics','STR'],['Deception','CHA'],['History','INT'],
      ['Insight','WIS'],['Intimidation','CHA'],['Investigation','INT'],
      ['Medicine','WIS'],['Nature','INT'],['Perception','WIS'],
      ['Performance','CHA'],['Persuasion','CHA'],['Religion','INT'],
      ['Sleight of Hand','DEX'],['Stealth','DEX'],['Survival','WIS'],
    ];
    const skillProfs = c.skill_proficiencies || [];
    const skillsHtml = SKILLS.map(([name, abil]) => {
      const prof  = skillProfs.includes(name);
      const total = this._mod(abs[abil] || 10) + (prof ? pb : 0);
      const sign  = total >= 0 ? '+' : '';
      return `<div class="save-row">
        <span class="save-pip ${prof ? 'prof' : ''}"></span>
        <span class="save-name" style="font-size:10px">${name}</span>
        <span class="save-val">${sign}${total}</span>
      </div>`;
    }).join('');

    // ── Spellcasting ──
    let spellHtml = '';
    const sc = c.spellcasting || {};
    if (sc.enabled) {
      const slots  = sc.slots_per_level || {};
      const used   = s.spell_slots_used || {};
      const slotRows = Object.entries(slots).filter(([, max]) => max > 0).map(([lvl, max]) => {
        const rem = Math.max(0, max - (used[lvl] || 0));
        const pips = Array.from({length: max}, (_, i) =>
          `<div class="pip ${i < rem ? 'filled' : ''}"></div>`).join('');
        return `<div class="feature-row"><span class="feature-name">Lv${lvl}</span><div class="feature-pips">${pips}</div></div>`;
      }).join('');
      spellHtml = `
        <div class="sidebar-section">
          <div class="sidebar-section-title">Spellcasting</div>
          <div class="sidebar-stat-row"><span>Spell DC</span><span>${sc.spell_dc || '—'}</span></div>
          <div class="sidebar-stat-row"><span>Attack</span><span>${sc.spell_attack_bonus >= 0 ? '+' : ''}${sc.spell_attack_bonus ?? '—'}</span></div>
          ${slotRows || '<div style="color:var(--dim);font-size:11px">No slots</div>'}
        </div>`;
    }

    // ── Feature charges ──
    const features = c.feature_uses || {};
    const featureHtml = Object.entries(features).map(([name, data]) => {
      const pips = Array.from({length: data.max || 0}, (_, i) =>
        `<div class="pip ${i < (data.current || 0) ? 'filled' : ''}"></div>`).join('');
      return `<div class="feature-row"><span class="feature-name">${name}</span><div class="feature-pips">${pips}</div></div>`;
    }).join('') || '<div style="color:var(--dim);font-size:11px">—</div>';

    // ── Attacks (sidebar shows variants via cached options, falls back to flat list) ──
    const _rawAtks = this._attackOpts || (c.attacks || []).map(a => ({
      label: a.name, weapon: a.name,
      bonus: a.attack_bonus || 0, damage: a.damage || '—', mode: 'melee',
    }));
    const attacksHtml = _rawAtks.map(a =>
      `<div class="attack-row">${a.label}<span class="attack-bonus"> +${a.bonus ?? 0}</span><span class="attack-damage"> ${a.damage || '—'}</span></div>`
    ).join('') || '<div style="color:var(--dim);font-size:11px">—</div>';

    // ── Combat tracker ──
    let combatHtml = '';
    if (s.in_combat) {
      const order = s.initiative_order || [];
      combatHtml = `
        <div class="sidebar-section">
          <div class="sidebar-section-title">⚔ Combat — Round ${s.round || 1}
            <button class="actions-btn" id="btn-actions">⚔ Actions</button>
          </div>
          <div class="combat-tracker">
            ${order.map((c2, i) => `
              <div class="combatant-row ${i === (s.current_turn||0) ? 'active' : ''} ${c2.hp <= 0 ? 'dead' : ''} ${c2.is_player ? 'player' : ''}">
                <span class="combatant-name">${c2.name}</span>
                <span class="combatant-hp">${c2.hp}/${c2.max_hp}</span>
              </div>`).join('')}
          </div>
        </div>`;
    }

    // ── Inventory ──
    const currency = c.currency || {};
    const gp = currency.gp || 0;
    const items = c.magic_items || [];
    const invHtml = `
      <div class="inventory-row">Gold <span class="val">${gp} gp</span></div>
      ${items.map(it => `<div class="magic-item">${it.name}${it.bonus ? ` +${it.bonus}` : ''}</div>`).join('')}`;

    // ── Death saves ──
    const ds = s.death_saves || {successes:0,failures:0};
    const deathHtml = curHp <= 0 && !s.stable
      ? `<div class="sidebar-section" style="border-color:var(--red)">
           <div class="sidebar-section-title" style="color:var(--red)">DEATH SAVES</div>
           <div style="font-size:12px">Successes: ${'●'.repeat(ds.successes)}${'○'.repeat(3-ds.successes)}</div>
           <div style="font-size:12px">Failures:  ${'●'.repeat(ds.failures)}${'○'.repeat(3-ds.failures)}</div>
         </div>` : '';

    // ── Party (companions) ──
    const companions = (s.companions || []).filter(cp => cp.status !== 'dead');
    const partyHtml = companions.length ? `
      <div class="sidebar-section">
        <div class="sidebar-section-title">Party</div>
        ${companions.map(cp => `
          <div class="sidebar-stat-row">
            <span>${cp.name} (${cp.class || '?'})</span>
            <span>${cp.current_hp ?? cp.hp ?? '?'}/${cp.max_hp ?? '?'}</span>
          </div>`).join('')}
      </div>` : '';

    sidebar.innerHTML = `
      <div class="sidebar-section">
        <div class="sidebar-section-title">${c.name || ''} · Lv ${level} ${c.class || ''}</div>
        <div class="hp-numbers">
          <span class="current ${hpClass}">${curHp}</span><span class="sep">/</span><span class="max">${maxHp}</span>
          ${tempHp > 0 ? `<span style="color:var(--blue);margin-left:6px">+${tempHp} tmp</span>` : ''}
        </div>
        <div class="hp-bar-wrap"><div class="hp-bar-fill ${hpClass}" style="width:${pct}%"></div></div>
        <div class="xp-bar-wrap"><div class="xp-bar-fill" style="width:${xpPct}%"></div></div>
        <div class="xp-label">XP ${xp.toLocaleString()} / ${nextXp.toLocaleString()}</div>
        <div class="sidebar-stat-row"><span>AC</span><span>${ac}</span></div>
        <div class="sidebar-stat-row"><span>Speed</span><span>${speed} ft</span></div>
        <div class="sidebar-stat-row"><span>Prof. Bonus</span><span>+${pb}</span></div>
        ${insp}
        ${conds.length ? `<div class="conditions-row">${conds.map(cn => `<div class="condition-chip">${cn}</div>`).join('')}</div>` : ''}
      </div>
      ${deathHtml}
      ${combatHtml}
      <div class="sidebar-section">
        <div class="sidebar-section-title">Abilities</div>
        <div class="ability-grid">${abilitiesHtml}</div>
      </div>
      <div class="sidebar-section">
        <div class="sidebar-section-title">Saving Throws</div>
        ${savesHtml}
      </div>
      <div class="sidebar-section">
        <div class="sidebar-section-title">Skills</div>
        ${skillsHtml}
      </div>
      ${spellHtml}
      <div class="sidebar-section">
        <div class="sidebar-section-title">Features</div>
        ${featureHtml}
      </div>
      <div class="sidebar-section">
        <div class="sidebar-section-title">Attacks</div>
        ${attacksHtml}
      </div>
      <div class="sidebar-section">
        <div class="sidebar-section-title">Inventory</div>
        ${invHtml}
      </div>
      ${partyHtml}
    `;

    // Update header location + story mode badge
    const loc = document.getElementById('hdr-loc');
    if (loc && s.location) loc.textContent = s.location;
    const badges = document.getElementById('hdr-badges');
    if (badges) {
      const existing = badges.querySelector('.story-mode-badge');
      if (s.story_mode && !existing) {
        const b = document.createElement('span');
        b.className = 'game-header-badge story-mode-badge';
        b.textContent = '◆ STORY MODE';
        badges.appendChild(b);
      } else if (!s.story_mode && existing) {
        existing.remove();
      }
    }

    // Wire up actions button if present
    const actBtn = document.getElementById('btn-actions');
    if (actBtn) actBtn.onclick = () => { this._openActions(); };
  }

  // ── DEV panel ───────────────────────────────────────────────────────────

  _openDev() {
    if (!this._devUnlocked) {
      this._devPasswordPrompt();
    } else {
      this._showDevPanel();
    }
  }

  _devPasswordPrompt() {
    const overlay = document.createElement('div');
    overlay.className = 'dev-overlay';
    overlay.innerHTML = `
      <div class="dev-panel">
        <div class="dev-title">DEV Access</div>
        <input class="dev-input" id="dev-pw" type="password" placeholder="Password" autocomplete="off">
        <div class="dev-error" id="dev-pw-err" style="color:var(--red);font-size:11px;min-height:16px"></div>
        <div style="display:flex;gap:8px;justify-content:flex-end">
          <button class="dev-action-btn" id="dev-pw-ok">Unlock</button>
          <button class="dev-action-btn" id="dev-pw-cancel">Cancel</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    const pw  = overlay.querySelector('#dev-pw');
    const err = overlay.querySelector('#dev-pw-err');
    pw.focus();
    overlay.querySelector('#dev-pw-ok').onclick = () => {
      if (pw.value === '0922') {
        this._devUnlocked = true;
        overlay.remove();
        this._showDevPanel();
      } else {
        err.textContent = 'Incorrect password.';
        pw.value = '';
        pw.focus();
      }
    };
    overlay.querySelector('#dev-pw-cancel').onclick = () => overlay.remove();
    pw.addEventListener('keydown', e => { if (e.key === 'Enter') overlay.querySelector('#dev-pw-ok').click(); });
  }

  _showDevPanel() {
    if (document.getElementById('dev-floating-panel')) return;
    const s = this._state.session || {};
    const c = this._state.character || {};
    const XP_TABLE = [0,300,900,2700,6500,14000,23000,34000,48000,64000,85000,
                      100000,120000,140000,165000,195000,225000,265000,305000,355000];
    const CONDITIONS = ['Blinded','Charmed','Deafened','Frightened','Grappled',
      'Incapacitated','Invisible','Paralyzed','Petrified','Poisoned','Prone',
      'Restrained','Stunned','Unconscious','Exhaustion'];

    const panel = document.createElement('div');
    panel.id = 'dev-floating-panel';
    panel.className = 'dev-floating-panel';
    panel.innerHTML = `
      <div class="dev-title" style="display:flex;justify-content:space-between;align-items:center">
        <span>⚙ DEV Panel</span>
        <button class="dev-close-btn" id="dev-close">✕</button>
      </div>

      <div class="dev-row">
        <label>Award XP</label>
        <input class="dev-input" id="dev-xp" type="number" value="300" min="0" style="width:70px">
        <button class="dev-action-btn" id="dev-xp-btn">+XP</button>
      </div>

      <div class="dev-row" style="flex-wrap:wrap;gap:4px">
        <label style="width:100%">Jump to level</label>
        ${[2,3,4,5,6,7,8,9,10].map(lv =>
          `<button class="dev-action-btn" data-lv="${lv}">Lv${lv}</button>`
        ).join('')}
      </div>

      <div class="dev-row">
        <label>Set HP</label>
        <input class="dev-input" id="dev-hp" type="number" value="${s.current_hp ?? c.hp?.max ?? 10}" min="0" style="width:70px">
        <button class="dev-action-btn" id="dev-hp-btn">Set</button>
      </div>

      <div class="dev-row">
        <label>Add condition</label>
        <select class="dev-input" id="dev-cond" style="flex:1">
          ${CONDITIONS.map(cd => `<option>${cd}</option>`).join('')}
        </select>
        <button class="dev-action-btn" id="dev-cond-btn">Add</button>
      </div>

      <div class="dev-row" style="gap:6px">
        <button class="dev-action-btn" id="dev-short-rest">Short Rest</button>
        <button class="dev-action-btn" id="dev-long-rest">Long Rest</button>
        <button class="dev-action-btn" id="dev-spawn">Spawn Combat</button>
      </div>

      <div class="dev-row">
        <button class="dev-action-btn" id="dev-story-toggle" style="flex:1">
          ${s.story_mode ? 'Exit Story Mode' : 'Enter Story Mode'}
        </button>
      </div>

      <div class="dev-status" id="dev-status"></div>
    `;
    document.body.appendChild(panel);

    const status = panel.querySelector('#dev-status');
    const flash  = msg => { status.textContent = msg; setTimeout(() => status.textContent = '', 2500); };

    panel.querySelector('#dev-close').onclick = () => panel.remove();

    panel.querySelector('#dev-xp-btn').onclick = async () => {
      const amt = parseInt(panel.querySelector('#dev-xp').value) || 0;
      try {
        const r = await API.post('/api/award/xp', { amount: amt });
        this._state = r.state;
        this._updateSidebar();
        flash(`+${amt} XP`);
        if (r.leveled_up) {
          flash(`Leveled up to ${r.new_level}!`);
          const fr = await API.get('/api/game/state');
          this._state = fr; this._updateSidebar();
          await LevelUpScene.show(this._state);
        }
      } catch(e) { flash(`Error: ${e.message}`); }
    };

    panel.querySelectorAll('[data-lv]').forEach(btn => {
      btn.onclick = async () => {
        const targetLv = parseInt(btn.dataset.lv);
        const xpNeeded = XP_TABLE[targetLv - 1] || 0;
        const cur = (this._state.character || {}).experience || 0;
        if (xpNeeded <= cur) { flash(`Already at Lv${targetLv}+`); return; }
        try {
          const r = await API.post('/api/award/xp', { amount: xpNeeded - cur });
          this._state = r.state; this._updateSidebar();
          if (r.leveled_up) {
            const fr = await API.get('/api/game/state');
            this._state = fr; this._updateSidebar();
            await LevelUpScene.show(this._state);
          }
        } catch(e) { flash(`Error: ${e.message}`); }
      };
    });

    panel.querySelector('#dev-hp-btn').onclick = async () => {
      const hp = parseInt(panel.querySelector('#dev-hp').value) || 0;
      try {
        const r = await API.post('/api/dev/set-hp', { hp });
        this._state = r.state; this._updateSidebar(); flash(`HP set to ${hp}`);
      } catch(e) { flash(`Error: ${e.message}`); }
    };

    panel.querySelector('#dev-cond-btn').onclick = async () => {
      const cond = panel.querySelector('#dev-cond').value;
      try {
        const r = await API.post('/api/dev/add-condition', { condition: cond });
        this._state = r.state; this._updateSidebar(); flash(`Added: ${cond}`);
      } catch(e) { flash(`Error: ${e.message}`); }
    };

    panel.querySelector('#dev-short-rest').onclick = async () => {
      try {
        const r = await API.post('/api/rest/short', { dice: 1 });
        this._state = r.state; this._updateSidebar(); flash('Short rest taken');
      } catch(e) { flash(`Error: ${e.message}`); }
    };

    panel.querySelector('#dev-long-rest').onclick = async () => {
      try {
        const r = await API.post('/api/rest/long');
        this._state = r.state; this._updateSidebar(); flash('Long rest taken');
      } catch(e) { flash(`Error: ${e.message}`); }
    };

    panel.querySelector('#dev-spawn').onclick = async () => {
      try {
        const r = await API.post('/api/dev/spawn-combat');
        this._state = r.state;
        this._appendNarration('⚔ Test combat spawned — 1 Goblin!', 'banner');
        this._updateSidebar();
      } catch(e) { flash(`Error: ${e.message}`); }
    };

    panel.querySelector('#dev-story-toggle').onclick = async () => {
      const cur = (this._state.session || {}).story_mode;
      try {
        const r = await API.post('/api/story-mode', { enter: !cur });
        this._state = r.state;
        this._updateSidebar();
        const btn = panel.querySelector('#dev-story-toggle');
        btn.textContent = r.story_mode ? 'Exit Story Mode' : 'Enter Story Mode';
        flash(r.story_mode ? 'Story Mode ON' : 'Story Mode OFF');
        if (r.story_mode) {
          this._appendNarration('◆ Story Mode active — game mechanics suspended.', 'banner');
          await this._sendStreaming('[STORY_MODE_START] Begin a vivid narrative scene for this character in the current setting.', false);
        }
      } catch(e) { flash(`Error: ${e.message}`); }
    };
  }

  // ── Actions reference panel ──────────────────────────────────────────────

  async _openActions() {
    if (document.getElementById('actions-panel')) return;
    const c   = this._state.character || {};
    const s   = this._state.session   || {};
    const sc  = c.spellcasting || {};
    const features = c.feature_uses || {};
    const condSet = new Set(s.conditions || []);
    const incap   = condSet.has('Incapacitated') || condSet.has('Paralyzed') ||
                    condSet.has('Stunned') || condSet.has('Unconscious');

    // Fetch expanded attack options (variants) from server
    let attackOpts = (c.attacks || []).map(a => ({
      label: `${a.name} +${a.attack_bonus||0} / ${a.damage||'—'}`,
      weapon: a.name, mode: 'melee',
    }));
    try {
      const r = await API.get('/api/combat/attack-options');
      if (r.options && r.options.length) attackOpts = r.options;
    } catch (_) { /* fall back to flat list */ }

    const spellRow = sc.enabled
      ? `<div class="action-row">✦ Cast a Spell (use slots below)</div>`
      : '';

    const featureRows = Object.entries(features).map(([name, data]) => {
      const avail = (data.current || 0) > 0;
      return `<div class="action-row ${avail ? '' : 'unavail'}">${name} ${avail ? `(${data.current}/${data.max})` : '(0 remaining)'}</div>`;
    }).join('');

    const offhandOpts = attackOpts.filter(o => o.mode === 'offhand');
    const mainOpts    = attackOpts.filter(o => o.mode !== 'offhand');

    const mkWeaponRow = (opt) => {
      const dmgStr = opt.damage ? ` / ${opt.damage}` : '';
      const bonStr = opt.bonus !== undefined ? ` +${opt.bonus}` : '';
      const noteStr = opt.note ? `<div style="font-size:10px;color:var(--dim)">${opt.note}</div>` : '';
      const cls = incap ? 'action-row unavail' : 'action-row atk-opt-btn';
      const incapNote = incap ? '<span class="action-reason">Incapacitated</span>' : '';
      return `<div class="${cls}" data-weapon="${opt.weapon}" data-mode="${opt.mode}">${opt.label}${bonStr}${dmgStr}${incapNote}${noteStr}</div>`;
    };

    const weaponRows  = mainOpts.map(mkWeaponRow).join('') || '<div class="action-row unavail">No weapons</div>';
    const bonusRows   = offhandOpts.map(mkWeaponRow).join('');

    const panel = document.createElement('div');
    panel.id = 'actions-panel';
    panel.className = 'actions-panel';
    panel.innerHTML = `
      <div class="dev-title" style="display:flex;justify-content:space-between">
        <span>⚔ Actions</span>
        <button class="dev-close-btn" id="actions-close">✕</button>
      </div>
      <div class="actions-section-title">ACTIONS — click to attack</div>
      ${weaponRows}
      ${spellRow}
      <div class="action-row">Dodge · Dash · Disengage · Hide (type in chat)</div>
      ${featureRows ? `<div class="actions-section-title">FEATURES</div>${featureRows}` : ''}
      ${bonusRows ? `<div class="actions-section-title">BONUS ACTIONS</div>${bonusRows}` : ''}
    `;
    document.body.appendChild(panel);
    panel.querySelector('#actions-close').onclick = () => panel.remove();

    // Wire clickable attack rows
    panel.querySelectorAll('.atk-opt-btn').forEach(el => {
      el.style.cursor = 'pointer';
      el.onclick = async () => {
        panel.remove();
        await this._doAttack(el.dataset.weapon, el.dataset.mode);
      };
    });
  }

  destroy() {}
}
