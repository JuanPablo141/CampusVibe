document.addEventListener("DOMContentLoaded", () => {
    
    // SECURITY: Forced Logout local
    // Sempre que o usuário entra na tela de login, nós destruímos qualquer token ou dado de sessão 
    // anterior que possa ter ficado preso na memória do navegador.
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user_data");

    const form = document.getElementById("loginForm");
    const errorBox = document.getElementById("error-message");
    const successBox = document.getElementById("success-message");
    const submitBtn = document.getElementById("submitBtn");

    // Defesa em Profundidade: Sanitização de input XSS
    const sanitizeHTML = (str) => {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    };

    const showError = (message) => {
        errorBox.textContent = message;
        errorBox.classList.remove("hidden");
        successBox.classList.add("hidden");
    };

    const showSuccess = (message) => {
        successBox.textContent = message;
        successBox.classList.remove("hidden");
        errorBox.classList.add("hidden");
    };

    form.addEventListener("submit", async (e) => {
        // SECURITY: Impede o reload que poderia expor dados da senha via parâmetros GET na URL
        e.preventDefault(); 

        errorBox.classList.add("hidden");
        successBox.classList.add("hidden");

        const email = sanitizeHTML(document.getElementById("email").value.trim());
        const senha = document.getElementById("senha").value;

        // Validação Mínima Local
        if (!email || !senha) {
            showError("Regra de Segurança: Preencha todos os campos corretamente.");
            return;
        }

        const payload = { 
            email: email, 
            senha: senha 
        };

        // Mitigação contra "Button Smashing" (Múltiplos envios)
        submitBtn.disabled = true;
        submitBtn.textContent = "Verificando credenciais...";

        try {
            const response = await fetch(`${API_BASE_URL}/users/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            // Lida com erros do Backend
            if (!response.ok) {
                // SECURITY: Prevenção de User Enumeration / Information Leakage
                // Se der erro 401 ou 422, damos a mesma mensagem padronizada.
                let errorMessage = "E-mail ou senha incorretos"; 
                if (data.detail && typeof data.detail === "string" && response.status !== 401) {
                    errorMessage = data.detail;
                }
                throw new Error(errorMessage);
            }

            showSuccess("Acesso Autenticado! Desbloqueando seu acesso...");

            // SECURITY: Session Storage (O Token morre quando a aba é fechada, evitando roubo)
            sessionStorage.setItem("access_token", data.access_token);
            sessionStorage.setItem("user_data", JSON.stringify(data.usuario));

            // SECURITY: Wipe-out (Limpa o form da tela imediatamente)
            form.reset();

            // Redirecionamento com delay para feedback visual
            setTimeout(() => { 
                // A definir na próxima sprint: Tela Social
                window.location.href = "dashboard.html"; 
            }, 1500);

        } catch (error) {
            console.error("[Auth Security Flow] Tentativa de Login Falhou:", error);
            showError(error.message || "Erro de conexão segura. Nossos servidores podem estar em manutenção.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Entrando...";
        }
    });
});
