// Projects Management Module
const Projects = {
  projects: [],
  scannedProjects: [],

  async loadProjects() {
    const res = await App.api('/api/projects');
    if (res.ok) {
      this.projects = res.data;
      this.render();
      App.loadStats();
    }
  },

  render() {
    const container = document.getElementById('projects-list');
    const search = (document.getElementById('project-search').value || '').toLowerCase();
    const filterStack = document.getElementById('project-filter-stack').value;

    const filtered = this.projects.filter(p => {
      const matchSearch = p.name.toLowerCase().includes(search) ||
                          (p.framework || '').toLowerCase().includes(search) ||
                          p.path.toLowerCase().includes(search);
      const matchStack = !filterStack || (p.stack || []).includes(filterStack) || p.framework === filterStack;
      return matchSearch && matchStack;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-muted);">
          <p style="font-size: 1.5rem; margin-bottom: 0.5rem;">📂</p>
          <p>${I18N.t('no_projects')}</p>
          <button class="btn btn-sm btn-primary" style="margin-top: 1rem;" onclick="Projects.openScanModal()">
            ${I18N.t('scan_home_btn')}
          </button>
        </div>`;
      return;
    }

    container.innerHTML = filtered.map(p => {
      const isRunning = p.runtime && p.runtime.status === 'running';
      const statusClass = isRunning ? 'running' : '';
      const dotColor = isRunning ? 'green' : (p.runtime && p.runtime.status === 'failed' ? 'red' : 'gray');
      const statusText = isRunning ? `${I18N.t('status_running')} (${p.runtime.mode.toUpperCase()} - PID ${p.runtime.pid})` : I18N.t('status_stopped');
      const uptime = isRunning && p.runtime.uptime_seconds ? ` • ${Math.floor(p.runtime.uptime_seconds / 60)}m ${p.runtime.uptime_seconds % 60}s` : '';

      return `
        <div class="project-card ${statusClass}" id="card-${p.id}">
          <div class="project-header">
            <div class="project-title-area">
              <div class="project-title">
                <span class="status-dot ${dotColor}"></span>
                ${p.name}
              </div>
              <div class="project-path" title="${p.path}">${p.path}</div>
            </div>
            <div style="display: flex; gap: 0.25rem;">
              <button class="btn btn-sm btn-icon" title="${I18N.t('btn_open_folder')}" onclick="Projects.openFolder('${p.path}')">📂</button>
              <button class="btn btn-sm btn-icon" title="${I18N.t('btn_open_editor')}" onclick="Projects.openEditor('${p.path}')">💻</button>
              <button class="btn btn-sm btn-icon" title="${I18N.t('btn_edit')}" onclick="Projects.openEditModal('${p.id}')">✏️</button>
              <button class="btn btn-sm btn-icon" title="${I18N.t('btn_delete')}" onclick="Projects.deleteProject('${p.id}')">🗑️</button>
            </div>
          </div>

          <div class="stack-tags">
            <span class="tag framework">${p.framework || 'Custom'}</span>
            ${(p.stack || []).map(s => `<span class="tag">${s}</span>`).join('')}
            ${p.port ? `<span class="tag port">Port :${p.port}</span>` : ''}
            ${p.is_git ? `<span class="tag git">Git (${p.git_branch || 'main'})</span>` : ''}
          </div>

          <div class="project-runtime-info">
            <span style="display: flex; align-items: center; gap: 0.4rem;">
              <span class="status-dot ${dotColor}"></span>
              <strong>${statusText}</strong>${uptime}
            </span>
            ${isRunning && p.port ? `<a href="http://localhost:${p.port}" target="_blank" class="btn btn-sm" style="text-decoration:none;">${I18N.t('open_port', { port: p.port })}</a>` : ''}
          </div>

          <div class="project-actions">
            ${isRunning ? `
              <button class="btn btn-sm btn-danger" onclick="Projects.stop('${p.id}')">${I18N.t('btn_stop')}</button>
              <button class="btn btn-sm" onclick="Projects.restart('${p.id}')">${I18N.t('btn_restart')}</button>
            ` : `
              ${p.dev_cmd ? `<button class="btn btn-sm btn-primary" onclick="Projects.start('${p.id}', 'dev')">${I18N.t('btn_start_dev')}</button>` : ''}
              ${p.prod_cmd ? `<button class="btn btn-sm btn-blue" onclick="Projects.start('${p.id}', 'prod')">${I18N.t('btn_start_prod')}</button>` : ''}
              ${p.test_cmd ? `<button class="btn btn-sm" onclick="Projects.start('${p.id}', 'test')">${I18N.t('btn_test')}</button>` : ''}
            `}
            <button class="btn btn-sm" style="margin-left: auto;" onclick="Projects.openTerminal('${p.id}')">${I18N.t('btn_logs')}</button>
          </div>
        </div>
      `;
    }).join('');
  },

  filter() {
    this.render();
  },

  async start(id, mode) {
    App.toast(`Démarrage de ${id} (${mode})...`, 'info');
    const res = await App.api(`/api/projects/${id}/start`, 'POST', { mode });
    if (res.ok && res.data.success) {
      App.toast(`Serveur ${id} lancé avec succès !`, 'success');
      this.loadProjects();
    } else {
      App.toast(`Erreur : ${res.data.message || res.data.error}`, 'error');
    }
  },

  async stop(id) {
    App.toast(`Arrêt de ${id}...`, 'info');
    const res = await App.api(`/api/projects/${id}/stop`, 'POST', {});
    if (res.ok) {
      App.toast(`Serveur ${id} arrêté.`, 'info');
      this.loadProjects();
    }
  },

  async restart(id) {
    App.toast(`Redémarrage de ${id}...`, 'info');
    const res = await App.api(`/api/projects/${id}/restart`, 'POST', {});
    if (res.ok && res.data.success) {
      App.toast(`Serveur ${id} redémarré avec succès !`, 'success');
      this.loadProjects();
    }
  },

  openTerminal(id) {
    App.navigate('terminal');
    Logs.switchProject(id);
  },

  async openFolder(path) {
    await App.api('/api/system/open-folder', 'POST', { path });
  },

  async openEditor(path) {
    await App.api('/api/system/open-editor', 'POST', { path });
    App.toast('Ouverture dans VS Code demandée...', 'info');
  },

  async deleteProject(id) {
    if (!confirm(`Voulez-vous retirer le projet '${id}' du tableau de bord ? (Aucun fichier ne sera supprimé)`)) return;
    const res = await App.api(`/api/projects/${id}`, 'DELETE');
    if (res.ok) {
      App.toast('Projet retiré', 'info');
      this.loadProjects();
    }
  },

  openAddModal() {
    document.getElementById('modal-project-title').textContent = 'Nouveau Projet';
    document.getElementById('proj-id').value = '';
    document.getElementById('proj-name').value = '';
    document.getElementById('proj-path').value = '';
    document.getElementById('proj-dev-cmd').value = '';
    document.getElementById('proj-prod-cmd').value = '';
    document.getElementById('proj-test-cmd').value = '';
    document.getElementById('proj-port').value = '3000';
    document.getElementById('modal-project').classList.add('open');
  },

  openEditModal(id) {
    const p = this.projects.find(x => x.id === id);
    if (!p) return;
    document.getElementById('modal-project-title').textContent = `Modifier '${p.name}'`;
    document.getElementById('proj-id').value = p.id;
    document.getElementById('proj-name').value = p.name;
    document.getElementById('proj-path').value = p.path;
    document.getElementById('proj-dev-cmd').value = p.dev_cmd || '';
    document.getElementById('proj-prod-cmd').value = p.prod_cmd || '';
    document.getElementById('proj-test-cmd').value = p.test_cmd || '';
    document.getElementById('proj-port').value = p.port || 3000;
    document.getElementById('modal-project').classList.add('open');
  },

  closeModal() {
    document.getElementById('modal-project').classList.remove('open');
  },

  async inspectPath(path) {
    if (!path) return;
    const res = await App.api(`/api/projects/scan?path=${encodeURIComponent(path)}`);
    if (res.ok && res.data.projects.length > 0) {
      const p = res.data.projects[0];
      if (!document.getElementById('proj-name').value) document.getElementById('proj-name').value = p.name;
      if (!document.getElementById('proj-dev-cmd').value) document.getElementById('proj-dev-cmd').value = p.dev_cmd;
      if (!document.getElementById('proj-prod-cmd').value) document.getElementById('proj-prod-cmd').value = p.prod_cmd;
      if (!document.getElementById('proj-test-cmd').value) document.getElementById('proj-test-cmd').value = p.test_cmd;
      if (p.port) document.getElementById('proj-port').value = p.port;
    }
  },

  async saveModal() {
    const payload = {
      id: document.getElementById('proj-id').value,
      name: document.getElementById('proj-name').value.trim(),
      path: document.getElementById('proj-path').value.trim(),
      dev_cmd: document.getElementById('proj-dev-cmd').value.trim(),
      prod_cmd: document.getElementById('proj-prod-cmd').value.trim(),
      test_cmd: document.getElementById('proj-test-cmd').value.trim(),
      port: parseInt(document.getElementById('proj-port').value) || 3000
    };
    if (!payload.name || !payload.path) {
      App.toast('Nom et chemin sont obligatoires', 'error');
      return;
    }
    const res = await App.api('/api/projects', 'POST', payload);
    if (res.ok) {
      App.toast('Projet enregistré avec succès', 'success');
      this.closeModal();
      this.loadProjects();
    }
  },

  // Scan Modal
  openScanModal() {
    document.getElementById('modal-scan').classList.add('open');
    this.executeScan();
  },

  closeScanModal() {
    document.getElementById('modal-scan').classList.remove('open');
  },

  async executeScan() {
    const dir = document.getElementById('scan-input-dir').value.trim();
    const resultsContainer = document.getElementById('scan-results');
    resultsContainer.innerHTML = `<p style="color:var(--text-muted); padding:1rem; text-align:center;">Scan en cours dans ${dir}...</p>`;

    const res = await App.api(`/api/projects/scan?path=${encodeURIComponent(dir)}`);
    if (res.ok) {
      this.scannedProjects = res.data.projects;
      if (this.scannedProjects.length === 0) {
        resultsContainer.innerHTML = `<p style="color:var(--text-muted); padding:1rem; text-align:center;">Aucun projet détecté dans ce répertoire.</p>`;
        return;
      }
      resultsContainer.innerHTML = this.scannedProjects.map((p, idx) => `
        <label style="display:flex; align-items:center; gap:0.75rem; background:var(--bg-card); padding:0.6rem 0.8rem; border-radius:6px; border:1px solid var(--border-color); cursor:pointer;">
          <input type="checkbox" id="scan-chk-${idx}" checked>
          <div style="flex:1;">
            <div style="font-weight:600; font-size:0.9rem;">${p.name} <span class="tag framework" style="font-size:0.7rem;">${p.framework}</span></div>
            <div style="font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">${p.path}</div>
          </div>
          <span style="font-size:0.75rem; color:var(--accent-blue-bright);">${p.dev_cmd || 'Pas de cmd'}</span>
        </label>
      `).join('');
    }
  },

  async importSelectedScanned() {
    const selected = [];
    this.scannedProjects.forEach((p, idx) => {
      const chk = document.getElementById(`scan-chk-${idx}`);
      if (chk && chk.checked) selected.push(p);
    });

    if (selected.length === 0) {
      App.toast('Aucun projet sélectionné', 'info');
      return;
    }

    const res = await App.api('/api/projects/import-scanned', 'POST', { projects: selected });
    if (res.ok) {
      App.toast(`${selected.length} projet(s) importé(s) !`, 'success');
      this.closeScanModal();
      this.loadProjects();
    }
  }
};
