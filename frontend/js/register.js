document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    const errorBox = document.getElementById("error-message");
    const successBox = document.getElementById("success-message");
    const submitBtn = document.getElementById("submitBtn");
    
    // Elementos de Cascata
    const blocoSelect = document.getElementById("bloco");
    const cursoSelect = document.getElementById("id_curso");

    // Banco de Dados de Cursos espelhado no Frontend
    const cursosPorBloco = {
        "0": [
            { id: 0, nome: "Ciência da Computação" },
            { id: 4, nome: "Sistemas de Informação" },
            { id: 5, nome: "Redes de Computadores" },
            { id: 6, nome: "Análise e Desenvolvimento de Sistemas" },
            { id: 7, nome: "Engenharia da Computação" },
            { id: 8, nome: "Engenharia Civil" },
            { id: 9, nome: "Engenharia de Produção" },
            { id: 10, nome: "Engenharia Elétrica" },
            { id: 11, nome: "Engenharia Mecânica" },
            { id: 12, nome: "Engenharia Química" },
            { id: 13, nome: "Engenharia Ambiental" },
            { id: 14, nome: "Construção de Edifícios" },
            { id: 15, nome: "Data Science" },
            { id: 16, nome: "Game Design" }
        ],
        "1": [
            { id: 17, nome: "Administração" },
            { id: 18, nome: "Ciências Contábeis" },
            { id: 19, nome: "Ciências Econômicas" },
            { id: 20, nome: "Gestão Financeira" },
            { id: 21, nome: "Gestão Comercial" },
            { id: 22, nome: "Gestão de Recursos Humanos" },
            { id: 23, nome: "Gestão Pública" },
            { id: 24, nome: "Gestão Hospitalar" },
            { id: 25, nome: "Gestão da Qualidade" },
            { id: 26, nome: "Gestão de Turismo" },
            { id: 27, nome: "Logística" },
            { id: 28, nome: "Marketing" },
            { id: 29, nome: "Processos Gerenciais" },
            { id: 30, nome: "Empreendedorismo Digital" }
        ],
        "2": [
            { id: 31, nome: "Direito" },
            { id: 32, nome: "Serviço Social" }
        ],
        "3": [
            { id: 33, nome: "Farmácia" },
            { id: 34, nome: "Enfermagem" },
            { id: 35, nome: "Medicina" },
            { id: 36, nome: "Odontologia" },
            { id: 37, nome: "Psicologia" },
            { id: 38, nome: "Fisioterapia" },
            { id: 39, nome: "Nutrição" },
            { id: 40, nome: "Biomedicina" },
            { id: 41, nome: "Radiologia" },
            { id: 42, nome: "Estética e Cosmética" },
            { id: 43, nome: "Educação Física" },
            { id: 44, nome: "Fonoaudiologia" }
        ]
    };

    // Dinâmica Interativa: Ao escolher o bloco, carrega apenas seus cursos
    blocoSelect.addEventListener("change", (e) => {
        const blocoId = e.target.value;
        const cursos = cursosPorBloco[blocoId];
        
        // Limpa o select de curso
        cursoSelect.innerHTML = '<option value="" disabled selected>Agora escolha seu curso...</option>';
        
        if (cursos) {
            cursos.forEach(curso => {
                const opt = document.createElement("option");
                opt.value = curso.id;
                opt.textContent = curso.nome;
                cursoSelect.appendChild(opt);
            });
            cursoSelect.disabled = false; // Destrava o segundo select
        } else {
            cursoSelect.disabled = true;
        }
    });

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
        e.preventDefault();

        errorBox.classList.add("hidden");
        successBox.classList.add("hidden");

        const nome = sanitizeHTML(document.getElementById("nome").value.trim());
        const email = sanitizeHTML(document.getElementById("email").value.trim());
        const id_curso = parseInt(document.getElementById("id_curso").value, 10);
        const senha = document.getElementById("senha").value;
        const confirmar_senha = document.getElementById("confirmar_senha").value;

        // Validações
        if (senha.length < 8) {
            showError("A senha deve conter no mínimo 8 caracteres.");
            return;
        }

        if (senha !== confirmar_senha) {
            showError("As senhas não coincidem. Digite exatamente igual.");
            return;
        }

        if (isNaN(id_curso) || id_curso <= 0) {
            showError("Selecione um curso válido do Bloco escolhido.");
            return;
        }

        const payload = { 
            nome: nome, 
            email: email, 
            senha: senha, 
            confirmacao_senha: confirmar_senha,
            id_curso: id_curso 
        };

        submitBtn.disabled = true;
        submitBtn.textContent = "Processando criptografia...";

        try {
            const response = await fetch("http://127.0.0.1:8000/users/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                // O FastAPI retorna um array de objetos em data.detail quando dá erro 422
                let errorMessage = "Não foi possível realizar o cadastro.";
                if (Array.isArray(data.detail)) {
                    // Pega a mensagem do primeiro erro do Pydantic
                    errorMessage = "Dados inválidos: " + data.detail[0].msg;
                } else if (typeof data.detail === "string") {
                    errorMessage = data.detail;
                }
                throw new Error(errorMessage);
            }

            showSuccess("Conta criada com sucesso! Redirecionando...");
            form.reset();
            cursoSelect.disabled = true;

            setTimeout(() => { window.location.href = "login.html"; }, 2000);

        } catch (error) {
            console.error("[Security Watchdog] Operação interrompida:", error);
            showError(error.message || "Falha na conexão segura com o servidor.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Finalizar Cadastro Seguro";
        }
    });
});
