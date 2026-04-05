"""
views/aluno_telas.py — Telas de Atividades, Histórico e Ranking do aluno.
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import flet as ft
import state
from constants import LABEL_TIPO, LISTA_ATIVIDADES, ALUNOS_POR_TURMA
from controllers.historico_controller import buscar_todos_resultados, buscar_detalhes_questoes, contar_tentativas
from views.aluno_helpers import (
    BLUE, ORANGE_BG, WHITE, GOLD, GREEN, RED,
    IMG_W, IMG_H,
    painel_verde, montar_layout_aluno,
)


# ============================================================
#  BLOCO CINZA — TELA DE ATIVIDADES
# ============================================================

def _painel_lista_atividades(scale, on_iniciar):
    """⬛ Bloco cinza — lista completa de atividades com status."""
    dados = buscar_todos_resultados()
    alunos_ativos = state.alunos_ativos or []

    ativa = next(
        (a for a in state.atividades_liberadas if a["turma"] == state.turma_atual),
        None,
    )

    linhas = []

    for ativ in LISTA_ATIVIDADES:
        nome = ativ["nome"]

        feita_por_regs = [r for r in dados if r["atividade"] == nome and r["aluno"] in alunos_ativos]
        feita_por = [r["aluno"] for r in feita_por_regs]
        liberada  = ativa and ativa["atividade"] == nome

        tentativas_por_aluno = {}
        for r in feita_por_regs:
            tentativas_por_aluno[r["aluno"]] = tentativas_por_aluno.get(r["aluno"], 0) + 1

        todos_completaram = all(tentativas_por_aluno.get(a, 0) >= 2 for a in alunos_ativos) if feita_por else False
        bloqueada = not liberada and not feita_por

        if feita_por and todos_completaram:
            icone        = ft.Icons.CHECK_CIRCLE
            cor_icone    = "#4CAF50"
            status_lines = []
            for r in feita_por_regs:
                t_num = sum(1 for rr in feita_por_regs if rr["aluno"] == r["aluno"] and rr["id"] <= r["id"])
                status_lines.append(ft.Text(
                    f"✔ {r['aluno']} T{t_num}: {r['pontuacao']}pts ({r['data']})",
                    color="#4CAF50", size=10 * scale))
            can_click = False
        elif feita_por and liberada and not todos_completaram:
            icone        = ft.Icons.REPLAY
            cor_icone    = GOLD
            status_lines = []
            for r in feita_por_regs:
                status_lines.append(ft.Text(
                    f"🔄 {r['aluno']}: {r['pontuacao']}pts",
                    color=GOLD, size=10 * scale))
            status_lines.append(ft.Text("2ª tentativa disponível", color=GOLD, size=9 * scale))
            can_click = True
        elif liberada:
            icone        = ft.Icons.PLAY_CIRCLE
            cor_icone    = BLUE
            status_lines = [ft.Text("Liberada", color=BLUE, size=10 * scale)]
            can_click    = True
        else:
            icone        = ft.Icons.LOCK
            cor_icone    = "#66FFFFFF"
            status_lines = [ft.Text("Bloqueada", color="#66FFFFFF", size=10 * scale)]
            can_click    = False

        tempo_txt = (
            f"⏱ {ativa.get('tempo_maximo', 600) // 60} min"
            if liberada and ativa else "⏱ —"
        )

        botao_iniciar = ft.Container(
            border_radius=16 * scale,
            bgcolor=BLUE if can_click else "#22FFFFFF",
            padding=ft.padding.symmetric(horizontal=14 * scale, vertical=7 * scale),
            on_click=(lambda e, n=nome: on_iniciar(n)) if can_click else None,
            ink=can_click,
            content=ft.Text(
                "▶  INICIAR",
                color=WHITE if can_click else "#44FFFFFF",
                size=11 * scale,
                weight="bold",
            ),
        )

        linha = ft.Container(
            border_radius=10 * scale,
            bgcolor="#0AFFFFFF" if not bloqueada else "#06FFFFFF",
            padding=ft.padding.symmetric(horizontal=16 * scale, vertical=10 * scale),
            content=ft.Row(
                spacing=14 * scale,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icone, color=cor_icone, size=20 * scale),
                    ft.Column(
                        spacing=2 * scale,
                        expand=True,
                        controls=[
                            ft.Text(nome, color=WHITE if not bloqueada else "#88FFFFFF",
                                    size=14 * scale, weight="bold"),
                            *status_lines,
                            ft.Text(tempo_txt, color="#88FFFFFF", size=10 * scale),
                        ],
                    ),
                    botao_iniciar,
                ],
            ),
        )
        linhas.append(linha)

    return ft.Container(
        width=1010 * scale,
        border_radius=16 * scale,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        padding=ft.padding.symmetric(horizontal=28 * scale, vertical=22 * scale),
        content=ft.Column(
            spacing=14 * scale,
            controls=[
                ft.Row(
                    spacing=8 * scale,
                    controls=[
                        ft.Icon(ft.Icons.MENU_BOOK, color=BLUE, size=20 * scale),
                        ft.Text("Atividades", color=WHITE, size=16 * scale, weight="bold"),
                    ],
                ),
                ft.Divider(color="#22FFFFFF", thickness=1),
                *linhas,
            ],
        ),
    )


# ============================================================
#  TELA DE ATIVIDADES
# ============================================================

def tela_atividades(page: ft.Page, navegar: dict):
    page.controls.clear()
    page.padding = 0
    page.bgcolor = "white"

    def build():
        page.controls.clear()
        W = page.width  or IMG_W
        H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W * scale
        img_h = IMG_H * scale

        def _voltar_menu(e): from views.aluno_view import menu; menu(page, navegar)
        def _atividades(e):  tela_atividades(page, navegar)
        def _historico(e):   tela_historico(page, navegar)
        def _ranking(e):     tela_ranking(page, navegar)
        def _sair(e):        navegar["login"]()

        def _fechar_dlg(dlg): dlg.open = False; page.update()
        def _fechar_e_iniciar(dlg, nm): dlg.open = False; page.update(); navegar["iniciar_atividade"](nm)

        def _iniciar(nome):
            bloqueados = [a for a in state.alunos_ativos if contar_tentativas(a, nome) >= 2]
            if bloqueados and len(bloqueados) == len(state.alunos_ativos):
                dlg = ft.AlertDialog(modal=True, title=ft.Text("Indisponível"),
                    content=ft.Text("Todos os alunos já realizaram as 2 tentativas."))
                dlg.actions = [ft.TextButton("OK", on_click=lambda ev: _fechar_dlg(dlg))]
                page.overlay.append(dlg); dlg.open = True; page.update(); return
            elif bloqueados:
                nomes = ", ".join(bloqueados)
                dlg = ft.AlertDialog(modal=True, title=ft.Text("Atenção"),
                    content=ft.Text(f"{nomes} já fez 2 tentativas.\nA atividade será iniciada para os demais."))
                dlg.actions = [ft.TextButton("OK, iniciar", on_click=lambda ev, n=nome: _fechar_e_iniciar(dlg, n))]
                page.overlay.append(dlg); dlg.open = True; page.update(); return
            navegar["iniciar_atividade"](nome)

        pv = painel_verde(scale, _atividades, _historico, _ranking, _sair, on_menu=_voltar_menu)
        montar_layout_aluno(page, scale, img_w, img_h, pv, _painel_lista_atividades(scale, _iniciar))

    page.on_resize = lambda e: build()
    build()


# ============================================================
#  BLOCO CINZA — TELA DE HISTÓRICO
# ============================================================

def _painel_historico(scale, page=None, navegar=None):
    """⬛ Bloco cinza — histórico com tentativas sinalizadas e detalhes expandíveis."""
    dados = buscar_todos_resultados()
    alunos_ativos = state.alunos_ativos or []

    blocos = []

    for aluno in alunos_ativos:
        registros = [r for r in dados if r["aluno"].strip() == aluno.strip()]
        total_pts = sum(r["pontuacao"] for r in registros)

        melhor_por_ativ = {}
        for r in registros:
            if r["atividade"] not in melhor_por_ativ or r["pontuacao"] > melhor_por_ativ[r["atividade"]]:
                melhor_por_ativ[r["atividade"]] = r["pontuacao"]

        blocos.append(ft.Row(spacing=8 * scale, controls=[
            ft.Icon(ft.Icons.PERSON, color="#AAFFFFFF", size=16 * scale),
            ft.Text(aluno, color=WHITE, size=14 * scale, weight="bold"),
            ft.Text("·", color="#AAFFFFFF", size=12 * scale),
            ft.Text(f"{total_pts} pts", color="#F9A825", size=13 * scale, weight="bold"),
        ]))

        if not registros:
            blocos.append(ft.Text("  Nenhuma atividade realizada ainda.", color="#66FFFFFF", size=11 * scale))
        else:
            header = ft.Container(
                border_radius=8 * scale, bgcolor="#15FFFFFF",
                padding=ft.padding.symmetric(horizontal=12 * scale, vertical=6 * scale),
                content=ft.Row(spacing=4*scale, controls=[
                    ft.Container(width=160 * scale, content=ft.Text("Atividade", color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=50 * scale,  content=ft.Text("T#",        color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=70 * scale,  content=ft.Text("Final",     color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=65 * scale,  content=ft.Text("Acertos",   color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=60 * scale,  content=ft.Text("Erros",     color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=70 * scale,  content=ft.Text("Tempo",     color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=100 * scale, content=ft.Text("Data",      color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=40 * scale,  content=ft.Text("",          size=10 * scale)),
                ]),
            )
            blocos.append(header)

            contagem = {}
            for r in registros:
                contagem[r["atividade"]] = contagem.get(r["atividade"], 0) + 1
                t_num = contagem[r["atividade"]]
                pts_final = r["pontuacao"]
                is_melhor = pts_final == melhor_por_ativ.get(r["atividade"], -1)
                tem_detalhes = len(buscar_detalhes_questoes(r["id"])) > 0

                def _ver_detalhes(e, rid=r["id"], ativ=r["atividade"], aluno_nome=aluno):
                    det = buscar_detalhes_questoes(rid)
                    if not det: return

                    linhas_det = []
                    for q in det:
                        cor_status = "#4CAF50" if q["acertou"] else "#FF5252"
                        icone_status = "✅" if q["acertou"] else "❌"
                        linhas_det.append(ft.Container(
                            border_radius=8,
                            bgcolor="#F8F8F8" if q["acertou"] else "#FFF5F5",
                            padding=ft.padding.symmetric(horizontal=14, vertical=10),
                            content=ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                                ft.Text(f"Q{q['numero']}", size=13, weight="bold", color="#666666", width=35),
                                ft.Column(spacing=2, expand=True, controls=[
                                    ft.Text(q["pergunta"], size=13, weight="bold", color="#333333"),
                                    ft.Row(spacing=16, controls=[
                                        ft.Text(f"Sua resposta: {q['resposta_aluno']}", size=12, color=cor_status, weight="bold"),
                                        ft.Text(f"Correta: {q['resposta_correta']}", size=12, color="#888888"),
                                    ]),
                                ]),
                                ft.Text(f"{q['tentativas']}x", size=12, color="#AAAAAA"),
                                ft.Text(icone_status, size=18),
                            ]),
                        ))

                    acertos_det = sum(1 for q in det if q["acertou"])
                    erros_det   = sum(1 for q in det if not q["acertou"])

                    dlg_content = ft.Container(
                        width=800, height=500,
                        content=ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, controls=[
                            ft.Row(spacing=12, alignment=ft.MainAxisAlignment.CENTER, controls=[
                                ft.Container(border_radius=8, bgcolor="#E8F5E9", padding=ft.padding.all(8),
                                    content=ft.Text(f"✅ {acertos_det} acertos", size=13, weight="bold", color="#4CAF50")),
                                ft.Container(border_radius=8, bgcolor="#FFEBEE", padding=ft.padding.all(8),
                                    content=ft.Text(f"❌ {erros_det} erros", size=13, weight="bold", color="#FF5252")),
                                ft.Container(border_radius=8, bgcolor="#E3F2FD", padding=ft.padding.all(8),
                                    content=ft.Text(f"📝 {len(det)} questões", size=13, weight="bold", color="#2F9EDC")),
                            ]),
                            ft.Divider(),
                            *linhas_det,
                        ]),
                    )

                    def _fechar(ev):
                        dlg.open = False; page.update()

                    dlg = ft.AlertDialog(
                        title=ft.Text(f"📋 {ativ} — {aluno_nome}", size=18, weight="bold"),
                        content=dlg_content,
                    )
                    dlg.actions = [ft.TextButton("Fechar", on_click=_fechar)]
                    page.overlay.append(dlg); dlg.open = True; page.update()

                bg = "#143C4CAF" if is_melhor else "#0AFFFFFF"
                btn_det = ft.Container(
                    width=40 * scale, alignment=ft.Alignment(0, 0),
                    content=ft.IconButton(ft.Icons.VISIBILITY, icon_size=14 * scale,
                        icon_color=BLUE, on_click=_ver_detalhes,
                        tooltip="Ver detalhes das questões"),
                ) if page and tem_detalhes else ft.Container(width=40 * scale)

                linha = ft.Container(
                    border_radius=8 * scale, bgcolor=bg,
                    padding=ft.padding.symmetric(horizontal=12 * scale, vertical=7 * scale),
                    content=ft.Row(spacing=4*scale, controls=[
                        ft.Container(width=160 * scale, content=ft.Text(r["atividade"], color=WHITE, size=11 * scale)),
                        ft.Container(width=50 * scale,  content=ft.Text(f"T{t_num}", color="#AAFFFFFF", size=11 * scale)),
                        ft.Container(width=70 * scale,  content=ft.Text(str(pts_final), color="#F9A825" if is_melhor else WHITE, size=11 * scale, weight="bold" if is_melhor else "normal")),
                        ft.Container(width=65 * scale,  content=ft.Text(str(r["acertos"]), color="#4CAF50", size=11 * scale)),
                        ft.Container(width=60 * scale,  content=ft.Text(str(r["erros"]), color="#FF5252", size=11 * scale)),
                        ft.Container(width=70 * scale,  content=ft.Text(r["tempo"], color=WHITE, size=11 * scale)),
                        ft.Container(width=100 * scale, content=ft.Text(r["data"], color="#77FFFFFF", size=10 * scale)),
                        btn_det,
                    ]),
                )
                blocos.append(linha)

        blocos.append(ft.Container(height=10 * scale))

    if not blocos:
        blocos.append(ft.Text("Nenhum histórico disponível.", color="#66FFFFFF", size=12 * scale))

    return ft.Container(
        width=1010 * scale,
        height=625 * scale,
        border_radius=16 * scale,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        padding=ft.padding.symmetric(horizontal=28 * scale, vertical=22 * scale),
        content=ft.Column(
            spacing=8 * scale,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    spacing=8 * scale,
                    controls=[
                        ft.Icon(ft.Icons.HISTORY, color=ORANGE_BG, size=20 * scale),
                        ft.Text("Meu Histórico", color=WHITE, size=16 * scale, weight="bold"),
                    ],
                ),
                ft.Divider(color="#22FFFFFF", thickness=1),
                *blocos,
            ],
        ),
    )


# ============================================================
#  TELA DE HISTÓRICO
# ============================================================

def tela_historico(page: ft.Page, navegar: dict):
    page.controls.clear()
    page.padding = 0
    page.bgcolor = "white"

    def build():
        page.controls.clear()
        W = page.width  or IMG_W
        H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W * scale
        img_h = IMG_H * scale

        def _voltar_menu(e): from views.aluno_view import menu; menu(page, navegar)
        def _atividades(e):  tela_atividades(page, navegar)
        def _historico(e):   tela_historico(page, navegar)
        def _ranking(e):     tela_ranking(page, navegar)
        def _sair(e):        navegar["login"]()

        pv = painel_verde(scale, _atividades, _historico, _ranking, _sair, on_menu=_voltar_menu)
        montar_layout_aluno(page, scale, img_w, img_h, pv, _painel_historico(scale, page, navegar))

    page.on_resize = lambda e: build()
    build()


def historico(page: ft.Page, navegar):
    tela_historico(page, navegar)


# ============================================================
#  BLOCO CINZA — TELA DE RANKING
# ============================================================

def _painel_ranking(scale):
    dados = buscar_todos_resultados()
    alunos_ativos = state.alunos_ativos or []

    pts_geral = {}
    for r in dados:
        pts_geral[r["aluno"]] = pts_geral.get(r["aluno"], 0) + r["pontuacao"]

    rank_geral = sorted(pts_geral.items(), key=lambda x: x[1], reverse=True)

    pts_por_turma = {t: {} for t in ALUNOS_POR_TURMA}
    for r in dados:
        t = r["turma"]
        if t in pts_por_turma:
            pts_por_turma[t][r["aluno"]] = pts_por_turma[t].get(r["aluno"], 0) + r["pontuacao"]

    rank_por_turma = {
        t: sorted(pts.items(), key=lambda x: x[1], reverse=True)
        for t, pts in pts_por_turma.items()
    }

    total_turma = {t: sum(pts.values()) for t, pts in pts_por_turma.items()}
    rank_turmas = sorted(total_turma.items(), key=lambda x: x[1], reverse=True)

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    aluno_turma = {r["aluno"]: r["turma"] for r in dados}

    def posicao_geral(aluno):
        for i, (n, _) in enumerate(rank_geral, start=1):
            if n == aluno:
                return i
        return 0

    def posicao_turma(aluno, turma):
        rt = rank_por_turma.get(turma, [])
        for i, (n, _) in enumerate(rt, start=1):
            if n == aluno:
                return i
        return 0

    def _rank_line_geral(pos, nome, pts, is_destaque, turma=""):
        is_top3 = pos <= 3
        bg = "#143C4CAF" if is_destaque else "#0AFFFFFF"
        medal = medals.get(pos, f"{pos}º")
        return ft.Container(
            border_radius=10 * scale,
            bgcolor=bg,
            padding=ft.padding.symmetric(horizontal=12 * scale, vertical=8 * scale),
            content=ft.Row(spacing=10 * scale, controls=[
                ft.Container(width=40 * scale,
                    content=ft.Text(medal, size=16 * scale if is_top3 else 13 * scale)),
                ft.Container(width=160 * scale,
                    content=ft.Text(nome, size=12 * scale,
                        weight="bold" if is_destaque else "normal",
                        color=BLUE if is_destaque else WHITE)),
                ft.Container(width=60 * scale,
                    content=ft.Text(f"Turma{turma}", size=10 * scale, color="#88FFFFFF")),
                ft.Container(expand=True),
                ft.Container(width=90 * scale,
                    content=ft.Row(alignment=ft.MainAxisAlignment.END, controls=[
                        ft.Text(f"{pts} pts", size=12 * scale, weight="bold",
                            color="#F9A825" if is_top3 else "#CCCCCC")])),
            ]),
        )

    def _rank_line(pos, nome, pts, is_destaque):
        medal = medals.get(pos, f"{pos}º")
        return ft.Container(
            border_radius=10 * scale,
            bgcolor="#143C4CAF" if is_destaque else "#0AFFFFFF",
            padding=ft.padding.symmetric(horizontal=12 * scale, vertical=8 * scale),
            content=ft.Row(spacing=10 * scale, controls=[
                ft.Container(width=40 * scale, content=ft.Text(medal)),
                ft.Container(width=180 * scale,
                    content=ft.Text(nome, size=12 * scale,
                        weight="bold" if is_destaque else "normal",
                        color=BLUE if is_destaque else WHITE)),
                ft.Container(expand=True),
                ft.Container(width=90 * scale,
                    content=ft.Row(alignment=ft.MainAxisAlignment.END, controls=[
                        ft.Text(f"{pts} pts", size=12 * scale, weight="bold", color="#F9A825")])),
            ]),
        )

    # ── Sua posição ─────────────────────────────────────────
    cards_posicao = []
    for aluno in alunos_ativos:
        pos_g = posicao_geral(aluno)
        pos_t = posicao_turma(aluno, state.turma_atual)
        pts_g = pts_geral.get(aluno, 0)
        pts_t = pts_por_turma.get(state.turma_atual, {}).get(aluno, 0)
        cards_posicao.append(ft.Container(
            border_radius=10 * scale, bgcolor="#1A2F9EDC",
            padding=ft.padding.symmetric(horizontal=14 * scale, vertical=8 * scale),
            content=ft.Row(spacing=8 * scale, wrap=True, controls=[
                ft.Icon(ft.Icons.PERSON, color=BLUE, size=16 * scale),
                ft.Text(aluno, color=WHITE, size=12 * scale, weight="bold"),
                ft.Text("·", color="#AAFFFFFF", size=12 * scale),
                ft.Text(f"{pos_g}º geral ({pts_g} pts)", color="#F9A825", size=12 * scale, weight="bold"),
                ft.Text("·", color="#AAFFFFFF", size=12 * scale),
                ft.Text(f"{pos_t}º turma ({pts_t} pts)", color=WHITE, size=12 * scale),
            ]),
        ))

    # ── Coluna GERAL ─────────────────────────────────────────
    linhas_geral = [
        _rank_line_geral(i, n, pts, n in alunos_ativos, aluno_turma.get(n, ""))
        for i, (n, pts) in enumerate(rank_geral[:10], start=1)
    ] or [ft.Text("Nenhum resultado.", color="#66FFFFFF", size=11 * scale)]

    col_geral = ft.Container(
        expand=True, border_radius=12 * scale, bgcolor="#0AFFFFFF",
        padding=ft.padding.all(10 * scale),
        content=ft.Column(spacing=5 * scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=6 * scale, controls=[
                ft.Text("🌍", size=13 * scale),
                ft.Text("Ranking Geral", color=WHITE, size=12 * scale, weight="bold"),
            ]),
            ft.Divider(color="#22FFFFFF", thickness=1),
            *linhas_geral,
        ]),
    )

    # ── Coluna TURMA ─────────────────────────────────────────
    rank_minha_turma = rank_por_turma.get(state.turma_atual, [])
    linhas_turma = [
        _rank_line(i, n, pts, n in alunos_ativos)
        for i, (n, pts) in enumerate(rank_minha_turma[:10], start=1)
    ] or [ft.Text("Nenhum resultado.", color="#66FFFFFF", size=11 * scale)]

    col_turma = ft.Container(
        expand=True, border_radius=12 * scale, bgcolor="#0AFFFFFF",
        padding=ft.padding.all(10 * scale),
        content=ft.Column(spacing=5 * scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=6 * scale, controls=[
                ft.Text("🏫", size=13 * scale),
                ft.Text(f"Ranking da Turma {state.turma_atual}", color=WHITE, size=12 * scale, weight="bold"),
            ]),
            ft.Divider(color="#22FFFFFF", thickness=1),
            *linhas_turma,
        ]),
    )

    # ── Coluna CLASSIFICAÇÃO DAS TURMAS ──────────────────────
    linhas_classif = []
    for i, (t, total) in enumerate(rank_turmas, start=1):
        destaque = t == state.turma_atual
        linhas_classif.append(ft.Container(
            border_radius=8 * scale,
            bgcolor="#1A2F9EDC" if destaque else "#0AFFFFFF",
            padding=ft.padding.symmetric(horizontal=10 * scale, vertical=5 * scale),
            content=ft.Row(spacing=8 * scale, controls=[
                ft.Text(medals.get(i, f"{i}º"), size=13 * scale),
                ft.Text(f"Turma {t}", color=BLUE if destaque else WHITE, size=11 * scale,
                         weight="bold" if destaque else "normal", expand=True),
                ft.Text(f"{total} pts", color="#F9A825" if destaque else "#AAFFFFFF",
                         size=11 * scale, weight="bold"),
            ]),
        ))

    if not linhas_classif:
        linhas_classif.append(ft.Text("Nenhum resultado.", color="#66FFFFFF", size=11 * scale))

    col_classif = ft.Container(
        expand=True, border_radius=12 * scale, bgcolor="#0AFFFFFF",
        padding=ft.padding.all(10 * scale),
        content=ft.Column(spacing=5 * scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=6 * scale, controls=[
                ft.Text("🏆", size=13 * scale),
                ft.Text("Classif. Turmas", color=WHITE, size=12 * scale, weight="bold"),
            ]),
            ft.Divider(color="#22FFFFFF", thickness=1),
            *linhas_classif,
        ]),
    )

    return ft.Container(
        width=1010 * scale,
        height=625 * scale,
        border_radius=20 * scale,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        padding=ft.padding.symmetric(horizontal=18 * scale, vertical=14 * scale),
        content=ft.Column(
            spacing=8 * scale,
            controls=[
                ft.Row(spacing=8 * scale, controls=[
                    ft.Icon(ft.Icons.LEADERBOARD, color="#F9A825", size=20 * scale),
                    ft.Text("Ranking", color=WHITE, size=16 * scale, weight="bold"),
                ]),
                *cards_posicao,
                ft.Divider(color="#22FFFFFF", thickness=1),
                ft.Row(
                    spacing=14 * scale,
                    expand=True,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[col_geral, col_turma, col_classif],
                ),
            ],
        ),
    )


# ============================================================
#  TELA DE RANKING
# ============================================================

def tela_ranking(page: ft.Page, navegar: dict):
    page.controls.clear()
    page.padding = 0
    page.bgcolor = "white"

    def build():
        page.controls.clear()
        W = page.width  or IMG_W
        H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W * scale
        img_h = IMG_H * scale

        def _voltar_menu(e): from views.aluno_view import menu; menu(page, navegar)
        def _atividades(e):  tela_atividades(page, navegar)
        def _historico(e):   tela_historico(page, navegar)
        def _ranking(e):     tela_ranking(page, navegar)
        def _sair(e):        navegar["login"]()

        pv = painel_verde(scale, _atividades, _historico, _ranking, _sair, on_menu=_voltar_menu)
        montar_layout_aluno(page, scale, img_w, img_h, pv, _painel_ranking(scale))

    page.on_resize = lambda e: build()
    build()


def ranking(page: ft.Page, navegar):
    tela_ranking(page, navegar)
