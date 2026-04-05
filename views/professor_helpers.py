"""
views/professor_helpers.py — Helpers visuais compartilhados pelas telas do professor.
"""
import os
import flet as ft
from constants import ALUNOS_POR_TURMA, BASE_DIR

# ── Cores ──────────────────────────────────────────────────
BLUE       = "#2F9EDC"
ORANGE_BG  = "#FF7A2F"
WHITE      = "#FFFFFF"
TEXT_COLOR  = "#333333"
GREEN      = "#4CAF50"
RED        = "#FF5252"
GOLD       = "#F9A825"

IMG_W = 1366
IMG_H = 768
IMAGEM_MENU = os.path.join(BASE_DIR, "views", "Menu_Professor.png")

TURMAS = list(ALUNOS_POR_TURMA.keys())
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

# ── Dimensões do painel cinza ──
CINZA_W = 1010
CINZA_H = 625


def btn_menu(texto, icone, cor_icone, on_click, scale):
    controles = []
    if icone:
        controles.append(ft.Icon(icone, color=cor_icone, size=22 * scale))
    controles.append(ft.Text(texto, size=13 * scale, weight="bold", color=TEXT_COLOR))
    return ft.Container(
        width=220 * scale, height=52 * scale, border_radius=14 * scale, bgcolor=WHITE,
        padding=ft.padding.symmetric(horizontal=16 * scale, vertical=8 * scale),
        on_click=on_click, ink=True,
        content=ft.Row(spacing=12 * scale, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER if not icone else ft.MainAxisAlignment.START,
            controls=controles),
    )


def painel_laranja_prof(scale):
    total_alunos = sum(len(v) for v in ALUNOS_POR_TURMA.values())
    n_turmas = len(TURMAS)
    return ft.Container(
        width=270 * scale, height=200 * scale,
        padding=ft.padding.only(left=18*scale, right=18*scale, top=28*scale, bottom=18*scale),
        alignment=ft.Alignment(0, 0),
        content=ft.Column(spacing=8 * scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True, controls=[
                ft.Icon(ft.Icons.SCHOOL, color=WHITE, size=28 * scale),
                ft.Text("PROFESSOR", color=WHITE, size=15 * scale, weight="bold", text_align="center"),
                ft.Divider(color="#66FFFFFF", thickness=1),
                ft.Row(spacing=0, alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                    ft.Column(spacing=2 * scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        ft.Text(str(n_turmas), color=WHITE, size=24 * scale, weight="bold"),
                        ft.Text("Turmas", color="#DDFFFFFF", size=9 * scale),
                    ]),
                    ft.Container(width=1, height=40 * scale, bgcolor="#55FFFFFF"),
                    ft.Column(spacing=2 * scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        ft.Text(str(total_alunos), color=WHITE, size=24 * scale, weight="bold"),
                        ft.Text("Alunos", color="#DDFFFFFF", size=9 * scale),
                    ]),
                ]),
            ]),
    )


def stat_card(label, valor, cor, scale):
    return ft.Container(
        expand=True, border_radius=10 * scale, bgcolor="#0AFFFFFF",
        padding=ft.padding.symmetric(horizontal=8 * scale, vertical=8 * scale),
        content=ft.Column(spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
            ft.Text(valor, color=cor, size=20 * scale, weight="bold"),
            ft.Text(label, color="#AAFFFFFF", size=9 * scale),
        ]),
    )


def painel_verde_nav(scale, botoes_extras, on_sair):
    GAP = 10 * scale
    controles = [
        ft.Row(spacing=6*scale, alignment=ft.MainAxisAlignment.CENTER, controls=[
            ft.Icon(ft.Icons.GRID_VIEW, color=WHITE, size=14*scale),
            ft.Text("MENU", color=WHITE, size=13 * scale, weight="bold"),
        ]),
        ft.Divider(color="#88FFFFFF", thickness=1),
        ft.Container(height=4 * scale),
    ]
    for b in botoes_extras:
        controles.append(b)
        controles.append(ft.Container(height=GAP))
    controles.append(ft.Container(
        width=220 * scale, height=44 * scale, border_radius=14 * scale,
        bgcolor="#33FFFFFF", on_click=on_sair, ink=True,
        padding=ft.padding.symmetric(horizontal=16 * scale, vertical=6 * scale),
        content=ft.Row(spacing=12 * scale, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
            ft.Icon(ft.Icons.LOGOUT, color=WHITE, size=20 * scale),
            ft.Text("Sair", color=WHITE, size=13 * scale, weight="bold"),
        ]),
    ))
    controles.append(ft.Container(expand=True))
    return ft.Container(
        width=265 * scale, height=510 * scale,
        padding=ft.padding.only(left=20 * scale, right=20 * scale, top=32 * scale, bottom=12 * scale),
        content=ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=controles),
    )


def painel_nav_prof(scale, on_inicio, on_ativ, on_rank, on_acomp, on_rel, on_hist, on_sair):
    """Painel de navegação completo do professor."""
    return painel_verde_nav(scale, [
        btn_menu("Início",          ft.Icons.HOME,        GREEN,     on_inicio, scale),
        btn_menu("Atividades",      ft.Icons.MENU_BOOK,   BLUE,      on_ativ,   scale),
        btn_menu("Ranking",         ft.Icons.LEADERBOARD, GOLD,      on_rank,   scale),
        btn_menu("Acompanhamento",  ft.Icons.PEOPLE,      GREEN,     on_acomp,  scale),
        btn_menu("Relatório Turma", ft.Icons.ASSESSMENT,  ORANGE_BG, on_rel,    scale),
        btn_menu("Histórico Geral", ft.Icons.HISTORY,     "#AA88FF", on_hist,   scale),
    ], on_sair)


def sub_verde(scale, on_voltar, on_sair):
    return painel_verde_nav(scale, [
        btn_menu("Voltar ao Menu", ft.Icons.ARROW_BACK, BLUE, on_voltar, scale),
    ], on_sair)


def montar_layout(page, scale, img_w, img_h, painel_verde, painel_cinza):
    fundo = ft.Image(src=IMAGEM_MENU, width=img_w, height=img_h, fit="fill")
    layout = ft.Container(width=img_w, height=img_h,
        content=ft.Stack(width=img_w, height=img_h, controls=[
            fundo,
            ft.Container(left=0, top=0, content=painel_laranja_prof(scale)),
            ft.Container(left=0, top=210 * scale, content=painel_verde),
            ft.Container(left=300 * scale, top=68 * scale, content=painel_cinza),
        ]))
    page.add(ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=layout))
    page.update()