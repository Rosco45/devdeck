// Logs & Terminal SSE Stream Module
const Logs = {
  currentProjectId: null,
  eventSource: null,
  autoScroll: true,

  init() {
    this.populateSelect();
    if (!this.currentProjectId && App.projects.length > 0) {
      this.switchProject(App.projects[0].id);
    }
  },

  populateSelect() {
    const sel = document.getElementById('terminal-project-select');
    if (!sel) return;
    sel.innerHTML = App.projects.map(p => `
      <option value="${p.id}" ${p.id === this.currentProjectId ? 'selected' : ''}>
        ${p.name} (${p.runtime && p.runtime.status === 'running' ? '🟢 En ligne' : '⚪ Arrêté'})
      </option>
    `).join('');
  },

  switchProject(projectId) {
    if (!projectId) return;
    this.currentProjectId = projectId;
    this.populateSelect();

    const screen = document.getElementById('terminal-screen');
    screen.innerHTML = `<span style="color:var(--text-muted);">Connexion au flux en direct de '${projectId}'...</span>\n`;

    // Update status badge
    const p = App.projects.find(x => x.id === projectId);
    const statusTag = document.getElementById('terminal-process-status');
    if (p && p.runtime && p.runtime.status === 'running') {
      statusTag.textContent = `En ligne (${p.runtime.mode.toUpperCase()} - PID ${p.runtime.pid})`;
      statusTag.className = 'tag framework';
    } else {
      statusTag.textContent = 'Arrêté';
      statusTag.className = 'tag';
    }

    // Close previous SSE
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    // Connect to SSE stream
    this.eventSource = new EventSource(`/api/projects/${projectId}/logs/stream`);
    screen.innerHTML = '';

    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'log') {
          const htmlChunk = App.ansiToHtml(data.chunk);
          screen.insertAdjacentHTML('beforeend', htmlChunk);
          if (this.autoScroll) {
            screen.scrollTop = screen.scrollHeight;
          }
        }
      } catch (e) {
        console.error('SSE log parse error', e);
      }
    };

    this.eventSource.onerror = () => {
      // Keep quiet on normal disconnects
    };
  },

  toggleAutoScroll() {
    this.autoScroll = !this.autoScroll;
    const btn = document.getElementById('btn-autoscroll');
    btn.textContent = `📜 Défilement auto: ${this.autoScroll ? 'ON' : 'OFF'}`;
    btn.style.color = this.autoScroll ? 'var(--accent-blue-bright)' : 'var(--text-muted)';
  },

  async restartCurrent() {
    if (!this.currentProjectId) return;
    await Projects.restart(this.currentProjectId);
    this.switchProject(this.currentProjectId);
  },

  async clear() {
    if (!this.currentProjectId) return;
    await App.api(`/api/projects/${this.currentProjectId}/logs`, 'DELETE');
    const screen = document.getElementById('terminal-screen');
    screen.innerHTML = '';
  },

  copy() {
    const screen = document.getElementById('terminal-screen');
    navigator.clipboard.writeText(screen.innerText).then(() => {
      App.toast('Logs copiés dans le presse-papiers !', 'success');
    });
  }
};
