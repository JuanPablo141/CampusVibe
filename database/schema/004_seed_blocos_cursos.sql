-- 004_seed_blocos_cursos.sql
-- Script de popularização do banco de dados com a estrutura hierárquica do campus

BEGIN;

-- =========================================
-- INSERÇÃO DOS BLOCOS (Com IDs forçados)
-- =========================================
-- Como a tabela foi criada com "GENERATED ALWAYS AS IDENTITY", 
-- precisamos usar "OVERRIDING SYSTEM VALUE" para forçar os IDs 0, 1, 2 e 3 solicitados.
INSERT INTO public.bloco (id_bloco, nome_bloco)
OVERRIDING SYSTEM VALUE
VALUES 
    (0, 'BLOCO A'),
    (1, 'BLOCO B'),
    (2, 'BLOCO C'),
    (3, 'BLOCO D')
ON CONFLICT (nome_bloco) DO NOTHING;

-- Ajusta a sequência automática do banco para não tentar usar os IDs que acabamos de forçar
SELECT setval(pg_get_serial_sequence('public.bloco', 'id_bloco'), 3);


-- =========================================
-- INSERÇÃO DOS CURSOS
-- =========================================
-- Nota: Deixamos o PostgreSQL gerar o "id_curso" automaticamente (Sistemas de Informação será o 1, e assim por diante).

-- Cursos do BLOCO A (id_bloco = 0)
INSERT INTO public.curso (nome_curso, id_bloco) VALUES 
    ('Sistemas de Informação', 0),
    ('Redes de Computadores', 0),
    ('Análise e Desenvolvimento de Sistemas', 0),
    ('Engenharia da Computação', 0),
    ('Engenharia Civil', 0),
    ('Engenharia de Produção', 0),
    ('Engenharia Elétrica', 0),
    ('Engenharia Mecânica', 0),
    ('Engenharia Química', 0),
    ('Engenharia Ambiental', 0),
    ('Construção de Edifícios', 0),
    ('Data Science', 0),
    ('Game Design', 0)
ON CONFLICT (nome_curso) DO NOTHING;

-- Cursos do BLOCO B (id_bloco = 1)
INSERT INTO public.curso (nome_curso, id_bloco) VALUES 
    ('Administração', 1),
    ('Ciências Contábeis', 1),
    ('Ciências Econômicas', 1),
    ('Gestão Financeira', 1),
    ('Gestão Comercial', 1),
    ('Gestão de Recursos Humanos', 1),
    ('Gestão Pública', 1),
    ('Gestão Hospitalar', 1),
    ('Gestão da Qualidade', 1),
    ('Gestão de Turismo', 1),
    ('Logística', 1),
    ('Marketing', 1),
    ('Processos Gerenciais', 1),
    ('Empreendedorismo Digital', 1)
ON CONFLICT (nome_curso) DO NOTHING;

-- Cursos do BLOCO C (id_bloco = 2)
INSERT INTO public.curso (nome_curso, id_bloco) VALUES 
    ('Direito', 2),
    ('Serviço Social', 2),
    ('Gestão de Serviços Jurídicos e Notariais', 2),
    ('Ciências Políticas', 2)
ON CONFLICT (nome_curso) DO NOTHING;

-- Cursos do BLOCO D (id_bloco = 3)
INSERT INTO public.curso (nome_curso, id_bloco) VALUES 
    ('Medicina', 3),
    ('Enfermagem', 3),
    ('Psicologia', 3),
    ('Nutrição', 3),
    ('Odontologia', 3),
    ('Farmácia', 3),
    ('Biomedicina', 3),
    ('Fisioterapia', 3),
    ('Educação Física', 3),
    ('Estética e Cosméticos', 3),
    ('Podologia', 3),
    ('Radiologia', 3)
ON CONFLICT (nome_curso) DO NOTHING;

COMMIT;
