// Developer Tools: HTTP Tester, JWT, UUID/Tokens, Hashes, DB Ping & Config Generator
const Tools = {
  init() {
    this.generateTokens();
  },

  async sendHttp() {
    const method = document.getElementById('tool-http-method').value;
    const url = document.getElementById('tool-http-url').value.trim();
    let body = document.getElementById('tool-http-body').value.trim();
    const resultBox = document.getElementById('tool-http-result');

    if (!url) {
      App.toast('URL requise', 'error');
      return;
    }

    resultBox.innerHTML = '<span style="color:var(--text-muted);">Envoi de la requête en cours...</span>';

    let jsonBody = null;
    if (body) {
      try {
        jsonBody = JSON.parse(body);
      } catch (e) {
        jsonBody = body;
      }
    }

    const res = await App.api('/api/tools/http', 'POST', {
      method,
      url,
      body: jsonBody
    });

    if (res.ok) {
      const data = res.data;
      const statusColor = data.status >= 200 && data.status < 300 ? 'var(--accent-green-bright)' : 'var(--accent-red-bright)';
      resultBox.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-color); padding-bottom:0.4rem; margin-bottom:0.6rem;">
          <div>Statut : <strong style="color:${statusColor}">${data.status || 'ERR'}</strong> • Durée : <strong>${data.duration_ms} ms</strong></div>
          <div style="font-size:0.75rem; color:var(--text-muted);">${data.size_bytes || 0} octets</div>
        </div>
        <pre style="white-space:pre-wrap; word-break:break-all;">${App.ansiToHtml(data.body || data.error || '')}</pre>
      `;
    } else {
      resultBox.innerHTML = `<span style="color:var(--accent-red-bright);">Erreur : ${res.data.error || 'Requête échouée'}</span>`;
    }
  },

  async decodeJwt(token) {
    const out = document.getElementById('tool-jwt-output');
    if (!token.trim()) {
      out.textContent = 'En attente de token...';
      return;
    }
    const res = await App.api('/api/tools/jwt', 'POST', { token });
    if (res.ok && res.data.valid) {
      out.textContent = JSON.stringify(res.data, null, 2);
    } else {
      out.textContent = res.data.error || 'Token JWT invalide';
    }
  },

  async generateTokens() {
    const out = document.getElementById('tool-tokens-output');
    if (!out) return;
    const res = await App.api('/api/tools/tokens');
    if (res.ok) {
      const { uuid_v4, hex_secret, urlsafe_token } = res.data;
      out.innerHTML = `
        <div style="margin-bottom:0.5rem;">
          <div style="color:var(--text-secondary); font-size:0.75rem; margin-bottom:2px;">UUID v4 :</div>
          <div style="display:flex; gap:0.5rem; align-items:center;">
            <input type="text" class="form-control" style="font-size:0.8rem; padding:0.3rem;" value="${uuid_v4[0]}" readonly>
            <button class="btn btn-sm" onclick="navigator.clipboard.writeText('${uuid_v4[0]}'); App.toast('UUID copié !', 'success')">Copier</button>
          </div>
        </div>
        <div style="margin-bottom:0.5rem;">
          <div style="color:var(--text-secondary); font-size:0.75rem; margin-bottom:2px;">Clé Secrète Hex (32 bytes) :</div>
          <div style="display:flex; gap:0.5rem; align-items:center;">
            <input type="text" class="form-control" style="font-size:0.8rem; padding:0.3rem;" value="${hex_secret[0]}" readonly>
            <button class="btn btn-sm" onclick="navigator.clipboard.writeText('${hex_secret[0]}'); App.toast('Clé secrète copiée !', 'success')">Copier</button>
          </div>
        </div>
        <div>
          <div style="color:var(--text-secondary); font-size:0.75rem; margin-bottom:2px;">Jeton URL-Safe :</div>
          <div style="display:flex; gap:0.5rem; align-items:center;">
            <input type="text" class="form-control" style="font-size:0.8rem; padding:0.3rem;" value="${urlsafe_token[0]}" readonly>
            <button class="btn btn-sm" onclick="navigator.clipboard.writeText('${urlsafe_token[0]}'); App.toast('Jeton copié !', 'success')">Copier</button>
          </div>
        </div>
      `;
    }
  },

  // -------------------------------------------------------------------------
  // Database Ping Tester
  // -------------------------------------------------------------------------
  async pingDb(dbType, port) {
    const statusEl = document.getElementById(`db-status-${dbType}`);
    if (statusEl) statusEl.textContent = 'Test en cours...';

    const res = await App.api('/api/tools/db-ping', 'POST', {
      host: '127.0.0.1',
      port: port,
      db_type: dbType
    });

    if (res.ok && res.data.ok) {
      statusEl.innerHTML = `<span style="color:var(--accent-green-bright); font-weight:600;">🟢 En ligne (${res.data.latency_ms} ms)</span>`;
      App.toast(`Base ${dbType.toUpperCase()} accessible en ${res.data.latency_ms} ms`, 'success');
    } else {
      statusEl.innerHTML = `<span style="color:var(--text-muted);">⚪ Inaccessible (: ${port})</span>`;
      App.toast(`Base ${dbType.toUpperCase()} non connectée`, 'info');
    }
  },

  // -------------------------------------------------------------------------
  // Configuration File Generator
  // -------------------------------------------------------------------------
  async generateConfigFile() {
    const configType = document.getElementById('gen-config-type').value;
    const stack = document.getElementById('gen-config-stack').value;
    const outBox = document.getElementById('gen-config-output');

    outBox.textContent = 'Génération en cours...';
    const res = await App.api('/api/tools/generate-config', 'POST', {
      config_type: configType,
      stack: stack
    });

    if (res.ok && res.data.content) {
      outBox.textContent = res.data.content;
      App.toast('Fichier de configuration généré !', 'success');
    } else {
      outBox.textContent = 'Erreur de génération.';
    }
  },

  copyGeneratedConfig() {
    const outBox = document.getElementById('gen-config-output');
    navigator.clipboard.writeText(outBox.textContent).then(() => {
      App.toast('Configuration copiée dans le presse-papiers !', 'success');
    });
  }
};
