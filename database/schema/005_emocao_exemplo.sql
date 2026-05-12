-- 005_emocao_exemplo.sql
-- Objetivo: Substituir a estratégia de "vetor âncora médio" por KNN com exemplos individuais.
-- Cada frase de seed vira sua própria linha (com seu vetor), e a classificação passa a usar
-- os k vizinhos mais próximos com voto ponderado pela distância.

BEGIN;

-- 1. O vetor_ancora antigo deixa de ser obrigatório (vai ficar como histórico/legado).
--    A nova classificação consulta emocao_exemplo, não mais o centroide.
ALTER TABLE public.emocao
    ALTER COLUMN vetor_ancora DROP NOT NULL;

-- =========================================
-- TABELA: emocao_exemplo
-- Cada linha = uma frase de exemplo + seu vetor.
-- O classificador faz KNN contra essa tabela.
-- =========================================
CREATE TABLE IF NOT EXISTS public.emocao_exemplo (
    id_exemplo INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_emocao INTEGER NOT NULL,
    texto TEXT NOT NULL,
    vetor vector(384) NOT NULL,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_emocao_exemplo_emocao
        FOREIGN KEY (id_emocao)
        REFERENCES public.emocao (id_emocao)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Índice na FK para joins/limpeza rápida por emoção
CREATE INDEX IF NOT EXISTS idx_emocao_exemplo_id_emocao
    ON public.emocao_exemplo (id_emocao);

-- Índice HNSW para busca vetorial (KNN) com distância de cosseno
CREATE INDEX IF NOT EXISTS idx_emocao_exemplo_vetor
    ON public.emocao_exemplo USING hnsw (vetor vector_cosine_ops);

COMMIT;
