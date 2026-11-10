// Docker Management Module
const Docker = {
  containers: [],

  async loadContainers() {
    const tbody = document.getElementById('docker-table-body');
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">Inspection de Docker...</td></tr>`;

    const res = await App.api('/api/docker/containers');
    if (!res.ok || !res.data.available) {
      tbody.innerHTML = `
        <tr>
          <td colspan="4" style="text-align:center; padding:2rem;">
            <p style="color:var(--accent-amber); font-weight:600; margin-bottom:0.5rem;">⚠️ Service Docker non accessible</p>
            <p style="font-size:0.8rem; color:var(--text-muted);">
              ${res.data.error || "Vérifiez que le démon Docker est démarré et que votre utilisateur a les droits sur /var/run/docker.sock"}
            </p>
          </td>
        </tr>`;
      return;
    }

    this.containers = res.data.containers || [];
    if (this.containers.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:2rem;">Aucun conteneur Docker en cours d'exécution.</td></tr>`;
      return;
    }

    tbody.innerHTML = this.containers.map(c => `
      <tr>
        <td><strong>${c.names}</strong></td>
        <td><code style="font-size:0.8rem; color:var(--accent-blue-bright);">${c.image}</code></td>
        <td>
          <span class="tag ${c.state === 'running' ? 'framework' : ''}">
            ${c.status}
          </span>
        </td>
        <td><span style="font-family:var(--font-mono); font-size:0.75rem;">${c.ports || '-'}</span></td>
      </tr>
    `).join('');
  }
};
