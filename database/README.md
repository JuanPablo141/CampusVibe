# Database — CampusVibe

Camada de persistência do CampusVibe. Usa **PostgreSQL** com a extensão **`pgvector`** para armazenar embeddings vetoriais e fazer busca por similaridade de cosseno via índice HNSW.

Em produção, o banco está hospedado no **Supabase** (PostgreSQL gerenciado com `pgvector` habilitado nativamente).

---

## Estrutura

```
database/
└── schema/
    ├── 001_initial_schema_v1.sql      # Tabelas iniciais (bloco, curso, usuario, comentario)
    ├── 002_vector_schema.sql          # pgvector + tabela embedding + índice HNSW
    ├── 003_emotions_schema.sql        # Tabelas emocao + classificacao_emocao
    ├── 004_seed_blocos_cursos.sql     # Seed de blocos e cursos do campus
    ├── 005_emocao_exemplo.sql         # Tabela emocao_exemplo (KNN) + vetor_ancora nullable
    └── test_schema_v1.sql             # Queries de teste do schema
```

---

## Migrations

Aplicar **na ordem numérica**. Cada migration é uma transação (`BEGIN; ... COMMIT;`).

| # | Arquivo | O que introduz |
|---|---------|----------------|
| 001 | `001_initial_schema_v1.sql` | Tabelas `bloco`, `curso`, `usuario`, `comentario`. Índice único case-insensitive em `usuario.email`. Constraints de FK e índices nos FKs. |
| 002 | `002_vector_schema.sql` | Habilita a extensão `pgvector`. Cria a tabela `embedding` com coluna `vetor vector(384)` e índice **HNSW** com `vector_cosine_ops`. |
| 003 | `003_emotions_schema.sql` | Cria `emocao` (com `vetor_ancora` — abordagem legada de centroide) e `classificacao_emocao` (1:1 com `comentario`). |
| 004 | `004_seed_blocos_cursos.sql` | Insere os 4 blocos (A, B, C, D) e os 44 cursos do campus com IDs forçados via `OVERRIDING SYSTEM VALUE`. |
| 005 | `005_emocao_exemplo.sql` | Torna `emocao.vetor_ancora` nullable e cria a tabela `emocao_exemplo` (KNN). Adiciona índice HNSW para busca vetorial rápida. |

---

## Hierarquia de dados

```
bloco (4 blocos físicos do campus)
 └── curso  (44 cursos distribuídos pelos blocos)
      └── usuario  (N alunos por curso)
           └── comentario  (N comentários por aluno)
                ├── embedding              (1 vetor de 384d por comentário)
                └── classificacao_emocao   (1 emoção por comentário, UNIQUE)

emocao (3 emoções base: Alegria, Irritado, Neutro)
 └── emocao_exemplo  (190 frases de referência usadas pelo KNN)
```

### Blocos e seus cursos

| ID | Nome | Conteúdo |
|---|---|---|
| 0 | BLOCO A | Tecnologia e Engenharia (Ciência da Computação, Engenharias, Data Science, Game Design, etc.) |
| 1 | BLOCO B | Negócios e Gestão (Administração, Marketing, Logística, Empreendedorismo Digital, etc.) |
| 2 | BLOCO C | Jurídico e Social (Direito, Serviço Social) |
| 3 | BLOCO D | Saúde (Medicina, Farmácia, Biomedicina, Psicologia, Enfermagem, etc.) |

---

## Como aplicar as migrations

### No Supabase (recomendado)

1. Acesse o painel do projeto: https://supabase.com/dashboard
2. Vá em **SQL Editor**
3. Para cada arquivo de `001_initial_schema_v1.sql` até `005_emocao_exemplo.sql`:
   - Cole o conteúdo
   - Clique em **Run**
   - Confirme que executou sem erros antes de passar para o próximo

A extensão `pgvector` já vem disponível no Supabase — a migration `002` apenas a habilita com `CREATE EXTENSION IF NOT EXISTS vector`.

### Em um PostgreSQL local com Docker

```bash
# Subir um PostgreSQL com pgvector
docker run -d \
    --name campusvibe-db \
    -e POSTGRES_PASSWORD=postgres \
    -p 5432:5432 \
    pgvector/pgvector:pg16

# Aplicar as migrations em ordem
for f in database/schema/00*.sql; do
    docker exec -i campusvibe-db psql -U postgres -d postgres < "$f"
done
```

---

## Seeds

O projeto tem **dois seeds independentes**:

### 1. Blocos e cursos (SQL)

Já incluído na migration `004_seed_blocos_cursos.sql` — roda automaticamente ao aplicar essa migration. Usa `ON CONFLICT (nome_*) DO NOTHING` para ser idempotente.

### 2. Emoções e exemplos do KNN (via API)

**Não é SQL puro** — depende do modelo de IA do backend (cada uma das 190 frases precisa ser convertida em vetor de 384 dimensões antes de ser inserida). Por isso é feito através de um endpoint da API:

```bash
curl -X POST http://127.0.0.1:8000/emotions/seed
# Ou em produção:
curl -X POST https://project-root-production-b179.up.railway.app/emotions/seed
```

Detalhes em [`../backend/README.md`](../backend/README.md#popular-o-seed-de-emoções-necessário-uma-vez).

---

## Testes do schema

O arquivo [`schema/test_schema_v1.sql`](./schema/test_schema_v1.sql) contém queries de verificação manual do schema (ex: contagem de cursos por bloco, validação de FKs). Não é um teste automatizado — rode manualmente no SQL Editor quando quiser auditar o estado do banco.

---

## Notas importantes

- **Índice HNSW** (Hierarchical Navigable Small World) — usado em `embedding.vetor` e `emocao_exemplo.vetor` para acelerar a busca vetorial. É um índice **aproximado**: pode não retornar os vizinhos matematicamente mais próximos, mas é ordens de magnitude mais rápido em datasets grandes. Para os 190 exemplos do seed, o erro é desprezível.

- **`OVERRIDING SYSTEM VALUE`** — usado na migration `004` para forçar IDs específicos dos blocos e cursos (ex: `id_bloco = 0` é sempre o BLOCO A), mesmo com colunas `GENERATED ALWAYS AS IDENTITY`. Isso é importante para que o frontend possa hard-codear referências sem depender da ordem de inserção. A migration usa `setval()` ao final para que próximas inserções não colidam.

- **`vetor_ancora` legado** — a coluna foi `NOT NULL` na migration `003` (estratégia inicial de "vetor médio" por emoção) e tornou-se `NULL` na migration `005`, quando o classificador migrou para KNN com exemplos individuais. A coluna foi mantida para preservar compatibilidade histórica, mas não é usada pela classificação atual.

- **Distância de cosseno** (`<=>`) — operador do `pgvector` usado em todas as buscas vetoriais. Mede o ângulo entre vetores (não o tamanho), o que é ideal para texto: documentos curtos e longos com o mesmo significado ficam próximos.

---

## Documentação relacionada

- Estrutura completa de tabelas e relacionamentos: [`../docs/ARCHITECTURE.md#4-banco-de-dados`](../docs/ARCHITECTURE.md#4-banco-de-dados)
- Modelos visuais (conceitual e lógico): [`../docs/`](../docs/) — arquivos `.png` e `.brM3`
- Escopo da versão inicial do schema: [`../docs/schema_v1_scope.md`](../docs/schema_v1_scope.md)
