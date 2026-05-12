# CampusVibe — Documentação de Arquitetura

> Plataforma anônima de análise de sentimentos acadêmicos com Inteligência Artificial, desenvolvida como projeto de faculdade pelos alunos de Ciência da Computação da UNINASSAU (campus Graças).

---

## Índice

1. [Visão geral do sistema](#1-visão-geral-do-sistema)
2. [Stack tecnológica](#2-stack-tecnológica)
3. [Estrutura de diretórios](#3-estrutura-de-diretórios)
4. [Banco de dados](#4-banco-de-dados)
5. [Backend](#5-backend)
   - [Ponto de entrada](#51-ponto-de-entrada--mainpy)
   - [Dependências globais](#52-dependências-globais--dependenciespy)
   - [Schemas](#53-schemas)
   - [Rotas (Routes)](#54-rotas-routes)
   - [Serviços (Services)](#55-serviços-services)
   - [Repositórios (Repositories)](#56-repositórios-repositories)
6. [Pipeline de IA](#6-pipeline-de-ia)
7. [Sistema de emoções e regras de desempate](#7-sistema-de-emoções-e-regras-de-desempate)
8. [Frontend](#8-frontend)
   - [Páginas](#81-páginas)
   - [Scripts](#82-scripts)
   - [Estilos](#83-estilos)
9. [Autenticação e segurança](#9-autenticação-e-segurança)
10. [Todos os endpoints da API](#10-todos-os-endpoints-da-api)
11. [Fluxos completos](#11-fluxos-completos)
12. [Mapa de conexões entre arquivos](#12-mapa-de-conexões-entre-arquivos)

---

## 1. Visão geral do sistema

O CampusVibe permite que alunos compartilhem comentários anônimos sobre aulas, professores e provas. Cada comentário passa por uma **pipeline de IA local** que o classifica em uma emoção (Alegria, Irritado ou Neutro). A partir dessas classificações, o sistema calcula estatisticamente a **emoção predominante de cada curso** e, subindo um nível, a **emoção predominante de cada bloco do campus**. Esse resultado é exibido em tempo real em duas telas visuais: o **Raio-X do Curso** e o **Mapa de Blocos**.

```
Comentário do aluno
       ↓
   Pipeline IA (fastembed + pgvector)
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

## 2. Stack tecnológica

| Camada | Tecnologia | Função |
|---|---|---|
| Backend | Python 3.12 + FastAPI | API REST, roteamento, validação |
| Banco | PostgreSQL + extensão `pgvector` | Armazenamento relacional + busca vetorial |
| Driver DB | psycopg3 | Conexão Python → PostgreSQL |
| IA / NLP | fastembed + `paraphrase-multilingual-MiniLM-L12-v2` | Gera vetores de 384 dimensões a partir de texto |
| Autenticação | PyJWT + Argon2 (bcrypt-style) | Tokens JWT + hashing seguro de senhas |
| Frontend | HTML5 + CSS3 + JavaScript puro | Sem frameworks, sem build tools |

---

## 3. Estrutura de diretórios

```
project-root/
├── backend/
│   └── app/
│       ├── main.py                        # Inicialização do FastAPI, registro de routers
│       ├── dependencies.py                # Conexão DB, autenticação JWT (get_current_user)
│       ├── schemas/
│       │   ├── user_register.py           # Pydantic: validação do cadastro
│       │   ├── user_login.py              # Pydantic: validação do login
│       │   └── user_profile.py            # Pydantic: resposta e atualização de perfil
│       ├── routes/
│       │   ├── health.py                  # GET /health
│       │   ├── users.py                   # Registro, login, perfil (CRUD)
│       │   ├── comentarios.py             # Pipeline completa de comentário + IA
│       │   ├── emotions.py                # Seed e classificação de emoções
│       │   ├── vectors.py                 # Embeddings e busca semântica
│       │   ├── dashboards.py              # Emoção geral por curso e por bloco
│       │   └── stats.py                   # Estatísticas completas para as telas visuais
│       ├── services/
│       │   ├── vector_service.py                    # Singleton do modelo de IA (fastembed)
│       │   ├── emotion_seed_examples.py             # 190 frases de seed (Alegria/Irritado/Neutro)
│       │   ├── emotion_classification_service.py    # Léxico de polaridade + decisão final pós-KNN
│       │   ├── user_register_service.py             # Lógica de negócio do cadastro
│       │   ├── user_register_validation.py          # Validações de campos do cadastro
│       │   ├── user_login_service.py                # Geração do JWT no login
│       │   ├── user_profile_service.py              # Lógica de leitura e atualização de perfil
│       │   ├── stats_service.py                     # Agregação de dados para dashboards
│       │   └── password_hasher.py                   # hash_password / verify_password (Argon2)
│       └── respositories/
│           ├── comentario_repository.py             # INSERT comentário, SELECT emoções por curso
│           ├── emotion_repository.py                # KNN com voto ponderado + helpers de seed
│           ├── vector_repository.py                 # INSERT embedding, busca semântica (cosseno)
│           ├── dashboard_repository.py              # Cálculo de moda + regras de desempate
│           ├── stats_repository.py                  # Queries para distribuição, cursos, comentários por bloco
│           ├── user_login_repository.py             # SELECT usuário por email (login)
│           ├── user_register_repository.py          # INSERT usuário, verificações de email/curso
│           └── user_profile_repository.py           # SELECT/UPDATE perfil do usuário
├── database/
│   └── schema/
│       ├── 001_initial_schema_v1.sql                # Tabelas iniciais (bloco, curso, usuario, comentario)
│       ├── 002_vector_schema.sql                    # pgvector + tabela embedding + índice HNSW
│       ├── 003_emotions_schema.sql                  # Tabelas emocao + classificacao_emocao
│       ├── 004_seed_blocos_cursos.sql               # Seed de blocos e cursos
│       └── 005_emocao_exemplo.sql                   # Tabela emocao_exemplo (KNN) + vetor_ancora nullable
└── frontend/
    ├── index.html                         # Landing page (pública)
    ├── pages/
    │   ├── login.html                     # Tela de login
    │   ├── register.html                  # Tela de cadastro
    │   ├── dashboard.html                 # Menu principal (autenticado)
    │   ├── dashboard_comment.html         # Tela de envio de comentário (autenticado)
    │   ├── dashboard_map.html             # Mapa de blocos (autenticado)
    │   ├── course_stats.html              # Raio-X do curso (autenticado)
    │   └── account.html                   # Configurações de conta (autenticado)
    ├── js/
    │   ├── login.js                       # Lógica de autenticação + sessionStorage
    │   ├── register.js                    # Cadastro com seletor cascata bloco → curso
    │   ├── dashboard.js                   # Guard de rota + saudação + logout
    │   ├── dashboard_comment.js           # Envio de comentário, exibição de emoção classificada
    │   ├── dashboard_map.js               # Fetch, renderização e interação do mapa
    │   ├── course_stats.js                # Fetch, filtros e feed de comentários do curso
    │   └── account.js                     # Abas, carregamento e atualização de perfil/senha
    └── css/
        ├── global.css                     # Variáveis, reset, classes utilitárias (.glass, .btn)
        ├── landing.css                    # Estilos da landing page
        ├── login.css                      # Estilos da tela de login
        ├── register.css                   # Estilos da tela de cadastro
        ├── dashboard.css                  # Estilos do menu principal
        ├── dashboard_comment.css          # Estilos da tela de comentário e card de resultado
        ├── dashboard_map.css              # Estilos do mapa de blocos
        ├── course_stats.css               # Estilos do Raio-X do curso
        └── account.css                    # Estilos da tela de conta
```

---

## 4. Banco de dados

### Estrutura das tabelas (inferida do código)

```
usuario
├── id_usuario   PK
├── nome
├── email        UNIQUE
├── senha_hash
└── id_curso     FK → curso

curso
├── id_curso     PK
├── nome_curso
└── id_bloco     FK → bloco

bloco
├── id_bloco     PK
└── nome_bloco

comentario
├── id_comentario  PK
├── texto
├── id_usuario     FK → usuario
└── data_criacao

embedding
├── id_embedding   PK
├── id_comentario  FK → comentario
└── vetor          vector(384)   ← campo pgvector

emocao
├── id_emocao      PK
├── nome_emocao    UNIQUE
└── vetor_ancora   vector(384) NULL   ← legado (centroide); o KNN consulta emocao_exemplo

emocao_exemplo                          ← migração 005 (substitui o centroide por KNN)
├── id_exemplo     PK
├── id_emocao      FK → emocao
├── texto          TEXT                 ← frase de referência (ex: "Péssima aula.")
├── vetor          vector(384)          ← embedding individual da frase
└── data_criacao   TIMESTAMPTZ
    + índice HNSW (vector_cosine_ops) para busca KNN rápida

classificacao_emocao
├── id_classificacao  PK
├── id_comentario     FK → comentario   UNIQUE
├── id_emocao         FK → emocao
└── distancia         float
```

### Hierarquia de dados

```
bloco (4 blocos físicos do campus)
 └── curso  (N cursos por bloco)
      └── usuario  (N alunos por curso)
           └── comentario  (N comentários por aluno)
                ├── embedding  (1 vetor por comentário)
                └── classificacao_emocao  (1 emoção por comentário)

emocao (3 emoções base: Alegria, Irritado, Neutro)
 └── emocao_exemplo  (N frases de referência por emoção — ~190 no total)
```

### Blocos e cursos cadastrados

| Bloco | Nome | Exemplos de cursos |
|---|---|---|
| 0 | Tecnologia e Engenharia | Ciência da Computação, Engenharia Civil, Data Science, Game Design |
| 1 | Negócios e Gestão | Administração, Marketing, Logística, Empreendedorismo Digital |
| 2 | Jurídico e Social | Direito, Serviço Social |
| 3 | Saúde | Medicina, Farmácia, Biomedicina, Psicologia, Enfermagem |

---

## 5. Backend

### 5.1 Ponto de entrada — `main.py`

Inicializa o FastAPI, configura o **middleware CORS** (libera todas as origens para desenvolvimento) e registra todos os routers. Rota raiz `GET /` retorna confirmação de que a API está no ar.

```python
app = FastAPI(title="API Projeto faculdade", version="0.1.0")
# Registra: health, users, vectors, emotions, comentarios, dashboards, stats
```

### 5.2 Dependências globais — `dependencies.py`

Dois injetáveis usados em todas as rotas protegidas:

**`get_db_connection()`** — abre uma conexão psycopg3, registra o suporte a pgvector, faz `commit` ao final ou `rollback` em caso de erro, e fecha a conexão (`yield` pattern do FastAPI).

**`get_current_user(token)`** — decodifica o JWT recebido no header `Authorization: Bearer`. Se inválido ou expirado, lança `401`. Retorna o payload com `sub` (id_usuario), `nome` e `id_curso`.

### 5.3 Schemas

Modelos Pydantic que validam os dados recebidos nas requisições:

| Schema | Campos | Usado em |
|---|---|---|
| `UserRegisterInput` | nome, email, senha, confirmacao_senha, id_curso | `POST /users/register` |
| `UserLoginInput` | email, senha | `POST /users/login` |
| `UserProfileResponse` | id_usuario, nome, email, id_curso, id_bloco | `GET /users/me` |
| `UserUpdateProfile` | nome, id_curso | `PUT /users/me` |
| `UserUpdatePassword` | current_password, new_password | `PUT /users/me/password` |

`UserRegisterInput` normaliza `nome` (strip) e `email` (strip + lowercase) antes da validação.

### 5.4 Rotas (Routes)

Cada arquivo de rota mapeia endpoints HTTP para chamadas de serviço. Erros de negócio são convertidos em `HTTPException` com o status correto.

#### `health.py`
```
GET /health → {"status": "ok"}
```
Usado para verificar se a API está respondendo.

---

#### `users.py` — prefixo `/users`

| Endpoint | Método | Auth | Descrição |
|---|---|---|---|
| `/users/register` | POST | Não | Cadastra novo aluno. Valida campos, verifica se email já existe e se o curso é válido, faz hash da senha com Argon2. |
| `/users/login` | POST | Não | Autentica o aluno. Retorna JWT com validade de 7 dias. Previne timing-attack com mensagem genérica de erro. |
| `/users/me` | GET | Sim | Retorna perfil completo (inclui `id_bloco` via JOIN com `curso`). |
| `/users/me` | PUT | Sim | Atualiza nome e curso do aluno. |
| `/users/me/password` | PUT | Sim | Atualiza senha exigindo a senha atual. Verifica o hash antes de salvar o novo. |

---

#### `comentarios.py` — prefixo `/comentarios`

| Endpoint | Método | Auth | Descrição |
|---|---|---|---|
| `/comentarios/` | POST | **Sim** | Pipeline completa: salva comentário → gera vetor (IA) → salva vetor → classifica via KNN → aplica léxico de polaridade → persiste decisão final. O `id_usuario` é extraído do JWT — o body recebe apenas `{ texto }`. Retorna a emoção identificada + `debug` com top do KNN, margem e se houve override do léxico. |
| `/comentarios/curso/{id_curso}/emocoes` | GET | Não | Retorna contagem de cada emoção registrada nos comentários de um curso. |

---

#### `emotions.py` — prefixo `/emotions`

| Endpoint | Método | Descrição |
|---|---|---|
| `/emotions/seed` | POST | **Idempotente.** Limpa `emocao_exemplo` e re-popula com 190 frases (Alegria: 57, Irritado: 69, Neutro: 64). Cada frase é embutida individualmente — não há mais centroide. Deve ser rodado uma vez após cada deploy que altere o seed. |
| `/emotions/classify` | POST | Reclassifica um comentário existente via KNN puro (sem aplicar o léxico). Útil para reprocessar comentários antigos ou debugar a IA. |

---

#### `vectors.py` — prefixo `/vectors`

| Endpoint | Método | Descrição |
|---|---|---|
| `/vectors/comentarios/embed` | POST | Gera e salva o embedding de um comentário existente. |
| `/vectors/search` | POST | Busca semântica: recebe um texto, gera seu vetor e retorna os comentários mais similares por distância de cosseno. |

---

#### `dashboards.py` — prefixo `/dashboard`

| Endpoint | Método | Descrição |
|---|---|---|
| `/dashboard/curso/{id_curso}` | GET | Retorna a emoção geral do curso com o total de votos. |
| `/dashboard/bloco/{id_bloco}` | GET | Retorna a emoção geral do bloco calculada pela moda dos cursos. |

Esses endpoints usam diretamente o `DashboardRepository` com as regras de desempate.

---

#### `stats.py` — prefixo `/stats`

| Endpoint | Método | Auth | Descrição |
|---|---|---|---|
| `/stats/course` | GET | Sim | Dashboard completo de um curso: nome, total de comentários, vibe predominante, lista de comentários, filtros de emoji disponíveis, lista de blocos. Se `id_curso` não for informado, usa o curso do usuário logado. Aceita filtro por emoji via query param `emoji`. |
| `/stats/courses-by-block/{id_bloco}` | GET | Não | Retorna a lista de cursos (id + nome) de um bloco. Usado para popular o seletor de cursos no Raio-X. |
| `/stats/blocks-map` | GET | Sim | Agrega dados de todos os blocos para o Mapa: emoção do bloco, distribuição de emoções, cursos com suas vibes individuais, comentários recentes e texto explicativo gerado dinamicamente. |

### 5.5 Serviços (Services)

Contêm a lógica de negócio, orquestrando chamadas aos repositórios.

**`vector_service.py`** — Singleton que carrega o modelo `paraphrase-multilingual-MiniLM-L12-v2` via fastembed (lazy-load para evitar timeout de boot no Railway). Exponibiliza três métodos:
- `generate_embedding(text)`: converte um texto em vetor de 384 dimensões
- `generate_embeddings_batch(texts)`: gera o vetor individual de cada frase de uma lista (usado pelo seed do KNN — uma única chamada ao modelo para todos os exemplos)
- `generate_average_embedding(texts)`: gera o centroid normalizado de uma lista de textos (legado — mantido para compatibilidade)

O modelo é carregado uma única vez na primeira chamada (`vector_service = VectorService()` cria a instância, mas só baixa/aloca o modelo ao acessar `model`).

**`emotion_seed_examples.py`** — Banco de 190 frases organizadas por emoção, com mix proposital de tamanhos:
- **Frases curtas** ("Péssima aula.", "Ótima aula.") para que o KNN acerte inputs de 2-3 palavras.
- **Frases médias e longas** para cobrir o contexto cheio dos comentários reais.
- **Vocabulário emocional redundante** (péssimo / horrível / ruim / chato) para reforçar o sinal no espaço vetorial.
- **Neutros com vocabulário ambíguo** ("Hoje tem aula de cálculo.", "Professor passou um exercício.") para que o KNN não confunda enunciados informativos com elogios.

**`emotion_classification_service.py`** — Léxico de polaridade que decide a emoção final após o KNN. Mantém duas listas:
- `NEGATIVE_LEXICON`: ~70 palavras de polaridade negativa clara (péssimo, horrível, odeio, estressado, decepção, reprovei, etc.)
- `POSITIVE_LEXICON`: ~50 palavras de polaridade positiva clara (ótimo, adorei, amei, incrível, passei, tirei 10, etc.)

Função central: `decide_final_emotion(texto, knn_result)` aplica 4 regras em ordem (ver seção [Pipeline de IA](#6-pipeline-de-ia)). O léxico não substitui o KNN — apenas corrige os casos onde o modelo de embeddings tropeça no vocabulário acadêmico.

**`user_login_service.py`** — Verifica email + senha (Argon2), gera JWT com payload `{sub, nome, id_curso, exp}`.

**`user_register_service.py`** — Valida campos (via `user_register_validation.py`), verifica duplicidade de email e existência do curso, chama `hash_password` e persiste o usuário.

**`user_profile_service.py`** — Leitura e atualização de perfil com verificação de senha atual para a troca de senha.

**`stats_service.py`** — Orquestra as queries do `stats_repository` e do `DashboardRepository` para montar as respostas ricas dos endpoints `/stats/*`. A função `_build_block_explanation` gera dinamicamente o texto: *"Bloco X está em Alegria porque essa foi a emoção predominante em N de Y cursos com base em Z comentários."*

**`password_hasher.py`** — Abstração sobre o Argon2: `hash_password(plain)` e `verify_password(plain, hashed)`.

### 5.6 Repositórios (Repositories)

Camada exclusiva de acesso ao banco de dados. Nenhum repositório contém lógica de negócio.

**`dashboard_repository.py`** — O repositório mais importante do sistema. Implementa as **regras de desempate** em Python após buscar as contagens do banco. Dois métodos principais:

- `get_emocao_geral_curso(id_curso)`: calcula a moda das emoções dos comentários de um curso e aplica o desempate
- `get_emocao_geral_bloco(id_bloco)`: itera sobre cada curso do bloco, chama `get_emocao_geral_curso` para cada um, e aplica o desempate novamente no nível do bloco

**`emotion_repository.py`** — Gerencia a tabela `emocao` (3 categorias) e `emocao_exemplo` (banco KNN). Métodos:

- **`upsert_emotion(nome)`** — Garante que a emoção exista. Não exige mais `vetor_ancora`.
- **`reset_examples()`** — Limpa todos os exemplos (chamado pelo `/emotions/seed` antes de re-popular).
- **`bulk_add_examples(id_emocao, [(texto, vetor), ...])`** — Insere vários exemplos em uma transação via `executemany`.
- **`get_emotion_id_by_name(nome)`** — Resolve o ID de uma emoção pelo nome (usado quando o léxico sobrescreve o KNN).
- **`save_classification(id_comentario, id_emocao, distancia)`** — Persiste a decisão final em `classificacao_emocao` com `ON CONFLICT DO UPDATE`.
- **`classify_comment(id_comentario)`** — Coração do classificador. Faz KNN com voto ponderado em uma única query:

```sql
WITH knn AS (
    SELECT ex.id_emocao, em.nome_emocao,
           (ex.vetor <=> e.vetor) AS distancia
    FROM public.embedding e
    CROSS JOIN public.emocao_exemplo ex
    JOIN public.emocao em ON em.id_emocao = ex.id_emocao
    WHERE e.id_comentario = $1
    ORDER BY distancia ASC LIMIT 7
),
scored AS (
    SELECT id_emocao, nome_emocao,
           SUM(1.0 / (distancia + 0.05)) AS score,
           AVG(distancia) AS distancia_media,
           MIN(distancia) AS distancia_min
    FROM knn GROUP BY id_emocao, nome_emocao
)
SELECT * FROM scored ORDER BY score DESC;
```

Retorna a emoção vencedora + `margem` (diferença relativa entre 1º e 2º colocados) + `distancia_min` (vizinho mais próximo) + `ranking` completo. Esses metadados alimentam o léxico de polaridade.

**`vector_repository.py`** — Persiste embeddings na tabela `embedding`. Implementa a busca semântica via `<=>` (cosseno) com `ORDER BY distancia ASC`.

**`stats_repository.py`** — Queries para as telas visuais:
- `get_course_comments`: comentários de um curso com join para a classificação de emoção, suportando filtro por emoção
- `get_block_emotion_counts`: distribuição percentual de emoções de um bloco
- `get_block_recent_comments`: comentários recentes que justificam a emoção do bloco
- `get_block_total_comments`: total de comentários de um bloco
- `get_all_blocks` / `get_courses_by_block`: listas para os seletores

---

## 6. Pipeline de IA

Este é o entregável central do projeto. A classificação combina três camadas: **embedding semântico**, **KNN com voto ponderado** e **léxico de polaridade**. Cada uma cobre o ponto cego da anterior.

### 6.1 Por que três camadas?

A versão anterior usava um único **centroide por emoção** (média de ~15 frases) e comparava o embedding do texto contra esses 3 vetores. O problema: a média dilui o sinal emocional e o modelo `paraphrase-multilingual-MiniLM` é treinado para similaridade temática, não para sentimento. Resultado: "péssima aula" caía em Neutro porque o vocabulário acadêmico ("aula") puxava o embedding para o centroide do Neutro.

A nova arquitetura ataca o problema em duas frentes:
1. **KNN substitui o centroide** — cada frase de seed entra como seu próprio vetor, preservando a variância e funcionando bem para frases curtas.
2. **Léxico atua como rede de segurança** — quando o modelo de embeddings tropeça em palavras emocionais óbvias, o léxico corrige.

### 6.2 Fluxo completo de `POST /comentarios/`

```
1. Recebe { texto } + JWT
        ↓
2. id_usuario = int(jwt["sub"])
        ↓
3. INSERT em comentario → id_comentario
        ↓
4. vector_service.generate_embedding(texto)
   Modelo: paraphrase-multilingual-MiniLM-L12-v2
   Output: list[float] de 384 dimensões
        ↓
5. INSERT em embedding (id_comentario, vetor)
        ↓
6. emotion_repository.classify_comment(id_comentario)   ← KNN com voto ponderado
        ↓
7. emotion_classification_service.decide_final_emotion(texto, knn_result)
        ↓
8. emo_repo.save_classification(id_comentario, id_emocao_final, distancia)
        ↓
9. Retorna { emocao_identificada, debug: { knn_top, knn_margem, override_aplicado, motivo } }
```

### 6.3 Etapa 6 — KNN com voto ponderado

A query SQL pega os **7 vizinhos mais próximos** entre as 190 frases de `emocao_exemplo` (usando distância de cosseno via pgvector) e calcula o score de cada emoção:

```
score(emocao) = Σ  1 / (distância + 0.05)
              vizinhos da emocao
```

A constante `0.05` evita divisão por zero e suaviza outliers. A emoção com maior score vence. A query também retorna:
- `distancia_min`: distância do vizinho mais próximo (medida de quão "familiar" o texto é em relação ao seed)
- `margem`: `(score_top - score_2nd) / score_top` — quão confiante o KNN está

### 6.4 Etapa 7 — Léxico de polaridade

`decide_final_emotion` aplica 4 regras em ordem. A primeira que casar decide:

| # | Condição | Resultado |
|---|---|---|
| 0 | `dist_min > 0.30` **E** `margem < 0.50` **E** léxico em silêncio **E** KNN ≠ Neutro | → **Neutro** (texto informativo, nenhum exemplo realmente próximo) |
| 1 | Texto tem palavras positivas **E** negativas (sinais mistos) | mantém o KNN |
| 2 | KNN disse **Neutro** mas léxico tem sinal forte unilateral | → emoção do léxico (override) |
| 3 | Léxico contraria o KNN **E** `margem < 0.10` (KNN indeciso) | → emoção do léxico (override) |
| – | nenhuma das anteriores | mantém o KNN |

#### Por que esses thresholds?

Medições empíricas no seed:
- Frases emocionalmente claras casam com seed exato → `dist_min < 0.10`
- Frases neutras informativas → `dist_min ≈ 0.30 – 0.42`
- KNN confiante → `margem > 0.40`
- KNN indeciso → `margem < 0.10`

A combinação `dist_min > 0.30 ∧ margem < 0.50` isola os casos onde o KNN "chuta" sem ter exemplos próximos. Se o KNN está confiante (margem alta), respeitamos a decisão dele mesmo com distância maior.

#### Por que o léxico não substitui o KNN?

O KNN cobre frases longas com nuance ("a aula foi confusa mas o professor é atencioso"). O léxico cobre frases curtas com vocabulário direto ("péssima aula"). Cada um falha onde o outro acerta — usar os dois juntos é mais robusto que escolher um.

### 6.5 Inicialização (`POST /emotions/seed`)

Idempotente — pode ser rodado várias vezes sem efeito colateral:

```
1. upsert_emotion(nome) para cada emoção base (Alegria, Irritado, Neutro)
2. reset_examples() → DELETE FROM emocao_exemplo
3. Para cada emoção em emotion_seed_examples.EMOTION_SEED_EXAMPLES:
     a. vector_service.generate_embeddings_batch(frases)  ← 1 chamada para todas
     b. bulk_add_examples(id_emocao, [(texto, vetor), ...])
```

Total de 190 frases inseridas. Tempo na primeira chamada: ~10-20s (carga do modelo + 190 embeddings). Subsequentes: ~3-5s.

---

## 7. Sistema de emoções e regras de desempate

### Emoções base (geradas pela IA)

| Emoção | Emoji | Cor no frontend |
|---|---|---|
| Alegria | 😊 | Verde (`#4ade80`) |
| Irritado | 😡 | Vermelho (`#f87171`) |
| Neutro | ✨ | Amarelo (`#facc15`) |

### Emoções compostas (resultado de desempate)

| Emoção | Emoji | Condição |
|---|---|---|
| Feliz | 🙂 | Empate entre Alegria e Neutro |
| Triste | 😰 | Empate entre Irritado e Neutro |
| Sem dados | ◇ | Nenhum comentário classificado |

### Regras de desempate (aplicadas em Python — `DashboardRepository._resolver_empate_emocoes`)

```
Alegria == Neutro            → Feliz
Irritado == Neutro           → Triste
Alegria == Irritado          → Neutro
3+ emoções empatadas         → Neutro
```

As mesmas regras são aplicadas **duas vezes**: primeiro para cada curso individual, depois para o bloco (moda das emoções dos cursos).

---

## 8. Frontend

Frontend 100% em HTML/CSS/JS puro, sem frameworks. Todas as páginas se comunicam com a API via `fetch`. O token JWT é armazenado em `sessionStorage` (expira ao fechar a aba).

### 8.1 Páginas

#### `index.html` — Landing page (pública)
Apresenta o projeto, explica o fluxo em 4 passos, destaca os diferenciais técnicos e lista os desenvolvedores. Links para cadastro e login. Não requer autenticação.

---

#### `pages/login.html` + `login.js` — Login
Formulário que chama `POST /users/login`. Em caso de sucesso:
- Salva `access_token` e `user_data` no `sessionStorage`
- Redireciona para `dashboard.html`

Proteções implementadas:
- Limpeza do `sessionStorage` antes de renderizar (força logout de sessões presas)
- Sanitização XSS dos inputs antes de enviar
- Botão desabilitado durante o request (anti-double-submit)
- Mensagem de erro genérica para status 401 (previne enumeração de usuários)

---

#### `pages/register.html` + `register.js` — Cadastro
Formulário com **seletor cascata**: ao escolher o Bloco, o select de Curso é populado dinamicamente com os cursos daquele bloco (dados embutidos no JS). Chama `POST /users/register`. Redireciona para `login.html` após sucesso.

---

#### `pages/dashboard.html` + `dashboard.js` — Menu principal
Guard de rota: verifica `sessionStorage` e redireciona para login se não houver token. Exibe saudação com o primeiro nome do aluno (lido do `sessionStorage`). Grid com 4 cards de navegação:
- **Fazer um Comentário** → `dashboard_comment.html`
- **Mapa dos Blocos** → `dashboard_map.html`
- **Raio-X do Curso** → `course_stats.html`
- **Minha Conta** → `account.html`

Botão de Logout limpa o `sessionStorage` e redireciona para `index.html`.

---

#### `pages/dashboard_comment.html` + `dashboard_comment.js` + `dashboard_comment.css` — Fazer um Comentário

Tela de desabafo anônimo onde o aluno escreve um comentário e recebe de volta a emoção identificada pela IA.

**Estrutura visual:**
- Chip com nome do aluno e curso vinculado (lido de `/users/me` + `/stats/courses-by-block`)
- Textarea com contador de caracteres (limite de 1.000)
- Indicador de privacidade ("Seu nome não é exposto a outros alunos")
- Card de resultado com emoji, nome da emoção, descrição e trecho original (oculto até o envio)

**Comportamento:**
- Ao carregar: busca `/users/me` para exibir nome e curso — sem possibilidade de escolher outro curso
- Ao enviar: chama `POST /comentarios/` com `Authorization: Bearer`. O `id_usuario` é extraído no backend via JWT.
- Ao receber a resposta: renderiza o card de resultado mapeando a emoção (`Alegria`, `Feliz`, `Neutro`, `Triste`, `Irritado`) para emoji, cor e descrição textual
- Botão "Fazer novo comentário": reseta o form sem recarregar a página
- Token inválido ou expirado: redireciona para `login.html`

**Variações visuais por emoção** (`--vibe-color` CSS custom property):

| Emoção | Cor |
|---|---|
| Alegria / Feliz | `#4ade80` (verde) |
| Neutro | `#facc15` (amarelo) |
| Triste | `#60a5fa` (azul) |
| Irritado | `#f87171` (vermelho) |

---

#### `pages/dashboard_map.html` + `dashboard_map.js` + `dashboard_map.css` — Mapa de Blocos

Tela visual que exibe a emoção de cada bloco em tempo real sobre um mapa fictício do campus.

**Estrutura visual:**
- Navbar com status de atualização e botão de voltar
- Cabeçalho com legenda dinâmica de emoções
- Mapa fictício com ruas, prédios, parques e canal (CSS puro, `aria-hidden`)
- 4 marcadores de bloco posicionados nos quadrantes do mapa
- Painel lateral com detalhes do bloco selecionado

**Comportamento:**
- Ao carregar: busca `GET /stats/blocks-map` e renderiza os marcadores
- Clicar em um bloco: abre o painel lateral com emoção, explicação, distribuição de emoções, cursos clicáveis e comentários recentes
- Clicar em um curso no painel: navega para `course_stats.html?block_id=X&course_id=Y`
- Botão "Abrir Raio-X dos cursos": navega para `course_stats.html?block_id=X`
- Atualização automática a cada **30 segundos**
- Bloco ativo tem animação `pulse-ring` na cor da sua emoção

---

#### `pages/course_stats.html` + `course_stats.js` + `course_stats.css` — Raio-X do Curso

Tela de análise detalhada de um curso com feed de comentários.

**Estrutura:**
- Navbar com dois seletores em cascata: Bloco → Curso
- Header com emoji da vibe atual
- Cards de métricas: total de interações e vibe predominante
- Filtros por emoção (apenas as que têm comentários)
- Feed de comentários classificados

**Comportamento:**
- Lê parâmetros de URL `?block_id=X&course_id=Y` para inicializar os seletores e buscar o curso correto diretamente
- Se `course_id` está na URL, `fetchData(course_id)` é chamado imediatamente — sem cascade de comparação
- Mudar o seletor de Bloco: recarrega seletor de Curso e busca dados do primeiro curso
- Mudar o seletor de Curso: busca dados do curso selecionado
- Filtro por emoji: refaz o fetch com `?emoji=X`
- Vibe predominante muda a cor do card de destaque (verde/vermelho/amarelo)

---

#### `pages/account.html` + `account.js` — Minha Conta

Tela com sistema de **abas** (tabs):
- **Meu Perfil**: formulário pré-preenchido com nome e curso atual (via `GET /users/me`). Seletor cascata igual ao do cadastro. Atualiza via `PUT /users/me`.
- **Segurança**: troca de senha com confirmação. Exige senha atual. Chama `PUT /users/me/password`.

### 8.2 Scripts

| Arquivo | Responsabilidade |
|---|---|
| `login.js` | Autenticação, armazenamento de token, proteções de segurança no formulário |
| `register.js` | Cadastro com cascata bloco → curso, validações client-side |
| `dashboard.js` | Guard de rota, saudação personalizada, logout |
| `dashboard_comment.js` | Carrega perfil do aluno, envia comentário via JWT, renderiza card de resultado com emoção |
| `dashboard_map.js` | Fetch do mapa, renderização dos marcadores e painel, click/select, auto-refresh |
| `course_stats.js` | Fetch de dados do curso, seletores em cascata, filtros de emoção, feed de comentários |
| `account.js` | Sistema de abas, carregamento e atualização de perfil e senha |

### 8.3 Estilos

| Arquivo | Escopo |
|---|---|
| `global.css` | Variáveis CSS (`--primary`, `--secondary`, `--bg-dark`), reset, fonte Outfit, classes `.glass`, `.btn`, `.btn-primary`, `.btn-outline` |
| `landing.css` | Hero, blobs animados, cards de steps e features, grid da equipe |
| `login.css` / `register.css` | Formulários centralizados, campos de input estilizados |
| `dashboard.css` | Grid de módulos, module-cards com hover |
| `dashboard_comment.css` | Chip de usuário/curso, textarea estilizada, card de resultado com `--vibe-color` por emoção, animação `bounceIn` no emoji |
| `dashboard_map.css` | Mapa fictício (`.fmap-*`), marcadores de bloco (`.block-marker`), painel lateral, animações `pulse-ring` e `loading-pulse` |
| `course_stats.css` | Header com emoji flutuante, cards de métricas com cor dinâmica por vibe, filtros de emoji, feed de comentários |
| `account.css` | Sistema de abas, formulários de edição, estados de sucesso/erro |

---

## 9. Autenticação e segurança

### Fluxo de autenticação

```
1. POST /users/login → { access_token, token_type, usuario }
2. Frontend salva em sessionStorage (não persiste entre abas/sessões)
3. Todas as requisições protegidas enviam: Authorization: Bearer <token>
4. Backend decodifica com get_current_user() e injeta o payload na rota
5. Ao fechar a aba ou clicar em Logout → sessionStorage.clear()
```

### Payload do JWT

```json
{
  "sub": "42",
  "nome": "Juan Pablo",
  "id_curso": 0,
  "exp": 1234567890
}
```

### Proteções implementadas

| Proteção | Onde | Como |
|---|---|---|
| Hash de senha Argon2 | Backend — `password_hasher.py` | Senhas nunca armazenadas em texto plano |
| Timing-attack prevention | `user_login_service.py` | Mensagem genérica para credenciais inválidas |
| User enumeration prevention | `login.js` | Mesmo erro para email inexistente e senha errada |
| XSS prevention | `login.js`, `register.js` | Sanitização via `document.createElement('div')` |
| Anti-double-submit | Todos os forms | Botão desabilitado durante o request |
| JWT stateless | `dependencies.py` | Sem estado no servidor, token auto-expirante |
| sessionStorage | Frontend | Token morre ao fechar a aba |
| Guard de rota | `dashboard.js`, `dashboard_comment.js`, `dashboard_map.js`, `course_stats.js` | Redirecionam para login se não houver token |

---

## 10. Todos os endpoints da API

Base URL: `http://127.0.0.1:8000`

| Método | Endpoint | Auth | Descrição |
|---|---|---|---|
| GET | `/health` | Não | Health check |
| POST | `/users/register` | Não | Cadastra novo aluno |
| POST | `/users/login` | Não | Login — retorna JWT |
| GET | `/users/me` | Sim | Perfil do usuário logado (com id_bloco) |
| PUT | `/users/me` | Sim | Atualiza nome e curso |
| PUT | `/users/me/password` | Sim | Troca de senha (exige senha atual) |
| POST | `/comentarios/` | **Sim** | Pipeline completa: texto → vetor → KNN → léxico → emoção. `id_usuario` extraído do JWT. Retorno inclui `debug` com top do KNN, margem e se o léxico fez override. |
| GET | `/comentarios/curso/{id_curso}/emocoes` | Não* | Contagem de emoções por curso |
| GET | `/dashboard/curso/{id_curso}` | Não | Emoção geral de um curso |
| GET | `/dashboard/bloco/{id_bloco}` | Não | Emoção geral de um bloco |
| POST | `/emotions/seed` | Não | (Re)popula `emocao_exemplo` com 190 frases. Idempotente — rodar após cada deploy que altere o seed. |
| POST | `/emotions/classify` | Não | Reclassifica um comentário por ID via KNN puro (sem léxico) |
| POST | `/vectors/comentarios/embed` | Não | Gera e salva embedding de um comentário |
| POST | `/vectors/search` | Não | Busca semântica por similaridade de texto |
| GET | `/stats/course` | Sim | Dashboard completo do curso (aceita `?id_curso=X&emoji=Y`) |
| GET | `/stats/courses-by-block/{id_bloco}` | Não | Lista cursos de um bloco |
| GET | `/stats/blocks-map` | Sim | Dados de todos os blocos para o mapa |

---

## 11. Fluxos completos

### Cadastro de um novo aluno

```
register.html (choose block → choose course → fill form → submit)
    → POST /users/register { nome, email, senha, confirmacao_senha, id_curso }
        → UserRegisterInput (Pydantic validation)
        → validate_user_register_business_rules()
        → email_exists() → 409 if duplicate
        → course_exists() → 404 if not found
        → hash_password(senha) → Argon2 hash
        → create_user() → INSERT usuario
    ← 201 { message: "usuario cadastrado com sucesso" }
→ redirect to login.html
```

### Login e acesso ao dashboard

```
login.html → POST /users/login { email, senha }
    → get_user_by_email()
    → verify_password(senha, senha_hash)
    → jwt.encode({ sub, nome, id_curso, exp })
    ← 200 { access_token, token_type, usuario }
→ sessionStorage.setItem("access_token", token)
→ redirect to dashboard.html
    → dashboard.js checks sessionStorage → ok
    → renders greeting from sessionStorage user_data
```

### Envio de comentário pela tela de desabafo

```
dashboard_comment.html loads
    → dashboard_comment.js checks sessionStorage → redirect to login if missing
    → GET /users/me (Bearer token) → { nome, id_curso, id_bloco }
    → GET /stats/courses-by-block/{id_bloco} → resolve nome do curso
    → renders chip "Nome do Aluno · Nome do Curso"

Aluno escreve texto → clica em "Enviar para a IA classificar":
    → POST /comentarios/ { texto } (Authorization: Bearer)
        → get_current_user() → extrai id_usuario do JWT
        → create_comentario(texto, id_usuario) → INSERT comentario → id_comentario
        → vector_service.generate_embedding(texto) → list[float] 384 dims
        → VectorRepository.create_embedding(id_comentario, vetor)
        → EmotionRepository.classify_comment(id_comentario)   ← KNN ponderado
            → SQL: top-7 vizinhos em emocao_exemplo (cosseno)
            → soma 1/(dist+0.05) por emoção, retorna ranking
        → emotion_classification_service.decide_final_emotion(texto, knn_result)
            → 4 regras: fallback de Neutro, sinais mistos, override de Neutro, override por margem
            → retorna { emocao_final, override_aplicado, motivo }
        → emo_repo.save_classification(id_comentario, id_emocao_final, distancia)
        ← { emocao_identificada, debug: { knn_top, knn_margem, override_aplicado, motivo } }
    → renderResult(emocao_identificada, texto)
        → applies vibe class (vibe-happy / vibe-sad / vibe-angry / vibe-neutral)
        → shows emoji + nome + descrição + trecho original
        → hides form, shows result card
```

---

### Comentário processado pela IA (via API direta)

```
POST /comentarios/ { texto }  — Authorization: Bearer <token>
    → get_current_user() → id_usuario = int(payload["sub"])
    → create_comentario(texto, id_usuario) → INSERT comentario → id_comentario
    → vector_service.generate_embedding(texto)
        → MiniLM model → list[float] 384 dims
    → VectorRepository.create_embedding(id_comentario, vetor)
        → INSERT embedding
    → EmotionRepository.classify_comment(id_comentario)
        → KNN top-7 contra emocao_exemplo
        → voto ponderado por 1/(distancia + 0.05)
        → retorna { id_emocao, nome_emocao, score, margem, distancia_min, ranking }
    → emotion_classification_service.decide_final_emotion(texto, knn_result)
        → polaridade = detect_polarity(texto)
        → aplica caso 0 (fallback Neutro), 1 (mistos), 2 (Neutro→polo), 3 (margem baixa)
        → retorna { emocao_final, override_aplicado, motivo }
    → emo_repo.save_classification(id_comentario, id_emocao_final, distancia_media)
        → INSERT/UPDATE classificacao_emocao
    ← { emocao_identificada, id_comentario, texto, debug }
```

### Inicialização do classificador KNN

```
POST /emotions/seed
    → EmotionRepository.upsert_emotion("Alegria") → id_emocao=1
    → EmotionRepository.upsert_emotion("Irritado") → id_emocao=2
    → EmotionRepository.upsert_emotion("Neutro") → id_emocao=3
    → EmotionRepository.reset_examples() → DELETE FROM emocao_exemplo
    → Para cada emoção em EMOTION_SEED_EXAMPLES (Alegria 57, Irritado 69, Neutro 64):
        → vector_service.generate_embeddings_batch(frases)  ← lote único
        → EmotionRepository.bulk_add_examples(id_emocao, [(texto, vetor), ...])
    ← { total_exemplos: 190, por_emocao: [...] }
```

### Visualização do Mapa de Blocos

```
dashboard_map.html loads
    → dashboard_map.js checks sessionStorage
    → GET /stats/blocks-map (Bearer token)
        → get_all_blocks() → lista de blocos
        → Para cada bloco:
            → DashboardRepository.get_emocao_geral_bloco()
                → Para cada curso do bloco:
                    → get_emocao_geral_curso() → moda + desempate
                → moda dos cursos + desempate
            → get_courses_by_block() + vibe de cada curso
            → get_block_emotion_counts() → distribuição
            → get_block_recent_comments() → 3 comentários
            → _build_block_explanation() → texto gerado
        ← { blocos: [...] }
    → renderBlocks(): cria <button class="block-marker"> no mapa
    → auto-selects first block → renderPanel()
    → setInterval(fetchBlocksMap, 30000) ← atualiza a cada 30s

Usuário clica em bloco X:
    → selectBlock(X) → renderPanel(block)
    → painel exibe: emoção, explicação, distribuição, cursos, comentários

Usuário clica no curso Y no painel:
    → navigate to course_stats.html?block_id=X&course_id=Y
```

### Raio-X do Curso (com navegação vinda do mapa)

```
course_stats.html?block_id=2&course_id=5 loads
    → course_stats.js reads initialBlockId=2, initialCourseId=5
    → fetchData(initialCourseId="5")
        → GET /stats/course?id_curso=5 (Bearer token)
            → get_course_name_by_id(5)
            → DashboardRepository.get_emocao_geral_curso(5)
            → get_course_comments(5)
            → get_available_emojis_for_course(5)
            → get_all_blocks()
            ← { curso, vibe_predominante, comentarios, filtros_emoji, lista_blocos }
        → initializeSelectors(data)
            → populates blockSelector with lista_blocos
            → GET /users/me → profile
            → blockSelector.value = "2" (from URL)
            → GET /stats/courses-by-block/2
            → courseSelector.value = "5"
        → initialCourseId is set → skip re-fetch cascade
        → updateMetrics(data) → shows course 5 data ✓
        → renderEmojiFilters(filtros_emoji)
        → renderComments(comentarios)
```

---

## 12. Mapa de conexões entre arquivos

```
main.py
├── dependencies.py          (get_db_connection, get_current_user)
├── routes/health.py
├── routes/users.py
│   ├── schemas/user_register.py
│   ├── schemas/user_login.py
│   ├── schemas/user_profile.py
│   ├── services/user_register_service.py
│   │   ├── services/user_register_validation.py
│   │   ├── services/password_hasher.py
│   │   └── respositories/user_register_repository.py
│   ├── services/user_login_service.py
│   │   ├── services/password_hasher.py
│   │   └── respositories/user_login_repository.py
│   └── services/user_profile_service.py
│       └── respositories/user_profile_repository.py
├── routes/comentarios.py                  (exige get_current_user)
│   ├── dependencies.py                    (get_current_user → id_usuario do JWT)
│   ├── services/vector_service.py         (fastembed singleton)
│   ├── services/emotion_classification_service.py  (léxico + decide_final_emotion)
│   ├── respositories/comentario_repository.py
│   ├── respositories/vector_repository.py
│   └── respositories/emotion_repository.py (KNN com voto ponderado)
├── routes/emotions.py
│   ├── services/vector_service.py
│   ├── services/emotion_seed_examples.py  (190 frases de seed)
│   └── respositories/emotion_repository.py
├── routes/vectors.py
│   ├── services/vector_service.py
│   └── respositories/vector_repository.py
├── routes/dashboards.py
│   └── respositories/dashboard_repository.py
└── routes/stats.py
    ├── services/stats_service.py
    │   ├── respositories/dashboard_repository.py
    │   └── respositories/stats_repository.py
    └── (get_current_user via dependencies.py)

Frontend:
index.html → (público, sem JS de negócio)
pages/login.html      ← js/login.js      → POST /users/login
pages/register.html   ← js/register.js   → POST /users/register
pages/dashboard.html  ← js/dashboard.js  → (guard de rota)
    → navega para dashboard_comment.html | dashboard_map.html | course_stats.html | account.html
pages/dashboard_comment.html ← js/dashboard_comment.js
    → GET /users/me
    → GET /stats/courses-by-block/{id_bloco}
    → POST /comentarios/ (Bearer token)
pages/dashboard_map.html ← js/dashboard_map.js
    → GET /stats/blocks-map
    → navega para course_stats.html?block_id=X&course_id=Y
pages/course_stats.html ← js/course_stats.js
    → GET /stats/course?id_curso=X
    → GET /stats/courses-by-block/{id_bloco}
    → GET /users/me
pages/account.html ← js/account.js
    → GET /users/me
    → PUT /users/me
    → PUT /users/me/password
```
