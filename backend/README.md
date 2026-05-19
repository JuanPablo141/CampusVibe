# Backend — CampusVibe

API REST do CampusVibe construída em **FastAPI**, responsável por toda a regra de negócio, autenticação via JWT e pelo pipeline de IA que classifica comentários em emoções.

URL em produção: https://project-root-production-b179.up.railway.app/

Documentação interativa (Swagger): https://project-root-production-b179.up.railway.app/docs

---

## Stack

| Tecnologia | Versão | Função |
|------------|--------|--------|
| Python | 3.12 | Linguagem base |
| FastAPI | 0.135 | Framework web (rotas, validação, OpenAPI) |
| Pydantic | 2.12 | Validação de schemas |
| psycopg3 | 3.3 | Driver PostgreSQL |
| pgvector | — | Operações vetoriais no PostgreSQL |
| fastembed | — | Geração de embeddings com modelo `paraphrase-multilingual-MiniLM-L12-v2` |
| PyJWT | — | Geração e validação de tokens JWT |
| pwdlib + Argon2 | 0.3 | Hashing seguro de senhas |
| Uvicorn | 0.42 | Servidor ASGI |

Lista completa em [`requirements.txt`](./requirements.txt).

---

## Estrutura interna

```
backend/
├── app/
│   ├── main.py                  # Inicialização do FastAPI, CORS e registro de routers
│   ├── dependencies.py          # get_db_connection() e get_current_user() (JWT)
│   ├── schemas/                 # Modelos Pydantic (validação de entrada/saída)
│   │   ├── user_register.py
│   │   ├── user_login.py
│   │   └── user_profile.py
│   ├── routes/                  # Endpoints HTTP (camada de apresentação)
│   │   ├── health.py
│   │   ├── users.py             # Cadastro, login, perfil
│   │   ├── comentarios.py       # Pipeline completa do comentário
│   │   ├── emotions.py          # Seed + classificação de emoções
│   │   ├── vectors.py           # Embeddings e busca semântica
│   │   ├── dashboards.py        # Emoção geral por curso/bloco
│   │   └── stats.py             # Endpoints ricos para o frontend
│   ├── services/                # Lógica de negócio (camada intermediária)
│   │   ├── vector_service.py            # Singleton do modelo de IA
│   │   ├── emotion_seed_examples.py     # 190 frases de seed
│   │   ├── emotion_classification_service.py  # Léxico de polaridade
│   │   ├── user_register_service.py
│   │   ├── user_register_validation.py
│   │   ├── user_login_service.py
│   │   ├── user_profile_service.py
│   │   ├── stats_service.py
│   │   └── password_hasher.py
│   └── respositories/           # Acesso ao banco (camada de dados)
│       ├── comentario_repository.py
│       ├── emotion_repository.py        # KNN com voto ponderado
│       ├── vector_repository.py
│       ├── dashboard_repository.py      # Moda + regras de desempate
│       ├── stats_repository.py
│       ├── user_login_repository.py
│       ├── user_register_repository.py
│       └── user_profile_repository.py
├── .env.example                 # Template de variáveis de ambiente
├── Procfile                     # Comando de start usado pelo Railway
└── requirements.txt
```

**Arquitetura em camadas:** `routes` → `services` → `respositories` → banco. Nenhum repositório contém lógica de negócio; nenhuma rota fala diretamente com o banco.

---

## Setup local

### Pré-requisitos

- Python 3.12
- Acesso a um PostgreSQL com a extensão `pgvector` habilitada (recomendado: [Supabase free tier](https://supabase.com))
- Migrations aplicadas no banco — ver [`../database/README.md`](../database/README.md)

### Passo a passo

```bash
# Entrar na pasta backend
cd backend

# Criar e ativar o ambiente virtual
python -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env e preencha DATABASE_URL com a string de conexão do seu PostgreSQL

# Rodar a API em modo desenvolvimento
uvicorn app.main:app --reload

# A API estará em http://127.0.0.1:8000
# Swagger interativo em http://127.0.0.1:8000/docs
```

### Popular o seed de emoções (necessário uma vez)

Depois de aplicar as migrations e subir a API, rode:

```bash
curl -X POST http://127.0.0.1:8000/emotions/seed
```

Isso popula a tabela `emocao_exemplo` com 190 frases de referência (57 Alegria, 69 Irritado, 64 Neutro), gerando o embedding individual de cada uma. O endpoint é **idempotente** — pode ser executado várias vezes; ele sempre apaga e re-popula, terminando com exatamente 190 exemplos.

A primeira chamada leva entre 10 e 20 segundos (download e carga do modelo + 190 embeddings). As subsequentes ficam em 3-5 segundos.

---

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `DATABASE_URL` | Sim | String de conexão completa do PostgreSQL no formato `postgresql://usuario:senha@host:porta/db`. Em Supabase, use a string do **Connection Pooling** (porta 5432). |

A chave secreta do JWT está embutida no código de [`dependencies.py`](./app/dependencies.py) para fins acadêmicos — em produção real, deveria ser movida para variável de ambiente.

---

## Pipeline de IA — resumo

A classificação de cada comentário passa por três camadas encadeadas:

1. **Embedding semântico** — `vector_service.generate_embedding(texto)` converte o texto em vetor de 384 dimensões usando o modelo `paraphrase-multilingual-MiniLM-L12-v2`. O modelo é carregado uma única vez (Singleton com lazy-load).
2. **KNN com voto ponderado** — `EmotionRepository.classify_comment()` faz uma query SQL que pega os 7 exemplos mais próximos no espaço vetorial (distância de cosseno via `pgvector`) e atribui um score por emoção: `score = Σ 1 / (distância + 0.05)`. A emoção com maior score vence.
3. **Léxico de polaridade** — `emotion_classification_service.decide_final_emotion()` atua como rede de segurança: se o KNN disse "Neutro" mas o texto contém palavras de polaridade clara (ex: "péssima", "ótima"), o léxico sobrescreve. Aplica 4 regras em ordem.

A explicação detalhada com a query SQL completa, os thresholds, e as justificativas de design está em [`../docs/ARCHITECTURE.md#6-pipeline-de-ia`](../docs/ARCHITECTURE.md#6-pipeline-de-ia).

---

## Endpoints principais

| Método | Endpoint | Auth | Descrição |
|--------|----------|------|-----------|
| GET | `/health` | Não | Health check |
| POST | `/users/register` | Não | Cadastra um aluno |
| POST | `/users/login` | Não | Login, retorna JWT (7 dias de validade) |
| GET | `/users/me` | Sim | Perfil do usuário logado |
| PUT | `/users/me` | Sim | Atualiza nome e curso |
| PUT | `/users/me/password` | Sim | Troca de senha (exige a atual) |
| POST | `/comentarios/` | **Sim** | Pipeline completa: texto → vetor → KNN → léxico → emoção |
| POST | `/emotions/seed` | Não | (Re)popula `emocao_exemplo` com 190 frases (idempotente) |
| POST | `/emotions/classify` | Não | Reclassifica um comentário existente via KNN puro |
| GET | `/dashboard/curso/{id_curso}` | Não | Emoção geral de um curso (moda + desempate) |
| GET | `/dashboard/bloco/{id_bloco}` | Não | Emoção geral de um bloco |
| GET | `/stats/course` | Sim | Dashboard completo de um curso (aceita filtros) |
| GET | `/stats/blocks-map` | Sim | Dados de todos os blocos para o Mapa |
| GET | `/stats/courses-by-block/{id_bloco}` | Não | Lista cursos de um bloco |
| POST | `/vectors/search` | Não | Busca semântica por similaridade |

A tabela completa, com todos os endpoints e seus payloads, está em [`../docs/ARCHITECTURE.md#10-todos-os-endpoints-da-api`](../docs/ARCHITECTURE.md#10-todos-os-endpoints-da-api).

---

## Deploy

A API roda no **Railway**, configurado via [`Procfile`](./Procfile):

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

O Railway lê o `requirements.txt`, instala as dependências, e executa o comando do `Procfile`. A variável `DATABASE_URL` é definida nas configurações do projeto no Railway, apontando para o PostgreSQL hospedado no Supabase.

---

## Notas

- **CORS está liberado para qualquer origem** (`allow_origins=["*"]`) em [`main.py`](./app/main.py) — adequado para desenvolvimento e para um projeto acadêmico, mas em produção real deveria ser restrito ao domínio do frontend.
- **A pasta é `respositories/` (com a letra `s` no início)** — typo histórico do projeto, mas funcional. Não é necessário renomear.
- O modelo de IA é baixado no primeiro `generate_embedding()` (lazy-load), evitando timeout no boot do Railway.
