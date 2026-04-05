"""
constants.py — Constantes e helpers compartilhados.
"""

import os
import json
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FATOR_ATRASO = {"dia": 1.0, "anterior": 0.75, "antiga": 0.5}
LABEL_TIPO   = {"dia": "do dia", "anterior": "anterior", "antiga": "antiga"}

LISTA_ATIVIDADES = [
    {"nome": "Atividade 1 - Frações",   "cor": "blue"},
    {"nome": "Atividade 2 - Equações",  "cor": "green"},
    {"nome": "Atividade 3 - Geometria", "cor": "orange"},
]

ARQUIVO_QUESTOES = {
    "Atividade 1 - Frações":   "dados/questoes_atividade1.json",
    "Atividade 2 - Equações":  "dados/questoes_atividade2.json",
    "Atividade 3 - Geometria": "dados/questoes_atividade3.json",
}

ALUNOS_POR_TURMA = {
    "A": ["Bianca", "Camila", "Daniela", "Diego", "Elisa", "Emanuel", "Giovana", "Karen", "Nathalia", "Omar", "Otávio", "Sabrina", "Sérgio", "Talita", "Vera", "Zeila"],
    "B": ["Alice", "Aline", "Camila", "Diego", "Débora", "Emanuel", "Hana", "Henrique", "Karen", "Laura", "Marcos", "Nathalia", "Nathan", "Paloma", "Sofia", "Talita", "Ursula", "Victor", "Yuri", "Zeila"],
    "C": ["Bianca", "Dara", "Eric", "Fernanda", "Igor", "Isabela", "Ivo", "Kevin", "Marcos", "Mariana", "Nathalia", "Olga", "Paula", "Renata", "Samuel", "Tiago", "Ulisses", "William", "Ximena", "Yuri", "Zeca"],
    "D": ["Bernardo", "Elisa", "Fabio", "Fernanda", "Graça", "Ingrid", "Ivo", "Joaquim", "João", "Karen", "Kevin", "Lucas", "Nathan", "Valentina", "Victor", "William", "Ximena", "Yuri"],
    "F": ["Bianca", "Diego", "Eduardo", "Fabio", "Giovana", "Helena", "Joana", "João", "Julia", "Lucas", "Milena", "Pedro", "Quésia", "Renata", "Samuel", "Vera", "Victor", "Wendy", "Yuri"],
}


def formatar_tempo(segundos: float) -> str:
    m = int(segundos) // 60
    s = int(segundos) % 60
    return f"{m:02d}:{s:02d}"


def _intercalar_por_dificuldade(perguntas: list) -> list:
    """Embaralha cada grupo de dificuldade e intercala em ciclos (F→M→D→F→M→D…)."""
    faceis   = [p for p in perguntas if p.get("dificuldade") == 1]
    medias   = [p for p in perguntas if p.get("dificuldade") == 2]
    dificeis = [p for p in perguntas if p.get("dificuldade") == 3]
    random.shuffle(faceis)
    random.shuffle(medias)
    random.shuffle(dificeis)
    grupos = [g[:] for g in [faceis, medias, dificeis] if g]
    resultado = []
    while any(grupos):
        for g in grupos:
            if g:
                resultado.append(g.pop(0))
    return resultado


def carregar_perguntas(nome_atividade: str) -> list[dict]:
    """Carrega TODAS as questões da atividade, intercaladas por dificuldade."""
    caminho_relativo = ARQUIVO_QUESTOES.get(nome_atividade, "dados/questoes_atividade1.json")
    caminho_completo = os.path.join(BASE_DIR, caminho_relativo)
    with open(caminho_completo, "r", encoding="utf-8") as f:
        perguntas = json.load(f)
    return _intercalar_por_dificuldade(perguntas)
