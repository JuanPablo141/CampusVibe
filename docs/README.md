# Documentação — CampusVibe

Esta pasta centraliza toda a documentação técnica do projeto. Os arquivos aqui não fazem parte do código de execução — são para leitura humana e referência.

---

## Índice dos documentos

### 1. [`ARCHITECTURE.md`](./ARCHITECTURE.md)

**Documentação completa de arquitetura.** ~950 linhas cobrindo:

- Visão geral do sistema e stack tecnológica
- Estrutura de diretórios anotada
- Schema do banco e hierarquia de dados
- Backend em detalhes: ponto de entrada, dependências, schemas Pydantic, rotas, serviços, repositórios
- **Pipeline de IA completo** — embedding, KNN com voto ponderado, léxico de polaridade, thresholds e justificativas
- Sistema de emoções e regras de desempate
- Frontend: páginas, scripts, estilos
- Autenticação e proteções de segurança
- Lista completa de todos os endpoints da API
- Fluxos completos de uso (cadastro, login, comentário, mapa, raio-x)
- Mapa de conexões entre todos os arquivos

**Para quem:** desenvolvedores que vão contribuir no projeto, professor avaliador, qualquer pessoa que precise entender uma decisão técnica específica.

### 2. [`schema_v1_scope.md`](./schema_v1_scope.md)

**Escopo da versão inicial do schema do banco.** Documento curto que registra as decisões de design da primeira versão das tabelas (`bloco`, `curso`, `usuario`, `comentario`) — antes de embeddings e classificação de emoção entrarem em cena.

**Para quem:** histórico de design, útil para entender a evolução do banco.

### 3. Modelos visuais do banco

| Arquivo | Formato | Conteúdo |
|---------|---------|----------|
| [`Modelo_conceitual_1.0.png`](./Modelo_conceitual_1.0.png) | Imagem PNG | Diagrama conceitual (entidades e relacionamentos no nível abstrato) |
| `Modelo_conceitual_1.0.brM3` | brModelo 3 | Mesmo modelo, em formato editável do brModelo |
| [`Modelo_logico_1.0.png`](./Modelo_logico_1.0.png) | Imagem PNG | Diagrama lógico (tabelas, colunas, chaves, tipos) |
| `Modelo_logico_1.0.brM3` | brModelo 3 | Mesmo modelo, em formato editável do brModelo |

**Para quem:** visualização rápida do banco sem precisar ler SQL. Os arquivos `.brM3` podem ser abertos no [brModelo](http://www.sis4.com/brModelo/) para edição.

---

## Roteiro de leitura sugerido

Dependendo do seu objetivo, sugiro abrir os documentos nesta ordem:

### Para uma visão geral rápida

1. [`../README.md`](../README.md) — visão de alto nível do projeto
2. [`ARCHITECTURE.md` — seções 1 a 3](./ARCHITECTURE.md#1-visão-geral-do-sistema) — visão geral, stack e estrutura de diretórios

### Para entender o pipeline de IA

1. [`ARCHITECTURE.md` — seção 6 (Pipeline de IA)](./ARCHITECTURE.md#6-pipeline-de-ia) — explicação completa das três camadas
2. [`ARCHITECTURE.md` — seção 7 (Sistema de emoções)](./ARCHITECTURE.md#7-sistema-de-emoções-e-regras-de-desempate) — regras de desempate
3. Código fonte:
   - [`../backend/app/services/emotion_classification_service.py`](../backend/app/services/emotion_classification_service.py) — léxico de polaridade
   - [`../backend/app/respositories/emotion_repository.py`](../backend/app/respositories/emotion_repository.py) — query SQL do KNN

### Para entender o banco

1. [`Modelo_logico_1.0.png`](./Modelo_logico_1.0.png) — visão visual rápida
2. [`ARCHITECTURE.md` — seção 4 (Banco de dados)](./ARCHITECTURE.md#4-banco-de-dados)
3. [`../database/README.md`](../database/README.md) — migrations e como aplicar
4. Os 5 arquivos SQL em ordem: `001` → `005`

### Para entender os fluxos de uso

1. [`ARCHITECTURE.md` — seção 11 (Fluxos completos)](./ARCHITECTURE.md#11-fluxos-completos) — passo a passo de cada caso de uso

### Para entender a estrutura de arquivos

1. [`ARCHITECTURE.md` — seção 12 (Mapa de conexões)](./ARCHITECTURE.md#12-mapa-de-conexões-entre-arquivos) — quem importa o que, do `main.py` até os repositórios

---

## Notas

- Toda documentação está em português.
- O `ARCHITECTURE.md` é a fonte canônica — se há divergência entre ele e outro documento, ele tem precedência.
- Modelos `.brM3` exigem o software brModelo para edição; os `.png` correspondentes podem ser abertos em qualquer visualizador de imagens.
