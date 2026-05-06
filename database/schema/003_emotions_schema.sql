-- 003_emotions_schema.sql
-- Objetivo: Criar tabelas para classificação semântica de emoções

BEGIN;

-- =========================================
-- TABELA: emocao
-- Armazena as emoções e o "vetor ideal" que representa cada uma
-- =========================================
CREATE TABLE public.emocao (
    id_emocao INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome_emocao VARCHAR(50) NOT NULL,
    vetor_ancora vector(384) NOT NULL, -- Vetor gerado pelas palavras-chave da emoção
    
    CONSTRAINT uq_emocao_nome UNIQUE (nome_emocao)
);

-- =========================================
-- TABELA: classificacao_emocao
-- Relaciona o comentário com a emoção calculada
-- =========================================
CREATE TABLE public.classificacao_emocao (
    id_classificacao INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_comentario INTEGER NOT NULL,
    id_emocao INTEGER NOT NULL,
    distancia DECIMAL(10,5), -- Armazena a distância (opcional, útil para saber o grau de confiança)
    data_classificacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_classificacao_comentario
        FOREIGN KEY (id_comentario)
        REFERENCES public.comentario (id_comentario)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_classificacao_emocao
        FOREIGN KEY (id_emocao)
        REFERENCES public.emocao (id_emocao)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
        
    -- Garante que um comentário não seja classificado duas vezes repetidas
    CONSTRAINT uq_classificacao_comentario UNIQUE (id_comentario)
);

COMMIT;
