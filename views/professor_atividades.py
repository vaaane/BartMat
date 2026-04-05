"""
views/professor_atividades.py — Telas de atividades do professor.
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import flet as ft
import state
from constants import LABEL_TIPO, LISTA_ATIVIDADES, ALUNOS_POR_TURMA
from controllers.historico_controller import (
    buscar_todos_resultados, buscar_resultados_por_turma, buscar_detalhes_questoes,
    registrar_liberacao, cancelar_liberacao, buscar_liberacoes,
)
from controllers.liberacoes_controller import salvar_liberadas
from views.professor_helpers import (
    BLUE, ORANGE_BG, WHITE, GREEN, RED, GOLD, IMG_W, IMG_H,
    TURMAS, MEDALS, CINZA_W, CINZA_H,
    btn_menu, stat_card, painel_nav_prof, montar_layout,
)


def _nav_ativ(scale, page, navegar, menu_fn):
    """Painel de navegação completo para as telas de atividades.
    Usa lazy imports para evitar import circular com professor_telas."""
    def _inicio(e): menu_fn(page, navegar)
    def _ativ(e):   tela_atividades(page, navegar, menu_fn)
    def _rank(e):
        from views.professor_telas import tela_ranking
        tela_ranking(page, navegar, menu_fn)
    def _acomp(e):
        from views.professor_telas import tela_acompanhamento
        tela_acompanhamento(page, navegar, menu_fn)
    def _rel(e):
        from views.professor_telas import tela_relatorio_turma
        tela_relatorio_turma(page, navegar, menu_fn)
    def _hist(e):
        from views.professor_telas import tela_historico_geral
        tela_historico_geral(page, navegar, menu_fn)
    def _sair(e): navegar["login"]()
    return painel_nav_prof(scale, _inicio, _ativ, _rank, _acomp, _rel, _hist, _sair)


def _historico_liberacoes(scale):
    from datetime import datetime as _dt
    libs=buscar_liberacoes()[:15]
    if not libs:
        return [ft.Text("Nenhuma liberação registrada.",color="#66FFFFFF",size=9*scale)]
    linhas=[]
    for lib in libs:
        if lib.get("cancelado_em"): estado_s="Cancelada"; cor=RED
        elif lib.get("expira_em") and lib["expira_em"]<_dt.now().isoformat(): estado_s="Expirada"; cor="#AAFFFFFF"
        else: estado_s="Ativa"; cor=GREEN
        nome_a=lib["atividade"].split(" - ")[1] if " - " in lib["atividade"] else lib["atividade"]
        ts=lib["liberado_em"][:16].replace("T"," ") if lib.get("liberado_em") else ""
        linhas.append(ft.Container(border_radius=6*scale,bgcolor="#08FFFFFF",
            padding=ft.padding.symmetric(horizontal=8*scale,vertical=5*scale),
            content=ft.Row(spacing=6*scale,controls=[
                ft.Column(spacing=1,expand=True,controls=[
                    ft.Text(f"{nome_a} — T{lib['turma']}",color=WHITE,size=9*scale,weight="bold"),
                    ft.Text(f"{lib['tipo']}  •  {ts}",color="#66FFFFFF",size=8*scale),
                ]),
                ft.Text(estado_s,color=cor,size=9*scale,weight="bold"),
            ])))
    return linhas


def tela_atividades(page, navegar, menu_fn):
    page.controls.clear()
    page.padding = 0
    page.bgcolor = "white"

    def build():
        page.controls.clear()
        W = page.width or IMG_W; H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W * scale; img_h = IMG_H * scale

        dados = buscar_todos_resultados()
        painel_verde = _nav_ativ(scale, page, navegar, menu_fn)

        cor_ativ = {"Atividade 1 - Frações": BLUE, "Atividade 2 - Equações": GREEN, "Atividade 3 - Geometria": ORANGE_BG}

        def _card_atividade(a):
            nome = a["nome"]; cor = cor_ativ.get(nome, BLUE)
            regs = [r for r in dados if r["atividade"] == nome]
            alunos_u = len(set(r["aluno"] for r in regs))
            media = round(sum(r["pontuacao"] for r in regs) / len(regs)) if regs else 0
            ac = sum(r["acertos"] for r in regs); er = sum(r["erros"] for r in regs)
            turmas_d = sorted(set(r["turma"] for r in regs))
            n_t = len(turmas_d); total_t = len(TURMAS)
            ativa = next((x for x in state.atividades_liberadas if x["atividade"] == nome), None)
            status_ctrl = ft.Row(spacing=6*scale, controls=[
                ft.Icon(ft.Icons.CIRCLE, color=GREEN, size=10*scale),
                ft.Text(f"Ativa — Turma {ativa['turma']}", color=GREEN, size=10*scale, weight="bold"),
            ]) if ativa else ft.Row(spacing=6*scale, controls=[
                ft.Icon(ft.Icons.CIRCLE, color="#555555", size=10*scale),
                ft.Text("Inativa", color="#888888", size=10*scale),
            ])
            def _abrir(e, n=nome): detalhe_atividade(page, navegar, n, menu_fn)
            return ft.Container(
                border_radius=16*scale, bgcolor="#0DFFFFFF", border=ft.border.all(1.5, cor+"88"),
                padding=ft.padding.all(14*scale), on_click=_abrir, ink=True,
                content=ft.Column(spacing=8*scale, controls=[
                    ft.Row(spacing=10*scale, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        ft.Container(width=42*scale, height=42*scale, border_radius=12*scale,
                            bgcolor=cor+"33", alignment=ft.Alignment(0,0),
                            content=ft.Icon(ft.Icons.MENU_BOOK, color=cor, size=22*scale)),
                        ft.Column(spacing=2*scale, expand=True, controls=[
                            ft.Text(nome, color=WHITE, size=13*scale, weight="bold"), status_ctrl]),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#55FFFFFF", size=18*scale),
                    ]),
                    ft.Divider(color="#15FFFFFF", thickness=1),
                    ft.Row(spacing=12*scale, controls=[
                        ft.Column(spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text(str(alunos_u), color=cor, size=18*scale, weight="bold"),
                            ft.Text("alunos", color="#88FFFFFF", size=8*scale)]),
                        ft.Column(spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text(str(media), color=GOLD, size=18*scale, weight="bold"),
                            ft.Text("média pts", color="#88FFFFFF", size=8*scale)]),
                        ft.Column(spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text(str(ac), color=GREEN, size=18*scale, weight="bold"),
                            ft.Text("acertos", color="#88FFFFFF", size=8*scale)]),
                        ft.Column(spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text(str(er), color=RED, size=18*scale, weight="bold"),
                            ft.Text("erros", color="#88FFFFFF", size=8*scale)]),
                    ]),
                    ft.Row(spacing=4*scale, controls=[
                        ft.Icon(ft.Icons.SCHOOL, color="#77FFFFFF", size=10*scale),
                        ft.Text(f"Turmas: {', '.join(turmas_d)}  •  {n_t}/{total_t} turmas" if turmas_d else "Nenhuma turma ainda",
                            color="#99FFFFFF", size=9*scale),
                    ]),
                ]),
            )

        cards_col = ft.Column(spacing=12*scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=8*scale, controls=[
                ft.Icon(ft.Icons.MENU_BOOK, color=BLUE, size=18*scale),
                ft.Text("Atividades", color=WHITE, size=16*scale, weight="bold"),
            ]),
            ft.Text("Clique em uma atividade para liberar, testar ou ver o histórico.", color="#88FFFFFF", size=11*scale),
            ft.Container(height=4*scale),
            *[_card_atividade(a) for a in LISTA_ATIVIDADES],
        ])

        lib_controls = []
        ativas = list(state.atividades_liberadas)
        if ativas:
            for a in ativas:
                tipo_label = LABEL_TIPO[a["tipo"]]; tempo_min = a.get("tempo_maximo", 600)//60
                def cancelar_esta(ev, lib=a):
                    from datetime import datetime
                    state.atividades_liberadas.remove(lib)
                    salvar_liberadas(state.atividades_liberadas)
                    if lib.get("_lib_id"): cancelar_liberacao(lib["_lib_id"], datetime.now().isoformat())
                    tela_atividades(page, navegar, menu_fn)
                lib_controls.append(ft.Container(
                    border_radius=10*scale, bgcolor="#1A4CAF50", border=ft.border.all(1, GREEN),
                    padding=ft.padding.symmetric(horizontal=10*scale, vertical=8*scale),
                    content=ft.Column(spacing=4*scale, controls=[
                        ft.Row(spacing=6*scale, controls=[
                            ft.Icon(ft.Icons.PLAY_CIRCLE, color=GREEN, size=14*scale),
                            ft.Text(a["atividade"].split(" - ")[1] if " - " in a["atividade"] else a["atividade"],
                                color=WHITE, size=11*scale, weight="bold")]),
                        ft.Text(f"Turma {a['turma']}  •  {tipo_label}  •  {tempo_min}min", color="#AAFFFFFF", size=9*scale),
                        ft.Container(border_radius=6*scale, bgcolor="#33FF5252",
                            padding=ft.padding.symmetric(horizontal=8*scale, vertical=3*scale),
                            on_click=cancelar_esta, ink=True, alignment=ft.Alignment(0,0),
                            content=ft.Text("⛔ Encerrar", color=RED, size=9*scale, weight="bold")),
                    ]),
                ))
        else:
            lib_controls.append(ft.Container(
                border_radius=10*scale, bgcolor="#0AFFFFFF",
                padding=ft.padding.symmetric(horizontal=10*scale, vertical=12*scale),
                content=ft.Column(spacing=4*scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Icon(ft.Icons.PAUSE_CIRCLE_OUTLINE, color="#55FFFFFF", size=28*scale),
                    ft.Text("Nenhuma atividade\nliberada no momento", color="#66FFFFFF", size=10*scale, text_align="center"),
                ]),
            ))

        painel_cinza = ft.Container(
            width=CINZA_W*scale, height=CINZA_H*scale,
            border_radius=20*scale, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            padding=ft.padding.symmetric(horizontal=16*scale, vertical=12*scale),
            content=ft.Row(spacing=14*scale, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
                ft.Container(expand=3, content=cards_col),
                ft.Container(width=1, height=(CINZA_H-40)*scale, bgcolor="#15FFFFFF"),
                ft.Container(expand=2, content=ft.Column(spacing=10*scale, scroll=ft.ScrollMode.AUTO, controls=[
                    ft.Row(spacing=8*scale, controls=[
                        ft.Icon(ft.Icons.BOLT, color=GREEN, size=16*scale),
                        ft.Text("Ativas agora", color=WHITE, size=13*scale, weight="bold")]),
                    *lib_controls,
                    ft.Divider(color="#22FFFFFF", thickness=1),
                    ft.Row(spacing=6*scale, controls=[
                        ft.Icon(ft.Icons.HISTORY, color=BLUE, size=14*scale),
                        ft.Text("Histórico de liberações", color=WHITE, size=11*scale, weight="bold")]),
                    *_historico_liberacoes(scale),
                ])),
            ]),
        )
        montar_layout(page, scale, img_w, img_h, painel_verde, painel_cinza)

    page.on_resize = lambda e: build()
    build()


def detalhe_atividade(page, navegar, nome_atividade, menu_fn):
    page.controls.clear(); page.padding = 0; page.bgcolor = "white"

    def build():
        page.controls.clear()
        W = page.width or IMG_W; H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W*scale; img_h = IMG_H*scale

        painel_verde = _nav_ativ(scale, page, navegar, menu_fn)

        dados = buscar_todos_resultados()
        regs = [r for r in dados if r["atividade"] == nome_atividade]
        cor_map = {"Atividade 1 - Frações": BLUE, "Atividade 2 - Equações": GREEN, "Atividade 3 - Geometria": ORANGE_BG}
        cor = cor_map.get(nome_atividade, BLUE)
        alunos_u = len(set(r["aluno"] for r in regs))
        media = round(sum(r["pontuacao"] for r in regs)/len(regs)) if regs else 0
        ac = sum(r["acertos"] for r in regs); er = sum(r["erros"] for r in regs)
        turmas_d = sorted(set(r["turma"] for r in regs))
        ativa = next((x for x in state.atividades_liberadas if x["atividade"] == nome_atividade), None)

        def _liberar(e): liberar_atividade(page, navegar, nome_atividade, menu_fn)
        def _testar(e): testar_atividade(page, navegar, nome_atividade, menu_fn)
        def _historico(e): historico_atividade(page, navegar, nome_atividade, menu_fn)
        def _ranking(e): ranking_atividade(page, navegar, nome_atividade, menu_fn)

        if ativa:
            tipo_l = LABEL_TIPO[ativa["tipo"]]; tempo_m = ativa.get("tempo_maximo",600)//60
            def encerrar(ev, lib=ativa):
                from datetime import datetime
                state.atividades_liberadas.remove(lib)
                salvar_liberadas(state.atividades_liberadas)
                if lib.get("_lib_id"): cancelar_liberacao(lib["_lib_id"], datetime.now().isoformat())
                detalhe_atividade(page, navegar, nome_atividade, menu_fn)
            status_card = ft.Container(
                border_radius=12*scale, bgcolor="#1A4CAF50", border=ft.border.all(1.5, GREEN),
                padding=ft.padding.all(12*scale),
                content=ft.Column(spacing=6*scale, controls=[
                    ft.Row(spacing=8*scale, controls=[
                        ft.Icon(ft.Icons.PLAY_CIRCLE, color=GREEN, size=18*scale),
                        ft.Text(f"Ativa — Turma {ativa['turma']}", color=GREEN, size=12*scale, weight="bold")]),
                    ft.Text(f"{tipo_l}  •  {tempo_m} min", color="#AAFFFFFF", size=10*scale),
                    ft.Container(border_radius=8*scale, bgcolor="#33FF5252",
                        padding=ft.padding.symmetric(horizontal=12*scale, vertical=6*scale),
                        on_click=encerrar, ink=True, alignment=ft.Alignment(0,0),
                        content=ft.Text("⛔ Encerrar atividade", color=RED, size=10*scale, weight="bold")),
                ]),
            )
        else:
            status_card = ft.Container(border_radius=12*scale, bgcolor="#0AFFFFFF", padding=ft.padding.all(12*scale),
                content=ft.Row(spacing=8*scale, controls=[
                    ft.Icon(ft.Icons.CIRCLE, color="#555555", size=14*scale),
                    ft.Text("Inativa no momento", color="#888888", size=11*scale)]))

        def _act(label, icone, cor_btn, on_click):
            return ft.Container(
                expand=True, border_radius=12*scale, bgcolor=cor_btn+"22", border=ft.border.all(1, cor_btn+"55"),
                padding=ft.padding.symmetric(horizontal=10*scale, vertical=12*scale),
                on_click=on_click, ink=True,
                content=ft.Column(spacing=6*scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Icon(icone, color=cor_btn, size=24*scale),
                    ft.Text(label, color=WHITE, size=10*scale, weight="bold", text_align="center")]))

        pts_a = {}; turma_a = {}
        for r in regs:
            pts_a[r["aluno"]] = pts_a.get(r["aluno"],0) + r["pontuacao"]
            turma_a[r["aluno"]] = r["turma"]
        rank = sorted(pts_a.items(), key=lambda x: x[1], reverse=True)[:5]
        rank_ctrl = []
        for i,(n,p) in enumerate(rank, 1):
            rank_ctrl.append(ft.Container(border_radius=6*scale, bgcolor="#0AFFFFFF",
                padding=ft.padding.symmetric(horizontal=8*scale, vertical=4*scale),
                content=ft.Row(spacing=6*scale, controls=[
                    ft.Text(MEDALS.get(i, f"{i}º"), size=12*scale),
                    ft.Text(n, color=WHITE, size=10*scale, weight="bold", expand=True),
                    ft.Text(f"T{turma_a.get(n,'—')}", color="#77FFFFFF", size=9*scale),
                    ft.Text(f"{p} pts", color=GOLD, size=10*scale, weight="bold")])))
        if not rank_ctrl: rank_ctrl.append(ft.Text("Nenhum resultado ainda.", color="#66FFFFFF", size=10*scale))

        col = ft.Column(spacing=10*scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=12*scale, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Container(width=48*scale, height=48*scale, border_radius=14*scale, bgcolor=cor+"33",
                    alignment=ft.Alignment(0,0), content=ft.Icon(ft.Icons.MENU_BOOK, color=cor, size=26*scale)),
                ft.Column(spacing=2*scale, expand=True, controls=[
                    ft.Text(nome_atividade, color=WHITE, size=16*scale, weight="bold"),
                    ft.Text(f"Turmas: {', '.join(turmas_d)}" if turmas_d else "Nenhuma turma", color="#88FFFFFF", size=10*scale)])]),
            ft.Row(spacing=8*scale, controls=[
                stat_card("Alunos", str(alunos_u), cor, scale),
                stat_card("Média pts", str(media), GOLD, scale),
                stat_card("Acertos", str(ac), GREEN, scale),
                stat_card("Erros", str(er), RED, scale)]),
            status_card,
            ft.Divider(color="#22FFFFFF", thickness=1),
            ft.Text("Ações", color=WHITE, size=13*scale, weight="bold"),
            ft.Row(spacing=10*scale, controls=[
                _act("Liberar\nAtividade", ft.Icons.LOCK_OPEN, GREEN, _liberar),
                _act("Testar\nAtividade", ft.Icons.PLAY_ARROW, BLUE, _testar),
                _act("Histórico\npor Turma", ft.Icons.HISTORY, ORANGE_BG, _historico),
                _act("Ranking\npor Turma", ft.Icons.LEADERBOARD, GOLD, _ranking)]),
            ft.Divider(color="#22FFFFFF", thickness=1),
            ft.Row(spacing=6*scale, controls=[
                ft.Icon(ft.Icons.EMOJI_EVENTS, color=GOLD, size=14*scale),
                ft.Text("Top 5 Alunos", color=GOLD, size=12*scale, weight="bold")]),
            *rank_ctrl,
        ])

        painel_cinza = ft.Container(width=CINZA_W*scale, height=CINZA_H*scale,
            border_radius=20*scale, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            padding=ft.padding.symmetric(horizontal=16*scale, vertical=12*scale), content=col)
        montar_layout(page, scale, img_w, img_h, painel_verde, painel_cinza)

    page.on_resize = lambda e: build()
    build()


def testar_atividade(page, navegar, nome_atividade, menu_fn):
    from views import atividade_view
    _t = state.turma_atual; _a = state.alunos_ativos; _m = state.modo
    state.turma_atual = "TESTE"; state.alunos_ativos = ["Professor (teste)"]
    def nav_t(d):
        def _fn(e):
            state.turma_atual = _t; state.alunos_ativos = _a; state.modo = _m
            detalhe_atividade(page, navegar, nome_atividade, menu_fn)
        return _fn
    nd = dict(navegar); nd["menu_aluno"] = nav_t("m"); nd["login"] = nav_t("l")
    atividade_view.iniciar(page, nome_atividade, nd, modo_teste=True)


def liberar_atividade(page, navegar, nome, menu_fn):
    page.controls.clear(); page.padding = 0; page.bgcolor = "white"
    sel = {"turma": None, "tipo": None, "tempo": "10"}

    def build():
        page.controls.clear()
        W = page.width or IMG_W; H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W*scale; img_h = IMG_H*scale
        painel_verde = _nav_ativ(scale, page, navegar, menu_fn)
        status_msg = ft.Text("", size=10*scale)

        def _sel_turma(t):
            ativo = sel["turma"]==t
            def _s(e, tv=t): sel["turma"]=tv; build()
            return ft.Container(border_radius=8*scale,
                bgcolor=ORANGE_BG+"99" if ativo else "#0DFFFFFF",
                border=ft.border.all(1.5, ORANGE_BG) if ativo else ft.border.all(1, "#22FFFFFF"),
                padding=ft.padding.symmetric(horizontal=12*scale, vertical=8*scale),
                on_click=_s, ink=True,
                content=ft.Text(f"Turma {t}", color=WHITE, size=11*scale, weight="bold" if ativo else "normal"))

        def _sel_tipo(valor, label, desc):
            ativo = sel["tipo"]==valor
            def _s(e, v=valor): sel["tipo"]=v; build()
            return ft.Container(border_radius=10*scale, bgcolor=BLUE+"44" if ativo else "#0AFFFFFF",
                border=ft.border.all(1.5, BLUE) if ativo else ft.border.all(1, "#22FFFFFF"),
                padding=ft.padding.symmetric(horizontal=14*scale, vertical=10*scale),
                on_click=_s, ink=True,
                content=ft.Column(spacing=2*scale, controls=[
                    ft.Text(label, color=WHITE, size=11*scale, weight="bold"),
                    ft.Text(desc, color="#88FFFFFF", size=9*scale)]))

        tempo_f = ft.TextField(value=sel["tempo"], width=120*scale, label="Minutos",
            text_size=12*scale, label_style=ft.TextStyle(size=10*scale),
            border_color="#44FFFFFF", bgcolor="#0AFFFFFF", color=WHITE, border_radius=10*scale,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            keyboard_type=ft.KeyboardType.NUMBER, on_change=lambda e: sel.update({"tempo": e.control.value}))

        def confirmar(e):
            turma=sel["turma"]; tipo=sel["tipo"]
            if not turma or not tipo: status_msg.value="⚠️ Selecione turma e tipo."; status_msg.color="#FFAA00"; page.update(); return
            try:
                tm=int(sel["tempo"])
                if tm<=0: raise ValueError
            except ValueError: status_msg.value="⚠️ Tempo inválido."; status_msg.color=RED; page.update(); return
            ja=next((a for a in state.atividades_liberadas if a["turma"]==turma), None)
            if ja: status_msg.value=f"❌ Turma {turma} já tem: {ja['atividade']}."; status_msg.color=RED; page.update(); return
            from datetime import datetime, timedelta
            agora=datetime.now(); expira=agora+timedelta(seconds=tm*60+300)
            nova_lib={"atividade":nome,"turma":turma,"tipo":tipo,"tempo_maximo":tm*60,
                "expira_em":expira.isoformat()}
            lib_id=registrar_liberacao({**nova_lib,"liberado_em":agora.isoformat()})
            nova_lib["_lib_id"]=lib_id
            state.atividades_liberadas.append(nova_lib)
            salvar_liberadas(state.atividades_liberadas)
            detalhe_atividade(page, navegar, nome, menu_fn)

        col = ft.Column(spacing=12*scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=8*scale, controls=[ft.Icon(ft.Icons.LOCK_OPEN, color=GREEN, size=18*scale),
                ft.Text(f"Liberar: {nome}", color=WHITE, size=15*scale, weight="bold")]),
            ft.Divider(color="#22FFFFFF", thickness=1),
            ft.Text("Selecione a turma:", color="#CCFFFFFF", size=11*scale, weight="bold"),
            ft.Row(spacing=6*scale, wrap=True, controls=[_sel_turma(t) for t in TURMAS]),
            ft.Container(height=4*scale),
            ft.Text("Tipo de atividade:", color="#CCFFFFFF", size=11*scale, weight="bold"),
            _sel_tipo("dia","Atividade do dia","Pontuação 100%"),
            _sel_tipo("anterior","Atividade anterior","Pontuação 75%"),
            _sel_tipo("antiga","Atividade antiga","Pontuação 50%"),
            ft.Container(height=4*scale),
            ft.Text("Tempo máximo:", color="#CCFFFFFF", size=11*scale, weight="bold"),
            tempo_f, ft.Container(height=6*scale), status_msg,
            ft.Container(border_radius=12*scale, bgcolor=GREEN, width=200*scale, height=42*scale,
                alignment=ft.Alignment(0,0), on_click=confirmar, ink=True,
                content=ft.Text("✅ Confirmar", color=WHITE, size=12*scale, weight="bold")),
        ])
        painel_cinza = ft.Container(width=CINZA_W*scale, height=CINZA_H*scale,
            border_radius=20*scale, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            padding=ft.padding.symmetric(horizontal=16*scale, vertical=12*scale), content=col)
        montar_layout(page, scale, img_w, img_h, painel_verde, painel_cinza)

    page.on_resize = lambda e: build()
    build()


def historico_atividade(page, navegar, nome_atividade, menu_fn):
    page.controls.clear(); page.padding = 0; page.bgcolor = "white"
    sel_turma = {"v": "Todas"}

    def build():
        page.controls.clear()
        W = page.width or IMG_W; H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W*scale; img_h = IMG_H*scale
        painel_verde = _nav_ativ(scale, page, navegar, menu_fn)

        turma = sel_turma["v"]
        dados = buscar_todos_resultados() if turma=="Todas" else buscar_resultados_por_turma(turma)
        regs = sorted([r for r in dados if r["atividade"]==nome_atividade], key=lambda r: r["id"], reverse=True)

        def _btn_t(t):
            ativo = sel_turma["v"]==t
            def _s(e, tv=t): sel_turma["v"]=tv; build()
            return ft.Container(border_radius=8*scale,
                bgcolor=ORANGE_BG+"99" if ativo else "#0DFFFFFF",
                border=ft.border.all(1.5, ORANGE_BG) if ativo else ft.border.all(1, "#22FFFFFF"),
                padding=ft.padding.symmetric(horizontal=10*scale, vertical=6*scale),
                on_click=_s, ink=True,
                content=ft.Text(t, color=WHITE, size=10*scale, weight="bold" if ativo else "normal"))

        TL = {"dia":"do dia","anterior":"anterior","antiga":"antiga"}

        def _ver_detalhes_ativ(e, rid, ativ, aluno):
            det = buscar_detalhes_questoes(rid)
            if not det: return
            ld = []
            for q in det:
                cs = "#4CAF50" if q["acertou"] else "#FF5252"
                ic = "✅" if q["acertou"] else "❌"
                ld.append(ft.Container(border_radius=8, bgcolor="#F8F8F8" if q["acertou"] else "#FFF5F5",
                    border=ft.border.all(1, "#E0E0E0"),
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                    content=ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        ft.Text(f"Q{q['numero']}", size=13, weight="bold", color="#666666", width=35),
                        ft.Column(spacing=2, expand=True, controls=[
                            ft.Text(q["pergunta"], size=13, weight="bold", color="#333333"),
                            ft.Row(spacing=16, controls=[
                                ft.Text(f"Resposta: {q['resposta_aluno']}", size=12, color=cs, weight="bold"),
                                ft.Text(f"Correta: {q['resposta_correta']}", size=12, color="#888888")])]),
                        ft.Text(f"{q['tentativas']}x", size=12, color="#AAAAAA"),
                        ft.Text(ic, size=18)])))
            acd = sum(1 for q in det if q["acertou"]); erd = sum(1 for q in det if not q["acertou"])
            dlg = ft.AlertDialog(
                title=ft.Text(f"📋 {ativ} — {aluno}", size=18, weight="bold"),
                content=ft.Container(width=800, height=500,
                    content=ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, controls=[
                        ft.Row(spacing=12, alignment=ft.MainAxisAlignment.CENTER, controls=[
                            ft.Container(border_radius=8, bgcolor="#E8F5E9", padding=ft.padding.all(8),
                                content=ft.Text(f"✅ {acd} acertos", size=13, weight="bold", color="#4CAF50")),
                            ft.Container(border_radius=8, bgcolor="#FFEBEE", padding=ft.padding.all(8),
                                content=ft.Text(f"❌ {erd} erros", size=13, weight="bold", color="#FF5252")),
                            ft.Container(border_radius=8, bgcolor="#E3F2FD", padding=ft.padding.all(8),
                                content=ft.Text(f"📝 {len(det)} questões", size=13, weight="bold", color="#2F9EDC"))]
                        ), ft.Divider(), *ld])))
            def _fechar(ev): dlg.open = False; page.update()
            dlg.actions = [ft.TextButton("Fechar", on_click=_fechar)]
            page.overlay.append(dlg); dlg.open = True; page.update()

        linhas = []
        for r in regs[:30]:
            tipo = TL.get(r.get("tipo_atividade","dia"),"")
            tem_det = len(buscar_detalhes_questoes(r["id"])) > 0
            eye_btn = ft.Container(
                width=28*scale, height=28*scale, border_radius=14*scale,
                bgcolor=BLUE+"33" if tem_det else "#0AFFFFFF",
                alignment=ft.Alignment(0, 0),
                on_click=(lambda e, rid=r["id"], av=r["atividade"], al=r["aluno"]: _ver_detalhes_ativ(e, rid, av, al)) if tem_det else None,
                ink=tem_det,
                content=ft.Icon(ft.Icons.VISIBILITY, color=BLUE if tem_det else "#33FFFFFF", size=14*scale),
            )
            linhas.append(ft.Container(border_radius=8*scale, bgcolor="#0AFFFFFF",
                padding=ft.padding.symmetric(horizontal=10*scale, vertical=6*scale),
                content=ft.Row(spacing=6*scale, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Column(spacing=1, expand=True, controls=[
                        ft.Row(spacing=6*scale, controls=[
                            ft.Text(r["aluno"], color=WHITE, size=10*scale, weight="bold"),
                            ft.Text(f"T{r['turma']}", color="#77FFFFFF", size=8*scale) if turma=="Todas" else ft.Container()]),
                        ft.Text(f"{tipo}  •  ⏱{r['tempo']}  •  {r['data']}", color="#66FFFFFF", size=8*scale)]),
                    eye_btn,
                    ft.Text(f"✅{r['acertos']} ❌{r['erros']}", color="#88FFFFFF", size=9*scale),
                    ft.Text(f"{r['pontuacao']} pts", color=GOLD, size=11*scale, weight="bold")])))
        if not linhas: linhas.append(ft.Text("Nenhum resultado.", color="#66FFFFFF", size=11*scale))
        tl = f"Turma {turma}" if turma!="Todas" else "Todas as turmas"

        col = ft.Column(spacing=10*scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=8*scale, controls=[ft.Icon(ft.Icons.HISTORY, color=BLUE, size=16*scale),
                ft.Text(f"Histórico — {nome_atividade}", color=WHITE, size=14*scale, weight="bold")]),
            ft.Row(spacing=6*scale, wrap=True, controls=[_btn_t("Todas"), *[_btn_t(t) for t in TURMAS]]),
            ft.Divider(color="#22FFFFFF", thickness=1),
            ft.Text(f"{len(regs)} resultado(s) — {tl}", color="#AAFFFFFF", size=10*scale),
            *linhas])
        painel_cinza = ft.Container(width=CINZA_W*scale, height=CINZA_H*scale,
            border_radius=20*scale, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            padding=ft.padding.symmetric(horizontal=16*scale, vertical=12*scale), content=col)
        montar_layout(page, scale, img_w, img_h, painel_verde, painel_cinza)

    page.on_resize = lambda e: build()
    build()


def ranking_atividade(page, navegar, nome_atividade, menu_fn):
    page.controls.clear(); page.padding = 0; page.bgcolor = "white"
    sel_turma = {"v": "Todas"}

    def build():
        page.controls.clear()
        W = page.width or IMG_W; H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W*scale; img_h = IMG_H*scale
        painel_verde = _nav_ativ(scale, page, navegar, menu_fn)

        turma = sel_turma["v"]
        todos = buscar_todos_resultados()
        dados = todos if turma=="Todas" else [r for r in todos if r["turma"]==turma]
        regs = [r for r in dados if r["atividade"]==nome_atividade]
        melhor = {}; turma_de = {}
        for r in regs:
            if r["aluno"] not in melhor or r["pontuacao"]>melhor[r["aluno"]]: melhor[r["aluno"]]=r["pontuacao"]
            turma_de[r["aluno"]]=r["turma"]
        rank = sorted(melhor.items(), key=lambda x: x[1], reverse=True)

        def _btn_t(t):
            ativo = sel_turma["v"]==t
            def _s(e, tv=t): sel_turma["v"]=tv; build()
            return ft.Container(border_radius=8*scale,
                bgcolor=BLUE+"88" if ativo else "#0AFFFFFF",
                border=ft.border.all(1, BLUE) if ativo else ft.border.all(1, "#22FFFFFF"),
                padding=ft.padding.symmetric(horizontal=10*scale, vertical=5*scale),
                on_click=_s, ink=True,
                content=ft.Text(t, color=WHITE if ativo else "#AAFFFFFF", size=10*scale, weight="bold" if ativo else "normal"))

        PC = {1:GOLD, 2:"#C0C0C0", 3:"#CD7F32"}
        PB = {1:"#33F9A825", 2:"#22C0C0C0", 3:"#22CD7F32"}
        rows = []
        for i,(n,p) in enumerate(rank[:20], 1):
            c=PC.get(i,"#CCFFFFFF"); bg=PB.get(i,"#0AFFFFFF")
            rows.append(ft.Container(border_radius=10*scale, bgcolor=bg,
                border=ft.border.all(1, c+"55") if i<=3 else None,
                padding=ft.padding.symmetric(horizontal=10*scale, vertical=7*scale),
                content=ft.Row(spacing=8*scale, controls=[
                    ft.Container(width=28*scale, alignment=ft.Alignment(0,0),
                        content=ft.Text(MEDALS.get(i, f"{i}º"), size=14*scale if i<=3 else 11*scale, weight="bold")),
                    ft.Column(spacing=1, controls=[
                        ft.Text(n, color=c if i<=3 else WHITE, size=13*scale if i<=3 else 11*scale, weight="bold"),
                        ft.Text(f"Turma {turma_de.get(n,'—')}", color="#88FFFFFF", size=8*scale)]),
                    ft.Container(border_radius=8*scale, bgcolor=c+"22",
                        padding=ft.padding.symmetric(horizontal=8*scale, vertical=3*scale),
                        content=ft.Text(f"{p} pts", color=c if i<=3 else GOLD, size=12*scale, weight="bold"))])))
        if not rows: rows.append(ft.Text("Nenhum resultado.", color="#66FFFFFF", size=11*scale))

        col = ft.Column(spacing=10*scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=8*scale, controls=[ft.Icon(ft.Icons.LEADERBOARD, color=GOLD, size=16*scale),
                ft.Text(f"Ranking — {nome_atividade}", color=WHITE, size=14*scale, weight="bold")]),
            ft.Row(spacing=6*scale, wrap=True, controls=[_btn_t("Todas"), *[_btn_t(t) for t in TURMAS]]),
            ft.Divider(color="#22FFFFFF", thickness=1), *rows])
        painel_cinza = ft.Container(width=CINZA_W*scale, height=CINZA_H*scale,
            border_radius=20*scale, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            padding=ft.padding.symmetric(horizontal=16*scale, vertical=12*scale), content=col)
        montar_layout(page, scale, img_w, img_h, painel_verde, painel_cinza)

    page.on_resize = lambda e: build()
    build()