// Environment Variables (.env) Editor Module
const Env = {
  currentProject: null,
  currentFile: '.env',
  variables: [],

  populateSelect() {
    const sel = document.getElementById('env-project-select');
    if (!sel) return;
    sel.innerHTML = App.projects.map(p => `
      <option value="${p.id}" ${this.currentProject && this.currentProject.id === p.id ? 'selected' : ''}>
        ${p.name}
      </option>
    `).join('');

    if (App.projects.length > 0 && (!this.currentProject || !App.projects.find(p => p.id === this.currentProject.id))) {
      this.loadEnv(App.projects[0].id);
    }
  },

  async loadEnv(projectId) {
    const p = App.projects.find(x => x.id === projectId);
    if (!p) return;
    this.currentProject = p;

    // Load available env files
    const res = await App.api(`/api/env?path=${encodeURIComponent(p.path)}`);
    if (res.ok) {
      const files = res.data.files || [];
      const fileSel = document.getElementById('env-file-select');
      fileSel.innerHTML = files.map(f => `<option value="${f}">${f}</option>`).join('');
      if (files.length > 0) {
        this.loadFile(files[0]);
      } else {
        fileSel.innerHTML = `<option value=".env">.env (Nouveau)</option>`;
        this.renderEmpty();
      }

      // Check comparison with example
      if (res.data.comparison && res.data.comparison.missing_keys.length > 0) {
        App.toast(`Attention : ${res.data.comparison.missing_keys.length} variable(s) du .env.example manquante(s) !`, 'info');
      }
    }
  },

  async loadFile(fileName) {
    this.currentFile = fileName;
    const res = await App.api(`/api/env/file?path=${encodeURIComponent(this.currentProject.path)}&file=${encodeURIComponent(fileName)}`);
    if (res.ok) {
      this.variables = (res.data.items || []).filter(i => i.type === 'variable');
      this.render();
    } else {
      this.renderEmpty();
    }
  },

  renderEmpty() {
    const container = document.getElementById('env-editor-container');
    container.innerHTML = `
      <div style="text-align:center; padding:2rem; color:var(--text-muted);">
        <p style="margin-bottom:0.5rem;">Aucun fichier ${this.currentFile} pour le moment.</p>
        <button class="btn btn-sm btn-primary" onclick="Env.addNewVar()">Créer et ajouter une variable</button>
      </div>`;
  },

  render() {
    const container = document.getElementById('env-editor-container');
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
        <div>
          <h4>Édition de <code>${this.currentFile}</code> (${this.variables.length} variables)</h4>
          <span style="font-size:0.75rem; color:var(--text-muted);">Une copie <code>.bak</code> est automatiquement générée avant chaque sauvegarde.</span>
        </div>
      </div>

      <div style="display:flex; flex-direction:column; gap:0.5rem; max-height:480px; overflow-y:auto;">
        ${this.variables.map((v, idx) => `
          <div style="display:flex; align-items:center; gap:0.5rem; background:var(--bg-primary); padding:0.5rem 0.75rem; border-radius:6px; border:1px solid var(--border-color);">
            <input type="text" class="form-control" style="width:280px; font-family:var(--font-mono); font-weight:600;" value="${v.key}" onchange="Env.updateKey(${idx}, this.value)" placeholder="VARIABLE_NAME">
            <span style="color:var(--text-muted);">=</span>
            <div style="flex:1; display:flex; position:relative;">
              <input type="${v.is_sensitive ? 'password' : 'text'}" id="env-val-${idx}" class="form-control" style="flex:1; font-family:var(--font-mono); font-size:0.85rem;" value="${v.value}" onchange="Env.updateVal(${idx}, this.value)" placeholder="valeur">
              ${v.is_sensitive ? `
                <button type="button" class="btn btn-sm btn-icon" style="position:absolute; right:4px; top:4px; background:transparent; border:none;" onclick="Env.toggleShow(${idx})" title="Afficher/Masquer">👁️</button>
              ` : ''}
            </div>
            <button class="btn btn-sm btn-danger btn-icon" title="Supprimer la variable" onclick="Env.removeVar(${idx})">✕</button>
          </div>
        `).join('')}
      </div>
    `;
  },

  updateKey(idx, key) {
    if (this.variables[idx]) this.variables[idx].key = key.trim();
  },

  updateVal(idx, val) {
    if (this.variables[idx]) this.variables[idx].value = val;
  },

  toggleShow(idx) {
    const input = document.getElementById(`env-val-${idx}`);
    if (input) {
      input.type = input.type === 'password' ? 'text' : 'password';
    }
  },

  addNewVar() {
    this.variables.push({
      type: 'variable',
      key: 'NEW_VARIABLE',
      value: '',
      is_sensitive: false
    });
    this.render();
  },

  removeVar(idx) {
    this.variables.splice(idx, 1);
    this.render();
  },

  async save() {
    if (!this.currentProject) return;
    const dict = {};
    for (const v of this.variables) {
      if (v.key) dict[v.key] = v.value || '';
    }

    App.toast(`Enregistrement de ${this.currentFile}...`, 'info');
    const res = await App.api('/api/env/file', 'POST', {
      path: this.currentProject.path,
      file: this.currentFile,
      variables: dict
    });

    if (res.ok && res.data.success) {
      App.toast(`Fichier ${this.currentFile} enregistré avec succès !`, 'success');
      this.loadFile(this.currentFile);
    } else {
      App.toast(`Erreur d'enregistrement : ${res.data.error}`, 'error');
    }
  }
};
