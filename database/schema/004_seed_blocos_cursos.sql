-- 004_seed_blocos_cursos.sql
-- Script de popularização do banco de dados com a estrutura hierárquica do campus

BEGIN;

-- =========================================
-- INSERÇÃO DOS BLOCOS (Com IDs forçados)
-- =========================================
INSERT INTO public.bloco (id_bloco, nome_bloco)
OVERRIDING SYSTEM VALUE
VALUES
    (0, 'BLOCO A'),
    (1, 'BLOCO B'),
    (2, 'BLOCO C'),
    (3, 'BLOCO D')
ON CONFLICT (nome_bloco) DO NOTHING;

SELECT setval(pg_get_serial_sequence('public.bloco', 'id_bloco'), 3);


-- =========================================
-- INSERÇÃO DOS CURSOS (Com IDs forçados)
-- =========================================

-- Cursos do BLOCO A (id_bloco = 0)
INSERT INTO public.curso (id_curso, nome_curso, id_bloco)
OVERRIDING SYSTEM VALUE
VALUES
    (0,  'Ciência da Computação',               0),
    (4,  'Sistemas de Informação',               0),
    (5,  'Redes de Computadores',                0),
    (6,  'Análise e Desenvolvimento de Sistemas',0),
    (7,  'Engenharia da Computação',             0),
    (8,  'Engenharia Civil',                     0),
    (9,  'Engenharia de Produção',               0),
    (10, 'Engenharia Elétrica',                  0),
    (11, 'Engenharia Mecânica',                  0),
    (12, 'Engenharia Química',                   0),
    (13, 'Engenharia Ambiental',                 0),
    (14, 'Construção de Edifícios',              0),
    (15, 'Data Science',                         0),
    (16, 'Game Design',                          0)
ON CONFLICT (nome_curso) DO NOTHING;

-- Cursos do BLOCO B (id_bloco = 1)
INSERT INTO public.curso (id_curso, nome_curso, id_bloco)
OVERRIDING SYSTEM VALUE
VALUES
    (17, 'Administração',               1),
    (18, 'Ciências Contábeis',          1),
    (19, 'Ciências Econômicas',         1),
    (20, 'Gestão Financeira',           1),
    (21, 'Gestão Comercial',            1),
    (22, 'Gestão de Recursos Humanos',  1),
    (23, 'Gestão Pública',              1),
    (24, 'Gestão Hospitalar',           1),
    (25, 'Gestão da Qualidade',         1),
    (26, 'Gestão de Turismo',           1),
    (27, 'Logística',                   1),
    (28, 'Marketing',                   1),
    (29, 'Processos Gerenciais',        1),
    (30, 'Empreendedorismo Digital',    1)
ON CONFLICT (nome_curso) DO NOTHING;

-- Cursos do BLOCO C (id_bloco = 2)
INSERT INTO public.curso (id_curso, nome_curso, id_bloco)
OVERRIDING SYSTEM VALUE
VALUES
    (31, 'Direito',         2),
    (32, 'Serviço Social',  2)
ON CONFLICT (nome_curso) DO NOTHING;

-- Cursos do BLOCO D (id_bloco = 3)
INSERT INTO public.curso (id_curso, nome_curso, id_bloco)
OVERRIDING SYSTEM VALUE
VALUES
    (33, 'Farmácia',            3),
    (34, 'Enfermagem',          3),
    (35, 'Medicina',            3),
    (36, 'Odontologia',         3),
    (37, 'Psicologia',          3),
    (38, 'Fisioterapia',        3),
    (39, 'Nutrição',            3),
    (40, 'Biomedicina',         3),
    (41, 'Radiologia',          3),
    (42, 'Estética e Cosmética',3),
    (43, 'Educação Física',     3),
    (44, 'Fonoaudiologia',      3)
ON CONFLICT (nome_curso) DO NOTHING;

-- Ajusta a sequência para não colidir com os IDs forçados
SELECT setval(pg_get_serial_sequence('public.curso', 'id_curso'), 44);

COMMIT;
