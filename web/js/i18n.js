// DevDeck Internationalization (i18n) Module: French & English
const I18N = {
  lang: 'fr',
  translations: {
    fr: {
      // Sidebar & Navigation
      nav_projects: 'Projets',
      nav_terminal: 'Terminal & Logs',
      nav_ports: 'Ports & Processus',
      nav_git: 'Git & GitHub',
      nav_env: 'Variables (.env)',
      nav_docker: 'Docker',
      nav_tools: 'DevTools',
      nav_settings: 'Réglages',
      server_online: 'Serveur local en ligne',

      // Topbar
      title_projects: 'Tableau de bord Projets',
      title_terminal: 'Terminal & Flux de Logs en Direct',
      title_ports: 'Inspecteur des Ports & Conflits',
      title_git: 'Gestionnaire Git & GitHub',
      title_env: 'Variables d’Environnement (.env)',
      title_docker: 'Services & Conteneurs Docker',
      title_tools: 'Boîte à outils Développeur',
      title_settings: 'Paramètres',
      btn_scan: 'Scanner un dossier',
      btn_new_project: 'Nouveau projet',
      stat_running: 'en marche',
      stat_ports: 'ports',

      // Themes
      theme_dark: '🌙 Sombre',
      theme_dracula: '🧛 Dracula',
      theme_midnight: '🌌 Midnight',
      theme_light: '☀️ Clair',

      // Projects View
      search_placeholder: 'Rechercher un projet ou un framework...',
      filter_all_stacks: 'Toutes les stacks',
      btn_start_dev: '⚡ Lancer Dev',
      btn_start_prod: '🚀 Lancer Prod',
      btn_test: '🧪 Tests',
      btn_stop: '🛑 Arrêter',
      btn_restart: '🔄 Redémarrer',
      btn_logs: '📟 Logs',
      btn_open_folder: 'Ouvrir dans l’explorateur',
      btn_open_editor: 'Ouvrir dans VS Code',
      btn_edit: 'Modifier',
      btn_delete: 'Supprimer',
      status_running: 'En ligne',
      status_stopped: 'Arrêté',
      status_failed: 'Erreur',
      no_projects: 'Aucun projet trouvé.',
      scan_home_btn: 'Scanner mon dossier utilisateur',
      open_port: 'Ouvrir :{port} ↗',

      // Terminal View
      lbl_project: 'Projet :',
      btn_autoscroll_on: '📜 Défilement auto: ON',
      btn_autoscroll_off: '📜 Défilement auto: OFF',
      btn_clear: '🧹 Effacer',
      btn_copy: '📋 Copier',
      terminal_placeholder: 'Sélectionnez un projet pour visualiser ses logs en direct...',
      terminal_connecting: 'Connexion au flux en direct de \'{id}\'...',

      // Ports View
      ports_title: 'Inspecteur des Ports & Conflits',
      ports_subtitle: 'Visualisez les ports occupés en temps réel et débloquez les conflits EADDRINUSE en un clic.',
      btn_scan_ports: '🔄 Scanner les ports',
      th_port: 'Port',
      th_process: 'Processus',
      th_pid: 'PID',
      th_user: 'Utilisateur',
      th_hint: 'Description / Stack',
      th_action: 'Action',
      btn_kill: 'Tuer (PID {pid})',
      ports_loading: 'Scan des ports en cours...',
      ports_empty: 'Aucun port de serveur en écoute détecté.',
      ports_system: 'Système',

      // Git View
      lbl_branch: 'Branche active :',
      btn_git_pull: '⬇️ Git Pull',
      btn_git_push: '⬆️ Git Push',
      btn_git_commit: '💾 Nouveau Commit',
      lbl_clean: '🟢 Propre (Clean)',
      lbl_dirty: '🟡 Modifications en attente',
      lbl_status: 'Statut :',
      lbl_modified: 'Modifiés :',
      lbl_staged: 'Indexés (Staged) :',
      lbl_untracked: 'Non suivis :',
      modified_files_title: 'Fichiers modifiés',
      recent_commits_title: 'Derniers commits',
      no_modified_files: 'Aucun fichier modifié.',
      not_a_git_repo: 'Ce projet n’est pas un dépôt Git.',
      loading_git: 'Lecture des informations Git...',

      // GitHub section
      github_synced: 'Synchronisé en direct',
      prs_title: '🔀 Pull Requests',
      issues_title: '⚠️ Issues',
      actions_title: '⚡ GitHub Actions CI/CD',
      no_prs: 'Aucune PR ouverte.',
      no_issues: 'Aucune issue ouverte.',
      no_actions: 'Aucun workflow récent.',

      // Env View
      lbl_env_file: 'Édition de {file} ({count} variables)',
      lbl_env_backup: 'Une copie .bak est automatiquement générée avant chaque sauvegarde.',
      btn_save_env: '💾 Enregistrer (.env)',
      btn_add_var: '➕ Ajouter une variable',
      no_env_file: 'Aucun fichier {file} pour le moment.',
      btn_create_env: 'Créer et ajouter une variable',

      // Docker View
      docker_title: 'Conteneurs & Services Docker',
      docker_subtitle: 'Supervisez vos conteneurs et les bases de données locales (Postgres, Redis, Mongo).',
      btn_refresh: '🔄 Rafraîchir',
      docker_unreachable: '⚠️ Service Docker non accessible',
      docker_empty: 'Aucun conteneur Docker en cours d’exécution.',

      // DevTools
      tools_http_title: '⚡ Testeur d’API HTTP (REST Client)',
      btn_send: 'Envoyer',
      lbl_body_json: 'Corps de la requête (JSON facultatif) :',
      res_placeholder: 'Résultat de la requête affiché ici...',
      jwt_title: '🔑 Décodeur JWT',
      jwt_placeholder: 'Coller un token JWT (eyJhbGciOi...)',
      jwt_waiting: 'En attente de token...',
      tokens_title: '🎲 Générateur de Secrets & UUID',
      btn_generate_new: 'Générer nouveau',
      lbl_uuid: 'UUID v4 :',
      lbl_hex_secret: 'Clé Secrète Hex (32 bytes) :',
      lbl_url_token: 'Jeton URL-Safe :',

      // Settings View
      settings_title: 'Configuration de DevDeck',
      lbl_setting_port: 'Port d’écoute du serveur :',
      lbl_setting_scan: 'Dossier de scan par défaut :',
      lbl_setting_token: 'GitHub Personal Access Token (optionnel pour PRs/Issues privées) :',
      btn_save_settings: 'Enregistrer les paramètres',

      // Modals
      modal_proj_add: 'Nouveau Projet',
      modal_proj_edit: 'Modifier \'{name}\'',
      lbl_proj_name: 'Nom du projet :',
      lbl_proj_path: 'Chemin absolu du dossier :',
      lbl_dev_cmd: 'Commande Dev :',
      lbl_prod_cmd: 'Commande Prod locale :',
      lbl_test_cmd: 'Commande Test :',
      lbl_port: 'Port :',
      btn_cancel: 'Annuler',
      btn_save: 'Enregistrer',
      modal_scan_title: 'Scanner un dossier de projets',
      btn_scan_action: 'Scanner',
      btn_import_selected: 'Importer les sélectionnés',
      modal_commit_title: 'Nouveau Commit Git',
      lbl_commit_msg: 'Message du commit :',
      lbl_stage_all: 'Inclure tous les fichiers modifiés (`git add -A`)',
      btn_commit: 'Commiter'
    },

    en: {
      // Sidebar & Navigation
      nav_projects: 'Projects',
      nav_terminal: 'Terminal & Logs',
      nav_ports: 'Ports & Processes',
      nav_git: 'Git & GitHub',
      nav_env: 'Environment (.env)',
      nav_docker: 'Docker',
      nav_tools: 'DevTools',
      nav_settings: 'Settings',
      server_online: 'Local server online',

      // Topbar
      title_projects: 'Projects Dashboard',
      title_terminal: 'Live Terminal & Log Stream',
      title_ports: 'Port & Process Inspector',
      title_git: 'Git & GitHub Manager',
      title_env: 'Environment Variables (.env)',
      title_docker: 'Docker Services & Containers',
      title_tools: 'Developer Tools',
      title_settings: 'Settings',
      btn_scan: 'Scan Directory',
      btn_new_project: 'New Project',
      stat_running: 'running',
      stat_ports: 'ports',

      // Themes
      theme_dark: '🌙 Dark',
      theme_dracula: '🧛 Dracula',
      theme_midnight: '🌌 Midnight',
      theme_light: '☀️ Light',

      // Projects View
      search_placeholder: 'Search project or framework...',
      filter_all_stacks: 'All stacks',
      btn_start_dev: '⚡ Start Dev',
      btn_start_prod: '🚀 Start Prod',
      btn_test: '🧪 Tests',
      btn_stop: '🛑 Stop',
      btn_restart: '🔄 Restart',
      btn_logs: '📟 Logs',
      btn_open_folder: 'Open in file manager',
      btn_open_editor: 'Open in VS Code',
      btn_edit: 'Edit',
      btn_delete: 'Delete',
      status_running: 'Running',
      status_stopped: 'Stopped',
      status_failed: 'Failed',
      no_projects: 'No projects found.',
      scan_home_btn: 'Scan user home folder',
      open_port: 'Open :{port} ↗',

      // Terminal View
      lbl_project: 'Project:',
      btn_autoscroll_on: '📜 Autoscroll: ON',
      btn_autoscroll_off: '📜 Autoscroll: OFF',
      btn_clear: '🧹 Clear',
      btn_copy: '📋 Copy',
      terminal_placeholder: 'Select a project to view its real-time logs...',
      terminal_connecting: 'Connecting to live stream for \'{id}\'...',

      // Ports View
      ports_title: 'Ports & Conflict Inspector',
      ports_subtitle: 'View occupied ports in real-time and resolve EADDRINUSE conflicts in one click.',
      btn_scan_ports: '🔄 Scan Ports',
      th_port: 'Port',
      th_process: 'Process',
      th_pid: 'PID',
      th_user: 'User',
      th_hint: 'Description / Stack',
      th_action: 'Action',
      btn_kill: 'Kill (PID {pid})',
      ports_loading: 'Scanning ports in progress...',
      ports_empty: 'No listening server ports detected.',
      ports_system: 'System',

      // Git View
      lbl_branch: 'Active branch:',
      btn_git_pull: '⬇️ Git Pull',
      btn_git_push: '⬆️ Git Push',
      btn_git_commit: '💾 New Commit',
      lbl_clean: '🟢 Clean',
      lbl_dirty: '🟡 Pending changes',
      lbl_status: 'Status:',
      lbl_modified: 'Modified:',
      lbl_staged: 'Staged:',
      lbl_untracked: 'Untracked:',
      modified_files_title: 'Modified Files',
      recent_commits_title: 'Recent Commits',
      no_modified_files: 'No modified files.',
      not_a_git_repo: 'This project is not a Git repository.',
      loading_git: 'Reading Git repository info...',

      // GitHub section
      github_synced: 'Live synced',
      prs_title: '🔀 Pull Requests',
      issues_title: '⚠️ Issues',
      actions_title: '⚡ GitHub Actions CI/CD',
      no_prs: 'No open PRs.',
      no_issues: 'No open issues.',
      no_actions: 'No recent workflows.',

      // Env View
      lbl_env_file: 'Editing {file} ({count} variables)',
      lbl_env_backup: 'A .bak backup is automatically created before each save.',
      btn_save_env: '💾 Save (.env)',
      btn_add_var: '➕ Add Variable',
      no_env_file: 'No {file} file found yet.',
      btn_create_env: 'Create and add variable',

      // Docker View
      docker_title: 'Docker Containers & Services',
      docker_subtitle: 'Supervise your containers and local databases (Postgres, Redis, Mongo).',
      btn_refresh: '🔄 Refresh',
      docker_unreachable: '⚠️ Docker service not reachable',
      docker_empty: 'No running Docker containers found.',

      // DevTools
      tools_http_title: '⚡ HTTP API Tester (REST Client)',
      btn_send: 'Send',
      lbl_body_json: 'Request body (Optional JSON):',
      res_placeholder: 'Request result displayed here...',
      jwt_title: '🔑 JWT Decoder',
      jwt_placeholder: 'Paste a JWT token (eyJhbGciOi...)',
      jwt_waiting: 'Waiting for token...',
      tokens_title: '🎲 Secret & UUID Generator',
      btn_generate_new: 'Generate New',
      lbl_uuid: 'UUID v4:',
      lbl_hex_secret: 'Hex Secret Key (32 bytes):',
      lbl_url_token: 'URL-Safe Token:',

      // Settings View
      settings_title: 'DevDeck Settings',
      lbl_setting_port: 'Server listening port:',
      lbl_setting_scan: 'Default scan directory:',
      lbl_setting_token: 'GitHub Personal Access Token (optional for private PRs/Issues):',
      btn_save_settings: 'Save Settings',

      // Modals
      modal_proj_add: 'New Project',
      modal_proj_edit: 'Edit \'{name}\'',
      lbl_proj_name: 'Project name:',
      lbl_proj_path: 'Absolute directory path:',
      lbl_dev_cmd: 'Dev Command:',
      lbl_prod_cmd: 'Local Prod Command:',
      lbl_test_cmd: 'Test Command:',
      lbl_port: 'Port:',
      btn_cancel: 'Cancel',
      btn_save: 'Save',
      modal_scan_title: 'Scan Project Directory',
      btn_scan_action: 'Scan',
      btn_import_selected: 'Import Selected',
      modal_commit_title: 'New Git Commit',
      lbl_commit_msg: 'Commit message:',
      lbl_stage_all: 'Stage all modified files (`git add -A`)',
      btn_commit: 'Commit'
    }
  },

  init() {
    const saved = localStorage.getItem('devdeck_lang') || 'fr';
    this.setLanguage(saved, false);
  },

  setLanguage(lang, updateUI = true) {
    if (!this.translations[lang]) lang = 'fr';
    this.lang = lang;
    localStorage.setItem('devdeck_lang', lang);

    const sel = document.getElementById('lang-selector');
    if (sel && sel.value !== lang) sel.value = lang;

    this.translateDOM();
    if (updateUI && window.App) {
      App.navigate(App.currentView);
    }
  },

  t(key, params = {}) {
    let str = (this.translations[this.lang] && this.translations[this.lang][key]) ||
              (this.translations.fr && this.translations.fr[key]) || key;
    for (const [k, v] of Object.entries(params)) {
      str = str.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
    }
    return str;
  },

  translateDOM() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      el.textContent = this.t(key);
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      el.setAttribute('placeholder', this.t(key));
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      el.setAttribute('title', this.t(key));
    });
  }
};
