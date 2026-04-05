"""blueprints/professor.py — Rotas da área do professor."""
import csv, io
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, session, redirect,
    url_for, request, Response, flash,
)
from constants import ALUNOS_POR_TURMA, LISTA_ATIVIDADES, FATOR_ATRASO
from controllers.historico_controller import (
    buscar_todos_resultados, buscar_resultados_por_turma,
    buscar_detalhes_questoes, buscar_alertas, marcar_alerta_visto,
    registrar_liberacao, cancelar_liberacao, buscar_liberacoes,
    buscar_conquistas,
)
from controllers.liberacoes_controller import carregar_liberadas, salvar_liberadas
from controllers.config_controller import carregar_config, salvar_config

professor_bp = Blueprint("professor", __name__, url_prefix="/professor")

TURMAS      = list(ALUNOS_POR_TURMA.keys())
LABEL_TIPO  = {"dia": "do dia", "anterior": "anterior", "antiga": "antiga"}


def _require_professor():
    if session.get("modo") != "professor":
        return redirect(url_for("auth.login"))


# ── Dashboard ────────────────────────────────────────────────

@professor_bp.route("/")
def dashboard():
    redir = _require_professor()
    if redir: return redir

    todos     = buscar_todos_resultados()
    liberadas = carregar_liberadas()
    alertas   = buscar_alertas(apenas_nao_vistos=True)

    total_alunos  = sum(len(v) for v in ALUNOS_POR_TURMA.values())
    total_turmas  = len(ALUNOS_POR_TURMA)
    total_result  = len(todos)
    total_alertas = len(alertas)

    melhor_dash = {}
    for r in todos:
        a, ativ = r["aluno"], r["atividade"]
        if a not in melhor_dash:
            melhor_dash[a] = {}
        melhor_dash[a][ativ] = max(melhor_dash[a].get(ativ, 0), r["pontuacao"])
    pts_por_aluno = {a: sum(v.values()) for a, v in melhor_dash.items()}
    top5 = sorted(pts_por_aluno.items(), key=lambda x: x[1], reverse=True)[:5]
    ultimos = sorted(todos, key=lambda r: r.get("id", 0), reverse=True)[:8]

    return render_template(
        "professor/dashboard.html",
        active_page="dashboard",
        total_alunos=total_alunos, total_turmas=total_turmas,
        total_result=total_result, total_alertas=total_alertas,
        liberadas=liberadas, alertas=alertas[:5],
        ultimos=ultimos, top5=top5,
        atividades=LISTA_ATIVIDADES,
    )


# ── Atividades ───────────────────────────────────────────────

@professor_bp.route("/atividades")
def atividades():
    redir = _require_professor()
    if redir: return redir
    return render_template(
        "professor/atividades.html",
        active_page="atividades",
        atividades=LISTA_ATIVIDADES,
        turmas=TURMAS,
        label_tipo=LABEL_TIPO,
        liberadas=carregar_liberadas(),
        historico=buscar_liberacoes()[:20],
        now_iso=datetime.now().isoformat(),
    )


@professor_bp.route("/liberar", methods=["POST"])
def liberar():
    redir = _require_professor()
    if redir: return redir

    atividade    = request.form.get("atividade", "").strip()
    turma        = request.form.get("turma", "").strip()
    tipo         = request.form.get("tipo", "dia").strip()
    tempo_minutos = int(request.form.get("tempo_maximo", 10))
    tempo_maximo  = tempo_minutos * 60

    if not atividade or not turma:
        flash("Selecione a atividade e a turma.", "error")
        return redirect(url_for("professor.atividades"))

    agora     = datetime.now()
    expira_em = (agora + timedelta(seconds=tempo_maximo + 300)).isoformat()

    # Remove liberação anterior da mesma atividade+turma, se existir
    lista = carregar_liberadas()
    lista = [a for a in lista if not (a["atividade"] == atividade and a["turma"] == turma)]

    nova = {
        "atividade":    atividade,
        "turma":        turma,
        "tipo":         tipo,
        "tempo_maximo": tempo_maximo,
        "liberado_em":  agora.isoformat(),
        "expira_em":    expira_em,
    }
    lib_id = registrar_liberacao(nova)
    nova["_lib_id"] = lib_id
    lista.append(nova)
    salvar_liberadas(lista)

    return redirect(url_for("professor.atividades"))


@professor_bp.route("/cancelar/<int:lib_id>", methods=["POST"])
def cancelar(lib_id):
    redir = _require_professor()
    if redir: return redir

    lista = carregar_liberadas()
    lista = [a for a in lista if a.get("_lib_id") != lib_id]
    salvar_liberadas(lista)
    cancelar_liberacao(lib_id, datetime.now().isoformat())

    flash("Atividade cancelada.", "info")
    return redirect(url_for("professor.atividades"))


# ── Ranking ──────────────────────────────────────────────────

@professor_bp.route("/ranking")
def ranking():
    redir = _require_professor()
    if redir: return redir

    turma_sel = request.args.get("turma", "Todas")
    todos     = buscar_todos_resultados()
    dados     = todos if turma_sel == "Todas" else [r for r in todos if r["turma"] == turma_sel]

    melhor_rank = {}   # {aluno: {atividade: max_pts}}
    turma_a = {}; ac_a = {}; err_a = {}; at_a = {}
    for r in dados:
        a, ativ = r["aluno"], r["atividade"]
        turma_a[a] = r["turma"]
        ac_a[a]    = ac_a.get(a, 0)  + r.get("acertos", 0)
        err_a[a]   = err_a.get(a, 0) + r.get("erros",   0)
        at_a.setdefault(a, set()).add(ativ)
        if a not in melhor_rank:
            melhor_rank[a] = {}
        melhor_rank[a][ativ] = max(melhor_rank[a].get(ativ, 0), r["pontuacao"])

    pts_a = {a: sum(v.values()) for a, v in melhor_rank.items()}

    rank = sorted(pts_a.items(), key=lambda x: x[1], reverse=True)
    ranking_list = [
        {
            "pos":     i,
            "aluno":   nome,
            "turma":   turma_a.get(nome, "—"),
            "pts":     pts,
            "acertos": ac_a.get(nome, 0),
            "erros":   err_a.get(nome, 0),
            "ativs":   len(at_a.get(nome, set())),
            "aproveit": round(ac_a.get(nome,0)/(ac_a.get(nome,0)+err_a.get(nome,0))*100)
                         if ac_a.get(nome,0)+err_a.get(nome,0) > 0 else 0,
        }
        for i, (nome, pts) in enumerate(rank, 1)
    ]

    return render_template(
        "professor/ranking.html",
        active_page="ranking",
        turmas=["Todas"] + TURMAS,
        turma_sel=turma_sel,
        ranking_list=ranking_list,
    )


# ── Acompanhamento ───────────────────────────────────────────

@professor_bp.route("/acompanhamento")
def acompanhamento():
    redir = _require_professor()
    if redir: return redir

    turma_sel = request.args.get("turma", "")
    aluno_sel = request.args.get("aluno", "")
    todos     = buscar_todos_resultados()

    alunos_turma = sorted(ALUNOS_POR_TURMA.get(turma_sel, []))

    # Resultados do aluno selecionado
    resultados_aluno = []
    if aluno_sel and turma_sel:
        for r in todos:
            if r["aluno"] == aluno_sel and r["turma"] == turma_sel:
                detalhes = buscar_detalhes_questoes(r["id"])
                resultados_aluno.append({**r, "detalhes": detalhes})

    # Atividades que o aluno selecionado ainda não fez
    atividades_nao_feitas = []
    if aluno_sel:
        feitas = {r["atividade"] for r in todos if r["aluno"] == aluno_sel}
        atividades_nao_feitas = [a["nome"] for a in LISTA_ATIVIDADES if a["nome"] not in feitas]

    # Por atividade: quais alunos da turma ainda não fizeram
    pendentes_por_atividade = {}
    if turma_sel:
        alunos_da_turma = set(ALUNOS_POR_TURMA.get(turma_sel, []))
        for ativ in LISTA_ATIVIDADES:
            fizeram = {r["aluno"] for r in todos
                       if r["atividade"] == ativ["nome"] and r["turma"] == turma_sel}
            faltam = sorted(alunos_da_turma - fizeram)
            pendentes_por_atividade[ativ["nome"]] = faltam

    return render_template(
        "professor/acompanhamento.html",
        active_page="acompanhamento",
        turmas=TURMAS,
        turma_sel=turma_sel,
        aluno_sel=aluno_sel,
        alunos_turma=alunos_turma,
        resultados_aluno=resultados_aluno,
        atividades_nao_feitas=atividades_nao_feitas,
        pendentes_por_atividade=pendentes_por_atividade,
    )


# ── Relatório ────────────────────────────────────────────────

@professor_bp.route("/relatorio")
def relatorio():
    redir = _require_professor()
    if redir: return redir

    turma_sel = request.args.get("turma", TURMAS[0])
    dados     = buscar_resultados_por_turma(turma_sel)

    # Resumo por aluno — pontuação = soma da melhor nota por atividade
    melhor = {}   # {aluno: {atividade: max_pts}}
    acertos_a = {}; erros_a = {}; tempo_a = {}; ativs_feitas = {}

    for r in dados:
        a, ativ = r["aluno"], r["atividade"]
        if a not in melhor:
            melhor[a] = {}
        melhor[a][ativ] = max(melhor[a].get(ativ, 0), r["pontuacao"])
        acertos_a[a]  = acertos_a.get(a, 0)  + r.get("acertos", 0)
        erros_a[a]    = erros_a.get(a, 0)    + r.get("erros",   0)
        ativs_feitas.setdefault(a, set()).add(ativ)
        try:
            tempo_a[a] = tempo_a.get(a, 0) + int(r.get("tempo","0s").replace("s",""))
        except Exception:
            pass

    tabela = []
    for aluno in sorted(ALUNOS_POR_TURMA.get(turma_sel, [])):
        if aluno in melhor:
            pts      = sum(melhor[aluno].values())
            n_ativs  = len(ativs_feitas.get(aluno, set()))
            ac       = acertos_a.get(aluno, 0)
            er       = erros_a.get(aluno, 0)
            total_r  = ac + er
            tabela.append({
                "aluno":    aluno,
                "pts":      pts,
                "ativs":    n_ativs,
                "media":    round(pts / n_ativs) if n_ativs else 0,
                "acertos":  ac,
                "erros":    er,
                "aproveit": round(ac / total_r * 100) if total_r else 0,
            })
        else:
            tabela.append({
                "aluno": aluno, "pts": 0, "ativs": 0,
                "media": 0, "acertos": 0, "erros": 0, "aproveit": 0,
            })

    tabela.sort(key=lambda x: x["pts"], reverse=True)

    return render_template(
        "professor/relatorio.html",
        active_page="relatorio",
        turmas=TURMAS, turma_sel=turma_sel,
        tabela=tabela,
    )


@professor_bp.route("/relatorio/csv")
def relatorio_csv():
    redir = _require_professor()
    if redir: return redir

    turma_sel = request.args.get("turma", TURMAS[0])
    dados     = buscar_resultados_por_turma(turma_sel)

    buf = io.StringIO()
    w   = csv.writer(buf)
    w.writerow(["aluno","turma","atividade","pontuacao_bruta","pontuacao",
                "tipo","acertos","erros","tempo","data"])
    for r in dados:
        w.writerow([r["aluno"], r["turma"], r["atividade"],
                    r["pontuacao_bruta"], r["pontuacao"], r["tipo_atividade"],
                    r.get("acertos",0), r.get("erros",0), r.get("tempo",""),
                    r.get("data","")])

    output = "\ufeff" + buf.getvalue()   # BOM para Excel
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition":
                 f"attachment; filename=relatorio_turma{turma_sel}_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


# ── Alertas ──────────────────────────────────────────────────

@professor_bp.route("/historico")
def historico():
    redir = _require_professor()
    if redir: return redir

    turma_sel  = request.args.get("turma", "Todas")
    atividade_sel = request.args.get("atividade", "Todas")
    todos      = buscar_todos_resultados()

    dados = todos
    if turma_sel != "Todas":
        dados = [r for r in dados if r["turma"] == turma_sel]
    if atividade_sel != "Todas":
        dados = [r for r in dados if r["atividade"] == atividade_sel]

    dados = sorted(dados, key=lambda r: r.get("id", 0), reverse=True)

    conquistas = buscar_conquistas()
    if turma_sel != "Todas":
        conquistas = [c for c in conquistas if c["turma"] == turma_sel]

    atividades_nomes = ["Todas"] + sorted({r["atividade"] for r in todos})

    return render_template(
        "professor/historico.html",
        active_page="historico",
        turmas=["Todas"] + TURMAS,
        turma_sel=turma_sel,
        atividades_nomes=atividades_nomes,
        atividade_sel=atividade_sel,
        dados=dados,
        conquistas=conquistas[:30],
    )


@professor_bp.route("/config", methods=["GET", "POST"])
def config():
    redir = _require_professor()
    if redir: return redir

    if request.method == "POST":
        atual    = request.form.get("senha_atual", "")
        nova     = request.form.get("nova_senha", "").strip()
        confirma = request.form.get("confirmar", "").strip()

        cfg = carregar_config()
        if atual != cfg.get("senha_professor", "123"):
            flash("Senha atual incorreta.", "error")
        elif not nova:
            flash("A nova senha não pode ser vazia.", "error")
        elif nova != confirma:
            flash("As senhas não coincidem.", "error")
        else:
            cfg["senha_professor"] = nova
            salvar_config(cfg)
            flash("✅ Senha alterada com sucesso!", "success")

        return redirect(url_for("professor.config"))

    return render_template("professor/config.html", active_page="config")


@professor_bp.route("/alertas/visto/<int:alerta_id>", methods=["POST"])
def marcar_visto(alerta_id):
    redir = _require_professor()
    if redir: return redir
    marcar_alerta_visto(alerta_id)
    return redirect(url_for("professor.dashboard"))
