// App Core: Navigation, API Client, Toasts, ANSI Color Parser, Themes, i18n & Command Palette
const App = {
  currentView: 'projects',
  currentTheme: 'dark',
  projects: [],
  networkInfo: { local_ip: '127.0.0.1' },
  readyTracker: new Set(),

  init() {
    this.initTheme();
    if (window.I18N) I18N.init();
    this.initPalette();
    this.navigate('projects');
    this.loadNetworkInfo();
    this.loadStats();
    setInterval(() => this.loadStats(), 3500);
  },

  async loadNetworkInfo() {
    const res = await this.api('/api/system/network-info');
    if (res.ok) {
      this.networkInfo = res.data;
    }
  },

  initTheme() {
    const saved = localStorage.getItem('devdeck_theme') || 'dark';
    this.setTheme(saved);
  },

  setTheme(theme) {
    this.currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('devdeck_theme', theme);
    const sel = document.getElementById('theme-selector');
    if (sel && sel.value !== theme) sel.value = theme;
  },

  setLanguage(lang) {
    if (window.I18N) {
      I18N.setLanguage(lang);
    }
  },

  async api(endpoint, method = 'GET', body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' }
    };
    if (body && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
      opts.body = JSON.stringify(body);
    }
    try {
      const res = await fetch(endpoint, opts);
      const data = await res.json();
      return { ok: res.ok, status: res.status, data };
    } catch (e) {
      console.error('API Error:', e);
      return { ok: false, status: 0, data: { error: e.message } };
    }
  },

  navigate(viewName) {
    this.currentView = viewName;
    document.querySelectorAll('.nav-links button').forEach(b => b.classList.remove('active'));
    const navBtn = document.getElementById(`nav-${viewName}`);
    if (navBtn) navBtn.classList.add('active');

    document.querySelectorAll('.view-container').forEach(v => v.classList.remove('active'));
    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) targetView.classList.add('active');

    const titleKey = `title_${viewName}`;
    const titleText = window.I18N ? I18N.t(titleKey) : viewName;
    document.getElementById('current-view-title').textContent = titleText;

    // Trigger view-specific loads
    if (viewName === 'projects') {
      Projects.loadProjects();
      if (window.Workspaces) Workspaces.loadWorkspaces();
    }
    if (viewName === 'ports') Ports.scan();
    if (viewName === 'git') Git.populateSelect();
    if (viewName === 'env') Env.populateSelect();
    if (viewName === 'docker') Docker.loadContainers();
    if (viewName === 'terminal') Logs.init();
    if (viewName === 'tools') Tools.init();
    if (viewName === 'settings') this.loadSettings();
  },

  async loadStats() {
    const res = await this.api('/api/projects');
    if (res.ok) {
      this.projects = res.data;
      const runningProjects = this.projects.filter(p => p.runtime && p.runtime.status === 'running');
      const runningCount = runningProjects.length;
      const runningUnit = window.I18N ? I18N.t('stat_running') : 'actif';
      document.getElementById('stat-running-text').textContent = `${runningCount} ${runningUnit}`;
      document.getElementById('badge-running-count').textContent = runningCount;
      document.getElementById('badge-projects-count').textContent = this.projects.length;

      const dot = document.getElementById('stat-dot');
      dot.className = runningCount > 0 ? 'status-dot green' : 'status-dot gray';

      // Health Check Notification: detect newly ready servers
      runningProjects.forEach(p => {
        if (p.runtime && p.runtime.ready && !this.readyTracker.has(p.id)) {
          this.readyTracker.add(p.id);
          const readySec = p.runtime.ready_time_ms ? (p.runtime.ready_time_ms / 1000).toFixed(1) + 's' : '';
          this.toast(`✨ <strong>${p.name}</strong> est prêt sur le port :${p.port} (${readySec}) ! <a href="http://localhost:${p.port}" target="_blank" style="color:#fff; text-decoration:underline; margin-left:8px;">Ouvrir ↗</a>`, 'success');
        }
      });

      // Clear ready tracker for stopped projects
      this.projects.forEach(p => {
        if (!p.runtime || p.runtime.status !== 'running') {
          this.readyTracker.delete(p.id);
        }
      });

      // Re-render live cards if projects view is active to update metrics in real-time
      if (this.currentView === 'projects' && document.getElementById('projects-list')) {
        Projects.updateMetrics(this.projects);
      }
    }

    const portsRes = await this.api('/api/ports');
    if (portsRes.ok) {
      const portCount = portsRes.data.length;
      const portsUnit = window.I18N ? I18N.t('stat_ports') : 'ports';
      document.getElementById('stat-ports-text').textContent = `${portCount} ${portsUnit}`;
      document.getElementById('badge-ports-count').textContent = portCount;
    }
  },

  async loadSettings() {
    const res = await this.api('/api/settings');
    if (res.ok) {
      const s = res.data;
      if (document.getElementById('setting-port')) document.getElementById('setting-port').value = s.port || 8888;
      if (document.getElementById('setting-scan-dir')) document.getElementById('setting-scan-dir').value = s.default_scan_dir || '~';
      if (document.getElementById('setting-github-token')) document.getElementById('setting-github-token').value = s.github_token || '';
    }
  },

  async saveSettings() {
    const s = {
      port: parseInt(document.getElementById('setting-port').value),
      default_scan_dir: document.getElementById('setting-scan-dir').value,
      github_token: document.getElementById('setting-github-token').value.trim()
    };
    const res = await this.api('/api/settings', 'POST', s);
    if (res.ok) {
      this.toast('Paramètres enregistrés avec succès', 'success');
    } else {
      this.toast('Erreur lors de la sauvegarde', 'error');
    }
  },

  toast(message, type = 'info') {
    const container = document.getElementById('toasts');
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    t.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(t);
    setTimeout(() => {
      t.style.opacity = '0';
      t.style.transform = 'translateY(10px)';
      setTimeout(() => t.remove(), 300);
    }, 4500);
  },

  ansiToHtml(text) {
    if (!text) return '';
    const colors = {
      '30': '#484f58', '31': '#f85149', '32': '#3fb950', '33': '#d29922',
      '34': '#58a6ff', '35': '#bc8cff', '36': '#39c5cf', '37': '#b1bac4',
      '90': '#6e7681', '91': '#ff7b72', '92': '#56d364', '93': '#e3b341',
      '94': '#79c0ff', '95': '#d2a8ff', '96': '#56d4dd', '97': '#f0f6fc'
    };

    let escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Clickable URLs detection in logs (localhost, LAN IPs, and HTTPS)
    escaped = escaped.replace(
      /(https?:\/\/(?:localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|[\w\.-]+)(?::\d+)?(?:[^\s<>"'\)]*)?)/g,
      '<a href="$1" target="_blank" rel="noopener noreferrer" style="color:var(--accent-blue-bright); text-decoration:underline; font-weight:600;">$1</a>'
    );

    return escaped.replace(/\x1b\[([0-9;]+)m/g, (match, code) => {
      if (code === '0') return '</span>';
      const c = colors[code];
      if (c) return `<span style="color:${c};">`;
      return '';
    });
  },

  // -------------------------------------------------------------------------
  // Command Palette (Ctrl+K / Cmd+K)
  // -------------------------------------------------------------------------
  initPalette() {
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        this.openPalette();
      } else if (e.key === 'Escape') {
        this.closePalette();
      }
    });
  },

  openPalette() {
    const modal = document.getElementById('modal-palette');
    if (!modal) return;
    modal.classList.add('open');
    const input = document.getElementById('palette-input');
    input.value = '';
    input.focus();
    this.filterPalette('');
  },

  closePalette() {
    const modal = document.getElementById('modal-palette');
    if (modal) modal.classList.remove('open');
  },

  filterPalette(query) {
    const q = (query || '').toLowerCase().trim();
    const resultsContainer = document.getElementById('palette-results');
    const items = [];

    // Views
    const views = [
      { label: '🚀 Projets (Dashboard)', action: () => App.navigate('projects') },
      { label: '📟 Terminal & Logs en direct', action: () => App.navigate('terminal') },
      { label: '🔌 Inspecteur des Ports & Conflits', action: () => App.navigate('ports') },
      { label: '🌿 Git & GitHub Hub', action: () => App.navigate('git') },
      { label: '🔐 Variables (.env)', action: () => App.navigate('env') },
      { label: '🐳 Services Docker', action: () => App.navigate('docker') },
      { label: '🛠️ Boîte à outils Développeur', action: () => App.navigate('tools') },
      { label: '⚙️ Réglages', action: () => App.navigate('settings') }
    ];
    views.forEach(v => {
      if (!q || v.label.toLowerCase().includes(q)) items.push(v);
    });

    // Themes
    const themes = [
      { label: '🎨 Thème : 🌙 Sombre (Dark)', action: () => App.setTheme('dark') },
      { label: '🎨 Thème : 🧛 Dracula', action: () => App.setTheme('dracula') },
      { label: '🎨 Thème : 🌌 Midnight (OLED)', action: () => App.setTheme('midnight') },
      { label: '🎨 Thème : ☀️ Clair (Light)', action: () => App.setTheme('light') }
    ];
    themes.forEach(t => {
      if (!q || t.label.toLowerCase().includes(q)) items.push(t);
    });

    // Languages
    items.push(
      { label: '🌐 Langue : 🇫🇷 Français', action: () => App.setLanguage('fr') },
      { label: '🌐 Language : 🇬🇧 English', action: () => App.setLanguage('en') }
    );

    // Projects actions
    App.projects.forEach(p => {
      const isRunning = p.runtime && p.runtime.status === 'running';
      if (!q || p.name.toLowerCase().includes(q)) {
        if (!isRunning && p.dev_cmd) {
          items.push({
            label: `⚡ Lancer Dev : ${p.name} (${p.dev_cmd})`,
            action: () => Projects.start(p.id, 'dev')
          });
        }
        if (!isRunning && p.prod_cmd) {
          items.push({
            label: `🚀 Lancer Prod : ${p.name}`,
            action: () => Projects.start(p.id, 'prod')
          });
        }
        if (isRunning) {
          items.push({
            label: `🛑 Arrêter : ${p.name}`,
            action: () => Projects.stop(p.id)
          });
          items.push({
            label: `🔄 Redémarrer : ${p.name}`,
            action: () => Projects.restart(p.id)
          });
        }
        items.push({
          label: `📟 Voir les Logs : ${p.name}`,
          action: () => Projects.openTerminal(p.id)
        });
        items.push({
          label: `💻 Ouvrir dans VS Code : ${p.name}`,
          action: () => Projects.openEditor(p.path)
        });
      }
    });

    // Render palette items
    if (items.length === 0) {
      resultsContainer.innerHTML = `<div style="padding:1rem; text-align:center; color:var(--text-muted);">Aucune commande trouvée.</div>`;
      return;
    }

    resultsContainer.innerHTML = items.slice(0, 10).map((it, idx) => `
      <div class="palette-item ${idx === 0 ? 'selected' : ''}" data-idx="${idx}" onclick="App.runPaletteItem(${idx})" style="padding:0.6rem 0.85rem; border-radius:6px; cursor:pointer; font-size:0.85rem; display:flex; align-items:center; justify-content:space-between; border:1px solid transparent;">
        <span>${it.label}</span>
        <span style="font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">↵ Entrée</span>
      </div>
    `).join('');

    this.paletteItems = items.slice(0, 10);
    this.paletteSelectedIndex = 0;
  },

  navigatePalette(dir) {
    if (!this.paletteItems || this.paletteItems.length === 0) return;
    this.paletteSelectedIndex = (this.paletteSelectedIndex + dir + this.paletteItems.length) % this.paletteItems.length;
    document.querySelectorAll('.palette-item').forEach((el, idx) => {
      el.classList.toggle('selected', idx === this.paletteSelectedIndex);
      if (idx === this.paletteSelectedIndex) el.scrollIntoView({ block: 'nearest' });
    });
  },

  executePaletteSelection() {
    if (this.paletteItems && this.paletteItems[this.paletteSelectedIndex]) {
      this.runPaletteItem(this.paletteSelectedIndex);
    }
  },

  runPaletteItem(idx) {
    if (this.paletteItems && this.paletteItems[idx]) {
      const item = this.paletteItems[idx];
      this.closePalette();
      item.action();
    }
  }
};

window.addEventListener('DOMContentLoaded', () => App.init());
