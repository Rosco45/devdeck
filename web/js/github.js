// GitHub Integration Module (PRs, Issues, Actions)
const GitHub = {
  async load(remoteUrl) {
    const container = document.getElementById('github-section');
    if (!container) return;

    container.innerHTML = `
      <div class="data-table-card" style="padding:1.25rem;">
        <h4 style="display:flex; align-items:center; gap:0.5rem; margin-bottom:1rem;">
          <span>🐙</span> GitHub Overview (Chargement...)
        </h4>
      </div>`;

    const res = await App.api(`/api/github/overview?remote=${encodeURIComponent(remoteUrl)}`);
    if (!res.ok) {
      container.innerHTML = `
        <div class="data-table-card" style="padding:1.25rem; color:var(--text-muted); font-size:0.85rem;">
          ℹ️ Pas d'accès direct à l'API GitHub pour ce dépôt (dépôt privé ou quota atteint). Vous pouvez configurer un Personal Access Token dans les <strong>Réglages</strong>.
        </div>`;
      return;
    }

    const { owner, repo, pull_requests, issues, actions } = res.data;

    container.innerHTML = `
      <div class="data-table-card" style="padding:1.25rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
          <h4 style="display:flex; align-items:center; gap:0.5rem;">
            <span>🐙</span> GitHub : <a href="https://github.com/${owner}/${repo}" target="_blank" style="color:var(--accent-blue-bright); text-decoration:none;">${owner}/${repo} ↗</a>
          </h4>
          <span style="font-size:0.8rem; color:var(--text-muted);">Synchronisé en direct</span>
        </div>

        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:1rem;">
          <!-- Pull Requests -->
          <div style="background:var(--bg-primary); padding:0.85rem; border-radius:6px; border:1px solid var(--border-color);">
            <div style="font-weight:600; font-size:0.85rem; margin-bottom:0.6rem; color:var(--text-secondary);">
              🔀 Pull Requests (${pull_requests.length})
            </div>
            ${pull_requests.length === 0 ? `<p style="font-size:0.8rem; color:var(--text-muted);">Aucune PR ouverte.</p>` : `
              <ul style="list-style:none; display:flex; flex-direction:column; gap:0.4rem; font-size:0.8rem;">
                ${pull_requests.map(pr => `
                  <li>
                    <a href="${pr.html_url}" target="_blank" style="color:var(--text-primary); text-decoration:none;">
                      #${pr.number} ${pr.title}
                    </a>
                    <div style="font-size:0.7rem; color:var(--text-muted);">par ${pr.author}</div>
                  </li>
                `).join('')}
              </ul>
            `}
          </div>

          <!-- Issues -->
          <div style="background:var(--bg-primary); padding:0.85rem; border-radius:6px; border:1px solid var(--border-color);">
            <div style="font-weight:600; font-size:0.85rem; margin-bottom:0.6rem; color:var(--text-secondary);">
              ⚠️ Issues (${issues.length})
            </div>
            ${issues.length === 0 ? `<p style="font-size:0.8rem; color:var(--text-muted);">Aucune issue ouverte.</p>` : `
              <ul style="list-style:none; display:flex; flex-direction:column; gap:0.4rem; font-size:0.8rem;">
                ${issues.map(iss => `
                  <li>
                    <a href="${iss.html_url}" target="_blank" style="color:var(--text-primary); text-decoration:none;">
                      #${iss.number} ${iss.title}
                    </a>
                  </li>
                `).join('')}
              </ul>
            `}
          </div>

          <!-- GitHub Actions -->
          <div style="background:var(--bg-primary); padding:0.85rem; border-radius:6px; border:1px solid var(--border-color);">
            <div style="font-weight:600; font-size:0.85rem; margin-bottom:0.6rem; color:var(--text-secondary);">
              ⚡ GitHub Actions CI/CD (${actions.length})
            </div>
            ${actions.length === 0 ? `<p style="font-size:0.8rem; color:var(--text-muted);">Aucun workflow récent.</p>` : `
              <ul style="list-style:none; display:flex; flex-direction:column; gap:0.4rem; font-size:0.8rem;">
                ${actions.map(act => {
                  const icon = act.conclusion === 'success' ? '🟢' : act.conclusion === 'failure' ? '🔴' : '🟡';
                  return `
                    <li style="display:flex; justify-content:space-between; align-items:center;">
                      <a href="${act.html_url}" target="_blank" style="color:var(--text-primary); text-decoration:none; display:flex; align-items:center; gap:0.3rem;">
                        <span>${icon}</span> ${act.name}
                      </a>
                      <span style="font-size:0.7rem; color:var(--text-muted); font-family:var(--font-mono);">${act.branch}</span>
                    </li>
                  `;
                }).join('')}
              </ul>
            `}
          </div>
        </div>
      </div>
    `;
  }
};
