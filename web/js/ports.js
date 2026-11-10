// Ports Inspector & Conflict Killer Module
const Ports = {
  ports: [],

  async scan() {
    const tbody = document.getElementById('ports-table-body');
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Scan des ports en cours...</td></tr>`;

    const res = await App.api('/api/ports');
    if (res.ok) {
      this.ports = res.data;
      this.render();
      App.loadStats();
    } else {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--accent-red-bright);">Erreur lors de la lecture des ports.</td></tr>`;
    }
  },

  render() {
    const tbody = document.getElementById('ports-table-body');
    if (this.ports.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">Aucun port de serveur en écoute détecté.</td></tr>`;
      return;
    }

    tbody.innerHTML = this.ports.map(p => `
      <tr>
        <td><strong style="color: var(--accent-purple-bright); font-family: var(--font-mono); font-size: 1rem;">:${p.port}</strong></td>
        <td><span style="font-weight: 600;">${p.command}</span></td>
        <td><span style="font-family: var(--font-mono); color: var(--text-muted);">${p.pid || 'N/A'}</span></td>
        <td><span style="font-size: 0.8rem; color: var(--text-secondary);">${p.user}</span></td>
        <td><span style="font-size: 0.8rem; color: var(--text-muted);">${p.hint || 'Processus local'}</span></td>
        <td style="text-align: right;">
          ${p.pid ? `
            <button class="btn btn-sm btn-danger" onclick="Ports.killPort(${p.port})">
              Tuer (PID ${p.pid})
            </button>
          ` : `
            <span style="color: var(--text-muted); font-size: 0.75rem;">Système</span>
          `}
        </td>
      </tr>
    `).join('');
  },

  async killPort(port) {
    if (!confirm(`Voulez-vous vraiment tuer le processus occupant le port :${port} ? Cela libérera le port immédiatement.`)) return;

    App.toast(`Tentative de libération du port :${port}...`, 'info');
    const res = await App.api('/api/ports/kill', 'POST', { port, force: true });
    if (res.ok && res.data.success) {
      App.toast(`Port :${port} libéré avec succès !`, 'success');
      this.scan();
    } else {
      App.toast(`Échec : ${res.data.message || res.data.error}`, 'error');
    }
  }
};
