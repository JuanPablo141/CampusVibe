document.addEventListener("DOMContentLoaded", () => {
    // SECURITY: Verifica se o usuário tem permissão para estar nesta página
    const token = sessionStorage.getItem("access_token");
    if (!token) {
        window.location.href = "login.html";
        return;
    }

    // Opcional: Mostra o nome real do usuário na saudação (se os dados estiverem no sessionStorage)
    const userDataStr = sessionStorage.getItem("user_data");
    if (userDataStr) {
        try {
            const userData = JSON.parse(userDataStr);
            const userGreeting = document.querySelector(".user-greeting");
            if (userGreeting && userData.nome) {
                // Pega apenas o primeiro nome
                const primeiroNome = userData.nome.split(" ")[0];
                userGreeting.textContent = `Olá, ${primeiroNome}!`;
            }
        } catch (e) {
            console.error("Erro ao ler user_data", e);
        }
    }

    // Botão de Logout
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            // SECURITY: Limpa os tokens da sessão para que não fiquem na memória
            sessionStorage.clear();
            // Redireciona para a página principal (landing page)
            window.location.href = "../index.html";
        });
    }
});
