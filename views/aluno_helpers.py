"""
views/aluno_helpers.py — Helpers visuais compartilhados pelas telas do aluno.
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import os
import flet as ft
import state
from constants import ALUNOS_POR_TURMA, BASE_DIR
from controllers.historico_controller import buscar_todos_resultados
from views.professor_helpers import btn_menu as _btn_menu_prof, painel_verde_nav as _painel_verde_nav_prof

# ── Cores ───────────────────────────────────────────────────
BLUE       = "#2F9EDC"
ORANGE_BG  = "#FF7A2F"
INPUT_BG   = "#F4F4F4"
BORDER     = "#D6D6D6"
TEXT_COLOR = "#333333"
WHITE      = "#FFFFFF"
GOLD       = "#F9A825"
GREEN      = "#4CAF50"
RED        = "#FF5252"

# ── Dimensões originais da imagem ──────────────────────────
IMG_W = 1366
IMG_H = 768

IMAGEM_MENU = os.path.join(BASE_DIR, "views", "Menu_Aluno.png")


# ============================================================
#  PAINÉIS FIXOS DO LAYOUT
# ============================================================

def painel_laranja(scale):
    turma  = state.turma_atual or "—"
    alunos = state.alunos_ativos or []

    aluno_widgets = []
    for a in alunos:
        aluno_widgets.append(
            ft.Row(
                spacing=6 * scale,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.PERSON, color=WHITE, size=16 * scale),
                    ft.Text(a.upper(), color=WHITE, size=13 * scale, weight="bold"),
                ],
            )
        )

    return ft.Container(
        width=270 * scale,
        height=200 * scale,
        padding=ft.padding.all(18 * scale),
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            spacing=14 * scale,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
            controls=[
                ft.Text(
                    f"TURMA  {turma}",
                    color=WHITE,
                    size=20 * scale,
                    weight="bold",
                    text_align="center",
                ),
                ft.Divider(color="#88FFFFFF", thickness=1),
                *aluno_widgets,
            ],
        ),
    )


def painel_azul_mini(scale):
    """🟦 Bloco azul pequeno (inferior esquerda) — ranking rápido do aluno."""
    dados = buscar_todos_resultados()

    pts_geral = {}
    for r in dados:
        pts_geral[r["aluno"]] = pts_geral.get(r["aluno"], 0) + r["pontuacao"]
    rank_geral = sorted(pts_geral.items(), key=lambda x: x[1], reverse=True)

    def posicao(aluno):
        for i, (n, _) in enumerate(rank_geral, start=1):
            if n == aluno:
                return i
        return None

    alunos = state.alunos_ativos or []
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    linhas = []

    for a in alunos:
        pos   = posicao(a)
        pts   = pts_geral.get(a, 0)
        medal = medals.get(pos, f"{pos}º") if pos else "—"
        linhas.append(
            ft.Row(
                spacing=8 * scale,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Text(medal, size=13 * scale, color=WHITE),
                    ft.Text(a, size=12 * scale, color=WHITE, weight="bold"),
                    ft.Text("·", size=12 * scale, color="#AAFFFFFF"),
                    ft.Text(f"{pos}º lugar" if pos else "—", size=12 * scale, color=WHITE),
                    ft.Text("·", size=12 * scale, color="#AAFFFFFF"),
                    ft.Text(f"{pts} pts", size=12 * scale, color=WHITE),
                ],
            )
        )

    return ft.Container(
        width=185 * scale,
        height=160 * scale,
        padding=ft.padding.only(left=14 * scale, right=14 * scale, top=42 * scale, bottom=14 * scale),
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
            controls=[
                ft.Row(
                    spacing=6 * scale,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.LEADERBOARD, color=WHITE, size=14 * scale),
                        ft.Text("Ranking Geral", color=WHITE, size=12 * scale, weight="bold"),
                    ],
                ),
                ft.Container(height=2 * scale),
                ft.Divider(color="#88FFFFFF", thickness=1),
                ft.Container(height=2 * scale),
                *[ctrl for linha in [[l, ft.Container(height=6 * scale)] for l in linhas] for ctrl in linha],
            ],
        ),
    )


def painel_azul(scale):
    alunos = state.alunos_ativos or []

    if len(alunos) >= 2:
        saudacao = f"Bem-vindo! 👋   Olá, {alunos[0]} e {alunos[1]}. Bom trabalho hoje!"
    elif len(alunos) == 1:
        saudacao = f"Bem-vindo! 👋   Olá, {alunos[0]}. Bom trabalho hoje!"
    else:
        saudacao = "Bem-vindo! 👋   Bom trabalho hoje!"

    return ft.Container(
        width=550 * scale,
        height=105 * scale,
        padding=ft.padding.only(
            left=28 * scale,
            top=18 * scale,
            right=20 * scale,
            bottom=18 * scale,
        ),
        alignment=ft.Alignment(-1, 0),
        content=ft.Text(
            saudacao,
            color=WHITE,
            size=15 * scale,
            weight="w600",
        ),
    )


def painel_verde(scale, on_atividades, on_historico, on_ranking, on_sair, on_menu=None):
    """Painel de navegação lateral do aluno — usa o mesmo estilo do professor."""
    botoes = []
    if on_menu:
        botoes.append(_btn_menu_prof("Início", ft.Icons.HOME, GREEN, on_menu, scale))
    botoes.append(_btn_menu_prof("Atividades", ft.Icons.MENU_BOOK,   BLUE,      on_atividades, scale))
    botoes.append(_btn_menu_prof("Histórico",  ft.Icons.HISTORY,     ORANGE_BG, on_historico,  scale))
    botoes.append(_btn_menu_prof("Ranking",    ft.Icons.LEADERBOARD, GOLD,      on_ranking,    scale))
    return _painel_verde_nav_prof(scale, botoes, on_sair)


def montar_layout_aluno(page, scale, img_w, img_h, painel_nav, painel_cinza):
    fundo = ft.Image(src=IMAGEM_MENU, width=img_w, height=img_h, fit="fill")
    layout = ft.Container(
        width=img_w,
        height=img_h,
        content=ft.Stack(
            width=img_w,
            height=img_h,
            controls=[
                fundo,
                ft.Container(left=0 * scale,   top=0 * scale,   content=painel_laranja(scale)),
                ft.Container(left=670 * scale, top=0 * scale,   content=painel_azul(scale)),
                ft.Container(left=0 * scale,   top=210 * scale, content=painel_nav),
                ft.Container(left=300 * scale, top=68 * scale,  content=painel_cinza),
                ft.Container(left=38 * scale,  top=560 * scale, content=painel_azul_mini(scale)),
            ],
        ),
    )
    page.add(ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=layout))
    page.update()
