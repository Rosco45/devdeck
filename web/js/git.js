// Git Manager Module
const Git = {
  currentProject: null,
  gitInfo: null,

  populateSelect() {
    const sel = document.getElementById('git-project-select');
    if (!sel) return;
    const gitProjects = App.projects.filter(p => p.is_git);
    sel.innerHTML = gitProjects.map(p => `
      <option value="${p.id}" ${this.currentProject && this.currentProject.id === p.id ? 'selected' : ''}>
        ${p.name} (${p.git_branch || 'git'})
      </option>
    `).join('');

    if (gitProjects.length > 0 && (!this.currentProject || !gitProjects.find(p => p.id === this.currentProject.id))) {
      this.loadInfo(gitProjects[0].id);
    }
  },

  async loadInfo(projectId) {
    const p = App.projects.find(x => x.id === projectId);
    if (!p) return;
    this.currentProject = p;

    const content = document.getElementById('git-content');
    content.innerHTML = `<p style="color:var(--text-muted); text-align:center; padding:2rem;">Lecture des informations Git...</p>`;

    const res = await App.api(`/api/git/info?path=${encodeURIComponent(p.path)}`);
    if (res.ok) {
      this.gitInfo = res.data;
      this.render();
      // Load GitHub section if applicable
      if (this.gitInfo.remote_url && this.gitInfo.remote_url.includes('github.com')) {
        GitHub.load(this.gitInfo.remote_url);
      }
    } else {
      content.innerHTML = `<p style="color:var(--accent-red-bright); padding:1rem;">Erreur de lecture Git : ${res.data.error}</p>`;
    }
  },

  refresh() {
    if (this.currentProject) this.loadInfo(this.currentProject.id);
  },

  render() {
    const content = document.getElementById('git-content');
    const info = this.gitInfo;
    if (!info || !info.is_git) {
      content.innerHTML = `<div class="data-table-card" style="padding:1.5rem; text-align:center; color:var(--text-muted);">Ce projet n'est pas un dépôt Git.</div>`;
      return;
    }

    const modifiedCount = (info.modified || []).length;
    const stagedCount = (info.staged || []).length;
    const untrackedCount = (info.untracked || []).length;
    const isClean = info.clean;

    content.innerHTML = `
      <!-- Git Top Card -->
      <div class="data-table-card" style="padding: 1.25rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
          <div>
            <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.25rem;">
              <span style="font-size:1.2rem;">🌿</span>
              <strong style="font-size:1.1rem;">Branche active :</strong>
              <select class="form-control" style="font-size:0.85rem; padding:0.25rem 0.5rem;" onchange="Git.switchBranch(this.value)">
                ${(info.branches || []).map(b => `<option value="${b}" ${b === info.branch ? 'selected' : ''}>${b}</option>`).join('')}
              </select>
              ${info.ahead > 0 ? `<span class="tag" style="background:#1f6feb33; color:var(--accent-blue-bright);">↑ ${info.ahead} à push</span>` : ''}
              ${info.behind > 0 ? `<span class="tag" style="background:#d2992233; color:var(--accent-amber);">↓ ${info.behind} à pull</span>` : ''}
            </div>
            <div style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">${info.remote_url || 'Aucun remote configuré'}</div>
          </div>

          <div style="display:flex; gap:0.5rem;">
            <button class="btn btn-sm btn-blue" onclick="Git.action('pull')">⬇️ Git Pull</button>
            <button class="btn btn-sm btn-primary" onclick="Git.action('push')">⬆️ Git Push</button>
            <button class="btn btn-sm" onclick="Git.openCommitModal()">💾 Nouveau Commit</button>
          </div>
        </div>

        <div style="display:flex; gap:1.5rem; margin-top:1.25rem; padding-top:1rem; border-top:1px solid var(--border-color); font-size:0.85rem;">
          <div>Statut : <strong>${isClean ? '🟢 Propre (Clean)' : '🟡 Modifications en attente'}</strong></div>
          <div>Modifiés : <strong style="color:var(--accent-amber);">${modifiedCount}</strong></div>
          <div>Indexés (Staged) : <strong style="color:var(--accent-green-bright);">${stagedCount}</strong></div>
          <div>Non suivis : <strong style="color:var(--text-muted);">${untrackedCount}</strong></div>
        </div>
      </div>

      <!-- Git Files & Commits Grid -->
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.25rem;">
        <!-- Files list -->
        <div class="data-table-card" style="padding:1.25rem;">
          <h4 style="margin-bottom:0.75rem;">Fichiers modifiés</h4>
          ${isClean ? `
            <p style="font-size:0.85rem; color:var(--text-muted);">Aucun fichier modifié.</p>
          ` : `
            <ul style="list-style:none; display:flex; flex-direction:column; gap:0.4rem; font-family:var(--font-mono); font-size:0.8rem; max-height:220px; overflow-y:auto;">
              ${(info.staged || []).map(f => `<li style="color:var(--accent-green-bright);">[+] ${f} (staged)</li>`).join('')}
              ${(info.modified || []).map(f => `<li style="color:var(--accent-amber);">[M] ${f}</li>`).join('')}
              ${(info.untracked || []).map(f => `<li style="color:var(--text-muted);">[?] ${f} (untracked)</li>`).join('')}
            </ul>
          `}
        </div>

        <!-- Recent commits -->
        <div class="data-table-card" style="padding:1.25rem;">
          <h4 style="margin-bottom:0.75rem;">Derniers commits</h4>
          <ul style="list-style:none; display:flex; flex-direction:column; gap:0.5rem; font-size:0.8rem;">
            ${(info.recent_commits || []).map(c => `
              <li style="border-bottom:1px solid var(--border-color); padding-bottom:0.35rem;">
                <div style="display:flex; justify-content:space-between;">
                  <strong style="color:var(--accent-blue-bright); font-family:var(--font-mono);">${c.hash}</strong>
                  <span style="color:var(--text-muted); font-size:0.75rem;">${c.date}</span>
                </div>
                <div style="color:var(--text-primary); margin-top:2px;">${c.message}</div>
              </li>
            `).join('')}
          </ul>
        </div>
      </div>

      <!-- GitHub Section Container -->
      <div id="github-section"></div>
    `;
  },

  async action(actionName, extra = {}) {
    if (!this.currentProject) return;
    App.toast(`Exécution de git ${actionName}...`, 'info');
    const res = await App.api('/api/git/action', 'POST', {
      action: actionName,
      path: this.currentProject.path,
      extra
    });
    if (res.ok && res.data.success) {
      App.toast(`Git ${actionName} terminé !`, 'success');
      this.refresh();
    } else {
      App.toast(`Erreur Git : ${res.data.output || res.data.error}`, 'error');
    }
  },

  async switchBranch(branchName) {
    await this.action('switch_branch', { branch: branchName });
  },

  openCommitModal() {
    document.getElementById('git-commit-msg').value = '';
    document.getElementById('modal-commit').classList.add('open');
  },

  closeCommitModal() {
    document.getElementById('modal-commit').classList.remove('open');
  },

  async submitCommit() {
    const msg = document.getElementById('git-commit-msg').value.trim();
    if (!msg) {
      App.toast('Le message de commit est obligatoire', 'error');
      return;
    }
    const stageAll = document.getElementById('git-stage-all').checked;
    this.closeCommitModal();
    await this.action('commit', { message: msg, stage_all: stageAll });
  }
};
