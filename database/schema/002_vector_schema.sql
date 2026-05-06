-- 002_vector_schema.sql
-- Objetivo: Configurar a extensão pgvector e criar a tabela de embeddings
-- Escopo: pgvector, tabela embedding

BEGIN;

-- 1. Ativar a extensão de vetores (Suportado nativamente pelo Supabase)
CREATE EXTENSION IF NOT EXISTS vector
WITH SCHEMA public;

-- =========================================
-- TABELA: embedding
-- =========================================
-- OBS: O tamanho do vetor (ex: 384) depende do modelo de IA que usaremos depois.
-- 384 é o padrão para modelos locais muito comuns (como o all-MiniLM-L6-v2).
-- Se optarmos pela OpenAI, o tamanho geralmente é 1536.
CREATE TABLE public.embedding (
    id_embedding INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_comentario INTEGER NOT NULL,
    vetor vector(384) NOT NULL, -- Vetor matemático de 384 dimensões
    
    CONSTRAINT fk_embedding_comentario
        FOREIGN KEY (id_comentario)
        REFERENCES public.comentario (id_comentario)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- =========================================
-- ÍNDICES
-- =========================================
-- Índice na chave estrangeira para buscas rápidas por comentário
CREATE INDEX idx_embedding_id_comentario
    ON public.embedding (id_comentario);

-- Índice HNSW (Hierarchical Navigable Small World)
-- Essencial para fazer buscas vetoriais rápidas no Supabase/pgvector
-- Usamos 'vector_cosine_ops' porque a similaridade por cosseno é a mais usada para textos
CREATE INDEX idx_embedding_vetor
    ON public.embedding USING hnsw (vetor vector_cosine_ops);

COMMIT;
