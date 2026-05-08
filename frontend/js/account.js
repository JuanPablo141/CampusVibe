document.addEventListener("DOMContentLoaded", () => {
    // ==========================================
    // 1. SISTEMA DE ABAS (TABS)
    // ==========================================
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active de todos
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Adiciona active no clicado
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // ==========================================
    // 2. LÓGICA DE CASCATA (BLOCO -> CURSO)
    // ==========================================
    const blocoSelect = document.getElementById("bloco");
    const cursoSelect = document.getElementById("id_curso");

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

    blocoSelect.addEventListener("change", (e) => {
        const blocoId = e.target.value;
        const cursos = cursosPorBloco[blocoId];
        
        cursoSelect.innerHTML = '<option value="" disabled selected>Agora escolha seu curso...</option>';
        
        if (cursos) {
            cursos.forEach(curso => {
                const opt = document.createElement("option");
                opt.value = curso.id;
                opt.textContent = curso.nome;
                cursoSelect.appendChild(opt);
            });
            cursoSelect.disabled = false;
        } else {
            cursoSelect.disabled = true;
        }
    });

    // ==========================================
    // 3. CARREGAR DADOS DO USUÁRIO (REAL)
    // ==========================================
    const token = sessionStorage.getItem("access_token");
    
    // Se não tiver token, expulsa para o login
    if (!token) {
        window.location.href = "login.html";
        return;
    }

    async function loadUserProfile() {
        try {
            const response = await fetch("http://127.0.0.1:8000/users/me", {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                // Token inválido ou expirado
                sessionStorage.clear();
                window.location.href = "login.html";
                return;
            }

            if (!response.ok) throw new Error("Erro ao carregar perfil");

            const data = await response.json();
            
            // Preenche os campos do form
            document.getElementById("email").value = data.email;
            document.getElementById("nome").value = data.nome;
            
            // Dispara o bloco
            blocoSelect.value = data.id_bloco;
            blocoSelect.dispatchEvent(new Event('change'));
            
            // Espera a UI reagir e define o curso
            setTimeout(() => {
                cursoSelect.value = data.id_curso;
            }, 50);

        } catch (error) {
            console.error(error);
            document.getElementById("profile-error").textContent = "Falha ao carregar os dados. O servidor pode estar offline.";
            document.getElementById("profile-error").classList.remove("hidden");
        }
    }

    loadUserProfile();

    // ==========================================
    // 4. SUBMISSÃO DE FORMULÁRIOS (Frontend Security)
    // ==========================================
    
    // Perfil
    const profileForm = document.getElementById("profileForm");
    profileForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const nome = document.getElementById("nome").value.trim();
        const cursoId = parseInt(document.getElementById("id_curso").value, 10);
        const errBox = document.getElementById("profile-error");
        const succBox = document.getElementById("profile-success");

        errBox.classList.add("hidden");
        succBox.classList.add("hidden");

        if(!nome || isNaN(cursoId) || cursoId < 0) {
            errBox.textContent = "Preencha todos os campos corretamente.";
            errBox.classList.remove("hidden");
            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:8000/users/me", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ nome: nome, id_curso: cursoId })
            });

            const data = await response.json();

            if (!response.ok) {
                let msg = "Não foi possível atualizar o perfil.";
                if(data.detail) msg = typeof data.detail === "string" ? data.detail : data.detail[0].msg;
                throw new Error(msg);
            }

            succBox.textContent = "Perfil atualizado com sucesso!";
            succBox.classList.remove("hidden");
            
            setTimeout(() => { succBox.classList.add("hidden"); }, 3000);
        } catch (error) {
            errBox.textContent = error.message;
            errBox.classList.remove("hidden");
        }
    });

    // Segurança (Senha)
    const securityForm = document.getElementById("securityForm");
    securityForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const currPass = document.getElementById("current_password").value;
        const newPass = document.getElementById("new_password").value;
        const confPass = document.getElementById("confirm_password").value;
        
        const errBox = document.getElementById("security-error");
        const succBox = document.getElementById("security-success");
        const submitBtn = securityForm.querySelector("button[type='submit']");
        
        errBox.classList.add("hidden");
        succBox.classList.add("hidden");

        if (newPass.length < 8) {
            errBox.textContent = "A nova senha deve ter no mínimo 8 caracteres.";
            errBox.classList.remove("hidden");
            return;
        }

        if (newPass !== confPass) {
            errBox.textContent = "A nova senha e a confirmação não coincidem.";
            errBox.classList.remove("hidden");
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = "Validando criptografia...";

        try {
            const response = await fetch("http://127.0.0.1:8000/users/me/password", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    current_password: currPass,
                    new_password: newPass
                })
            });

            const data = await response.json();

            if (!response.ok) {
                // Se errar a senha, o backend retorna 401
                let msg = "Erro ao trocar a senha.";
                if(data.detail && typeof data.detail === "string") {
                    msg = data.detail; // Mostra "A senha atual está incorreta."
                }
                throw new Error(msg);
            }

            succBox.textContent = "Senha alterada com segurança! Sessões antigas foram invalidadas.";
            succBox.classList.remove("hidden");
            
            // Anti-shoulder-surfing: Limpa os campos visuais imediatamente após sucesso
            securityForm.reset();

            setTimeout(() => { succBox.classList.add("hidden"); }, 4000);
        } catch (error) {
            errBox.textContent = error.message;
            errBox.classList.remove("hidden");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Atualizar Senha";
        }
    });
});
