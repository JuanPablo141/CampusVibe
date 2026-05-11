document.addEventListener('DOMContentLoaded', async () => {
    const token = sessionStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    const blocksLayer = document.getElementById('blocks-layer');
    const blockPanel = document.getElementById('block-panel');
    const lastUpdate = document.getElementById('last-update');
    const legend = document.getElementById('map-legend');

    const blockPositions = [
        { left: '18%', top: '20%' },
        { left: '78%', top: '16%' },
        { left: '20%', top: '74%' },
        { left: '76%', top: '70%' }
    ];

    const vibeConfig = {
        'Alegria': { className: 'vibe-happy', color: '#4ade80', emoji: '😊' },
        'Feliz': { className: 'vibe-happy', color: '#22c55e', emoji: '🙂' },
        'Neutro': { className: 'vibe-neutral', color: '#facc15', emoji: '✨' },
        'Triste': { className: 'vibe-sad', color: '#60a5fa', emoji: '😰' },
        'Irritado': { className: 'vibe-angry', color: '#f87171', emoji: '😡' },
        'Sem dados': { className: 'vibe-empty', color: '#94a3b8', emoji: '◇' }
    };

    let selectedBlockId = null;
    let blocksCache = [];

    renderLegend();
    await fetchBlocksMap();
    setInterval(fetchBlocksMap, 30000);

    async function fetchBlocksMap() {
        try {
            blocksLayer.innerHTML = `<div class="blocks-loading"><span class="blocks-loading-dot"></span>Carregando blocos...</div>`;
            const response = await fetch('http://127.0.0.1:8000/stats/blocks-map', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) throw new Error('Falha ao buscar mapa dos blocos');

            const data = await response.json();
            blocksCache = data.blocos || [];
            renderBlocks(blocksCache);

            const currentBlock = blocksCache.find(block => String(block.id) === String(selectedBlockId)) || blocksCache[0];
            if (currentBlock) selectBlock(currentBlock.id);

            lastUpdate.textContent = `Atualizado às ${new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
        } catch (error) {
            console.error(error);
            blocksLayer.innerHTML = '';
            blockPanel.innerHTML = `<div class="error-box">Nao foi possivel carregar o mapa agora. Confira se a API esta rodando e tente novamente.</div>`;
            lastUpdate.textContent = 'Mapa indisponivel';
        }
    }

    function renderBlocks(blocks) {
        blocksLayer.innerHTML = blocks.map((block, index) => {
            const config = getVibeConfig(block.emocao_geral);
            const position = blockPositions[index % blockPositions.length];

            return `
                <button
                    class="block-marker ${String(block.id) === String(selectedBlockId) ? 'active' : ''}"
                    style="left: ${position.left}; top: ${position.top}; --accent: ${config.color};"
                    data-block-id="${block.id}"
                    aria-label="Abrir ${escapeHtml(block.nome)}"
                >
                    <span class="block-marker-top">
                        <span class="block-name">${escapeHtml(block.nome)}</span>
                        <span class="block-emoji">${config.emoji}</span>
                    </span>
                    <span class="block-vibe">${escapeHtml(block.emocao_geral)}</span>
                    <span class="block-meta">${block.total_comentarios} comentarios · ${block.total_cursos} cursos</span>
                </button>
            `;
        }).join('');

        document.querySelectorAll('.block-marker').forEach(marker => {
            marker.addEventListener('focus', () => selectBlock(marker.dataset.blockId));
            marker.addEventListener('click', () => selectBlock(marker.dataset.blockId));
        });
    }

    function selectBlock(blockId) {
        selectedBlockId = blockId;
        const block = blocksCache.find(item => String(item.id) === String(blockId));
        if (!block) return;

        document.querySelectorAll('.block-marker').forEach(marker => {
            marker.classList.toggle('active', String(marker.dataset.blockId) === String(blockId));
        });

        renderPanel(block);
    }

    function renderPanel(block) {
        const config = getVibeConfig(block.emocao_geral);
        const distribution = renderDistribution(block.distribuicao_emocoes || [], config.color);
        const courses = renderCourses(block.cursos || [], block.id);
        const reasons = renderReasons(block.comentarios_recentes || []);

        blockPanel.innerHTML = `
            <div class="panel-header">
                <div class="panel-emoji" style="box-shadow: 0 0 28px ${config.color}44;">${config.emoji}</div>
                <div>
                    <h2>${escapeHtml(block.nome)}</h2>
                    <p>${escapeHtml(block.emocao_geral)} · ${block.total_comentarios} comentarios</p>
                </div>
            </div>

            <div class="explanation-box">${escapeHtml(block.explicacao)}</div>

            <div class="panel-section">
                <h3>Distribuicao de emocoes</h3>
                <div class="emotion-bars">${distribution}</div>
            </div>

            <div class="panel-section">
                <h3>Cursos deste bloco</h3>
                <div class="course-list">${courses}</div>
            </div>

            <div class="panel-section">
                <h3>Comentarios que explicam</h3>
                <div class="reason-list">${reasons}</div>
            </div>

            <div class="panel-actions">
                <a class="panel-link" href="course_stats.html?block_id=${block.id}">Abrir Raio-X dos cursos</a>
            </div>
        `;
    }

    function renderDistribution(items, fallbackColor) {
        if (!items.length) {
            return `<div class="course-chip">Sem comentarios classificados ainda<span>◇</span></div>`;
        }

        const max = Math.max(...items.map(item => item.total), 1);
        return items.map(item => {
            const config = getVibeConfig(item.nome);
            const width = Math.max((item.total / max) * 100, 8);

            return `
                <div class="emotion-row" style="--accent: ${config.color || fallbackColor};">
                    <div class="emotion-row-label">
                        <span>${config.emoji} ${escapeHtml(item.nome)}</span>
                        <strong>${item.total}</strong>
                    </div>
                    <div class="emotion-track">
                        <div class="emotion-fill" style="width: ${width}%"></div>
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderCourses(courses, blockId) {
        if (!courses.length) {
            return `<div class="course-chip">Nenhum curso cadastrado<span>◇</span></div>`;
        }

        return courses.slice(0, 6).map(course => {
            const config = getVibeConfig(course.emocao_geral);
            return `
                <a class="course-chip" href="course_stats.html?block_id=${blockId}&course_id=${course.id}">
                    <span>${escapeHtml(course.nome)}</span>
                    <strong>${config.emoji}</strong>
                </a>
            `;
        }).join('');
    }

    function renderReasons(comments) {
        if (!comments.length) {
            return `<div class="reason-card"><p>Ainda nao ha comentarios classificados para explicar esta vibe.</p></div>`;
        }

        return comments.map(comment => {
            const date = new Date(comment.data_criacao).toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });

            return `
                <div class="reason-card">
                    <p>"${escapeHtml(comment.texto)}"</p>
                    <span>${comment.emoji} ${escapeHtml(comment.nome_emocao)} · ${escapeHtml(comment.nome_curso)} · ${date}</span>
                </div>
            `;
        }).join('');
    }

    function renderLegend() {
        legend.innerHTML = Object.entries(vibeConfig)
            .filter(([name]) => name !== 'Sem dados')
            .map(([name, config]) => `<span class="legend-pill">${config.emoji} ${name}</span>`)
            .join('');
    }

    function getVibeConfig(vibeName) {
        return vibeConfig[vibeName] || vibeConfig['Neutro'];
    }

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
