// Level-up modal — called from GameScene when an XP award triggers a level gain.
// Usage:
//   const choices = await LevelUpScene.show(state);
//   // choices = {hp_roll, subclass?, asi?, spells?}
//   await API.post('/api/levelup', choices);
const LevelUpScene = {
  show(state) {
    return new Promise(resolve => {
      const char  = state.character;
      const level = char.level;
      const cls   = char.class;

      const overlay = document.createElement('div');
      overlay.className = 'levelup-overlay';
      document.body.appendChild(overlay);

      const choices = { hp_roll: 0, subclass: null, asi: null, spells: [] };

      // Step sequence
      const steps = ['hp'];
      // Subclass trigger check
      const subclassTriggers = {
        Artificer:3, Barbarian:3, Bard:3, Cleric:1, Druid:2, Fighter:3,
        Monk:3, Paladin:3, Ranger:3, Rogue:3, Sorcerer:1, Warlock:1, Wizard:2,
      };
      if ((subclassTriggers[cls] || 3) === level && !char.subclass) steps.push('subclass');

      // ASI levels
      const asiLevels = {
        Fighter: [4,6,8,12,14,16,19],
        Rogue:   [4,8,10,12,16,19],
      };
      const defaultAsi = [4,8,12,16,19];
      if ((asiLevels[cls] || defaultAsi).includes(level)) steps.push('asi');

      // Spells (for caster classes)
      const casters = ['Bard','Ranger','Sorcerer','Warlock','Wizard','Cleric','Druid','Paladin','Artificer'];
      if (casters.includes(cls)) steps.push('spells');

      steps.push('done');
      let stepIdx = 0;

      function render(stepName) {
        overlay.innerHTML = '';
        const card = document.createElement('div');
        card.className = 'levelup-card';
        overlay.appendChild(card);

        if (stepName === 'hp') {
          const hitDice = { Fighter:'d10', Barbarian:'d12', Paladin:'d10', Ranger:'d10',
            Monk:'d8', Rogue:'d8', Bard:'d8', Cleric:'d8', Druid:'d8', Warlock:'d8',
            Wizard:'d6', Sorcerer:'d6', Artificer:'d8' };
          const die = hitDice[cls] || 'd8';
          const sides = parseInt(die.replace('d',''));
          const avg = Math.floor(sides / 2) + 1;
          card.innerHTML = `
            <div class="levelup-title">⬆ Level ${level}!</div>
            <div class="levelup-subtitle">${cls} — roll your hit die (${die})</div>
            <div class="levelup-hp-display" id="lu-hp-display">?</div>
            <div style="text-align:center;color:var(--dim);font-size:12px" id="lu-hp-label">Roll your ${die} or take the average</div>
            <div class="levelup-btn-row">
              <button class="menu-btn" id="lu-avg">Take ${avg}</button>
              <button class="menu-btn primary" id="lu-roll">🎲 Roll ${die}</button>
            </div>
          `;
          card.querySelector('#lu-avg').onclick = async () => {
            choices.hp_roll = avg;
            card.querySelector('#lu-hp-display').textContent = avg;
            card.querySelector('#lu-hp-display').style.color = 'var(--green)';
            card.querySelector('#lu-hp-label').textContent = `+${avg} HP (average)`;
            await new Promise(r => setTimeout(r, 800));
            stepIdx++;
            render(steps[stepIdx]);
          };
          card.querySelector('#lu-roll').onclick = async () => {
            const rolled = await DiceRoller.roll(sides, `Roll ${die} for HP`);
            choices.hp_roll = rolled;
            card.querySelector('#lu-hp-display').textContent = rolled;
            card.querySelector('#lu-hp-display').style.color = 'var(--green)';
            card.querySelector('#lu-hp-label').textContent = `+${rolled} HP rolled`;
            await new Promise(r => setTimeout(r, 600));
            stepIdx++;
            render(steps[stepIdx]);
          };
        }

        else if (stepName === 'subclass') {
          const subclasses = {
            Barbarian: ['Berserker','Totem Warrior','Storm Herald','Zealot','Ancestral Guardian'],
            Bard:      ['Lore','Valor','Glamour','Swords','Whispers'],
            Cleric:    ['Life','Light','War','Knowledge','Trickery','Nature','Tempest'],
            Druid:     ['Land','Moon','Dreams','Shepherd','Spores'],
            Fighter:   ['Champion','Battle Master','Eldritch Knight','Arcane Archer','Cavalier','Samurai'],
            Monk:      ['Open Hand','Shadow','Four Elements','Sun Soul','Kensei'],
            Paladin:   ['Devotion','Vengeance','Ancients','Conquest','Redemption'],
            Ranger:    ['Hunter','Beast Master','Gloom Stalker','Horizon Walker','Monster Slayer'],
            Rogue:     ['Thief','Assassin','Arcane Trickster','Inquisitive','Mastermind','Scout','Swashbuckler'],
            Sorcerer:  ['Draconic','Wild Magic','Storm','Shadow','Divine Soul'],
            Warlock:   ['Archfey','Fiend','Great Old One','Celestial','Hexblade'],
            Wizard:    ['Abjuration','Conjuration','Divination','Enchantment','Evocation','Illusion','Necromancy','Transmutation'],
            Artificer: ['Alchemist','Armorer','Artillerist','Battle Smith'],
          };
          const opts = (subclasses[cls] || ['Unknown']).map(s =>
            `<option value="${s}">${s}</option>`).join('');
          card.innerHTML = `
            <div class="levelup-title">Choose Your Subclass</div>
            <div class="levelup-subtitle">${cls} · Level ${level}</div>
            <div class="levelup-section">
              <div class="levelup-section-title">Subclass</div>
              <select class="levelup-select" id="lu-subclass"><option value="">— Pick a subclass —</option>${opts}</select>
            </div>
            <div class="levelup-btn-row">
              <button class="menu-btn primary" id="lu-next" disabled>Next →</button>
            </div>
          `;
          const sel = card.querySelector('#lu-subclass');
          const btn = card.querySelector('#lu-next');
          sel.onchange = () => { btn.disabled = !sel.value; };
          btn.onclick  = () => {
            choices.subclass = sel.value;
            stepIdx++;
            render(steps[stepIdx]);
          };
        }

        else if (stepName === 'asi') {
          card.innerHTML = `
            <div class="levelup-title">Ability Score Improvement</div>
            <div class="levelup-subtitle">Level ${level}</div>
            <div class="levelup-section">
              <div class="levelup-radio-group" id="lu-asi-type">
                <label class="levelup-radio"><input type="radio" name="asi" value="+2"> +2 to one ability</label>
                <label class="levelup-radio"><input type="radio" name="asi" value="+1+1"> +1 to two abilities</label>
                <label class="levelup-radio"><input type="radio" name="asi" value="feat"> Take a feat</label>
              </div>
            </div>
            <div class="levelup-section" id="lu-asi-detail"></div>
            <div class="levelup-btn-row">
              <button class="menu-btn primary" id="lu-next" disabled>Next →</button>
            </div>
          `;
          const abilities = ['strength','dexterity','constitution','intelligence','wisdom','charisma'];
          const abilOpts = abilities.map(a => `<option value="${a}">${a.charAt(0).toUpperCase()+a.slice(1)} (${char.abilities[a]||10})</option>`).join('');
          const feats = ['Alert','Athlete','Actor','Charger','Crossbow Expert','Defensive Duelist',
            'Dual Wielder','Dungeon Delver','Durable','Great Weapon Master','Healer','Inspiring Leader',
            'Lucky','Mage Slayer','Magic Initiate','Martial Adept','Mobile','Observant','Polearm Master',
            'Resilient','Savage Attacker','Sentinel','Sharpshooter','Shield Master','Skilled',
            'Tavern Brawler','Tough','War Caster','Weapon Master'];
          const featOpts = feats.map(f => `<option value="${f}">${f}</option>`).join('');

          const detail = card.querySelector('#lu-asi-detail');
          const btn    = card.querySelector('#lu-next');
          const asiObj = {};

          card.querySelectorAll('input[name=asi]').forEach(radio => {
            radio.onchange = () => {
              const t = radio.value;
              asiObj.type = t;
              if (t === '+2') {
                detail.innerHTML = `<div class="levelup-section-title">Ability</div>
                  <select class="levelup-select" id="lu-a1"><option value="">—</option>${abilOpts}</select>`;
                detail.querySelector('#lu-a1').onchange = e => { asiObj.a1 = e.target.value; btn.disabled = !asiObj.a1; };
              } else if (t === '+1+1') {
                detail.innerHTML = `<div class="levelup-section-title">First ability</div>
                  <select class="levelup-select" id="lu-a1"><option value="">—</option>${abilOpts}</select>
                  <div class="levelup-section-title" style="margin-top:8px">Second ability</div>
                  <select class="levelup-select" id="lu-a2"><option value="">—</option>${abilOpts}</select>`;
                const check = () => { btn.disabled = !(asiObj.a1 && asiObj.a2 && asiObj.a1 !== asiObj.a2); };
                detail.querySelector('#lu-a1').onchange = e => { asiObj.a1 = e.target.value; check(); };
                detail.querySelector('#lu-a2').onchange = e => { asiObj.a2 = e.target.value; check(); };
              } else {
                detail.innerHTML = `<div class="levelup-section-title">Feat</div>
                  <select class="levelup-select" id="lu-feat"><option value="">—</option>${featOpts}</select>`;
                detail.querySelector('#lu-feat').onchange = e => { asiObj.feat = e.target.value; btn.disabled = !asiObj.feat; };
              }
              btn.disabled = true;
            };
          });

          btn.onclick = () => {
            choices.asi = asiObj;
            stepIdx++;
            render(steps[stepIdx]);
          };
        }

        else if (stepName === 'spells') {
          const knownSpells = (char.spellcasting?.spells_known || []);
          const prepareOnly = ['Cleric','Druid','Paladin','Artificer'].includes(cls);

          if (prepareOnly) {
            card.innerHTML = `
              <div class="levelup-title">Spellcasting</div>
              <div class="levelup-subtitle">${cls} prepares spells from the full list after each long rest. No spell selection needed at level-up.</div>
              <div class="levelup-btn-row"><button class="menu-btn primary" id="lu-next">Next →</button></div>
            `;
            card.querySelector('#lu-next').onclick = () => { stepIdx++; render(steps[stepIdx]); };
          } else {
            // Very simplified spell list — show text input to type spell names
            card.innerHTML = `
              <div class="levelup-title">Learn New Spells</div>
              <div class="levelup-subtitle">${cls} — level ${level}</div>
              <div class="levelup-section">
                <div class="levelup-section-title">Known spells: ${knownSpells.join(', ') || 'none'}</div>
                <div style="font-size:12px;color:var(--dim);margin-bottom:8px">Enter new spell names (one per line)</div>
                <textarea id="lu-spells" style="width:100%;height:80px;background:var(--input-bg);
                  color:var(--fg);border:1px solid var(--border);border-radius:4px;
                  padding:8px;font-size:12px;resize:none;font-family:inherit"></textarea>
              </div>
              <div class="levelup-btn-row">
                <button class="menu-btn" id="lu-skip">Skip</button>
                <button class="menu-btn primary" id="lu-next">Next →</button>
              </div>
            `;
            card.querySelector('#lu-skip').onclick = () => { stepIdx++; render(steps[stepIdx]); };
            card.querySelector('#lu-next').onclick = () => {
              const raw = card.querySelector('#lu-spells').value;
              choices.spells = raw.split('\n').map(s => s.trim()).filter(Boolean);
              stepIdx++;
              render(steps[stepIdx]);
            };
          }
        }

        else if (stepName === 'done') {
          card.innerHTML = `
            <div class="levelup-title">Level ${level} — Ready!</div>
            <div class="levelup-subtitle">Your changes have been saved.</div>
            <div class="levelup-btn-row">
              <button class="menu-btn primary" id="lu-finish">Continue →</button>
            </div>
          `;
          card.querySelector('#lu-finish').onclick = async () => {
            try {
              await API.post('/api/levelup', choices);
            } catch (e) { /* ignore */ }
            document.body.removeChild(overlay);
            resolve(choices);
          };
        }
      }

      render(steps[0]);
    });
  },
};
