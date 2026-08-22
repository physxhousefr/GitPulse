document.addEventListener('DOMContentLoaded', () => {
    // State
    let currentConfig = null;

    // DOM Elements
    const btnToggleBot = document.getElementById('btnToggleBot');
    const botStatusText = document.getElementById('botStatusText');
    const dryRunToggle = document.getElementById('dryRunToggle');
    const btnSettings = document.getElementById('btnSettings');
    const btnAddRepo = document.getElementById('btnAddRepo');
    
    // Metrics
    const valActiveRepos = document.getElementById('valActiveRepos');
    const valTotalCommits = document.getElementById('valTotalCommits');
    const valDiffStats = document.getElementById('valDiffStats');
    const valDryRunStatus = document.getElementById('valDryRunStatus');
    const repoCountTag = document.getElementById('repoCountTag');
    const heatmapTooltip = document.getElementById('heatmapTooltip');

    // Repos & Console
    const repoList = document.getElementById('repoList');
    const emptyReposState = document.getElementById('emptyReposState');
    const consoleBody = document.getElementById('consoleBody');
    const btnClearLogs = document.getElementById('btnClearLogs');
    const historyList = document.getElementById('historyList');

    // Modals
    const modalAddRepo = document.getElementById('modalAddRepo');
    const modalSettings = document.getElementById('modalSettings');
    const btnCloseAddRepoModal = document.getElementById('btnCloseAddRepoModal');
    const btnCancelAddRepo = document.getElementById('btnCancelAddRepo');
    const btnConfirmAddRepo = document.getElementById('btnConfirmAddRepo');
    const btnBrowseFolder = document.getElementById('btnBrowseFolder');

    const inputRepoPath = document.getElementById('inputRepoPath');
    const inputRepoName = document.getElementById('inputRepoName');
    const selectRepoMode = document.getElementById('selectRepoMode');
    const inputRepoInterval = document.getElementById('inputRepoInterval');

    const btnCloseSettingsModal = document.getElementById('btnCloseSettingsModal');
    const btnCancelSettings = document.getElementById('btnCancelSettings');
    const btnSaveSettings = document.getElementById('btnSaveSettings');
    const settingCommitStyle = document.getElementById('settingCommitStyle');
    const settingCommitTemplate = document.getElementById('settingCommitTemplate');
    const settingActivityFilename = document.getElementById('settingActivityFilename');
    const settingRandomize = document.getElementById('settingRandomize');
    const settingMinRandom = document.getElementById('settingMinRandom');
    const settingMaxRandom = document.getElementById('settingMaxRandom');
    const aiSettingsGroup = document.getElementById('aiSettingsGroup');
    const settingAiProvider = document.getElementById('settingAiProvider');
    const settingAiApiKey = document.getElementById('settingAiApiKey');
    const settingAiModel = document.getElementById('settingAiModel');

    // --- INITIALIZATION ---
    fetchConfig();
    initLogSSE();
    setInterval(fetchConfig, 8000);

    // --- FETCH & RENDER CONFIG ---
    async function fetchConfig() {
        try {
            const res = await fetch('/api/config');
            if (res.ok) {
                currentConfig = await res.json();
                renderUI();
            }
        } catch (err) {
            console.error('Erreur fetchConfig:', err);
        }
    }

    function renderUI() {
        if (!currentConfig) return;

        // Master Bot Toggle
        const isActive = currentConfig.bot_active;
        if (isActive) {
            btnToggleBot.className = 'btn btn-master active';
            botStatusText.textContent = 'BOT EN EXECUTION';
        } else {
            btnToggleBot.className = 'btn btn-master inactive';
            botStatusText.textContent = 'BOT EN PAUSE';
        }

        // Dry Run Toggle
        dryRunToggle.checked = currentConfig.dry_run;
        valDryRunStatus.textContent = currentConfig.dry_run ? 'ON (Simulé)' : 'OFF (Réel)';

        // Metrics
        const repos = currentConfig.repos || [];
        valActiveRepos.textContent = repos.filter(r => r.enabled).length;
        repoCountTag.textContent = repos.length;

        let totalCommits = 0;
        repos.forEach(r => totalCommits += (r.commit_count || 0));
        valTotalCommits.textContent = totalCommits;

        const diffTotals = currentConfig.diff_totals || { lines_added: 0, lines_deleted: 0 };
        valDiffStats.textContent = `+${diffTotals.lines_added} / -${diffTotals.lines_deleted}`;

        // Render Heatmap with real Git history data
        renderRealHeatmap(currentConfig.heatmap_data || {});

        // Render Repo Cards
        renderRepoCards(repos);

        // Render History Timeline
        renderHistory(currentConfig.history || []);
    }

    function renderRealHeatmap(heatmapData) {
        const grid = document.getElementById('heatmapGrid');
        grid.innerHTML = '';

        const today = new Date();
        const dates = [];
        for (let i = 364; i >= 0; i--) {
            const d = new Date(today);
            d.setDate(d.getDate() - i);
            const dateStr = d.toISOString().split('T')[0];
            dates.push({ dateStr, count: heatmapData[dateStr] || 0 });
        }

        dates.forEach(item => {
            const cell = document.createElement('div');
            let lvl = '';
            if (item.count >= 8) lvl = 'lvl-4';
            else if (item.count >= 5) lvl = 'lvl-3';
            else if (item.count >= 2) lvl = 'lvl-2';
            else if (item.count >= 1) lvl = 'lvl-1';

            cell.className = `cell ${lvl}`;
            cell.setAttribute('data-date', item.dateStr);
            cell.setAttribute('data-count', item.count);

            cell.addEventListener('mouseenter', () => {
                heatmapTooltip.textContent = `${item.count} commit(s) le ${item.dateStr}`;
            });
            cell.addEventListener('mouseleave', () => {
                heatmapTooltip.textContent = 'Survolez un carré pour voir les détails';
            });

            grid.appendChild(cell);
        });
    }

    function renderRepoCards(repos) {
        if (!repos || repos.length === 0) {
            repoList.innerHTML = '';
            repoList.appendChild(emptyReposState);
            emptyReposState.style.display = 'block';
            return;
        }

        emptyReposState.style.display = 'none';
        repoList.innerHTML = '';

        repos.forEach(repo => {
            const gitInfo = repo.git_info || {};
            const branch = gitInfo.branch || 'main';
            const isDirty = gitInfo.is_dirty;
            const diffStats = gitInfo.diff_stats || { lines_added: 0, lines_deleted: 0 };

            const card = document.createElement('div');
            card.className = 'repo-card';
            card.innerHTML = `
                <div class="repo-header">
                    <div class="repo-title">
                        <i class="fa-solid fa-folder"></i>
                        <span>${escapeHtml(repo.name)}</span>
                        <span class="tag-branch"><i class="fa-solid fa-code-branch"></i> ${escapeHtml(branch)}</span>
                        <span class="tag-status ${isDirty ? 'dirty' : 'clean'}">
                            ${isDirty ? `Fichiers Modifiés (+${diffStats.lines_added} / -${diffStats.lines_deleted})` : 'Propre'}
                        </span>
                    </div>
                    <div class="repo-header-actions">
                        <button class="btn btn-secondary btn-sm btn-trigger-now" data-id="${repo.id}" title="Commiter et Pusher maintenant">
                            <i class="fa-solid fa-paper-plane"></i> Push
                        </button>
                        <button class="btn btn-icon btn-delete-repo" data-id="${repo.id}" title="Supprimer">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                </div>
                <div class="repo-meta">
                    <i class="fa-regular fa-folder-open"></i> ${escapeHtml(repo.path)}
                </div>
                <div class="repo-actions">
                    <span class="mode-badge"><i class="fa-solid fa-sliders"></i> Mode: ${escapeHtml(repo.mode)} (${repo.interval_minutes}m)</span>
                    <span class="text-subtle" style="font-size: 11px;">Dernier commit: ${repo.last_run || 'Jamais'}</span>
                </div>
            `;

            card.querySelector('.btn-trigger-now').addEventListener('click', () => triggerRepoPush(repo.id));
            card.querySelector('.btn-delete-repo').addEventListener('click', () => deleteRepo(repo.id));

            repoList.appendChild(card);
        });
    }

    function renderHistory(history) {
        historyList.innerHTML = '';
        if (!history || history.length === 0) {
            historyList.innerHTML = '<div class="text-subtle" style="font-size:12px; padding:10px;">Aucun historique de commit enregistré.</div>';
            return;
        }

        history.slice(0, 10).forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            const isSuccess = item.status === 'Success' || item.status === 'Dry-Run';
            const icon = isSuccess ? '<i class="fa-solid fa-circle-check" style="color:var(--accent-emerald)"></i>' : '<i class="fa-solid fa-circle-xmark" style="color:var(--accent-coral)"></i>';

            div.innerHTML = `
                <div class="history-msg">${icon} [${escapeHtml(item.repo_name)}] ${escapeHtml(item.commit_msg)}</div>
                <div class="history-time">${escapeHtml(item.timestamp)}</div>
            `;
            historyList.appendChild(div);
        });
    }

    // --- SSE LIVE LOGS ---
    function initLogSSE() {
        const evtSource = new EventSource('/api/logs/stream');
        evtSource.onmessage = (e) => {
            appendLog(e.data);
        };
        evtSource.onerror = () => {
            console.warn("Connexion SSE interrompue. Tentative de reconnexion...");
        };
    }

    function appendLog(line) {
        const div = document.createElement('div');
        const isError = line.includes('[!]');
        div.className = `log-line ${isError ? 'error' : 'info'}`;
        div.textContent = line;
        consoleBody.appendChild(div);
        consoleBody.scrollTop = consoleBody.scrollHeight;
    }

    btnClearLogs.addEventListener('click', () => {
        consoleBody.innerHTML = '';
    });

    // --- BOT MASTER TOGGLE & DRY RUN ---
    btnToggleBot.addEventListener('click', async () => {
        const newState = !currentConfig.bot_active;
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bot_active: newState })
        });
        fetchConfig();
    });

    dryRunToggle.addEventListener('change', async () => {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dry_run: dryRunToggle.checked })
        });
        fetchConfig();
    });

    // --- REPO ACTIONS ---
    async function triggerRepoPush(repoId) {
        appendLog(`[-] gitpulse : Déclenchement manuel du push pour le dépôt ${repoId}...`);
        try {
            const res = await fetch(`/api/repos/${repoId}/trigger`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                appendLog(`[-] gitpulse : Push manuel réussi ! (${data.status})`);
            } else {
                appendLog(`[!] gitpulse : Erreur push manuel : ${data.details || data.error}`);
            }
            fetchConfig();
        } catch (err) {
            appendLog(`[!] gitpulse : Exception lors du push manuel.`);
        }
    }

    async function deleteRepo(repoId) {
        if (!confirm('Voulez-vous vraiment retirer ce dépôt de l\'automatisation ?')) return;
        await fetch(`/api/repos/${repoId}`, { method: 'DELETE' });
        fetchConfig();
    }

    // --- MODAL ADD REPO ---
    btnAddRepo.addEventListener('click', () => {
        inputRepoPath.value = '';
        inputRepoName.value = '';
        modalAddRepo.classList.add('active');
    });

    const closeAddModal = () => modalAddRepo.classList.remove('active');
    btnCloseAddRepoModal.addEventListener('click', closeAddModal);
    btnCancelAddRepo.addEventListener('click', closeAddModal);

    btnBrowseFolder.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/select_folder');
            const data = await res.json();
            if (data.success && data.path) {
                let cleanPath = data.path.trim();
                inputRepoPath.value = cleanPath;
                
                const parts = cleanPath.split(/[/\\]/).filter(Boolean);
                let cleanName = parts[parts.length - 1];
                if (cleanName && cleanName.toLowerCase() === '.git') {
                    cleanName = parts[parts.length - 2];
                }
                inputRepoName.value = cleanName || 'Mon Dépôt';
            }
        } catch (err) {
            alert('Impossible d\'ouvrir le sélecteur de dossier.');
        }
    });

    btnConfirmAddRepo.addEventListener('click', async () => {
        let path = inputRepoPath.value.trim();
        if (!path) {
            alert('Veuillez entrer un chemin de dépôt valide.');
            return;
        }

        if (path.toLowerCase().endsWith('/.git') || path.toLowerCase().endsWith('\\.git')) {
            path = path.substring(0, path.length - 5);
        }

        const payload = {
            path: path,
            name: inputRepoName.value.trim() || undefined,
            mode: selectRepoMode.value,
            interval_minutes: parseInt(inputRepoInterval.value) || 30
        };

        try {
            const res = await fetch('/api/repos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (data.success) {
                closeAddModal();
                fetchConfig();
            } else {
                alert(`Erreur: ${data.error}`);
            }
        } catch (err) {
            alert('Erreur lors de l\'ajout du dépôt.');
        }
    });

    // --- MODAL SETTINGS ---
    btnSettings.addEventListener('click', () => {
        if (currentConfig) {
            settingCommitStyle.value = currentConfig.commit_style || 'smart_conventional';
            settingCommitTemplate.value = currentConfig.commit_message_template || '';
            settingActivityFilename.value = currentConfig.activity_file_name || 'ACTIVITY.md';
            settingRandomize.checked = !!currentConfig.randomize_schedule;
            settingMinRandom.value = currentConfig.min_random_delay_mins || 3;
            settingMaxRandom.value = currentConfig.max_random_delay_mins || 25;
            settingAiProvider.value = currentConfig.ai_provider || 'none';
            settingAiApiKey.value = currentConfig.ai_api_key || '';
            settingAiModel.value = currentConfig.ai_model || '';
        }
        
        const toggleAiSettings = () => {
            aiSettingsGroup.style.display = settingCommitStyle.value === 'smart_ai' ? 'block' : 'none';
        };
        settingCommitStyle.removeEventListener('change', toggleAiSettings);
        settingCommitStyle.addEventListener('change', toggleAiSettings);
        toggleAiSettings();

        modalSettings.classList.add('active');
    });

    const closeSettingsModal = () => modalSettings.classList.remove('active');
    btnCloseSettingsModal.addEventListener('click', closeSettingsModal);
    btnCancelSettings.addEventListener('click', closeSettingsModal);

    btnSaveSettings.addEventListener('click', async () => {
        const payload = {
            commit_style: settingCommitStyle.value,
            commit_message_template: settingCommitTemplate.value.trim(),
            activity_file_name: settingActivityFilename.value.trim(),
            randomize_schedule: settingRandomize.checked,
            min_random_delay_mins: parseInt(settingMinRandom.value) || 1,
            max_random_delay_mins: parseInt(settingMaxRandom.value) || 10,
            ai_provider: settingAiProvider.value,
            ai_api_key: settingAiApiKey.value.trim(),
            ai_model: settingAiModel.value.trim()
        };

        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        closeSettingsModal();
        fetchConfig();
    });

    function escapeHtml(str) {
        return (str || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
});
