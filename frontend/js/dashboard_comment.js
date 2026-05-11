document.addEventListener('DOMContentLoaded', async () => {
    const token = sessionStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    const userInfo = document.getElementById('user-info');
    const form = document.getElementById('commentForm');
    const textarea = document.getElementById('comment-text');
    const charCounter = document.getElementById('char-counter');
    const submitBtn = document.getElementById('submitBtn');
    const errorBox = document.getElementById('comment-error');

    const resultCard = document.getElementById('result-card');
    const resultEmoji = document.getElementById('result-emoji');
    const resultName = document.getElementById('result-name');
    const resultDescription = document.getElementById('result-description');
    const resultText = document.getElementById('result-text');
    const newCommentBtn = document.getElementById('newCommentBtn');

    const MAX_CHARS = 1000;

    const vibeMap = {
        'Alegria':  { class: 'vibe-happy',   emoji: '😊', titulo: 'Alegria',  texto: 'Seu texto tem um tom claramente positivo e animado.' },
        'Feliz':    { class: 'vibe-happy',   emoji: '🙂', titulo: 'Feliz',    texto: 'Seu texto traz uma vibe leve e otimista.' },
        'Neutro':   { class: 'vibe-neutral', emoji: '✨', titulo: 'Neutro',   texto: 'Seu texto é informativo e sem carga emocional forte.' },
        'Triste':   { class: 'vibe-sad',     emoji: '😰', titulo: 'Triste',   texto: 'Seu texto carrega sinais de desânimo ou cansaço.' },
        'Irritado': { class: 'vibe-angry',   emoji: '😡', titulo: 'Irritado', texto: 'Seu texto traz indícios de frustração ou raiva.' },
    };

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function showError(message) {
        errorBox.textContent = message;
        errorBox.classList.remove('hidden');
    }

    function clearError() {
        errorBox.classList.add('hidden');
        errorBox.textContent = '';
    }

    async function loadUserContext() {
        try {
            const profileResp = await fetch('http://127.0.0.1:8000/users/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (profileResp.status === 401) {
                sessionStorage.clear();
                window.location.href = 'login.html';
                return;
            }
            if (!profileResp.ok) throw new Error('Falha ao buscar perfil');

            const profile = await profileResp.json();

            // Busca cursos do bloco do usuário para descobrir o nome do curso vinculado.
            const coursesResp = await fetch(`http://127.0.0.1:8000/stats/courses-by-block/${profile.id_bloco}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            let nomeCurso = `Curso #${profile.id_curso}`;
            if (coursesResp.ok) {
                const courses = await coursesResp.json();
                const match = courses.find(c => String(c.id) === String(profile.id_curso));
                if (match) nomeCurso = match.nome;
            }

            userInfo.textContent = `${profile.nome} · ${nomeCurso}`;
        } catch (error) {
            console.error(error);
            userInfo.textContent = 'Perfil indisponível no momento';
        }
    }

    function updateCharCounter() {
        const len = textarea.value.length;
        charCounter.textContent = `${len} / ${MAX_CHARS}`;
        charCounter.classList.remove('near-limit', 'at-limit');
        if (len >= MAX_CHARS) charCounter.classList.add('at-limit');
        else if (len >= MAX_CHARS * 0.85) charCounter.classList.add('near-limit');
    }

    function renderResult(emocao, textoOriginal) {
        const config = vibeMap[emocao] || vibeMap['Neutro'];

        resultCard.classList.remove('vibe-happy', 'vibe-sad', 'vibe-angry', 'vibe-neutral');
        resultCard.classList.add(config.class);

        resultEmoji.textContent = config.emoji;
        resultName.textContent = config.titulo;
        resultDescription.textContent = config.texto;
        resultText.innerHTML = escapeHtml(textoOriginal);

        resultCard.classList.remove('hidden');
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    textarea.addEventListener('input', updateCharCounter);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearError();

        const texto = textarea.value.trim();
        if (texto.length < 3) {
            showError('Escreva um comentário com pelo menos 3 caracteres.');
            return;
        }
        if (texto.length > MAX_CHARS) {
            showError(`O comentário não pode ultrapassar ${MAX_CHARS} caracteres.`);
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Classificando emoção...';

        try {
            const response = await fetch('http://127.0.0.1:8000/comentarios/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ texto })
            });

            if (response.status === 401) {
                sessionStorage.clear();
                window.location.href = 'login.html';
                return;
            }

            const data = await response.json();
            if (!response.ok) {
                const detail = data.detail;
                const msg = typeof detail === 'string'
                    ? detail
                    : (Array.isArray(detail) && detail[0]?.msg) || 'Não foi possível enviar seu comentário.';
                throw new Error(msg);
            }

            renderResult(data.emocao_identificada, texto);
            form.classList.add('hidden');
        } catch (error) {
            showError(error.message || 'Erro inesperado. Tente novamente.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Enviar para a IA classificar';
        }
    });

    newCommentBtn.addEventListener('click', () => {
        resultCard.classList.add('hidden');
        form.classList.remove('hidden');
        textarea.value = '';
        updateCharCounter();
        textarea.focus();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    updateCharCounter();
    await loadUserContext();
});
