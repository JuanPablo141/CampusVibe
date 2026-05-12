<div align="center">

# CampusVibe

### Qual é a **vibe** do seu curso hoje?

Plataforma anônima de análise de sentimentos acadêmicos com Inteligência Artificial — desenvolvida como projeto de faculdade pelos alunos de Ciência da Computação da UNINASSAU (campus Graças).

[![Live Demo](https://img.shields.io/badge/demo-online-brightgreen?style=for-the-badge)](https://campusvibe-lovat.vercel.app)
[![Made with FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL + pgvector](https://img.shields.io/badge/database-PostgreSQL%20%2B%20pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Vanilla JS](https://img.shields.io/badge/frontend-Vanilla%20JS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

**[🌐 Acessar a aplicação ao vivo →](https://campusvibe-lovat.vercel.app)**

</div>

---

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [A ideia inicial](#a-ideia-inicial)
- [O que o sistema faz](#o-que-o-sistema-faz)
- [Como a IA classifica emoções](#como-a-ia-classifica-emoções)
- [Stack tecnológica](#stack-tecnológica)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como rodar localmente](#como-rodar-localmente)
- [Como testar a aplicação](#como-testar-a-aplicação)
- [Evolução do projeto](#evolução-do-projeto)
- [Equipe](#equipe)
- [Documentação técnica](#documentação-técnica)

---

## Sobre o projeto

Toda turma da faculdade tem aquele professor que ninguém gosta, aquela prova que destruiu o semestre, aquela aula que foi um divisor de águas. Mas essa informação fica perdida em conversas de corredor — a coordenação nunca sabe, os calouros chegam às cegas e os próprios alunos não conseguem ler o clima do seu próprio curso.

**O CampusVibe resolve isso transformando desabafos anônimos em dados.**

Um aluno escreve como foi a aula de hoje, e a Inteligência Artificial transforma o texto em uma emoção (Alegria, Irritado ou Neutro). Cruzando todos os comentários, o sistema calcula a **emoção predominante de cada curso** e, subindo um nível, **a vibe geral de cada bloco do campus** — em tempo real, com dashboards visuais.

```
Comentário do aluno
       ↓
   Pipeline de IA (fastembed + pgvector + KNN)
       ↓
   Classificação de emoção por comentário
       ↓
   Moda estatística por curso  (com regras de desempate)
       ↓
   Moda dos cursos por bloco   (com as mesmas regras)
       ↓
   Dashboard visual em tempo real
```

---

## A ideia inicial

O projeto nasceu como exigência acadêmica da disciplina de Banco de Dados — precisávamos construir um sistema completo que demonstrasse modelagem relacional, normalização e SQL avançado. Mas, em vez de fazer "mais um CRUD de biblioteca", a equipe quis algo que combinasse:

1. **Um problema real** que afetasse a vida na faculdade.
2. **Banco de dados como protagonista** — não apenas como persistência burra.
3. **Uma camada de inteligência** que justificasse a complexidade.

A ideia evoluiu rapidamente do conceito de "termômetro de humor da turma" para uma plataforma estruturada com:

- **Autenticação real** (JWT + Argon2)
- **PostgreSQL com extensão `pgvector`** para armazenar embeddings de IA
- **Pipeline de NLP local** (sem custo de API externa)
- **Dashboards interativos** que respondem ao banco em tempo real
- **Regras de negócio não-triviais** (moda estatística com desempate em duas camadas)

O nome **CampusVibe** veio do fato de que a "vibe" do curso é uma sensação intuitiva que os alunos têm, mas que ninguém nunca conseguiu medir. Esse projeto tenta exatamente isso.

---

## O que o sistema faz

### Para o aluno

| Funcionalidade | O que faz |
|---|---|
| **Cadastro** | Aluno se registra escolhendo bloco → curso (seletor cascata). Senha protegida com Argon2. |
| **Login** | Autenticação via JWT com expiração de 7 dias. Token guardado em `sessionStorage` (morre ao fechar a aba). |
| **Comentário com IA** | Aluno escreve um desabafo anônimo. A IA classifica a emoção em tempo real e mostra de volta. |
| **Mapa de Blocos** | Visualização tipo "mapa do campus" mostrando a vibe atual de cada bloco. Auto-refresh a cada 30s. |
| **Raio-X do Curso** | Dashboard com vibe predominante, distribuição de emoções, feed de comentários filtráveis por emoji. |
| **Minha Conta** | Atualização de perfil (nome, curso) e troca de senha. |

### Para o sistema

- **Pipeline de IA local** — sem chamada externa, sem custo de API, sem latência de rede.
- **Busca vetorial nativa** via `pgvector` com índice HNSW.
- **Classificação KNN** com voto ponderado sobre 190 frases de referência.
- **Léxico de polaridade** que age como rede de segurança quando o modelo de embeddings tropeça em vocabulário acadêmico.
- **Regras de desempate em duas camadas** (curso e bloco) gerando emoções compostas (Feliz, Triste) a partir de empates entre as base.

### Galeria de emoções

| Emoção | Emoji | Como surge |
|---|---|---|
| Alegria | 😊 | Detectada diretamente pela IA |
| Irritado | 😡 | Detectada diretamente pela IA |
| Neutro | ✨ | Detectada diretamente pela IA |
| Feliz | 🙂 | Empate entre Alegria e Neutro |
| Triste | 😰 | Empate entre Irritado e Neutro |
| Sem dados | ◇ | Nenhum comentário classificado ainda |

---

## Como a IA classifica emoções

A classificação é feita 100% **localmente**, sem depender de OpenAI ou qualquer API externa. Combina três camadas que se complementam:

### 1. Embedding semântico

O texto do aluno passa pelo modelo `paraphrase-multilingual-MiniLM-L12-v2` (via [fastembed](https://github.com/qdrant/fastembed)) e vira um vetor de **384 dimensões** que representa o significado da frase.

### 2. KNN com voto ponderado

Em vez de comparar contra um "centroide médio" de cada emoção (abordagem que falhava feio em frases curtas), o sistema mantém **190 frases de referência individuais** no banco. Para classificar, busca os **7 vizinhos mais próximos** via distância de cosseno e vota com peso inverso à distância:

```sql
WITH knn AS (
    SELECT em.nome_emocao, (ex.vetor <=> e.vetor) AS distancia
    FROM embedding e
    CROSS JOIN emocao_exemplo ex
    JOIN emocao em ON em.id_emocao = ex.id_emocao
    WHERE e.id_comentario = $1
    ORDER BY distancia ASC LIMIT 7
)
SELECT nome_emocao, SUM(1.0 / (distancia + 0.05)) AS score
FROM knn GROUP BY nome_emocao ORDER BY score DESC;
```

### 3. Léxico de polaridade

O modelo de embeddings é treinado para similaridade semântica geral, não para sentimento. Resultado: "péssima aula" parecia "ótima aula" (ambas falam de aula). Para corrigir esse ponto cego, mantemos uma lista de ~120 palavras de polaridade clara (péssimo, horrível, adorei, incrível…) que sobrescreve o KNN quando ele está indeciso ou claramente errado.

**Resultado final:** classificação correta para frases como:

| Entrada | Antes | Depois |
|---|---|---|
| "péssima aula" | Neutro ❌ | Irritado ✓ |
| "ótima aula" | Neutro ❌ | Alegria ✓ |
| "odiei a prova" | Neutro ❌ | Irritado ✓ |
| "tirei 10" | Neutro ❌ | Alegria ✓ |
| "hoje tem aula de cálculo" | Neutro ✓ | Neutro ✓ |

Detalhes técnicos completos em [`docs/ARCHITECTURE.md § 6 — Pipeline de IA`](docs/ARCHITECTURE.md#6-pipeline-de-ia).

---

## Stack tecnológica

| Camada | Tecnologia | Por quê |
|---|---|---|
| **Backend** | Python 3.12 + FastAPI | Performance, validação automática via Pydantic, documentação Swagger gratuita |
| **Banco** | PostgreSQL + `pgvector` | Único banco para dados relacionais E busca vetorial (sem precisar de Pinecone/Weaviate) |
| **Driver DB** | psycopg3 | Suporte nativo a pgvector + async-ready |
| **IA / NLP** | fastembed + MiniLM-L12-v2 | Roda local, é multilíngue (português incluso), 384 dim caem bem em produção |
| **Auth** | PyJWT + Argon2 | Argon2 venceu a Password Hashing Competition em 2015 |
| **Frontend** | HTML5 + CSS3 + JavaScript puro | Zero build, zero framework — para provar que não precisamos de React para um projeto bem feito |
| **Deploy Backend** | Railway | Free tier funcional, suporta pgvector no Postgres |
| **Deploy Frontend** | Vercel | CDN global, deploy automático no push da `main` |
| **Banco em produção** | Supabase (Postgres + pgvector) | Free tier generoso, pgvector pré-instalado |

---

## Estrutura do repositório

```
project-root/
├── backend/
│   └── app/
│       ├── main.py                 # FastAPI bootstrap + CORS + routers
│       ├── dependencies.py         # get_db_connection, get_current_user (JWT)
│       ├── routes/                 # users, comentarios, emotions, vectors, stats, dashboards, health
│       ├── services/               # vector_service, emotion_classification_service, login, register…
│       ├── respositories/          # Acesso a banco (1 repo por entidade)
│       └── schemas/                # Pydantic models para validação
├── frontend/
│   ├── index.html                  # Landing page
│   ├── pages/                      # login, register, dashboard, dashboard_comment, dashboard_map, course_stats, account
│   ├── js/                         # 1 .js por página, sem build
│   └── css/                        # 1 .css por página + global.css com variáveis e .glass
├── database/
│   └── schema/                     # Migrations SQL numeradas (001…005)
└── docs/
    └── ARCHITECTURE.md             # Documentação técnica completa (12 seções)
```

---

## Como rodar localmente

### Pré-requisitos

- Python 3.12+
- PostgreSQL 14+ com extensão `pgvector` instalada
- Node não é necessário (frontend é HTML puro)

### 1. Clone e instale o backend

```bash
git clone https://github.com/JuanPablo141/project-root.git
cd project-root/backend

python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 2. Configure o banco

Crie um arquivo `backend/.env`:

```env
DATABASE_URL=postgresql://usuario:senha@host:5432/database
```

Aplique as migrations na ordem:

```bash
psql "$DATABASE_URL" -f database/schema/001_initial_schema_v1.sql
psql "$DATABASE_URL" -f database/schema/002_vector_schema.sql
psql "$DATABASE_URL" -f database/schema/003_emotions_schema.sql
psql "$DATABASE_URL" -f database/schema/004_seed_blocos_cursos.sql
psql "$DATABASE_URL" -f database/schema/005_emocao_exemplo.sql
```

### 3. Suba a API

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload
```

A API ficará em `http://127.0.0.1:8000`. Documentação Swagger em `http://127.0.0.1:8000/docs`.

### 4. Inicialize a IA

Chame o endpoint de seed **uma vez** para popular as 190 frases de referência do classificador:

```bash
curl -X POST http://127.0.0.1:8000/emotions/seed
```

Resposta esperada:

```json
{
  "message": "Exemplos de emoção (re)cadastrados com sucesso.",
  "total_exemplos": 190,
  "por_emocao": [
    {"emocao": "Alegria", "exemplos": 57},
    {"emocao": "Irritado", "exemplos": 69},
    {"emocao": "Neutro", "exemplos": 64}
  ]
}
```

### 5. Sirva o frontend

Qualquer servidor HTTP estático serve. O mais simples:

```bash
cd frontend
python -m http.server 5500
```

Abra `http://127.0.0.1:5500` no navegador.

> Importante: o frontend espera a API em `http://127.0.0.1:8000` durante o desenvolvimento (configurável em `frontend/js/config.js`).

---

## Como testar a aplicação

### Versão hospedada (recomendado)

A aplicação está rodando em produção:

**[👉 https://campusvibe-lovat.vercel.app](https://campusvibe-lovat.vercel.app)**

Fluxo sugerido para testar:

1. Abra o link, clique em **Cadastre-se**.
2. Preencha nome, e-mail e senha. Selecione um **Bloco** e o **Curso** correspondente.
3. Após o login, vá em **Fazer um Comentário** e digite algo como `"péssima aula"` ou `"ótima aula"` — observe a IA classificando em tempo real.
4. Volte ao menu e abra o **Mapa dos Blocos** — veja a sua emoção influenciando o bloco do seu curso.
5. Abra o **Raio-X do Curso** para ver a distribuição completa e o feed de comentários filtráveis.

### Frases para experimentar com a IA

| Tente digitar | Resultado esperado |
|---|---|
| `péssima aula` | Irritado 😡 |
| `ótima aula, professor incrível` | Alegria 😊 |
| `odiei a prova de cálculo` | Irritado 😡 |
| `passei na prova!` | Alegria 😊 |
| `amanhã tem aula no laboratório` | Neutro ✨ |
| `tô estressado com esse semestre` | Irritado 😡 |
| `que matéria chata` | Irritado 😡 |
| `adorei o conteúdo de hoje` | Alegria 😊 |

---

## Evolução do projeto

O projeto foi desenvolvido em fases incrementais ao longo do semestre. Cada fase trouxe uma camada nova:

### Fase 1 — Fundação (setup e modelagem)
- Setup do FastAPI com rota `/health`
- Modelagem conceitual e lógica do banco (BrModelo)
- Schema inicial: bloco → curso → usuario → comentario

### Fase 2 — Autenticação
- Cadastro com validação de campos e hashing Argon2
- Login com JWT + proteções contra timing attack e enumeração de usuários
- Página de perfil com atualização de dados e troca de senha

### Fase 3 — Inteligência Artificial (versão inicial)
- Ativação da extensão `pgvector` no PostgreSQL
- Integração do `fastembed` para gerar embeddings de 384 dimensões
- Classificação por centroide médio (3 vetores âncora)

### Fase 4 — Telas e dashboards
- Landing page com hero animado
- Mapa de Blocos com auto-refresh e painel lateral
- Raio-X do Curso com seletor cascata e filtros por emoji
- Tela de envio de comentário com card de resultado animado

### Fase 5 — Deploy em produção
- Backend hospedado no **Railway**
- Banco hospedado no **Supabase** (Postgres + pgvector)
- Frontend hospedado no **Vercel**
- Ajustes finos: carregamento diferido do modelo de IA, restrição de CORS, validação de e-mail

### Fase 6 — Reescrita do classificador (estado atual)
- Detectado o problema: "péssima aula" era classificado como Neutro
- Substituição do centroide médio por **KNN com voto ponderado**
- Seed expandido de ~38 para **190 frases** com mix de tamanhos
- Adição do **léxico de polaridade** como rede de segurança
- Resultado: 18/18 casos de teste passando, incluindo edge cases

---

## Equipe

Estudantes de Ciência da Computação da UNINASSAU (campus Graças):

| Nome | GitHub |
|---|---|
| Juan Pablo | [@JuanPablo141](https://github.com/JuanPablo141) |
| Geovanna Santos | [@geoalmeiida](https://github.com/geoalmeiida) |
| Josinaldo Xavier | [@josinaldoxavier215-droid](https://github.com/josinaldoxavier215-droid) |
| Gabrielly Rodrigues | [@gabriellyrcarneiro](https://github.com/gabriellyrcarneiro) |
| Isabelle Victoria | [@belyisa-bit](https://github.com/belyisa-bit) |
| Gabriela Araujo | [@gabrielasparaujo](https://github.com/gabrielasparaujo) |
| Erick Lourenço | [@ErickLGou](https://github.com/ErickLGou) |

---

## Documentação técnica

Para entender em profundidade como cada parte do sistema funciona, consulte:

- **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)** — Documentação completa em 12 seções: estrutura do banco, todas as rotas, pipeline de IA detalhada com fórmulas, regras de desempate, autenticação, fluxos completos por funcionalidade e mapa de conexões entre arquivos.

- **Swagger da API** — Quando rodando localmente: `http://127.0.0.1:8000/docs`.

---

<div align="center">

**Desenvolvido para o Projeto da Faculdade — UNINASSAU © 2026**

[Aplicação ao vivo](https://campusvibe-lovat.vercel.app) · [Documentação técnica](docs/ARCHITECTURE.md) · [Repositório](https://github.com/JuanPablo141/project-root)

</div>
