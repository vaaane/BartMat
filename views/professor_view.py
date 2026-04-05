"""
views/professor_view.py — Menu principal do professor + dashboard.

Sub-módulos:
  professor_helpers.py    — helpers visuais compartilhados
  professor_atividades.py — atividades, detalhe, liberar, testar, histórico/ranking por atividade
  professor_telas.py      — ranking geral, acompanhamento, relatório turma, histórico geral
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import flet as ft
import state
from constants import LABEL_TIPO, LISTA_ATIVIDADES, ALUNOS_POR_TURMA
from controllers.historico_controller import (
    buscar_todos_resultados, cancelar_liberacao, buscar_alertas, marcar_alerta_visto,
)
from controllers.liberacoes_controller import salvar_liberadas
from controllers.config_controller import salvar_config
from views.professor_helpers import (
    BLUE, ORANGE_BG, WHITE, GREEN, RED, GOLD, IMG_W, IMG_H,
    TURMAS, MEDALS, CINZA_W, CINZA_H,
    btn_menu, stat_card, painel_nav_prof, montar_layout,
)
from views.professor_atividades import tela_atividades
from views.professor_telas import tela_ranking, tela_acompanhamento, tela_relatorio_turma, tela_historico_geral


# ============================================================
#  DASHBOARD
# ============================================================

def _painel_dashboard(scale, page, navegar, on_config=None):
    dados = buscar_todos_resultados()
    total_res = len(dados)
    alunos_u = len(set(r["aluno"] for r in dados))
    turmas_at = len(set(r["turma"] for r in dados))
    media_pts = round(sum(r["pontuacao"] for r in dados) / total_res) if total_res else 0

    pts_al = {}; turma_de = {}
    for r in dados:
        pts_al[r["aluno"]] = pts_al.get(r["aluno"], 0) + r["pontuacao"]
        turma_de[r["aluno"]] = r["turma"]
    top3 = sorted(pts_al.items(), key=lambda x: x[1], reverse=True)[:3] if pts_al else []

    por_ativ = {}; turmas_por_ativ = {}
    for r in dados:
        a = r["atividade"]
        if a not in por_ativ:
            por_ativ[a] = {"alunos": set(), "pts": 0, "acertos": 0, "erros": 0, "total": 0}
            turmas_por_ativ[a] = set()
        por_ativ[a]["alunos"].add(r["aluno"]); por_ativ[a]["total"] += 1
        por_ativ[a]["pts"] += r["pontuacao"]; por_ativ[a]["acertos"] += r["acertos"]
        por_ativ[a]["erros"] += r["erros"]; turmas_por_ativ[a].add(r["turma"])

    por_turma = {}
    for r in dados:
        if r["turma"] not in por_turma:
            por_turma[r["turma"]] = {"pts": 0, "n": 0, "alunos": set(), "atividades": set()}
        por_turma[r["turma"]]["pts"] += r["pontuacao"]; por_turma[r["turma"]]["n"] += 1
        por_turma[r["turma"]]["alunos"].add(r["aluno"]); por_turma[r["turma"]]["atividades"].add(r["atividade"])

    stats_cards = ft.Row(spacing=10*scale, alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
        stat_card("Resultados", str(total_res), BLUE, scale),
        stat_card("Alunos", str(alunos_u), GREEN, scale),
        stat_card("Turmas", str(turmas_at), ORANGE_BG, scale),
        stat_card("Média pts", str(media_pts), GOLD, scale)])

    PC = {1: GOLD, 2: "#C0C0C0", 3: "#CD7F32"}
    t3c = []
    for i, (nome, pts) in enumerate(top3, 1):
        cor = PC.get(i, GOLD)
        t3c.append(ft.Row(spacing=6*scale, controls=[
            ft.Text(MEDALS.get(i, ""), size=13*scale),
            ft.Text(nome, color=cor, size=11*scale, weight="bold"),
            ft.Text(f"Turma {turma_de.get(nome, '—')}", color="#77FFFFFF", size=9*scale),
            ft.Container(expand=True),
            ft.Text(f"{pts} pts", color=cor, size=11*scale, weight="bold")]))
    if not t3c: t3c.append(ft.Text("—", color="#66FFFFFF", size=10*scale))

    melhor_card = ft.Container(
        border_radius=10*scale, bgcolor="#22FFD700", border=ft.border.all(1.5, GOLD),
        padding=ft.padding.symmetric(horizontal=12*scale, vertical=8*scale),
        content=ft.Column(spacing=4*scale, controls=[
            ft.Row(spacing=6*scale, controls=[ft.Text("⭐", size=14*scale),
                ft.Text("Top 3 Alunos", color=GOLD, size=11*scale, weight="bold")]),
            *t3c]))

    # Resumo por atividade
    ativ_linhas = []
    for na in [a["nome"] for a in LISTA_ATIVIDADES]:
        info = por_ativ.get(na, {"alunos":set(),"pts":0,"acertos":0,"erros":0,"total":0})
        n_al = len(info["alunos"]); td = turmas_por_ativ.get(na, set())
        te = sum(len(ALUNOS_POR_TURMA.get(t,[])) for t in td)
        ma = round(info["pts"]/info["total"]) if info["total"] else 0
        tl = ", ".join(f"T{t}" for t in sorted(td)) if td else "Nenhuma"
        nt = len(td); tt = len(TURMAS)
        ativ_linhas.append(ft.Container(border_radius=8*scale, bgcolor="#0AFFFFFF",
            padding=ft.padding.symmetric(horizontal=10*scale, vertical=6*scale),
            content=ft.Column(spacing=3*scale, controls=[
                ft.Text(na, color=WHITE, size=11*scale, weight="bold"),
                ft.Row(spacing=6*scale, controls=[
                    ft.Text(f"👥 {n_al}/{te}" if te else f"👥 {n_al}", color="#AAFFFFFF", size=9*scale),
                    ft.Text(f"Média: {ma} pts", color=GOLD, size=9*scale, weight="bold"),
                    ft.Text(f"✅{info['acertos']}", color=GREEN, size=9*scale),
                    ft.Text(f"❌{info['erros']}", color=RED, size=9*scale)]),
                ft.Row(spacing=4*scale, controls=[
                    ft.Icon(ft.Icons.SCHOOL, color="#88FFFFFF", size=9*scale),
                    ft.Text(f"Turmas: {tl}  •  {nt}/{tt} atividades realizadas", color="#88FFFFFF", size=8*scale)])])))

    # Ranking turmas
    turma_linhas = []
    rank_t = sorted(por_turma.items(), key=lambda x: x[1]["pts"], reverse=True)
    for i, (t, info) in enumerate(rank_t, 1):
        af = len(info.get("atividades", set()))
        turma_linhas.append(ft.Container(border_radius=8*scale, bgcolor="#0AFFFFFF",
            margin=ft.margin.only(right=8*scale, top=4*scale),
            padding=ft.padding.symmetric(horizontal=10*scale, vertical=8*scale),
            content=ft.Row(spacing=6*scale, controls=[
                ft.Text(MEDALS.get(i, f"{i}º"), size=13*scale),
                ft.Column(spacing=1*scale, controls=[
                    ft.Text(f"Turma {t}", color=WHITE, size=11*scale, weight="bold"),
                    ft.Text(f"{af}/{len(LISTA_ATIVIDADES)} atividades realizadas", color="#88FFFFFF", size=8*scale)]),
                ft.Container(expand=True),
                ft.Text(f"{info['pts']} pts", color=GOLD, size=10*scale, weight="bold")])))

    # Atividades liberadas
    lib_c = []
    ativas = list(state.atividades_liberadas)
    if ativas:
        for a in ativas:
            tl2 = LABEL_TIPO[a["tipo"]]; tm = a.get("tempo_maximo",600)//60
            def cancel(ev, lib=a):
                from datetime import datetime
                state.atividades_liberadas.remove(lib)
                salvar_liberadas(state.atividades_liberadas)
                if lib.get("_lib_id"): cancelar_liberacao(lib["_lib_id"], datetime.now().isoformat())
                menu(page, navegar)
            lib_c.append(ft.Container(border_radius=8*scale, bgcolor="#1A4CAF50", border=ft.border.all(1, GREEN),
                padding=ft.padding.symmetric(horizontal=10*scale, vertical=6*scale),
                content=ft.Column(spacing=4*scale, controls=[
                    ft.Row(spacing=6*scale, controls=[ft.Icon(ft.Icons.PLAY_CIRCLE, color=GREEN, size=14*scale),
                        ft.Text(f"{a['atividade']}", color=WHITE, size=10*scale, weight="bold")]),
                    ft.Row(spacing=6*scale, controls=[
                        ft.Text(f"Turma {a['turma']}  •  {tl2}  •  {tm}min", color="#AAFFFFFF", size=9*scale),
                        ft.Container(expand=True),
                        ft.Container(border_radius=6*scale, bgcolor="#33FF5252",
                            padding=ft.padding.symmetric(horizontal=6*scale, vertical=2*scale),
                            on_click=cancel, ink=True,
                            content=ft.Text("Cancelar", color=RED, size=9*scale, weight="bold"))])])))
    else:
        lib_c.append(ft.Text("Nenhuma atividade liberada.", color="#66FFFFFF", size=11*scale))

    # Atividades por turma — colunas
    nomes_a = [a["nome"] for a in LISTA_ATIVIDADES]
    tcols = []
    for t in TURMAS:
        af2 = set(r["atividade"] for r in dados if r["turma"]==t)
        chips = []
        for na in nomes_a:
            f = na in af2
            chips.append(ft.Container(border_radius=4*scale, bgcolor="#1A4CAF50" if f else "#0AFFFFFF",
                padding=ft.padding.symmetric(horizontal=4*scale, vertical=2*scale),
                content=ft.Text(na.split(" - ")[1] if " - " in na else na, color=GREEN if f else "#55FFFFFF", size=7*scale)))
        tcols.append(ft.Container(expand=True, border_radius=6*scale, bgcolor="#06FFFFFF",
            padding=ft.padding.symmetric(horizontal=6*scale, vertical=5*scale),
            content=ft.Column(spacing=3*scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Text(f"T{t}", color=WHITE, size=10*scale, weight="bold", text_align="center"), *chips])))

    gear = ft.Container(
        width=22*scale, height=22*scale, border_radius=11*scale,
        bgcolor="#22FFFFFF", on_click=on_config, ink=True,
        alignment=ft.Alignment(0,0),
        content=ft.Icon(ft.Icons.SETTINGS, color="#88FFFFFF", size=13*scale),
    ) if on_config else ft.Container()

    col_esq = ft.Container(expand=3, content=ft.Column(spacing=10*scale, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Row(spacing=8*scale, controls=[ft.Icon(ft.Icons.DASHBOARD, color=BLUE, size=18*scale),
            ft.Text("Dashboard", color=WHITE, size=15*scale, weight="bold"),
            ft.Container(expand=True), gear]),
        stats_cards, melhor_card,
        ft.Divider(color="#22FFFFFF", thickness=1),
        ft.Row(spacing=8*scale, controls=[ft.Icon(ft.Icons.MENU_BOOK, color=BLUE, size=16*scale),
            ft.Text("Resumo por Atividade", color=WHITE, size=13*scale, weight="bold")]),
        *ativ_linhas]))

    # Alertas de tentativas suspeitas
    alertas_db = buscar_alertas(apenas_nao_vistos=True)
    alerta_linhas = []
    for al in alertas_db:
        def _ver(ev, aid=al["id"]): marcar_alerta_visto(aid); menu(page, navegar)
        alerta_linhas.append(ft.Container(border_radius=8*scale, bgcolor="#1AFF5252",
            border=ft.border.all(1, RED), padding=ft.padding.all(8*scale),
            content=ft.Row(spacing=6*scale, controls=[
                ft.Icon(ft.Icons.WARNING, color=RED, size=14*scale),
                ft.Column(spacing=1, expand=True, controls=[
                    ft.Text(f"{al['aluno']} — {al['atividade']}", color=WHITE, size=10*scale, weight="bold"),
                    ft.Text(al["motivo"], color="#AAFFFFFF", size=9*scale),
                    ft.Text(al["data"], color="#66FFFFFF", size=8*scale),
                ]),
                ft.Container(border_radius=6*scale, bgcolor="#33FFFFFF", on_click=_ver, ink=True,
                    padding=ft.padding.symmetric(horizontal=6*scale, vertical=2*scale),
                    content=ft.Text("✓ OK", color=WHITE, size=9*scale, weight="bold")),
            ])))
    if not alerta_linhas:
        alerta_linhas.append(ft.Text("Nenhum alerta.", color="#66FFFFFF", size=10*scale))

    col_dir = ft.Container(expand=2, content=ft.Column(spacing=10*scale, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Row(spacing=8*scale, controls=[ft.Icon(ft.Icons.BOLT, color=GREEN, size=16*scale),
            ft.Text("Atividades Ativas", color=WHITE, size=13*scale, weight="bold")]),
        *lib_c,
        ft.Divider(color="#22FFFFFF", thickness=1),
        ft.Row(spacing=8*scale, controls=[ft.Icon(ft.Icons.HISTORY, color=BLUE, size=16*scale),
            ft.Text("Atividades por Turma", color=WHITE, size=13*scale, weight="bold")]),
        ft.Row(spacing=4*scale, controls=tcols),
        ft.Divider(color="#22FFFFFF", thickness=1),
        ft.Row(spacing=8*scale, controls=[ft.Icon(ft.Icons.SCHOOL, color=ORANGE_BG, size=16*scale),
            ft.Text("Ranking das Turmas", color=WHITE, size=13*scale, weight="bold")]),
        *turma_linhas,
        ft.Divider(color="#22FFFFFF", thickness=1),
        ft.Row(spacing=8*scale, controls=[ft.Icon(ft.Icons.WARNING_AMBER, color=RED, size=16*scale),
            ft.Text("Alertas", color=RED, size=13*scale, weight="bold")]),
        *alerta_linhas]))

    return ft.Container(width=CINZA_W*scale, height=CINZA_H*scale,
        border_radius=20*scale, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        padding=ft.padding.symmetric(horizontal=16*scale, vertical=12*scale),
        content=ft.Row(spacing=14*scale, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
            col_esq, ft.Container(width=1, height=(CINZA_H-40)*scale, bgcolor="#15FFFFFF"), col_dir]))


# ============================================================
#  MENU PRINCIPAL
# ============================================================

def menu(page: ft.Page, navegar):
    page.controls.clear(); page.padding = 0; page.bgcolor = "white"

    def build():
        page.controls.clear()
        W = page.width or IMG_W; H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W*scale; img_h = IMG_H*scale

        def _inicio(e): menu(page, navegar)
        def _ativ(e): tela_atividades(page, navegar, menu)
        def _rank(e): tela_ranking(page, navegar, menu)
        def _acomp(e): tela_acompanhamento(page, navegar, menu)
        def _rel(e): tela_relatorio_turma(page, navegar, menu)
        def _hist(e): tela_historico_geral(page, navegar, menu)
        def _sair(e): navegar["login"]()

        def _config(e):
            f_atual = ft.TextField(hint_text="Senha atual", password=True, can_reveal_password=True,
                border_radius=12, border_color="#CCCCCC", bgcolor="white")
            f_nova  = ft.TextField(hint_text="Nova senha",  password=True, can_reveal_password=True,
                border_radius=12, border_color="#CCCCCC", bgcolor="white")
            f_conf  = ft.TextField(hint_text="Confirmar",   password=True, can_reveal_password=True,
                border_radius=12, border_color="#CCCCCC", bgcolor="white")
            msg = ft.Text("", color="red", size=12)
            def salvar(ev):
                atual = state.config.get("senha_professor","123")
                if f_atual.value != atual: msg.value="Senha atual incorreta."; page.update(); return
                if not f_nova.value: msg.value="Nova senha não pode ser vazia."; page.update(); return
                if f_nova.value != f_conf.value: msg.value="Senhas não coincidem."; page.update(); return
                state.config["senha_professor"] = f_nova.value
                salvar_config(state.config)
                dlg.open=False; page.update()
            def fechar(ev): dlg.open=False; page.update()
            dlg = ft.AlertDialog(modal=True, title=ft.Text("⚙ Configurar Senha"),
                content=ft.Column(tight=True, spacing=10, width=300, controls=[
                    f_atual, f_nova, f_conf, msg]),
                actions=[ft.TextButton("Cancelar", on_click=fechar),
                         ft.ElevatedButton("Salvar", on_click=salvar)])
            page.overlay.append(dlg); dlg.open=True; page.update()

        pv = painel_nav_prof(scale, _inicio, _ativ, _rank, _acomp, _rel, _hist, _sair)

        pc = _painel_dashboard(scale, page, navegar, on_config=_config)
        montar_layout(page, scale, img_w, img_h, pv, pc)

    page.on_resize = lambda e: build()
    build()
