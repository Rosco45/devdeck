// Workspaces (Project Groups) Module
const Workspaces = {
  workspaces: [],

  async loadWorkspaces() {
    const res = await App.api('/api/workspaces');
    if (res.ok) {
      this.workspaces = res.data;
      this.renderBar();
    }
  },

  renderBar() {
    const bar = document.getElementById('workspaces-bar');
    if (!bar) return;

    if (this.workspaces.length === 0) {
      bar.innerHTML = `
        <div style="display:flex; align-items:center; gap:0.75rem; background:var(--bg-secondary); padding:0.5rem 0.85rem; border-radius:var(--radius-sm); border:1px solid var(--border-color); font-size:0.8rem; color:var(--text-muted);">
          <span>📦 <strong>Groupes / Workspaces :</strong> Lancez plusieurs projets en 1 clic (ex: Frontend + Backend + Docker).</span>
          <button class="btn btn-sm" onclick="Workspaces.openModal()" style="margin-left:auto;">➕ Créer un groupe</button>
        </div>`;
      return;
    }

    bar.innerHTML = `
      <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap; background:var(--bg-secondary); padding:0.5rem 0.85rem; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
        <span style="font-size:0.8rem; font-weight:600; color:var(--text-secondary); margin-right:0.25rem;">📦 Workspaces :</span>
        ${this.workspaces.map(w => `
          <div style="display:inline-flex; align-items:center; gap:0.4rem; background:var(--bg-tertiary); padding:3px 8px; border-radius:6px; border:1px solid var(--border-color); font-size:0.8rem;">
            <strong>${w.name}</strong>
            <span style="color:var(--text-muted); font-size:0.7rem;">(${w.project_ids.length})</span>
            <button class="btn btn-sm btn-primary" style="padding:2px 6px; font-size:0.7rem;" onclick="Workspaces.startWorkspace('${w.id}')" title="Démarrer tous les serveurs du groupe">⚡ Démarrer</button>
            <button class="btn btn-sm btn-danger" style="padding:2px 6px; font-size:0.7rem;" onclick="Workspaces.stopWorkspace('${w.id}')" title="Arrêter tout le groupe">🛑</button>
            <button class="btn btn-sm btn-icon" style="padding:2px 4px; font-size:0.7rem; background:transparent; border:none;" onclick="Workspaces.deleteWorkspace('${w.id}')" title="Supprimer le groupe">🗑️</button>
          </div>
        `).join('')}
        <button class="btn btn-sm" onclick="Workspaces.openModal()" style="margin-left:auto; font-size:0.75rem;">➕ Nouveau groupe</button>
      </div>`;
  },

  async startWorkspace(id) {
    App.toast(`Démarrage du workspace ${id}...`, 'info');
    const res = await App.api(`/api/workspaces/${id}/start`, 'POST', {});
    if (res.ok) {
      App.toast(res.data.message || 'Démarrage du groupe en cours...', 'success');
      setTimeout(() => Projects.loadProjects(), 1500);
    }
  },

  async stopWorkspace(id) {
    App.toast(`Arrêt du workspace ${id}...`, 'info');
    const res = await App.api(`/api/workspaces/${id}/stop`, 'POST', {});
    if (res.ok) {
      App.toast('Tous les serveurs du groupe ont été arrêtés', 'info');
      setTimeout(() => Projects.loadProjects(), 800);
    }
  },

  async deleteWorkspace(id) {
    if (!confirm('Supprimer ce groupe de projets ?')) return;
    const res = await App.api(`/api/workspaces/${id}`, 'DELETE');
    if (res.ok) {
      App.toast('Groupe supprimé', 'info');
      this.loadWorkspaces();
    }
  },

  openModal() {
    const list = document.getElementById('ws-modal-projects-list');
    list.innerHTML = App.projects.map(p => `
      <label style="display:flex; align-items:center; gap:0.6rem; padding:0.4rem 0.6rem; background:var(--bg-primary); border:1px solid var(--border-color); border-radius:4px; font-size:0.85rem; cursor:pointer;">
        <input type="checkbox" value="${p.id}" class="ws-proj-chk">
        <span><strong>${p.name}</strong> <span style="font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">(${p.dev_cmd || 'pas de commande'})</span></span>
      </label>
    `).join('');
    document.getElementById('ws-modal-name').value = '';
    document.getElementById('modal-workspace').classList.add('open');
  },

  closeModal() {
    document.getElementById('modal-workspace').classList.remove('open');
  },

  async saveModal() {
    const name = document.getElementById('ws-modal-name').value.trim();
    if (!name) {
      App.toast('Le nom du groupe est obligatoire', 'error');
      return;
    }
    const selected = [];
    document.querySelectorAll('.ws-proj-chk:checked').forEach(c => selected.push(c.value));
    if (selected.length === 0) {
      App.toast('Sélectionnez au moins un projet pour ce groupe', 'error');
      return;
    }

    const res = await App.api('/api/workspaces', 'POST', {
      name,
      project_ids: selected
    });

    if (res.ok) {
      App.toast(`Groupe '${name}' créé avec succès !`, 'success');
      this.closeModal();
      this.loadWorkspaces();
    }
  }
};
