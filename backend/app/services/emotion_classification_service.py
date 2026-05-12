"""
Camada de decisão final do classificador de emoções.

O pipeline é:
    1. Embedding do texto      (vector_service)
    2. KNN no banco            (emotion_repository.classify_comment)
    3. Léxico de palavras-fortes deste módulo decide se sobrescreve o KNN.

O léxico cobre o caso em que o modelo de embeddings é "puxado" pelo vocabulário
acadêmico (aula, prova, professor) e ignora o sinal emocional óbvio ("péssima",
"ótima", "odiei"). Ele só dispara quando há sinal forte e o KNN está indeciso
ou disse Neutro — nunca contradiz um veredito vetorial claro de polaridade certa.
"""

import re
import unicodedata


# Polaridade negativa forte — gatilho para "Irritado".
NEGATIVE_LEXICON = {
    # Avaliações ruins
    "pessimo", "pessima", "pessimos", "pessimas",
    "horrivel", "horriveis", "horroroso", "horrorosa",
    "ruim", "ruins",
    "chato", "chata", "chatos", "chatas", "chatice",
    "ridiculo", "ridicula", "ridiculos", "ridiculas",
    "lamentavel", "lamentaveis",
    "vergonhoso", "vergonhosa",
    "decepcionante", "decepcionado", "decepcionada", "decepcao", "decepcionei",
    "frustrante", "frustrado", "frustrada", "frustracao",
    "humilhante", "humilhado", "humilhada",
    "insuportavel", "insuportaveis",
    "desorganizado", "desorganizada", "desorganizacao",
    # Palavrões / desabafo
    "merda", "porcaria", "lixo", "bosta", "desgraca",
    # Emoções negativas explícitas
    "odeio", "odiei", "odiar", "odio",
    "detesto", "detestei", "detestar",
    "raiva", "furia", "furioso", "furiosa",
    "triste", "tristeza", "deprimido", "deprimida", "depressao", "depressivo",
    "ansiedade", "ansioso", "ansiosa",
    "estresse", "estressado", "estressada", "estressante",
    "panico", "desespero", "desesperado", "desesperada",
    "sofrimento", "sofrendo", "sofrer", "sofri",
    "cansado", "cansada", "cansativo", "cansativa", "exausto", "exausta",
    "esgotado", "esgotada", "esgotamento",
    "desanimado", "desanimada", "desanimo",
    "burnout",
    # Reprovação / fracasso
    "reprovado", "reprovada", "reprovei", "reprovou",
    "rodei", "rodou",
    "fracasso", "fracassei", "fracassou",
    "zero", "zerei",
    # Críticas ao professor / instituição
    "incompetente", "incompetencia",
    "arrogante", "grosseiro", "grosseira", "rude",
    "preguicoso", "preguicosa",
}

# Polaridade positiva forte — gatilho para "Alegria".
POSITIVE_LEXICON = {
    # Avaliações boas
    "otimo", "otima", "otimos", "otimas",
    "excelente", "excelentes",
    "incrivel", "incriveis",
    "maravilhoso", "maravilhosa",
    "perfeito", "perfeita", "perfeitos", "perfeitas",
    "fantastico", "fantastica", "fantasticos", "fantasticas",
    "sensacional", "espetacular", "brilhante",
    "lindo", "linda", "belo", "bela",
    # Emoções positivas
    "adorei", "adoro", "adorando",
    "amei", "amo", "amando",
    "feliz", "felizes", "felicidade",
    "alegre", "alegria",
    "satisfeito", "satisfeita", "satisfacao",
    "encantado", "encantada", "encantador", "encantadora",
    "empolgado", "empolgada", "empolgacao",
    "motivado", "motivada", "motivacao",
    "agradecido", "agradecida", "gratidao", "grato", "grata",
    "orgulho", "orgulhoso", "orgulhosa",
    "celebrar", "celebrando", "celebracao",
    # Sucessos — "passou" foi removido intencionalmente: "professor passou trabalho"
    # usa o mesmo verbo no sentido de "atribuiu", gerando falso positivo.
    "passei", "aprovado", "aprovada", "aprovei", "aprovou",
    "sucesso", "vitoria", "conquista", "conquistei",
    # Avaliações casuais positivas
    "show", "top", "massa", "daora", "bacana", "irado",
    "facil", "facinho", "tranquilo", "tranquila",
}


# Quando o KNN tem margem abaixo deste limiar, consideramos a classificação "indecisa"
# e damos voz ao léxico se houver sinal forte.
LOW_MARGIN_THRESHOLD = 0.10

# Quando o vizinho mais próximo está além desta distância E o léxico está em silêncio,
# é provável que nenhum exemplo do seed seja realmente similar ao texto — isso ocorre
# com frases informativas/neutras que ficam num "deserto" entre os clusters emocionais.
# Nesse caso, fallback seguro é Neutro.
NEUTRAL_DISTANCE_FALLBACK = 0.30


def _strip_accents(text: str) -> str:
    """Remove acentos para que 'péssima' e 'pessima' caiam no mesmo conjunto."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _tokens(text: str) -> set[str]:
    normalized = _strip_accents(text).lower()
    return set(re.findall(r"\b\w+\b", normalized))


def detect_polarity(texto: str) -> dict:
    """
    Retorna um diagnóstico do que o léxico viu no texto.
    {
        "has_negative": bool,
        "has_positive": bool,
        "negative_hits": [...],
        "positive_hits": [...]
    }
    """
    tokens = _tokens(texto)
    negative_hits = sorted(tokens & NEGATIVE_LEXICON)
    positive_hits = sorted(tokens & POSITIVE_LEXICON)
    return {
        "has_negative": bool(negative_hits),
        "has_positive": bool(positive_hits),
        "negative_hits": negative_hits,
        "positive_hits": positive_hits,
    }


def decide_final_emotion(texto: str, knn_result: dict) -> dict:
    """
    Recebe o resultado do KNN e decide a emoção final, considerando o léxico.

    Regras (em ordem):
      1. Sinais mistos (positivo + negativo) → mantém o KNN (caso ambíguo).
      2. KNN disse Neutro e há sinal forte unilateral → override.
      3. KNN tem margem < LOW_MARGIN_THRESHOLD e há sinal forte unilateral
         contrário ao top → override.
      4. KNN tem opinião clara e o léxico concorda (ou está em silêncio) → mantém.

    Retorna dict com:
        emocao_final, override_aplicado, motivo, knn (resultado original),
        polaridade (diagnóstico do léxico).
    """
    polaridade = detect_polarity(texto)
    top_nome = knn_result["nome_emocao"]
    margem = knn_result.get("margem", 1.0)
    dist_min = knn_result.get("distancia_min", 0.0)

    # Caso 0: distância mínima alta + margem baixa + léxico em silêncio.
    # Frases informativas neutras ficam num "deserto" entre os clusters emocionais
    # (dist alta) e não produzem um ganhador claro (margem baixa). Se o KNN é
    # muito confiante (margem >= 0.50), não interferimos — ele achou algo próximo.
    if (
        dist_min > NEUTRAL_DISTANCE_FALLBACK
        and margem < 0.50
        and not polaridade["has_negative"]
        and not polaridade["has_positive"]
        and top_nome != "Neutro"
    ):
        return {
            "emocao_final": "Neutro",
            "override_aplicado": True,
            "motivo": (
                f"nenhum exemplo próximo (dist_min={dist_min:.2f} > {NEUTRAL_DISTANCE_FALLBACK})"
                " e léxico em silêncio — texto provavelmente informativo"
            ),
            "knn": knn_result,
            "polaridade": polaridade,
        }

    # Caso 1: sinais conflitantes → o KNN decide.
    if polaridade["has_negative"] and polaridade["has_positive"]:
        return {
            "emocao_final": top_nome,
            "override_aplicado": False,
            "motivo": "sinais mistos no texto, mantido o veredito do KNN",
            "knn": knn_result,
            "polaridade": polaridade,
        }

    target = None
    if polaridade["has_negative"] and not polaridade["has_positive"]:
        target = "Irritado"
    elif polaridade["has_positive"] and not polaridade["has_negative"]:
        target = "Alegria"

    if target is None:
        return {
            "emocao_final": top_nome,
            "override_aplicado": False,
            "motivo": "léxico em silêncio",
            "knn": knn_result,
            "polaridade": polaridade,
        }

    # Caso 2: KNN disse Neutro mas há sinal forte → override sempre.
    if top_nome == "Neutro":
        return {
            "emocao_final": target,
            "override_aplicado": True,
            "motivo": f"KNN disse Neutro mas o texto contém sinal forte de {target}",
            "knn": knn_result,
            "polaridade": polaridade,
        }

    # Caso 3: KNN contrariou o léxico com margem pequena → override.
    if top_nome != target and margem < LOW_MARGIN_THRESHOLD:
        return {
            "emocao_final": target,
            "override_aplicado": True,
            "motivo": (
                f"KNN ficou indeciso (margem {margem:.2f}) e o léxico aponta para {target}"
            ),
            "knn": knn_result,
            "polaridade": polaridade,
        }

    return {
        "emocao_final": top_nome,
        "override_aplicado": False,
        "motivo": "léxico concorda ou KNN tem confiança suficiente",
        "knn": knn_result,
        "polaridade": polaridade,
    }
