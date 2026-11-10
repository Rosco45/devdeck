// App Core: Navigation, API Client, Toasts, ANSI Color Parser, Themes & i18n
const App = {
  currentView: 'projects',
  currentTheme: 'dark',
  projects: [],

  init() {
    this.initTheme();
    if (window.I18N) I18N.init();
    this.navigate('projects');
    this.loadStats();
    setInterval(() => this.loadStats(), 4000);
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
    if (viewName === 'projects') Projects.loadProjects();
    if (viewName === 'ports') Ports.scan();
    if (viewName === 'git') Git.populateSelect();
    if (viewName === 'env') Env.populateSelect();
    if (viewName === 'docker') Docker.loadContainers();
    if (viewName === 'terminal') Logs.init();
    if (viewName === 'tools') Tools.generateTokens();
    if (viewName === 'settings') this.loadSettings();
  },

  async loadStats() {
    const res = await this.api('/api/projects');
    if (res.ok) {
      this.projects = res.data;
      const runningCount = this.projects.filter(p => p.runtime && p.runtime.status === 'running').length;
      const runningUnit = window.I18N ? I18N.t('stat_running') : 'actif';
      document.getElementById('stat-running-text').textContent = `${runningCount} ${runningUnit}`;
      document.getElementById('badge-running-count').textContent = runningCount;
      document.getElementById('badge-projects-count').textContent = this.projects.length;

      const dot = document.getElementById('stat-dot');
      dot.className = runningCount > 0 ? 'status-dot green' : 'status-dot gray';
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
    }, 3500);
  },

  ansiToHtml(text) {
    if (!text) return '';
    // Basic ANSI color converter
    const colors = {
      '30': '#484f58', '31': '#f85149', '32': '#3fb950', '33': '#d29922',
      '34': '#58a6ff', '35': '#bc8cff', '36': '#39c5cf', '37': '#b1bac4',
      '90': '#6e7681', '91': '#ff7b72', '92': '#56d364', '93': '#e3b341',
      '94': '#79c0ff', '95': '#d2a8ff', '96': '#56d4dd', '97': '#f0f6fc'
    };

    let escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return escaped.replace(/\x1b\[([0-9;]+)m/g, (match, code) => {
      if (code === '0') return '</span>';
      const c = colors[code];
      if (c) return `<span style="color:${c};">`;
      return '';
    });
  }
};

window.addEventListener('DOMContentLoaded', () => App.init());
