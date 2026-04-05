"""blueprints/aluno.py — Rotas da área do aluno."""
import time, random
from datetime import datetime
from fractions import Fraction

from flask import (
    Blueprint, render_template, session, redirect,
    url_for, request, jsonify, flash,
)
from constants import LISTA_ATIVIDADES, FATOR_ATRASO, carregar_perguntas, _intercalar_por_dificuldade
from controllers.historico_controller import (
    buscar_todos_resultados, buscar_detalhes_questoes,
    adicionar_resultado, atualizar_resultado, salvar_detalhes_questoes,
    registrar_conquista, verificar_conquista_existente,
    registrar_alerta, verificar_tentativas_suspeitas,
    contar_tentativas,
)
from controllers.liberacoes_controller import carregar_liberadas

aluno_bp = Blueprint("aluno", __name__, url_prefix="/aluno")

BASES = {1: 10, 2: 20, 3: 30}
FATORES_TENTATIVA = [1.0, 0.75, 0.5, 0.25]
MAX_TENTATIVAS_ATIVIDADE = 2


def _melhor_pts_por_atividade(regs):
    """Retorna {ativ: max_pts} — apenas a melhor tentativa por atividade."""
    melhor = {}
    for r in regs:
        ativ = r["atividade"]
        melhor[ativ] = max(melhor.get(ativ, 0), r["pontuacao"])
    return melhor


def _require_aluno():
    if session.get("modo") != "aluno":
        return redirect(url_for("auth.login"))


def _respostas_equivalentes(a, c):
    a, c = a.strip(), c.strip()
    if a == c:
        return True
    try:
        return Fraction(a) == Fraction(c)
    except Exception:
        pass
    try:
        return abs(float(a) - float(c)) < 1e-9
    except Exception:
        return False


# ── Menu ─────────────────────────────────────────────────────

@aluno_bp.route("/")
def menu():
    redir = _require_aluno()
    if redir: return redir

    alunos = session.get("alunos", [])
    turma  = session.get("turma", "")

    liberadas          = carregar_liberadas()
    atividade_liberada = next((a for a in liberadas if a["turma"] == turma), None)

    todos = buscar_todos_resultados()
    historico_por_aluno = {}
    resumo_por_aluno    = {}

    for aluno in alunos:
        regs = [r for r in todos if r["aluno"] == aluno]
        historico_por_aluno[aluno] = list(reversed(regs[-4:])) if regs else []
        melhor       = _melhor_pts_por_atividade(regs)
        total_pts    = sum(melhor.values())
        total_ativ   = len(melhor)
        resumo_por_aluno[aluno] = {
            "total_pts":     total_pts,
            "total_ativ":    total_ativ,
            "media_pts":     round(total_pts / total_ativ) if total_ativ else 0,
            "total_acertos": sum(r.get("acertos", 0) for r in regs),
            "total_erros":   sum(r.get("erros",   0) for r in regs),
        }

    return render_template(
        "aluno/menu.html",
        active_page="inicio",
        alunos=alunos,
        turma=turma,
        atividade_liberada=atividade_liberada,
        historico_por_aluno=historico_por_aluno,
        resumo_por_aluno=resumo_por_aluno,
        atividades=LISTA_ATIVIDADES,
    )


# ── Atividades ───────────────────────────────────────────────

@aluno_bp.route("/atividades")
def atividades():
    redir = _require_aluno()
    if redir: return redir
    liberadas     = carregar_liberadas()
    turma         = session.get("turma", "")
    alunos        = session.get("alunos", [])
    ativ_liberada = next((a for a in liberadas if a["turma"] == turma), None)

    # Tentativas restantes por atividade (leva em conta toda a dupla)
    bloqueio_por_atividade = {}
    for ativ in LISTA_ATIVIDADES:
        n = ativ["nome"]
        tent = {al: contar_tentativas(al, n) for al in alunos}
        bloqueado_por = [al for al, t in tent.items() if t >= MAX_TENTATIVAS_ATIVIDADE]
        min_rest      = min((MAX_TENTATIVAS_ATIVIDADE - t for t in tent.values()), default=MAX_TENTATIVAS_ATIVIDADE)
        bloqueio_por_atividade[n] = {
            "bloqueado":    bool(bloqueado_por),
            "bloqueado_por": bloqueado_por,
            "min_restantes": max(0, min_rest),
        }

    return render_template(
        "aluno/atividades.html",
        active_page="atividades",
        atividades=LISTA_ATIVIDADES,
        ativ_liberada=ativ_liberada,
        bloqueio_por_atividade=bloqueio_por_atividade,
        max_tent=MAX_TENTATIVAS_ATIVIDADE,
        turma=turma,
        alunos=alunos,
    )


# ── Histórico ────────────────────────────────────────────────

@aluno_bp.route("/historico")
def historico():
    redir = _require_aluno()
    if redir: return redir

    alunos = session.get("alunos", [])
    turma  = session.get("turma", "")
    todos  = buscar_todos_resultados()

    historico_por_aluno = {}
    for aluno in alunos:
        regs = [r for r in todos if r["aluno"] == aluno]
        regs = sorted(regs, key=lambda r: r.get("id", 0), reverse=True)
        for r in regs:
            r["detalhes"] = buscar_detalhes_questoes(r["id"])
        historico_por_aluno[aluno] = regs

    return render_template(
        "aluno/historico.html",
        active_page="historico",
        alunos=alunos,
        turma=turma,
        historico_por_aluno=historico_por_aluno,
    )


# ── Ranking ──────────────────────────────────────────────────

@aluno_bp.route("/ranking")
def ranking():
    redir = _require_aluno()
    if redir: return redir

    alunos = session.get("alunos", [])
    turma  = session.get("turma", "")
    todos  = buscar_todos_resultados()
    tab    = request.args.get("tab", "geral")

    # Acumula: melhor pontuação por aluno×atividade; acertos somam tudo
    melhor_a = {}   # {aluno: {atividade: max_pts}}
    turma_a  = {}; ac_a = {}; at_a = {}; alunos_t = {}
    for r in todos:
        a, t, ativ = r["aluno"], r["turma"], r["atividade"]
        turma_a[a] = t
        ac_a[a]    = ac_a.get(a, 0) + r.get("acertos", 0)
        at_a.setdefault(a, set()).add(ativ)
        alunos_t.setdefault(t, set()).add(a)
        if a not in melhor_a:
            melhor_a[a] = {}
        melhor_a[a][ativ] = max(melhor_a[a].get(ativ, 0), r["pontuacao"])

    # Soma das melhores pontuações por atividade
    pts_a = {a: sum(v.values()) for a, v in melhor_a.items()}
    # Pontos por turma = soma dos pts_a dos alunos da turma
    pts_t = {}
    for a, pts in pts_a.items():
        t = turma_a.get(a, "")
        if t:
            pts_t[t] = pts_t.get(t, 0) + pts

    rank_list = [
        {
            "pos":      i,
            "aluno":    nome,
            "turma":    turma_a.get(nome, "—"),
            "pts":      pts,
            "acertos":  ac_a.get(nome, 0),
            "ativs":    len(at_a.get(nome, set())),
            "destaque": nome in alunos,
        }
        for i, (nome, pts) in enumerate(
            sorted(pts_a.items(), key=lambda x: x[1], reverse=True), 1)
    ]

    rank_turma = []
    for i, r in enumerate(
        [r for r in rank_list if r["turma"] == turma], 1
    ):
        rank_turma.append({**r, "pos": i})

    rank_turmas = [
        {
            "pos":      i,
            "turma":    t,
            "pts":      pts,
            "alunos":   len(alunos_t.get(t, set())),
            "media":    round(pts / len(alunos_t[t])) if alunos_t.get(t) else 0,
            "destaque": t == turma,
        }
        for i, (t, pts) in enumerate(
            sorted(pts_t.items(), key=lambda x: x[1], reverse=True), 1)
    ]

    posicoes = {r["aluno"]: r["pos"] for r in rank_list if r["aluno"] in alunos}

    return render_template(
        "aluno/ranking.html",
        active_page="ranking",
        tab=tab,
        rank_list=rank_list,
        rank_turma=rank_turma,
        rank_turmas=rank_turmas,
        alunos=alunos,
        turma=turma,
        posicoes=posicoes,
        total=len(rank_list),
        total_turmas=len(rank_turmas),
    )


# ── API de status ────────────────────────────────────────────

@aluno_bp.route("/api/liberada")
def api_liberada():
    if session.get("modo") != "aluno":
        return jsonify({"nome": None})
    turma = session.get("turma", "")
    liberadas = carregar_liberadas()
    lib = next((a for a in liberadas if a["turma"] == turma), None)
    return jsonify({"nome": lib["atividade"] if lib else None})


# ── Motor de atividade ───────────────────────────────────────

@aluno_bp.route("/jogar/<path:nome>")
def jogar(nome):
    redir = _require_aluno()
    if redir: return redir

    alunos = session.get("alunos", [])
    turma  = session.get("turma", "")

    # Verificar liberação
    liberadas = carregar_liberadas()
    lib = next((a for a in liberadas if a["atividade"] == nome and a["turma"] == turma), None)
    if not lib:
        flash("Esta atividade não está liberada para sua turma.", "error")
        return redirect(url_for("aluno.atividades"))

    # Verificar limite de tentativas ANTES de registrar
    for al in alunos:
        tent = contar_tentativas(al, nome)
        if tent >= MAX_TENTATIVAS_ATIVIDADE:
            outros = [x for x in alunos if x != al]
            if outros:
                msg = f"{al} já usou as {MAX_TENTATIVAS_ATIVIDADE} tentativas disponíveis para '{nome}'. A dupla não pode iniciar."
            else:
                msg = f"Você já usou as {MAX_TENTATIVAS_ATIVIDADE} tentativas disponíveis para '{nome}'."
            flash(msg, "error")
            return redirect(url_for("aluno.atividades"))

    tipo_atividade = lib["tipo"]
    tempo_maximo   = lib.get("tempo_maximo", 600)
    fator_atraso   = FATOR_ATRASO[tipo_atividade]
    perguntas      = carregar_perguntas(nome)

    # Pré-registrar resultado (já conta como tentativa)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    resultado_ids = {}
    for al in alunos:
        rid = adicionar_resultado({
            "aluno": al, "turma": turma, "atividade": nome,
            "pontuacao_bruta": 0, "pontuacao": 0,
            "tipo_atividade": tipo_atividade, "fator_atraso": fator_atraso,
            "acertos": 0, "erros": 0, "tempo": "0s", "data": agora,
            "atraso": tipo_atividade != "dia",
        })
        resultado_ids[al] = rid

    session["jogo"] = {
        "nome":          nome,
        "perguntas":     perguntas,
        "indice":        0,
        "pontuacao":     0,
        "acertos":       0,
        "erros":         0,
        "respondidas":   0,
        "tentativas":    0,
        "ajuda_usada":   False,
        "historico":     [],
        "tipo":          tipo_atividade,
        "tempo_maximo":  tempo_maximo,
        "fator_atraso":  fator_atraso,
        "resultado_ids": resultado_ids,
        "inicio_ts":     time.time(),
        "finalizado":    False,
        "alunos":        alunos,
        "turma":         turma,
        "pontuacao_final": 0,
        "pontuacao_bruta": 0,
        "tempo_segundos":  0,
        "novas_conquistas": [],
        "questao_num":     1,
        "encerrado_voluntariamente": False,
    }

    return redirect(url_for("aluno.jogar_view"))


@aluno_bp.route("/jogar")
def jogar_view():
    redir = _require_aluno()
    if redir: return redir

    jogo = session.get("jogo")
    if not jogo:
        return redirect(url_for("aluno.atividades"))
    if jogo.get("finalizado"):
        return redirect(url_for("aluno.jogar_resultado"))

    indice = jogo["indice"]
    perg   = jogo["perguntas"][indice]
    base   = BASES.get(perg["dificuldade"], 10)
    fat    = FATORES_TENTATIVA[min(jogo["tentativas"], 3)]
    fa     = 0.5 if jogo["ajuda_usada"] else 1.0
    vale   = max(1, int(base * fat * fa))
    niveis = {1: ("Fácil", "green"), 2: ("Média", "orange"), 3: ("Difícil", "red")}
    nivel, nivel_cor = niveis.get(perg["dificuldade"], ("Fácil", "green"))

    return render_template(
        "aluno/jogar.html",
        active_page="atividades",
        jogo=jogo,
        perg=perg,
        base=base,
        vale=vale,
        nivel=nivel,
        nivel_cor=nivel_cor,
        num=jogo.get("questao_num", 1),
        LABEL_TIPO={"dia": "do dia", "anterior": "anterior", "antiga": "antiga"},
    )


@aluno_bp.route("/jogar/responder", methods=["POST"])
def jogar_responder():
    if session.get("modo") != "aluno":
        return jsonify({"erro": "não autorizado"}), 403

    jogo = session.get("jogo")
    if not jogo or jogo.get("finalizado"):
        return jsonify({"erro": "sem jogo ativo"}), 400

    # Verificar tempo
    decorrido = time.time() - jogo["inicio_ts"]
    if decorrido >= jogo["tempo_maximo"]:
        _finalizar_jogo(jogo)
        session["jogo"] = jogo
        return jsonify({"tempo_esgotado": True})

    data     = request.get_json(silent=True) or {}
    resposta = data.get("resposta", "").strip()
    indice   = jogo["indice"]
    perg     = jogo["perguntas"][indice]
    base     = BASES.get(perg["dificuldade"], 10)
    fat      = FATORES_TENTATIVA[min(jogo["tentativas"], 3)]
    fa       = 0.5 if jogo["ajuda_usada"] else 1.0

    if _respostas_equivalentes(resposta, str(perg["resposta"])):
        pts = max(1, int(base * fat * fa))
        jogo["pontuacao"]   += pts
        jogo["acertos"]     += 1
        jogo["respondidas"] += 1
        jogo["tentativas"]  += 1
        jogo["historico"].append({
            "pergunta":         perg["pergunta"],
            "resposta_aluno":   resposta,
            "resposta_correta": str(perg["resposta"]),
            "tentativas":       jogo["tentativas"],
            "acertou":          True,
        })

        _avancar_questao(jogo, indice)
        session["jogo"] = jogo
        return jsonify({
            "acertou":   True,
            "pts":       pts,
            "pontuacao": jogo["pontuacao"],
            "msg":       f"Correto! +{pts} pontos",
            "fim":       False,
        })

    else:
        jogo["tentativas"] += 1
        if jogo["tentativas"] >= 4:
            jogo["erros"]       += 1
            jogo["respondidas"] += 1
            jogo["historico"].append({
                "pergunta":         perg["pergunta"],
                "resposta_aluno":   resposta,
                "resposta_correta": str(perg["resposta"]),
                "tentativas":       jogo["tentativas"],
                "acertou":          False,
            })

            _avancar_questao(jogo, indice)
            session["jogo"] = jogo
            return jsonify({
                "acertou":   False,
                "esgotou":   True,
                "correta":   str(perg["resposta"]),
                "pontuacao": jogo["pontuacao"],
                "msg":       f"Errou 4× — Resposta: {perg['resposta']}",
                "fim":       False,
            })
        else:
            fat_novo = FATORES_TENTATIVA[min(jogo["tentativas"], 3)]
            vale     = max(1, int(base * fat_novo * fa))
            session["jogo"] = jogo
            return jsonify({
                "acertou":   False,
                "esgotou":   False,
                "tentativas": jogo["tentativas"],
                "msg":       f"Errado ({jogo['tentativas']}/4) — tente novamente",
                "vale":      vale,
            })


@aluno_bp.route("/jogar/ajuda", methods=["POST"])
def jogar_ajuda():
    if session.get("modo") != "aluno":
        return jsonify({"erro": "não autorizado"}), 403

    jogo = session.get("jogo")
    if not jogo or jogo.get("finalizado"):
        return jsonify({"erro": "sem jogo ativo"}), 400
    if jogo["ajuda_usada"]:
        return jsonify({"erro": "ajuda já usada"}), 400

    jogo["ajuda_usada"] = True
    jogo["tentativas"]  = 0   # reset ao usar ajuda
    perg = jogo["perguntas"][jogo["indice"]]
    alternativas = perg.get("alternativas", [])
    session["jogo"] = jogo
    return jsonify({"alternativas": alternativas})


@aluno_bp.route("/jogar/encerrar", methods=["POST"])
def jogar_encerrar():
    if session.get("modo") != "aluno":
        return redirect(url_for("auth.login"))

    jogo = session.get("jogo")
    if jogo and not jogo.get("finalizado"):
        jogo["encerrado_voluntariamente"] = True
        _finalizar_jogo(jogo)
        session["jogo"] = jogo

    return redirect(url_for("aluno.jogar_resultado"))


@aluno_bp.route("/jogar/resultado")
def jogar_resultado():
    redir = _require_aluno()
    if redir: return redir

    jogo = session.get("jogo")
    if not jogo:
        return redirect(url_for("aluno.atividades"))

    LABEL_TIPO = {"dia": "do dia", "anterior": "anterior", "antiga": "antiga"}
    return render_template(
        "aluno/resultado.html",
        active_page="atividades",
        jogo=jogo,
        LABEL_TIPO=LABEL_TIPO,
    )


# ── Helpers privados ─────────────────────────────────────────

def _avancar_questao(jogo: dict, indice: int) -> None:
    """Avança para a próxima questão, ciclando o pool quando esgotado."""
    jogo["questao_num"] = jogo.get("questao_num", 1) + 1
    if indice >= len(jogo["perguntas"]) - 1:
        # Pool esgotado — reembaralha e recomeça
        jogo["perguntas"] = _intercalar_por_dificuldade(jogo["perguntas"])
        jogo["indice"] = 0
    else:
        jogo["indice"] += 1
    jogo["tentativas"]  = 0
    jogo["ajuda_usada"] = False

def _finalizar_jogo(jogo):
    """Salva resultado, conquistas e alertas. Modifica jogo in-place."""
    if jogo.get("finalizado"):
        return
    jogo["finalizado"] = True

    fim_ts  = time.time()
    tt      = round(fim_ts - jogo["inicio_ts"])
    pb      = jogo["pontuacao"]
    pf      = max(1, int(pb * jogo["fator_atraso"])) if pb > 0 else 0
    agora   = datetime.now().strftime("%d/%m/%Y %H:%M")
    nome    = jogo["nome"]
    turma   = jogo["turma"]
    alunos  = jogo["alunos"]

    jogo["tempo_segundos"]  = tt
    jogo["pontuacao_final"] = pf
    jogo["pontuacao_bruta"] = pb

    dados_finais = {
        "pontuacao_bruta":  pb,
        "pontuacao":        pf,
        "tipo_atividade":   jogo["tipo"],
        "fator_atraso":     jogo["fator_atraso"],
        "acertos":          jogo["acertos"],
        "erros":            jogo["erros"],
        "tempo":            f"{tt}s",
        "data":             agora,
        "atraso":           jogo["tipo"] != "dia",
    }

    for al in alunos:
        rid = jogo["resultado_ids"].get(al)
        if rid:
            atualizar_resultado(rid, dados_finais)
        else:
            rid = adicionar_resultado({"aluno": al, "turma": turma, "atividade": nome, **dados_finais})
            jogo["resultado_ids"][al] = rid
        salvar_detalhes_questoes(rid, jogo["historico"])

    # Conquistas e alertas
    novas_conquistas = []
    todos = buscar_todos_resultados()

    for al in alunos:
        hist_al   = [r for r in todos if r["aluno"] == al]
        hist_ativ = [r for r in hist_al if r["atividade"] == nome]
        rid_atual = jogo["resultado_ids"].get(al)

        def _conceder(al_=al, tipo_=None, desc_=None):
            if not verificar_conquista_existente(al_, tipo_, nome):
                registrar_conquista({"aluno": al_, "turma": turma,
                    "atividade": nome, "tipo": tipo_,
                    "descricao": desc_, "data": agora})
                novas_conquistas.append(desc_)

        # Completo = tempo esgotou naturalmente (não encerramento manual)
        jogo_completo = not jogo.get("encerrado_voluntariamente", False)

        if jogo_completo and jogo["erros"] == 0 and jogo["respondidas"] > 0:
            _conceder(tipo_="sem_erros", desc_="Sem erros! ✨")

        todas_1a = (jogo_completo
                    and jogo["respondidas"] > 0
                    and jogo["erros"] == 0
                    and all(h["tentativas"] == 1 for h in jogo["historico"]))
        if todas_1a:
            _conceder(tipo_="nota_maxima", desc_="Nota máxima! 🏆")

        # Recorde de questões respondidas (independe de como encerrou)
        max_resp_prev = max(
            (r.get("acertos", 0) + r.get("erros", 0)
             for r in hist_ativ if r.get("id") != rid_atual),
            default=0
        )
        if jogo["respondidas"] > max_resp_prev and jogo["respondidas"] > 0:
            _conceder(tipo_="recorde_questoes", desc_="Recorde de questões! 📊")

        if not hist_al:
            _conceder(tipo_="primeira_atividade", desc_="Primeira atividade! 🎉")
        else:
            prev = [r["pontuacao"] for r in hist_ativ if r.get("id") != rid_atual]
            if prev and pf > max(prev):
                _conceder(tipo_="melhorou_nota", desc_="Melhorou a nota! 📈")
            max_geral = max((r["pontuacao"] for r in hist_al), default=0)
            if pf > max_geral:
                _conceder(tipo_="superou_recorde_pessoal", desc_="Novo recorde pessoal! 🌟")

        if verificar_tentativas_suspeitas(al, nome):
            registrar_alerta({"aluno": al, "turma": turma, "atividade": nome,
                "motivo": "3+ tentativas em 10 minutos", "data": agora})

    jogo["novas_conquistas"] = novas_conquistas
