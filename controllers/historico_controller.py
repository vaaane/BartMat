"""
controllers/historico_controller.py — Persistência em SQLite.

Tabelas:
  - resultados: pontuação por atividade/aluno
  - detalhes_questoes: revisão questão a questão de cada resultado
  - liberacoes: log de atividades liberadas pelo professor
  - conquistas: conquistas desbloqueadas pelos alunos
  - alertas: alertas de tentativas suspeitas
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import os
import sqlite3
import json
from datetime import datetime

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH   = os.path.join(BASE_DIR, "dados.db")
JSON_PATH = os.path.join(BASE_DIR, "dados.json")


def _conectar():
    return sqlite3.connect(DB_PATH)


def _inicializar():
    with _conectar() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS resultados (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                aluno            TEXT    NOT NULL,
                turma            TEXT    NOT NULL,
                atividade        TEXT    NOT NULL,
                pontuacao_bruta  INTEGER NOT NULL DEFAULT 0,
                pontuacao        INTEGER NOT NULL DEFAULT 0,
                tipo_atividade   TEXT    NOT NULL DEFAULT 'dia',
                fator_atraso     REAL    NOT NULL DEFAULT 1.0,
                acertos          INTEGER NOT NULL DEFAULT 0,
                erros            INTEGER NOT NULL DEFAULT 0,
                tempo            TEXT    NOT NULL DEFAULT '0s',
                data             TEXT    NOT NULL,
                atraso           INTEGER NOT NULL DEFAULT 0
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS detalhes_questoes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                resultado_id    INTEGER NOT NULL,
                numero          INTEGER NOT NULL,
                pergunta        TEXT    NOT NULL,
                resposta_aluno  TEXT    NOT NULL DEFAULT '—',
                resposta_correta TEXT   NOT NULL,
                tentativas      INTEGER NOT NULL DEFAULT 0,
                acertou         INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (resultado_id) REFERENCES resultados(id)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS liberacoes (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                atividade    TEXT    NOT NULL,
                turma        TEXT    NOT NULL,
                tipo         TEXT    NOT NULL,
                tempo_maximo INTEGER,
                liberado_em  TEXT    NOT NULL,
                expira_em    TEXT,
                cancelado_em TEXT
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS conquistas (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                aluno     TEXT NOT NULL,
                turma     TEXT NOT NULL,
                atividade TEXT NOT NULL,
                tipo      TEXT NOT NULL,
                descricao TEXT NOT NULL,
                data      TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS alertas (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                aluno     TEXT NOT NULL,
                turma     TEXT NOT NULL,
                atividade TEXT NOT NULL,
                motivo    TEXT NOT NULL,
                data      TEXT NOT NULL,
                visto     INTEGER NOT NULL DEFAULT 0
            )
        """)
        con.commit()

    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                registros = json.load(f)
            for r in registros:
                adicionar_resultado(r)
            os.rename(JSON_PATH, JSON_PATH + ".migrado")
        except Exception:
            pass


_inicializar()


# ---------------------------------------------------------------------------
#  API pública
# ---------------------------------------------------------------------------

def buscar_todos_resultados() -> list[dict]:
    with _conectar() as con:
        con.row_factory = sqlite3.Row
        cursor = con.execute("SELECT * FROM resultados ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]


def buscar_resultados_por_aluno(aluno: str) -> list[dict]:
    with _conectar() as con:
        con.row_factory = sqlite3.Row
        cursor = con.execute("SELECT * FROM resultados WHERE aluno = ? ORDER BY id", (aluno,))
        return [dict(row) for row in cursor.fetchall()]


def buscar_resultados_por_turma(turma: str) -> list[dict]:
    with _conectar() as con:
        con.row_factory = sqlite3.Row
        cursor = con.execute("SELECT * FROM resultados WHERE turma = ? ORDER BY id", (turma,))
        return [dict(row) for row in cursor.fetchall()]


def adicionar_resultado(novo: dict) -> int:
    """Insere resultado e retorna o id gerado."""
    with _conectar() as con:
        cur = con.execute("""
            INSERT INTO resultados
                (aluno, turma, atividade, pontuacao_bruta, pontuacao,
                 tipo_atividade, fator_atraso, acertos, erros, tempo, data, atraso)
            VALUES
                (:aluno, :turma, :atividade, :pontuacao_bruta, :pontuacao,
                 :tipo_atividade, :fator_atraso, :acertos, :erros, :tempo, :data, :atraso)
        """, {
            "aluno":           novo.get("aluno", ""),
            "turma":           novo.get("turma", ""),
            "atividade":       novo.get("atividade", ""),
            "pontuacao_bruta": novo.get("pontuacao_bruta", novo.get("pontuacao", 0)),
            "pontuacao":       novo.get("pontuacao", 0),
            "tipo_atividade":  novo.get("tipo_atividade", "dia"),
            "fator_atraso":    novo.get("fator_atraso", 1.0),
            "acertos":         novo.get("acertos", 0),
            "erros":           novo.get("erros", 0),
            "tempo":           novo.get("tempo", "0s"),
            "data":            novo.get("data", datetime.now().strftime("%d/%m/%Y %H:%M")),
            "atraso":          int(novo.get("atraso", False)),
        })
        con.commit()
        return cur.lastrowid


def salvar_detalhes_questoes(resultado_id: int, questoes: list[dict]) -> None:
    """Salva o detalhamento questão a questão de um resultado."""
    with _conectar() as con:
        for i, q in enumerate(questoes, 1):
            con.execute("""
                INSERT INTO detalhes_questoes
                    (resultado_id, numero, pergunta, resposta_aluno, resposta_correta, tentativas, acertou)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                resultado_id, i,
                q.get("pergunta", ""),
                q.get("resposta_aluno", "—"),
                q.get("resposta_correta", ""),
                q.get("tentativas", 0),
                int(q.get("acertou", False)),
            ))
        con.commit()


def buscar_detalhes_questoes(resultado_id: int) -> list[dict]:
    """Retorna detalhes das questões de um resultado específico."""
    with _conectar() as con:
        con.row_factory = sqlite3.Row
        cursor = con.execute(
            "SELECT * FROM detalhes_questoes WHERE resultado_id = ? ORDER BY numero",
            (resultado_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def contar_tentativas(aluno: str, atividade: str) -> int:
    """Conta quantas vezes o aluno fez esta atividade."""
    with _conectar() as con:
        cur = con.execute(
            "SELECT COUNT(*) FROM resultados WHERE aluno = ? AND atividade = ?",
            (aluno, atividade)
        )
        return cur.fetchone()[0]


def atualizar_resultado(resultado_id: int, dados: dict) -> None:
    """Atualiza os campos de score de um resultado existente."""
    with _conectar() as con:
        con.execute("""
            UPDATE resultados SET
                pontuacao_bruta=:pontuacao_bruta, pontuacao=:pontuacao,
                tipo_atividade=:tipo_atividade, fator_atraso=:fator_atraso,
                acertos=:acertos, erros=:erros, tempo=:tempo, data=:data, atraso=:atraso
            WHERE id=:id
        """, {
            "id": resultado_id,
            "pontuacao_bruta": dados.get("pontuacao_bruta", 0),
            "pontuacao":       dados.get("pontuacao", 0),
            "tipo_atividade":  dados.get("tipo_atividade", "dia"),
            "fator_atraso":    dados.get("fator_atraso", 1.0),
            "acertos":         dados.get("acertos", 0),
            "erros":           dados.get("erros", 0),
            "tempo":           dados.get("tempo", "0s"),
            "data":            dados.get("data", datetime.now().strftime("%d/%m/%Y %H:%M")),
            "atraso":          int(dados.get("atraso", False)),
        })
        con.commit()


def deletar_resultado(resultado_id: int) -> None:
    with _conectar() as con:
        con.execute("DELETE FROM detalhes_questoes WHERE resultado_id = ?", (resultado_id,))
        con.execute("DELETE FROM resultados WHERE id = ?", (resultado_id,))
        con.commit()


# ---------------------------------------------------------------------------
#  Liberações
# ---------------------------------------------------------------------------

def registrar_liberacao(lib: dict) -> int:
    with _conectar() as con:
        cur = con.execute("""
            INSERT INTO liberacoes (atividade, turma, tipo, tempo_maximo, liberado_em, expira_em)
            VALUES (:atividade, :turma, :tipo, :tempo_maximo, :liberado_em, :expira_em)
        """, {
            "atividade":    lib.get("atividade", ""),
            "turma":        lib.get("turma", ""),
            "tipo":         lib.get("tipo", "dia"),
            "tempo_maximo": lib.get("tempo_maximo"),
            "liberado_em":  lib.get("liberado_em", datetime.now().isoformat()),
            "expira_em":    lib.get("expira_em"),
        })
        con.commit()
        return cur.lastrowid


def cancelar_liberacao(lib_id: int, timestamp: str) -> None:
    with _conectar() as con:
        con.execute("UPDATE liberacoes SET cancelado_em = ? WHERE id = ?", (timestamp, lib_id))
        con.commit()


def buscar_liberacoes() -> list[dict]:
    with _conectar() as con:
        con.row_factory = sqlite3.Row
        cursor = con.execute("SELECT * FROM liberacoes ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]


# ---------------------------------------------------------------------------
#  Conquistas
# ---------------------------------------------------------------------------

def registrar_conquista(c: dict) -> None:
    with _conectar() as con:
        con.execute("""
            INSERT INTO conquistas (aluno, turma, atividade, tipo, descricao, data)
            VALUES (:aluno, :turma, :atividade, :tipo, :descricao, :data)
        """, {
            "aluno":     c.get("aluno", ""),
            "turma":     c.get("turma", ""),
            "atividade": c.get("atividade", ""),
            "tipo":      c.get("tipo", ""),
            "descricao": c.get("descricao", ""),
            "data":      c.get("data", datetime.now().strftime("%d/%m/%Y %H:%M")),
        })
        con.commit()


def buscar_conquistas(aluno: str | None = None) -> list[dict]:
    with _conectar() as con:
        con.row_factory = sqlite3.Row
        if aluno:
            cursor = con.execute(
                "SELECT * FROM conquistas WHERE aluno = ? ORDER BY id DESC", (aluno,))
        else:
            cursor = con.execute("SELECT * FROM conquistas ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]


def verificar_conquista_existente(aluno: str, tipo: str, atividade: str) -> bool:
    """Retorna True se o aluno já tem esta conquista nesta atividade."""
    with _conectar() as con:
        cur = con.execute(
            "SELECT COUNT(*) FROM conquistas WHERE aluno=? AND tipo=? AND atividade=?",
            (aluno, tipo, atividade))
        return cur.fetchone()[0] > 0


# ---------------------------------------------------------------------------
#  Alertas
# ---------------------------------------------------------------------------

def registrar_alerta(a: dict) -> None:
    with _conectar() as con:
        con.execute("""
            INSERT INTO alertas (aluno, turma, atividade, motivo, data)
            VALUES (:aluno, :turma, :atividade, :motivo, :data)
        """, {
            "aluno":     a.get("aluno", ""),
            "turma":     a.get("turma", ""),
            "atividade": a.get("atividade", ""),
            "motivo":    a.get("motivo", ""),
            "data":      a.get("data", datetime.now().strftime("%d/%m/%Y %H:%M")),
        })
        con.commit()


def buscar_alertas(apenas_nao_vistos: bool = False) -> list[dict]:
    with _conectar() as con:
        con.row_factory = sqlite3.Row
        if apenas_nao_vistos:
            cursor = con.execute(
                "SELECT * FROM alertas WHERE visto=0 ORDER BY id DESC")
        else:
            cursor = con.execute("SELECT * FROM alertas ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]


def marcar_alerta_visto(alerta_id: int) -> None:
    with _conectar() as con:
        con.execute("UPDATE alertas SET visto=1 WHERE id=?", (alerta_id,))
        con.commit()


def verificar_tentativas_suspeitas(aluno: str, atividade: str) -> bool:
    """Retorna True se o aluno fez 3+ tentativas desta atividade nos últimos 10 minutos."""
    from datetime import timedelta
    limite = (datetime.now() - timedelta(minutes=10)).strftime("%d/%m/%Y %H:%M")
    with _conectar() as con:
        cur = con.execute("""
            SELECT COUNT(*) FROM resultados
            WHERE aluno=? AND atividade=? AND data >= ?
        """, (aluno, atividade, limite))
        return cur.fetchone()[0] >= 3