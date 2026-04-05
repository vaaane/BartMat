"""
views/professor_telas.py — Ranking, Acompanhamento, Relatório, Histórico Geral.
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import flet as ft
import state
from constants import LABEL_TIPO, LISTA_ATIVIDADES, ALUNOS_POR_TURMA
from controllers.historico_controller import (
    buscar_todos_resultados, buscar_resultados_por_turma, buscar_detalhes_questoes,
    buscar_conquistas, buscar_liberacoes,
)
from views.professor_helpers import (
    BLUE, ORANGE_BG, WHITE, GREEN, RED, GOLD, IMG_W, IMG_H,
    TURMAS, MEDALS, CINZA_W, CINZA_H,
    btn_menu, stat_card, painel_nav_prof, montar_layout,
)
from views.professor_atividades import tela_atividades


# ============================================================
#  RANKING GERAL — rows at half-width, balanced spacing
# ============================================================

def tela_ranking(page, navegar, menu_fn):
    page.controls.clear(); page.padding = 0; page.bgcolor = "white"
    turma_sel = {"v": "Todas"}

    def build():
        page.controls.clear()
        W = page.width or IMG_W; H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W*scale; img_h = IMG_H*scale
        def _inicio(e): menu_fn(page, navegar)
        def _ativ(e):   tela_atividades(page, navegar, menu_fn)
        def _rank(e):   tela_ranking(page, navegar, menu_fn)
        def _acomp(e):  tela_acompanhamento(page, navegar, menu_fn)
        def _rel(e):    tela_relatorio_turma(page, navegar, menu_fn)
        def _hist(e):   tela_historico_geral(page, navegar, menu_fn)
        def _sair(e):   navegar["login"]()
        pv = painel_nav_prof(scale, _inicio, _ativ, _rank, _acomp, _rel, _hist, _sair)

        turma = turma_sel["v"]
        todos = buscar_todos_resultados()
        dados = todos if turma=="Todas" else [r for r in todos if r["turma"]==turma]
        pts_a={}; turma_a={}; ac_a={}; at_a={}
        for r in dados:
            a=r["aluno"]; pts_a[a]=pts_a.get(a,0)+r["pontuacao"]; turma_a[a]=r["turma"]
            ac_a[a]=ac_a.get(a,0)+r["acertos"]; at_a.setdefault(a,set()).add(r["atividade"])
        rank = sorted(pts_a.items(), key=lambda x: x[1], reverse=True)
        PC={1:GOLD,2:"#C0C0C0",3:"#CD7F32"}; PB={1:"#33F9A825",2:"#22C0C0C0",3:"#22CD7F32"}

        def _row(i, nome, pts):
            c=PC.get(i,"#CCFFFFFF"); bg=PB.get(i,"#0AFFFFFF")
            ac=ac_a.get(nome,0); at=len(at_a.get(nome,set()))
            return ft.Container(
                border_radius=10*scale, bgcolor=bg,
                border=ft.border.all(1, c+"55") if i<=3 else None,
                padding=ft.padding.symmetric(horizontal=10*scale, vertical=7*scale),
                content=ft.Row(spacing=10*scale, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Container(width=28*scale, alignment=ft.Alignment(0,0),
                        content=ft.Text(MEDALS.get(i, f"{i}º"), size=14*scale if i<=3 else 11*scale, weight="bold")),
                    ft.Column(spacing=1, expand=True, controls=[
                        ft.Text(nome, color=c if i<=3 else WHITE, size=11*scale, weight="bold"),
                        ft.Text(f"Turma {turma_a.get(nome,'—')}", color="#88FFFFFF", size=8*scale)]),
                    ft.Text(f"{at} ativ.", color=BLUE, size=9*scale),
                    ft.Text(f"{ac} acertos", color=GREEN, size=9*scale),
                    ft.Container(border_radius=8*scale, bgcolor=c+"22",
                        padding=ft.padding.symmetric(horizontal=8*scale, vertical=3*scale),
                        content=ft.Text(f"{pts} pts", color=c if i<=3 else GOLD, size=12*scale, weight="bold")),
                ]),
            )

        rc = [_row(i,n,p) for i,(n,p) in enumerate(rank[:25],1)]
        if not rc: rc.append(ft.Container(border_radius=12*scale, bgcolor="#0AFFFFFF", padding=ft.padding.all(20*scale),
            content=ft.Column(spacing=6*scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Icon(ft.Icons.LEADERBOARD, color="#44FFFFFF", size=36*scale),
                ft.Text("Nenhum resultado.", color="#66FFFFFF", size=12*scale)])))

        def _bt(t):
            sel = turma_sel["v"]==t
            def _s(e, tv=t): turma_sel["v"]=tv; build()
            return ft.Container(border_radius=8*scale, bgcolor=BLUE+"88" if sel else "#0AFFFFFF",
                border=ft.border.all(1, BLUE) if sel else ft.border.all(1, "#22FFFFFF"),
                padding=ft.padding.symmetric(horizontal=10*scale, vertical=5*scale),
                on_click=_s, ink=True,
                content=ft.Text(t, color=WHITE if sel else "#AAFFFFFF", size=10*scale, weight="bold" if sel else "normal"))

        n_a=len(rank); top_p=rank[0][1] if rank else 0; med=round(sum(p for _,p in rank)/n_a) if n_a else 0
        col = ft.Column(spacing=10*scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=8*scale, controls=[ft.Icon(ft.Icons.LEADERBOARD, color=GOLD, size=20*scale),
                ft.Text("Ranking Geral", color=WHITE, size=16*scale, weight="bold")]),
            ft.Row(spacing=6*scale, wrap=True, controls=[_bt("Todas"),*[_bt(t) for t in TURMAS]]),
            ft.Row(spacing=8*scale, controls=[stat_card("Alunos",str(n_a),BLUE,scale),
                stat_card("Top pts",str(top_p),GOLD,scale), stat_card("Média",str(med),GREEN,scale)]),
            ft.Container(height=2*scale), *rc])

        pc = ft.Container(width=CINZA_W*scale, height=CINZA_H*scale,
            border_radius=20*scale, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            padding=ft.padding.symmetric(horizontal=16*scale, vertical=12*scale), content=col)
        montar_layout(page, scale, img_w, img_h, pv, pc)

    page.on_resize = lambda e: build()
    build()


# ============================================================
#  ACOMPANHAMENTO INDIVIDUAL
# ============================================================

def tela_acompanhamento(page, navegar, menu_fn):
    page.controls.clear(); page.padding = 0; page.bgcolor = "white"
    sel = {"turma": None, "aluno": None}

    def build():
        page.controls.clear()
        W = page.width or IMG_W; H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W*scale; img_h = IMG_H*scale
        def _inicio(e): menu_fn(page, navegar)
        def _ativ(e):   tela_atividades(page, navegar, menu_fn)
        def _rank(e):   tela_ranking(page, navegar, menu_fn)
        def _acomp(e):  tela_acompanhamento(page, navegar, menu_fn)
        def _rel(e):    tela_relatorio_turma(page, navegar, menu_fn)
        def _hist(e):   tela_historico_geral(page, navegar, menu_fn)
        def _sair(e):   navegar["login"]()
        pv = painel_nav_prof(scale, _inicio, _ativ, _rank, _acomp, _rel, _hist, _sair)
        dados = buscar_todos_resultados()
        ts = sel["turma"]; als = sel["aluno"]

        def _bt(t):
            a = ts==t
            def _s(e, tv=t): sel["turma"]=tv; sel["aluno"]=None; build()
            return ft.Container(border_radius=10*scale, bgcolor=ORANGE_BG+"99" if a else "#0DFFFFFF",
                border=ft.border.all(1.5, ORANGE_BG) if a else ft.border.all(1, "#22FFFFFF"),
                padding=ft.padding.symmetric(horizontal=12*scale, vertical=8*scale), on_click=_s, ink=True,
                content=ft.Row(spacing=8*scale, controls=[
                    ft.Icon(ft.Icons.GROUPS, color=WHITE if a else "#88FFFFFF", size=14*scale),
                    ft.Text(f"Turma {t}", color=WHITE if a else "#AAFFFFFF", size=11*scale, weight="bold" if a else "normal"),
                    ft.Container(expand=True),
                    ft.Text(str(len(ALUNOS_POR_TURMA.get(t,[]))), color=ORANGE_BG if a else "#66FFFFFF", size=10*scale, weight="bold")]))

        def _ba(al):
            a = als==al
            regs = [r for r in dados if r["aluno"]==al and r["turma"]==ts]
            pts = sum(r["pontuacao"] for r in regs)
            def _s(e, av=al): sel["aluno"]=av; build()
            return ft.Container(border_radius=8*scale, bgcolor=BLUE+"88" if a else "#0AFFFFFF",
                border=ft.border.all(1, BLUE) if a else None,
                padding=ft.padding.symmetric(horizontal=10*scale, vertical=6*scale), on_click=_s, ink=True,
                content=ft.Row(spacing=6*scale, controls=[
                    ft.Icon(ft.Icons.PERSON, color=WHITE if a else "#88FFFFFF", size=12*scale),
                    ft.Text(al, color=WHITE if a else "#CCFFFFFF", size=10*scale, weight="bold" if a else "normal", expand=True),
                    ft.Text(f"{pts}pts" if regs else "—", color=GOLD if pts else "#44FFFFFF", size=9*scale)]))

        col_sel = ft.Column(spacing=8*scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=6*scale, controls=[ft.Icon(ft.Icons.PEOPLE, color=ORANGE_BG, size=16*scale),
                ft.Text("Turmas", color=WHITE, size=13*scale, weight="bold")]),
            *[_bt(t) for t in TURMAS],
            *([ft.Divider(color="#22FFFFFF", thickness=1),
               ft.Row(spacing=6*scale, controls=[ft.Icon(ft.Icons.PERSON_SEARCH, color=BLUE, size=16*scale),
                   ft.Text(f"Alunos — Turma {ts}", color=WHITE, size=13*scale, weight="bold")]),
               *[_ba(al) for al in ALUNOS_POR_TURMA.get(ts,[])]] if ts else [])])

        if als:
            regs = [r for r in dados if r["aluno"]==als and r["turma"]==ts]
            tot_pts = sum(r["pontuacao"] for r in regs)
            tot_ac = sum(r["acertos"] for r in regs); tot_er = sum(r["erros"] for r in regs)
            feitas = len(set(r["atividade"] for r in regs)); tot_at = len(LISTA_ATIVIDADES)
            pg={}
            for r in dados: pg[r["aluno"]]=pg.get(r["aluno"],0)+r["pontuacao"]
            rg = sorted(pg.items(), key=lambda x: x[1], reverse=True)
            pos_g = next((i for i,(n,_) in enumerate(rg,1) if n==als), None)
            pt={}
            for r in dados:
                if r["turma"]==ts: pt[r["aluno"]]=pt.get(r["aluno"],0)+r["pontuacao"]
            rt = sorted(pt.items(), key=lambda x: x[1], reverse=True)
            pos_t = next((i for i,(n,_) in enumerate(rt,1) if n==als), None)
            mg = MEDALS.get(pos_g, f"{pos_g}º") if pos_g else "—"
            mt = MEDALS.get(pos_t, f"{pos_t}º") if pos_t else "—"

            hc = []
            for a in LISTA_ATIVIDADES:
                na = a["nome"]; ra = [r for r in regs if r["atividade"]==na]
                ca = {"Atividade 1 - Frações":BLUE,"Atividade 2 - Equações":GREEN,"Atividade 3 - Geometria":ORANGE_BG}.get(na,BLUE)
                ln = na.split(" - ")[1] if " - " in na else na
                if ra:
                    m = max(ra, key=lambda r: r["pontuacao"])
                    def _acomp_ver(e, rid=m["id"], av=na, al=als):
                        det=buscar_detalhes_questoes(rid)
                        if not det: return
                        ld=[]
                        for q in det:
                            cs="#4CAF50" if q["acertou"] else "#FF5252"; ic="✅" if q["acertou"] else "❌"
                            ld.append(ft.Container(border_radius=8,bgcolor="#F8F8F8" if q["acertou"] else "#FFF5F5",
                                border=ft.border.all(1,"#E0E0E0"),
                                padding=ft.padding.symmetric(horizontal=14,vertical=10),
                                content=ft.Row(spacing=12,vertical_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                                    ft.Text(f"Q{q['numero']}",size=13,weight="bold",color="#666666",width=35),
                                    ft.Column(spacing=2,expand=True,controls=[
                                        ft.Text(q["pergunta"],size=13,weight="bold",color="#333333"),
                                        ft.Row(spacing=16,controls=[
                                            ft.Text(f"Resp: {q['resposta_aluno']}",size=12,color=cs,weight="bold"),
                                            ft.Text(f"Correta: {q['resposta_correta']}",size=12,color="#888888")])]),
                                    ft.Text(f"{q['tentativas']}x",size=12,color="#AAAAAA"),
                                    ft.Text(ic,size=18)])))
                        acd=sum(1 for q in det if q["acertou"]); erd=sum(1 for q in det if not q["acertou"])
                        dlg=ft.AlertDialog(title=ft.Text(f"📋 {av.split(' - ')[-1]} — {al}",size=16,weight="bold"),
                            content=ft.Container(width=700,height=460,
                                content=ft.Column(spacing=10,scroll=ft.ScrollMode.AUTO,controls=[
                                    ft.Row(spacing=10,alignment=ft.MainAxisAlignment.CENTER,controls=[
                                        ft.Container(border_radius=8,bgcolor="#E8F5E9",padding=ft.padding.all(8),
                                            content=ft.Text(f"✅ {acd} acertos",size=13,weight="bold",color="#4CAF50")),
                                        ft.Container(border_radius=8,bgcolor="#FFEBEE",padding=ft.padding.all(8),
                                            content=ft.Text(f"❌ {erd} erros",size=13,weight="bold",color="#FF5252"))]),
                                    ft.Divider(),*ld])))
                        def _fc(ev): dlg.open=False; page.update()
                        dlg.actions=[ft.TextButton("Fechar",on_click=_fc)]
                        page.overlay.append(dlg); dlg.open=True; page.update()
                    hc.append(ft.Container(border_radius=10*scale, bgcolor="#0DFFFFFF", border=ft.border.all(1, ca+"55"),
                        padding=ft.padding.symmetric(horizontal=12*scale, vertical=8*scale),
                        content=ft.Row(spacing=10*scale, controls=[
                            ft.Container(width=32*scale, height=32*scale, border_radius=8*scale, bgcolor=ca+"33",
                                alignment=ft.Alignment(0,0), content=ft.Icon(ft.Icons.MENU_BOOK, color=ca, size=16*scale)),
                            ft.Column(spacing=1, expand=True, controls=[
                                ft.Text(ln, color=WHITE, size=10*scale, weight="bold"),
                                ft.Text(f"{len(ra)} tentativa(s)", color="#88FFFFFF", size=8*scale)]),
                            ft.Container(width=28*scale,height=28*scale,border_radius=14*scale,
                                bgcolor=BLUE+"33",alignment=ft.Alignment(0,0),
                                on_click=_acomp_ver,ink=True,
                                content=ft.Icon(ft.Icons.VISIBILITY,color=BLUE,size=14*scale)),
                            ft.Column(spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END, controls=[
                                ft.Text(f"{m['pontuacao']} pts", color=GOLD, size=12*scale, weight="bold"),
                                ft.Text(f"✅{m['acertos']} ❌{m['erros']}  ⏱{m['tempo']}", color="#88FFFFFF", size=8*scale)])])))
                else:
                    hc.append(ft.Container(border_radius=10*scale, bgcolor="#06FFFFFF",
                        padding=ft.padding.symmetric(horizontal=12*scale, vertical=8*scale),
                        content=ft.Row(spacing=10*scale, controls=[
                            ft.Container(width=32*scale, height=32*scale, border_radius=8*scale, bgcolor="#0AFFFFFF",
                                alignment=ft.Alignment(0,0), content=ft.Icon(ft.Icons.LOCK_OUTLINE, color="#44FFFFFF", size=16*scale)),
                            ft.Text(ln, color="#55FFFFFF", size=10*scale), ft.Container(expand=True),
                            ft.Text("Não realizada", color="#33FFFFFF", size=9*scale)])))

            col_d = ft.Column(spacing=10*scale, scroll=ft.ScrollMode.AUTO, controls=[
                ft.Row(spacing=8*scale, controls=[ft.Icon(ft.Icons.PERSON, color=BLUE, size=18*scale),
                    ft.Column(spacing=1, controls=[ft.Text(als, color=WHITE, size=15*scale, weight="bold"),
                        ft.Text(f"Turma {ts}", color="#88FFFFFF", size=10*scale)])]),
                ft.Row(spacing=8*scale, controls=[stat_card("Pontos",str(tot_pts),GOLD,scale),
                    stat_card("Atividades",f"{feitas}/{tot_at}",BLUE,scale),
                    stat_card("Acertos",str(tot_ac),GREEN,scale), stat_card("Erros",str(tot_er),RED,scale)]),
                ft.Container(border_radius=10*scale, bgcolor="#22FFD700", border=ft.border.all(1, GOLD),
                    padding=ft.padding.symmetric(horizontal=12*scale, vertical=8*scale),
                    content=ft.Row(spacing=16*scale, alignment=ft.MainAxisAlignment.CENTER, controls=[
                        ft.Column(spacing=2*scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text("🌍 Geral", color="#AAFFFFFF", size=9*scale), ft.Text(mg, size=18*scale),
                            ft.Text(f"de {len(rg)}", color="#77FFFFFF", size=8*scale)]),
                        ft.Container(width=1, height=40*scale, bgcolor="#33FFFFFF"),
                        ft.Column(spacing=2*scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text(f"🏫 Turma {ts}", color="#AAFFFFFF", size=9*scale), ft.Text(mt, size=18*scale),
                            ft.Text(f"de {len(rt)}", color="#77FFFFFF", size=8*scale)])])),
                ft.Divider(color="#22FFFFFF", thickness=1),
                ft.Row(spacing=6*scale, controls=[ft.Icon(ft.Icons.HISTORY, color=BLUE, size=14*scale),
                    ft.Text("Histórico de Atividades", color=WHITE, size=12*scale, weight="bold")]),
                *hc])
        else:
            col_d = ft.Column(spacing=10*scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Container(height=60*scale), ft.Icon(ft.Icons.PERSON_SEARCH, color="#33FFFFFF", size=48*scale),
                ft.Text("Selecione uma turma\ne depois um aluno" if ts else "Selecione uma turma",
                    color="#55FFFFFF", size=13*scale, text_align="center")])

        pc = ft.Container(width=CINZA_W*scale, height=CINZA_H*scale,
            border_radius=20*scale, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            padding=ft.padding.symmetric(horizontal=16*scale, vertical=12*scale),
            content=ft.Row(spacing=14*scale, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
                ft.Container(expand=2, content=col_sel),
                ft.Container(width=1, height=(CINZA_H-40)*scale, bgcolor="#15FFFFFF"),
                ft.Container(expand=3, content=col_d)]))
        montar_layout(page, scale, img_w, img_h, pv, pc)

    page.on_resize = lambda e: build()
    build()


# ============================================================
#  RELATÓRIO DE TURMA — all students ranked, ausentes = who missed any released activity
# ============================================================

def tela_relatorio_turma(page, navegar, menu_fn):
    page.controls.clear(); page.padding = 0; page.bgcolor = "white"
    sel = {"turma": TURMAS[0] if TURMAS else None}

    def build():
        page.controls.clear()
        W = page.width or IMG_W; H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W*scale; img_h = IMG_H*scale
        def _inicio(e): menu_fn(page, navegar)
        def _ativ(e):   tela_atividades(page, navegar, menu_fn)
        def _rank(e):   tela_ranking(page, navegar, menu_fn)
        def _acomp(e):  tela_acompanhamento(page, navegar, menu_fn)
        def _rel(e):    tela_relatorio_turma(page, navegar, menu_fn)
        def _hist(e):   tela_historico_geral(page, navegar, menu_fn)
        def _sair(e):   navegar["login"]()
        pv = painel_nav_prof(scale, _inicio, _ativ, _rank, _acomp, _rel, _hist, _sair)

        dados = buscar_todos_resultados()
        turma = sel["turma"]

        def _bt(t):
            a = sel["turma"]==t
            def _s(e, tv=t): sel["turma"]=tv; build()
            return ft.Container(border_radius=8*scale, bgcolor=ORANGE_BG+"99" if a else "#0DFFFFFF",
                border=ft.border.all(1.5, ORANGE_BG) if a else ft.border.all(1, "#22FFFFFF"),
                padding=ft.padding.symmetric(horizontal=12*scale, vertical=6*scale), on_click=_s, ink=True,
                content=ft.Text(f"Turma {t}", color=WHITE, size=10*scale, weight="bold" if a else "normal"))

        regs = [r for r in dados if r["turma"]==turma]
        al_turma = ALUNOS_POR_TURMA.get(turma, [])
        n_al = len(al_turma)
        al_part = set(r["aluno"] for r in regs)
        particip = len(al_part)
        tot_pts = sum(r["pontuacao"] for r in regs)
        tot_ac = sum(r["acertos"] for r in regs)
        med = round(tot_pts/len(regs)) if regs else 0
        tot_at = len(LISTA_ATIVIDADES)
        at_feitas = len(set(r["atividade"] for r in regs))

        stats = ft.Row(spacing=8*scale, controls=[
            stat_card("Participação", f"{particip}/{n_al}", ORANGE_BG, scale),
            stat_card("Atividades", f"{at_feitas}/{tot_at}", BLUE, scale),
            stat_card("Média pts", str(med), GOLD, scale),
            stat_card("Acertos", str(tot_ac), GREEN, scale)])

        # ALL students ranked by points, top 3 highlighted
        pts_al = {}
        for r in regs: pts_al[r["aluno"]] = pts_al.get(r["aluno"],0)+r["pontuacao"]
        # Include students with 0 pts
        for a in al_turma:
            if a not in pts_al: pts_al[a] = 0
        rank = sorted(pts_al.items(), key=lambda x: x[1], reverse=True)

        PC = {1:GOLD, 2:"#C0C0C0", 3:"#CD7F32"}
        PB = {1:"#33F9A825", 2:"#22C0C0C0", 3:"#22CD7F32"}
        rank_rows = []
        for i,(nome,pts) in enumerate(rank, 1):
            c = PC.get(i, "#CCFFFFFF"); bg = PB.get(i, "#0AFFFFFF")
            rank_rows.append(ft.Container(
                border_radius=8*scale, bgcolor=bg,
                border=ft.border.all(1, c+"55") if i<=3 else None,
                padding=ft.padding.symmetric(horizontal=8*scale, vertical=5*scale),
                content=ft.Row(spacing=6*scale, controls=[
                    ft.Container(width=24*scale, alignment=ft.Alignment(0,0),
                        content=ft.Text(MEDALS.get(i, f"{i}º"), size=12*scale if i<=3 else 10*scale, weight="bold")),
                    ft.Text(nome, color=c if i<=3 else WHITE,
                        size=11*scale if i<=3 else 10*scale, weight="bold" if i<=3 else "normal", expand=True),
                    ft.Text(f"{pts} pts", color=c if i<=3 else GOLD, size=10*scale, weight="bold")])))

        # Desempenho por atividade
        ativ_bars = []
        for a in LISTA_ATIVIDADES:
            na = a["nome"]; ra = [r for r in regs if r["atividade"]==na]
            af = len(set(r["aluno"] for r in ra))
            ma = round(sum(r["pontuacao"] for r in ra)/len(ra)) if ra else 0
            pct = min(af/n_al, 1.0) if n_al else 0
            ca = {"Atividade 1 - Frações":BLUE,"Atividade 2 - Equações":GREEN,"Atividade 3 - Geometria":ORANGE_BG}.get(na,BLUE)
            lb = na.split(" - ")[1] if " - " in na else na
            bw = 300*scale
            ativ_bars.append(ft.Container(border_radius=10*scale, bgcolor="#0AFFFFFF",
                padding=ft.padding.symmetric(horizontal=12*scale, vertical=8*scale),
                content=ft.Column(spacing=6*scale, controls=[
                    ft.Row(spacing=8*scale, controls=[
                        ft.Text(lb, color=WHITE, size=10*scale, weight="bold", expand=True),
                        ft.Text(f"{af}/{n_al} alunos", color="#88FFFFFF", size=8*scale),
                        ft.Text(f"Média {ma} pts", color=GOLD, size=9*scale, weight="bold")]),
                    ft.Stack(width=bw, height=8*scale, controls=[
                        ft.Container(width=bw, height=8*scale, border_radius=4*scale, bgcolor="#1AFFFFFF"),
                        ft.Container(width=bw*pct, height=8*scale, border_radius=4*scale, bgcolor=ca)])])))

        # Ausentes: students who missed ANY activity that was already done by this turma
        atividades_da_turma = set(r["atividade"] for r in regs)
        ausentes_ctrl = []
        ausentes_info = []
        for aluno in al_turma:
            ativs_feitas_aluno = set(r["atividade"] for r in regs if r["aluno"]==aluno)
            faltantes = atividades_da_turma - ativs_feitas_aluno
            if faltantes:
                falt_labels = [f.split(" - ")[1] if " - " in f else f for f in sorted(faltantes)]
                ausentes_info.append((aluno, falt_labels))

        if ausentes_info:
            ausentes_ctrl.append(ft.Text(f"{len(ausentes_info)} aluno(s) com atividades pendentes:",
                color="#AAFFFFFF", size=9*scale))
            for aluno, falt in ausentes_info:
                ausentes_ctrl.append(ft.Container(
                    border_radius=6*scale, bgcolor="#1AFF5252",
                    padding=ft.padding.symmetric(horizontal=8*scale, vertical=4*scale),
                    content=ft.Column(spacing=2*scale, controls=[
                        ft.Row(spacing=4*scale, controls=[
                            ft.Icon(ft.Icons.PERSON_OFF, color=RED, size=11*scale),
                            ft.Text(aluno, color="#CCFFFFFF", size=9*scale, weight="bold")]),
                        ft.Text(f"Falta: {', '.join(falt)}", color="#88FFFFFF", size=8*scale)])))
        else:
            ausentes_ctrl.append(ft.Text("✅ Todos realizaram todas as atividades!", color=GREEN, size=10*scale, weight="bold"))

        def exportar_csv(e):
            import csv, os as _os
            from datetime import datetime as _dt
            desktop=_os.path.join(_os.path.expanduser("~"),"Desktop")
            fname=f"relatorio_turma{turma}_{_dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
            fpath=_os.path.join(desktop,fname)
            try:
                with open(fpath,"w",newline="",encoding="utf-8-sig") as f:
                    w=csv.DictWriter(f,fieldnames=["aluno","turma","atividade","pontuacao_bruta","pontuacao","tipo_atividade","acertos","erros","tempo","data"])
                    w.writeheader()
                    for r in regs: w.writerow({k:r.get(k,"") for k in w.fieldnames})
                import os as _os2; _os2.startfile(fpath)
                page.snack_bar=ft.SnackBar(ft.Text(f"✅ Exportado: {fname}"),open=True)
            except Exception as ex:
                page.snack_bar=ft.SnackBar(ft.Text(f"❌ Erro: {ex}"),open=True)
            page.update()

        col_esq = ft.Column(spacing=10*scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=6*scale, controls=[
                ft.Icon(ft.Icons.ASSESSMENT, color=ORANGE_BG, size=16*scale),
                ft.Text(f"Relatório — Turma {turma}", color=WHITE, size=14*scale, weight="bold"),
                ft.Container(expand=True),
                ft.Container(border_radius=8*scale, bgcolor="#1A2F9EDC",
                    padding=ft.padding.symmetric(horizontal=10*scale, vertical=4*scale),
                    on_click=exportar_csv, ink=True,
                    content=ft.Row(spacing=4*scale, controls=[
                        ft.Icon(ft.Icons.DOWNLOAD, color=BLUE, size=12*scale),
                        ft.Text("CSV", color=BLUE, size=10*scale, weight="bold")])),
            ]),
            ft.Row(spacing=6*scale, controls=[_bt(t) for t in TURMAS]),
            stats,
            ft.Divider(color="#22FFFFFF", thickness=1),
            ft.Row(spacing=6*scale, controls=[ft.Icon(ft.Icons.EMOJI_EVENTS, color=GOLD, size=14*scale),
                ft.Text("Todos os Alunos (por pontuação)", color=GOLD, size=11*scale, weight="bold")]),
            *rank_rows])

        col_dir = ft.Column(spacing=10*scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=6*scale, controls=[ft.Icon(ft.Icons.BAR_CHART, color=BLUE, size=16*scale),
                ft.Text("Desempenho por Atividade", color=WHITE, size=13*scale, weight="bold")]),
            *ativ_bars,
            ft.Divider(color="#22FFFFFF", thickness=1),
            ft.Row(spacing=6*scale, controls=[ft.Icon(ft.Icons.WARNING_AMBER, color=RED, size=14*scale),
                ft.Text("Atividades Pendentes", color=WHITE, size=12*scale, weight="bold")]),
            *ausentes_ctrl])

        pc = ft.Container(width=CINZA_W*scale, height=CINZA_H*scale,
            border_radius=20*scale, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            padding=ft.padding.symmetric(horizontal=16*scale, vertical=12*scale),
            content=ft.Row(spacing=14*scale, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
                ft.Container(expand=3, content=col_esq),
                ft.Container(width=1, height=(CINZA_H-40)*scale, bgcolor="#15FFFFFF"),
                ft.Container(expand=3, content=col_dir)]))
        montar_layout(page, scale, img_w, img_h, pv, pc)

    page.on_resize = lambda e: build()
    build()


# ============================================================
#  HISTÓRICO GERAL — with eye icon to see question details
# ============================================================

def tela_historico_geral(page, navegar, menu_fn):
    page.controls.clear(); page.padding = 0; page.bgcolor = "white"
    fil = {"turma": "Todas", "atividade": "Todas"}

    def build():
        page.controls.clear()
        W = page.width or IMG_W; H = page.height or IMG_H
        scale = min(W / IMG_W, H / IMG_H)
        img_w = IMG_W*scale; img_h = IMG_H*scale
        def _inicio(e): menu_fn(page, navegar)
        def _ativ(e):   tela_atividades(page, navegar, menu_fn)
        def _rank(e):   tela_ranking(page, navegar, menu_fn)
        def _acomp(e):  tela_acompanhamento(page, navegar, menu_fn)
        def _rel(e):    tela_relatorio_turma(page, navegar, menu_fn)
        def _hist(e):   tela_historico_geral(page, navegar, menu_fn)
        def _sair(e):   navegar["login"]()
        pv = painel_nav_prof(scale, _inicio, _ativ, _rank, _acomp, _rel, _hist, _sair)

        todos = buscar_todos_resultados()
        filtrado = todos
        if fil["turma"]!="Todas": filtrado = [r for r in filtrado if r["turma"]==fil["turma"]]
        if fil["atividade"]!="Todas": filtrado = [r for r in filtrado if r["atividade"]==fil["atividade"]]
        filtrado = sorted(filtrado, key=lambda r: r["id"], reverse=True)

        op_t = ["Todas"]+TURMAS
        op_a = ["Todas"]+[a["nome"].split(" - ")[1] for a in LISTA_ATIVIDADES]
        nm = {"Todas":"Todas", **{a["nome"].split(" - ")[1]:a["nome"] for a in LISTA_ATIVIDADES}}

        def _chip(label, key, val, cor):
            a = fil[key]==val
            rv = nm.get(val, val) if key=="atividade" else val
            def _s(e, k=key, v=rv): fil[k]=v; build()
            return ft.Container(border_radius=8*scale, bgcolor=cor+"88" if a else "#0AFFFFFF",
                border=ft.border.all(1, cor) if a else ft.border.all(1, "#22FFFFFF"),
                padding=ft.padding.symmetric(horizontal=8*scale, vertical=4*scale),
                on_click=_s, ink=True,
                content=ft.Text(label, color=WHITE, size=9*scale, weight="bold" if a else "normal"))

        tr = len(filtrado); au = len(set(r["aluno"] for r in filtrado))
        mf = round(sum(r["pontuacao"] for r in filtrado)/tr) if tr else 0

        cam = {"Atividade 1 - Frações":BLUE,"Atividade 2 - Equações":GREEN,"Atividade 3 - Geometria":ORANGE_BG}
        TL = {"dia":"do dia","anterior":"anterior","antiga":"antiga"}

        def _ver_detalhes(e, rid, ativ, aluno):
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
                                content=ft.Text(f"📝 {len(det)} questões", size=13, weight="bold", color="#2F9EDC"))]),
                        ft.Divider(), *ld])))
            def _fechar(ev): dlg.open = False; page.update()
            dlg.actions = [ft.TextButton("Fechar", on_click=_fechar)]
            page.overlay.append(dlg); dlg.open = True; page.update()

        linhas = []
        for r in filtrado[:40]:
            ca = cam.get(r["atividade"], BLUE)
            la = r["atividade"].split(" - ")[1] if " - " in r["atividade"] else r["atividade"]
            tipo = TL.get(r.get("tipo_atividade","dia"), r.get("tipo_atividade",""))
            tem_det = len(buscar_detalhes_questoes(r["id"])) > 0

            eye_btn = ft.Container(
                width=28*scale, height=28*scale, border_radius=14*scale,
                bgcolor=BLUE+"33" if tem_det else "#0AFFFFFF",
                alignment=ft.Alignment(0, 0),
                on_click=(lambda e, rid=r["id"], av=r["atividade"], al=r["aluno"]: _ver_detalhes(e, rid, av, al)) if tem_det else None,
                ink=tem_det,
                content=ft.Icon(ft.Icons.VISIBILITY, color=BLUE if tem_det else "#33FFFFFF", size=14*scale),
            )

            linhas.append(ft.Container(border_radius=8*scale, bgcolor="#0AFFFFFF",
                padding=ft.padding.symmetric(horizontal=10*scale, vertical=6*scale),
                content=ft.Row(spacing=6*scale, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Container(width=5*scale, height=32*scale, border_radius=3*scale, bgcolor=ca),
                    ft.Column(spacing=1, expand=True, controls=[
                        ft.Row(spacing=4*scale, controls=[
                            ft.Text(r["aluno"], color=WHITE, size=10*scale, weight="bold"),
                            ft.Container(border_radius=4*scale, bgcolor=ca+"33",
                                padding=ft.padding.symmetric(horizontal=4*scale, vertical=1*scale),
                                content=ft.Text(la, color=ca, size=8*scale)),
                            ft.Text(f"T{r['turma']}", color="#77FFFFFF", size=8*scale)]),
                        ft.Text(f"{tipo}  •  ⏱{r['tempo']}  •  {r['data']}", color="#66FFFFFF", size=8*scale)]),
                    eye_btn,
                    ft.Column(spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END, controls=[
                        ft.Text(f"{r['pontuacao']} pts", color=GOLD, size=11*scale, weight="bold"),
                        ft.Text(f"✅{r['acertos']} ❌{r['erros']}", color="#88FFFFFF", size=8*scale)])])))

        if not linhas:
            linhas.append(ft.Container(border_radius=12*scale, bgcolor="#0AFFFFFF", padding=ft.padding.all(20*scale),
                content=ft.Column(spacing=6*scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Icon(ft.Icons.HISTORY, color="#33FFFFFF", size=36*scale),
                    ft.Text("Nenhum resultado.", color="#55FFFFFF", size=11*scale)])))

        # Conquistas
        conquistas_db = buscar_conquistas()
        if fil["turma"]!="Todas": conquistas_db=[c for c in conquistas_db if c["turma"]==fil["turma"]]
        ICONES_C={"sem_erros":"✨","nota_maxima":"🏆","top_velocidade":"⚡",
            "primeira_atividade":"🎉","melhorou_nota":"📈","superou_recorde_pessoal":"🌟"}
        conq_linhas=[]
        for c in conquistas_db[:20]:
            ic=ICONES_C.get(c["tipo"],"🏅")
            conq_linhas.append(ft.Container(border_radius=6*scale,bgcolor="#1AFFD700",
                padding=ft.padding.symmetric(horizontal=8*scale,vertical=5*scale),
                content=ft.Row(spacing=6*scale,controls=[
                    ft.Text(ic,size=14*scale),
                    ft.Column(spacing=1,expand=True,controls=[
                        ft.Text(c["descricao"],color=GOLD,size=10*scale,weight="bold"),
                        ft.Text(f"{c['aluno']}  •  T{c['turma']}  •  {c['atividade'].split(' - ')[-1]}",
                            color="#AAFFFFFF",size=8*scale),
                    ]),
                    ft.Text(c["data"],color="#66FFFFFF",size=8*scale),
                ])))
        if not conq_linhas:
            conq_linhas.append(ft.Text("Nenhuma conquista registrada.",color="#66FFFFFF",size=10*scale))

        col = ft.Column(spacing=8*scale, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Row(spacing=6*scale, controls=[ft.Icon(ft.Icons.TUNE, color=ORANGE_BG, size=14*scale),
                ft.Text("Filtrar por Turma", color=WHITE, size=11*scale, weight="bold")]),
            ft.Row(spacing=4*scale, wrap=True, controls=[_chip(t,"turma",t,ORANGE_BG) for t in op_t]),
            ft.Row(spacing=6*scale, controls=[ft.Icon(ft.Icons.MENU_BOOK, color=BLUE, size=14*scale),
                ft.Text("Filtrar por Atividade", color=WHITE, size=11*scale, weight="bold")]),
            ft.Row(spacing=4*scale, wrap=True, controls=[_chip(v,"atividade",v,BLUE) for v in op_a]),
            ft.Row(spacing=8*scale, controls=[stat_card("Resultados",str(tr),BLUE,scale),
                stat_card("Alunos únicos",str(au),ORANGE_BG,scale), stat_card("Média pts",str(mf),GOLD,scale)]),
            ft.Divider(color="#22FFFFFF", thickness=1),
            ft.Row(spacing=6*scale, controls=[ft.Icon(ft.Icons.HISTORY, color=BLUE, size=16*scale),
                ft.Text(f"Histórico ({tr} registros)", color=WHITE, size=13*scale, weight="bold")]),
            *linhas,
            ft.Divider(color="#22FFFFFF", thickness=1),
            ft.Row(spacing=6*scale, controls=[ft.Icon(ft.Icons.MILITARY_TECH, color=GOLD, size=16*scale),
                ft.Text(f"Conquistas ({len(conquistas_db)})", color=GOLD, size=13*scale, weight="bold")]),
            *conq_linhas,
        ])

        pc = ft.Container(width=CINZA_W*scale, height=CINZA_H*scale,
            border_radius=20*scale, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            padding=ft.padding.symmetric(horizontal=16*scale, vertical=12*scale), content=col)
        montar_layout(page, scale, img_w, img_h, pv, pc)

    page.on_resize = lambda e: build()
    build()
