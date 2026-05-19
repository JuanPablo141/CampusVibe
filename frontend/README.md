# Frontend — CampusVibe

Frontend do CampusVibe construído **sem frameworks** — apenas HTML5, CSS3 e JavaScript puro. Cada página é autônoma, com seu próprio script e folha de estilos. A comunicação com a API é feita via `fetch`, e a sessão do usuário é guardada em `sessionStorage` (morre ao fechar a aba).

URL em produção: https://campusvibe-lovat.vercel.app/

---

## Stack

| Tecnologia | Função |
|------------|--------|
| HTML5 | Estrutura semântica das páginas |
| CSS3 | Estilos, variáveis customizadas, animações |
| JavaScript (vanilla) | Lógica de cada página, chamadas `fetch`, manipulação do DOM |
| Fonte | Outfit (Google Fonts, importada no `global.css`) |

**Sem build, sem npm, sem bundler.** É só abrir os arquivos em um servidor estático e funciona.

---

## Estrutura interna

```
frontend/
├── index.html                  # Landing page pública
├── pages/                      # Páginas autenticadas
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html          # Menu principal pós-login
│   ├── dashboard_comment.html  # Tela de envio de comentário
│   ├── dashboard_map.html      # Mapa de Blocos
│   ├── course_stats.html       # Raio-X do Curso
│   └── account.html            # Configurações de conta
├── js/
│   ├── config.js               # API_BASE_URL — apontar aqui para mudar o backend
│   ├── login.js
│   ├── register.js
│   ├── dashboard.js
│   ├── dashboard_comment.js
│   ├── dashboard_map.js
│   ├── course_stats.js
│   └── account.js
└── css/
    ├── global.css              # Variáveis CSS, reset, classes utilitárias (.glass, .btn)
    ├── landing.css
    ├── login.css
    ├── register.css
    ├── dashboard.css
    ├── dashboard_comment.css
    ├── dashboard_map.css
    ├── course_stats.css
    └── account.css
```

---

## Páginas

| Página | Auth | Função | Endpoints consumidos |
|--------|------|--------|----------------------|
| `index.html` | Não | Landing page com apresentação, fluxo e equipe | — |
| `pages/login.html` | Não | Login do aluno | `POST /users/login` |
| `pages/register.html` | Não | Cadastro com seletor cascata Bloco → Curso | `POST /users/register` |
| `pages/dashboard.html` | Sim | Menu principal (4 cards de navegação) | — (apenas guard de rota) |
| `pages/dashboard_comment.html` | Sim | Envio de comentário com classificação por IA | `GET /users/me`, `GET /stats/courses-by-block/{id}`, `POST /comentarios/` |
| `pages/dashboard_map.html` | Sim | Mapa de Blocos com auto-refresh a cada 30s | `GET /stats/blocks-map` |
| `pages/course_stats.html` | Sim | Raio-X do Curso com filtros e feed de comentários | `GET /stats/course`, `GET /stats/courses-by-block/{id}`, `GET /users/me` |
| `pages/account.html` | Sim | Edição de perfil e troca de senha | `GET /users/me`, `PUT /users/me`, `PUT /users/me/password` |

---

## Autenticação

O frontend usa JWT armazenado em `sessionStorage`:

```javascript
// Após o login bem-sucedido:
sessionStorage.setItem("access_token", data.access_token);
sessionStorage.setItem("user_data", JSON.stringify(data.usuario));

// Em requisições protegidas:
fetch(`${API_BASE_URL}/comentarios/`, {
    method: "POST",
    headers: {
        "Authorization": `Bearer ${sessionStorage.getItem("access_token")}`,
        "Content-Type": "application/json"
    },
    body: JSON.stringify({ texto })
});
```

**Por que `sessionStorage` e não `localStorage`?** O `sessionStorage` é apagado quando a aba é fechada, limitando a janela de exposição do token. O `localStorage` persistiria até a expiração de 7 dias do JWT, mesmo em computadores compartilhados (laboratório da faculdade).

### Guards de rota

Cada página autenticada começa com a mesma verificação:

```javascript
const token = sessionStorage.getItem("access_token");
if (!token) {
    window.location.href = "/pages/login.html";
    return;
}
```

### Proteções implementadas no frontend

- **Limpeza preventiva no login** — `sessionStorage.removeItem("access_token")` antes de renderizar a tela de login (força logout de sessões presas)
- **Sanitização de XSS** — inputs passam por `document.createElement('div').textContent` antes de serem enviados
- **Anti-double-submit** — botão de submit desabilitado durante a requisição
- **Mensagem genérica de erro no login** — mesmo erro para email inexistente e senha errada (previne enumeração de usuários)
- **Sem `e.preventDefault()` ausente** — todos os forms evitam o reload que poderia expor a senha via parâmetros GET na URL

---

## Setup local

### Pré-requisitos

- Um servidor estático (Python, Node, ou extensão do VS Code)
- Backend rodando em algum lugar (localmente ou Railway) — ver [`../backend/README.md`](../backend/README.md)

### Servir os arquivos

Qualquer um destes funciona:

```bash
# Opção 1: Python (built-in)
cd frontend
python -m http.server 5500
# Acesse http://127.0.0.1:5500

# Opção 2: Node (npx, sem instalar nada)
cd frontend
npx serve -p 5500

# Opção 3: VS Code Live Server
# Instale a extensão "Live Server" e clique com botão direito em index.html → "Open with Live Server"
```

---

## Configurar a URL da API

O frontend lê o endereço do backend de um único lugar: [`js/config.js`](./js/config.js).

```javascript
// js/config.js
const API_BASE_URL = "https://project-root-production-b179.up.railway.app";
```

**Para apontar para o backend local**, edite para:

```javascript
const API_BASE_URL = "http://127.0.0.1:8000";
```

Todos os arquivos `.js` da pasta importam essa constante e a usam nas chamadas `fetch`, então alterar `config.js` muda todo o frontend de uma vez.

---

## Deploy

O frontend está hospedado na **Vercel** como projeto estático. Como não há build step, a Vercel apenas serve os arquivos diretamente do repositório.

Para fazer o deploy de uma versão atualizada:

1. Faça push no GitHub na branch que a Vercel observa (`main`)
2. A Vercel detecta o push e publica automaticamente em https://campusvibe-lovat.vercel.app/

Antes de fazer deploy de uma versão "local", **lembre de garantir que o `API_BASE_URL` em [`js/config.js`](./js/config.js) aponta para o backend de produção** (Railway), não para `http://127.0.0.1:8000`.

---

## Notas

- **`package.json` mínimo** — existe um na raiz da pasta, mas é apenas o esqueleto de nome e versão. Não há dependências instaladas, não há scripts npm executados. É vestigial e pode ser ignorado.
- **Acessibilidade** — o mapa de blocos usa `aria-hidden` nos elementos puramente decorativos do mapa fictício; os marcadores de bloco são `<button>` para serem navegáveis por teclado.
- **Sem cache busting** — alterações em `.js` e `.css` podem exigir `Ctrl+F5` no navegador para serem refletidas.
- **CORS** — o backend libera todas as origens em desenvolvimento, então o frontend local pode chamar o backend em Railway sem problemas.
