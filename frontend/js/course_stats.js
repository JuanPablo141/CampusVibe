document.addEventListener('DOMContentLoaded', async () => {
    const token = sessionStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    const commentsContainer = document.getElementById('comments-container');
    const emojiFiltersContainer = document.getElementById('emoji-filters');
    const courseSelector = document.getElementById('course-selector');
    const blockSelector = document.getElementById('block-selector');
    const pageParams = new URLSearchParams(window.location.search);
    const initialBlockId = pageParams.get('block_id');
    const initialCourseId = pageParams.get('course_id');

    let selectedEmoji = 'all';

    async function fetchData(courseId = null, emoji = 'all') {
        try {
            let url = `${API_BASE_URL}/stats/course`;
            const params = new URLSearchParams();
            if (courseId !== null && courseId !== undefined && courseId !== "") params.append('id_curso', courseId);
            if (emoji && emoji !== 'all') params.append('emoji', emoji);
            if (params.toString()) url += `?${params.toString()}`;

            const response = await fetch(url, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('Falha ao buscar dados');
            const data = await response.json();

            // Configuração inicial dos seletores
            if (!blockSelector.dataset.initialized) {
                blockSelector.dataset.initialized = 'true';
                await initializeSelectors(data);
                // Se viemos com course_id na URL, data já é do curso correto — só atualiza UI
                if (initialCourseId) {
                    updateMetrics(data);
                    renderEmojiFilters(data.filtros_emoji, emoji);
                    renderComments(data.comentarios);
                    return;
                }
                // Sem course_id na URL: redireciona se o seletor aponta para curso diferente
                const selectedCourse = courseSelector.value;
                if (selectedCourse && String(selectedCourse) !== String(data.id_curso)) {
                    await fetchData(selectedCourse, selectedEmoji);
                    return;
                }
            }

            // Atualiza Interface Principal
            updateMetrics(data);
            renderEmojiFilters(data.filtros_emoji, emoji);
            renderComments(data.comentarios);

        } catch (error) {
            console.error(error);
            commentsContainer.innerHTML = "<p class='error'>Ocorreu um erro ao carregar os dados. Tente recarregar a página.</p>";
        }
    }

    async function initializeSelectors(data) {
        // 1. Popula Blocos
        blockSelector.innerHTML = '<option value="" disabled>Selecione um Bloco</option>' + 
            data.lista_blocos.map(b => `<option value="${b.id}">${b.nome}</option>`).join("");
        
        // 2. Busca o perfil do usuário para saber o bloco dele
        const profileResp = await fetch(`${API_BASE_URL}/users/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (profileResp.ok) {
            const profile = await profileResp.json();
            const targetBlockId = initialBlockId || profile.id_bloco;
            const targetCourseId = initialCourseId || profile.id_curso;

            blockSelector.value = targetBlockId;
            
            // 3. Carrega cursos do bloco escolhido pelo mapa ou do usuário
            return await updateCourseSelectorByBlock(targetBlockId, targetCourseId);
        }
        return null;
    }

    async function updateCourseSelectorByBlock(blockId, selectedCourseId = null) {
        try {
            const response = await fetch(`${API_BASE_URL}/stats/courses-by-block/${blockId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('Erro ao buscar cursos do bloco');
            const courses = await response.json();

            courseSelector.innerHTML = '<option value="" disabled>Escolha o curso...</option>' + 
                courses.map(c => `<option value="${c.id}">${c.nome}</option>`).join("");
            
            courseSelector.disabled = false;
            if (selectedCourseId !== null && selectedCourseId !== undefined) {
                courseSelector.value = selectedCourseId;
            }
            if (!courseSelector.value && courses.length > 0) {
                courseSelector.value = courses[0].id;
            }

            return courseSelector.value;
        } catch (error) {
            console.error(error);
            return null;
        }
    }

    function updateMetrics(data) {
        document.getElementById("course-name").textContent = data.curso;
        document.getElementById("vibe-emoji").textContent = data.emoji_vibe;
        document.getElementById("total-comments").textContent = data.total_comentarios;
        
        const highlightsCard = document.querySelector(".metric-card.highlights");
        const highlightsIcon = highlightsCard.querySelector(".metric-icon");
        
        const vibeMap = {
            "Alegria": { nome: "Alegria", class: "vibe-happy", emoji: "😊" },
            "Feliz": { nome: "Feliz", class: "vibe-happy", emoji: "🙂" },
            "Neutro": { nome: "Neutro", class: "vibe-neutral", emoji: "✨" },
            "Triste": { nome: "Triste", class: "vibe-sad", emoji: "😰" },
            "Irritado": { nome: "Irritado", class: "vibe-angry", emoji: "😡" }
        };

        const config = vibeMap[data.emoji_vibe] || vibeMap[data.vibe_predominante] || vibeMap["Neutro"];
        
        document.getElementById("top-vibe").textContent = config.nome;
        highlightsIcon.textContent = config.emoji;
        document.getElementById("vibe-emoji").textContent = config.emoji;

        // Limpa classes anteriores e adiciona a nova
        highlightsCard.classList.remove("vibe-happy", "vibe-sad", "vibe-angry", "vibe-tired", "vibe-neutral");
        highlightsCard.classList.add(config.class);
    }

    function renderEmojiFilters(filtros, currentSelected) {
        let html = `<button class="filter-btn ${currentSelected === 'all' ? 'active' : ''}" data-emoji="all">Todas</button>`;
        filtros.forEach(f => {
            html += `<button class="filter-btn ${currentSelected === f.emoji ? 'active' : ''}" data-emoji="${f.emoji}">
                        ${f.emoji} ${f.nome.split(" ")[0]}
                    </button>`;
        });
        emojiFiltersContainer.innerHTML = html;

        document.querySelectorAll(".filter-btn").forEach(btn => {
            btn.onclick = () => {
                selectedEmoji = btn.dataset.emoji;
                fetchData(courseSelector.value, selectedEmoji);
            };
        });
    }

    function renderComments(comments) {
        if (!comments || comments.length === 0) {
            commentsContainer.innerHTML = "<p class='empty-msg'>Nenhum comentário encontrado para esta vibe.</p>";
            return;
        }

        commentsContainer.innerHTML = comments.map(c => {
            let vibeClass = "";
            if (c.emoji === "😊") vibeClass = "vibe-happy";
            if (c.emoji === "😰") vibeClass = "vibe-sad";
            if (c.emoji === "😡") vibeClass = "vibe-angry";
            if (c.emoji === "😴") vibeClass = "vibe-tired";
            if (c.emoji === "✨") vibeClass = "vibe-neutral";

            const dataFormatada = new Date(c.data_criacao).toLocaleDateString('pt-BR', {
                day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
            });

            return `
                <div class="comment-card glass ${vibeClass}">
                    <div class="comment-header">
                        <span class="comment-emoji">${c.emoji}</span>
                        <span class="comment-date">${dataFormatada}</span>
                    </div>
                    <p class="comment-text">"${c.texto}"</p>
                </div>
            `;
        }).join("");
    }

    blockSelector.addEventListener('change', async (e) => {
        const selectedCourse = await updateCourseSelectorByBlock(e.target.value);
        if (selectedCourse) {
            selectedEmoji = 'all';
            fetchData(selectedCourse, selectedEmoji);
        }
    });

    courseSelector.addEventListener('change', (e) => {
        selectedEmoji = 'all';
        fetchData(e.target.value, selectedEmoji);
    });

    // Início — passa initialCourseId direto para evitar double-fetch e exibir o curso correto
    fetchData(initialCourseId || null);
});
