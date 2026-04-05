"""
controllers/liberacoes_controller.py — Persistência das atividades liberadas em JSON.

Cada item tem o mesmo formato de state.atividades_liberadas, com campo extra:
  expira_em: str ISO timestamp
  _lib_id: int (id na tabela liberacoes do DB, para log de cancelamento)
"""
import os
import json
from datetime import datetime

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_PATH  = os.path.join(BASE_DIR, "dados", "atividades_liberadas.json")


def salvar_liberadas(lista: list) -> None:
    os.makedirs(os.path.dirname(LIB_PATH), exist_ok=True)
    with open(LIB_PATH, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)


def carregar_liberadas() -> list:
    if not os.path.exists(LIB_PATH):
        return []
    try:
        with open(LIB_PATH, "r", encoding="utf-8") as f:
            lista = json.load(f)
        agora = datetime.now().isoformat()
        # Filtra atividades expiradas
        ativas = [a for a in lista if not a.get("expira_em") or a["expira_em"] > agora]
        if len(ativas) != len(lista):
            salvar_liberadas(ativas)
        return ativas
    except Exception:
        return []
