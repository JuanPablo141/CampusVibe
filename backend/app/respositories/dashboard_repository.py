from psycopg import Connection

class DashboardRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    def _resolver_empate_emocoes(self, results: list[tuple[str, int]]):
        """
        Lógica central de desempate solicitada:
        - Alegria == Neutro => Feliz
        - Irritado == Neutro => Triste
        - Alegria == Irritado => Neutro
        - Os três iguais (ou outros empates complexos) => Neutro
        """
        if not results:
            return {"emocao_geral": "Sem dados", "quantidade_vencedora": 0}
            
        max_total = results[0][1]
        empatados = [row[0] for row in results if row[1] == max_total]
        
        if len(empatados) == 1:
            return {"emocao_geral": empatados[0], "quantidade_vencedora": max_total}
            
        empate_set = set(empatados)
        
        # Regra 4: Os três iguais ou mais
        if len(empate_set) >= 3:
            return {"emocao_geral": "Neutro", "quantidade_vencedora": max_total}
            
        # Regra 1: Alegria == Neutro
        if "Alegria" in empate_set and "Neutro" in empate_set:
            return {"emocao_geral": "Feliz", "quantidade_vencedora": max_total}
            
        # Regra 2: Irritado == Neutro
        if "Irritado" in empate_set and "Neutro" in empate_set:
            return {"emocao_geral": "Triste", "quantidade_vencedora": max_total}
            
        # Regra 3: Alegria == Irritado
        if "Alegria" in empate_set and "Irritado" in empate_set:
            return {"emocao_geral": "Neutro", "quantidade_vencedora": max_total}
            
        return {"emocao_geral": "Neutro", "quantidade_vencedora": max_total}

    def get_emocao_geral_curso(self, id_curso: int):
        """
        Retorna a emoção predominante de um curso.
        Removemos o LIMIT 1 do SQL para poder tratar os empates em Python.
        """
        query = """
            SELECT e.nome_emocao, COUNT(ce.id_classificacao) as total
            FROM public.usuario u
            JOIN public.comentario com ON com.id_usuario = u.id_usuario
            JOIN public.classificacao_emocao ce ON ce.id_comentario = com.id_comentario
            JOIN public.emocao e ON e.id_emocao = ce.id_emocao
            WHERE u.id_curso = %s
            GROUP BY e.nome_emocao
            ORDER BY total DESC;
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (id_curso,))
        results = cursor.fetchall() # Devolve uma lista de (nome_emocao, total)
        
        return self._resolver_empate_emocoes(results)

    def get_emocao_geral_bloco(self, id_bloco: int):
        """
        Calcula a moda dos cursos, mas aplicando a regra de desempate INDIVIDUAL em cada curso
        antes de computar os votos para o bloco.
        """
        # 1. Pega todos os IDs de cursos desse bloco
        query_cursos = "SELECT id_curso FROM public.curso WHERE id_bloco = %s"
        cursor = self.connection.cursor()
        cursor.execute(query_cursos, (id_bloco,))
        cursos = cursor.fetchall()
        
        if not cursos:
            return {"emocao_geral": "Sem dados", "quantidade_vencedora": 0}
            
        frequencias_emocao = {}
        
        # 2. Roda a regra completa para cada curso do bloco
        for (id_curso,) in cursos:
            resultado_curso = self.get_emocao_geral_curso(id_curso)
            emocao_curso = resultado_curso["emocao_geral"]
            
            if emocao_curso != "Sem dados":
                frequencias_emocao[emocao_curso] = frequencias_emocao.get(emocao_curso, 0) + 1
                
        if not frequencias_emocao:
            return {"emocao_geral": "Sem dados", "quantidade_vencedora": 0}
            
        # 3. Converte o dicionário para uma lista de tuplas e ordena (Ex: [('Alegria', 2), ('Neutro', 2)])
        lista_freq = sorted(frequencias_emocao.items(), key=lambda x: x[1], reverse=True)
        
        # 4. Aplica as MESMAS regras de desempate no nível do bloco
        return self._resolver_empate_emocoes(lista_freq)
