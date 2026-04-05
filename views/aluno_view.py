"""
views/aluno_view.py — Menu principal do aluno + painel de dashboard.

Sub-módulos:
  aluno_helpers.py — helpers visuais compartilhados (painéis laranja, azul, verde)
  aluno_telas.py   — atividades, histórico e ranking
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import flet as ft
import state
from constants import LABEL_TIPO, LISTA_ATIVIDADES, ALUNOS_POR_TURMA
from controllers.historico_controller import buscar_todos_resultados
from views.aluno_helpers import (
    BLUE, ORANGE_BG, WHITE, GOLD, GREEN, RED,
    IMG_W, IMG_H,
    painel_verde, montar_layout_aluno,
)
from views.aluno_telas import tela_atividades, tela_historico, historico, tela_ranking, ranking


# ============================================================
#  BLOCO CINZA — DASHBOARD DO MENU PRINCIPAL
# ============================================================

def _painel_atividades(scale, on_iniciar):
    """⬛ Bloco cinza — atividade liberada + histórico recente + resumo de desempenho."""
    dados = buscar_todos_resultados()

    ativa = next(
        (a for a in state.atividades_liberadas if a["turma"] == state.turma_atual),
        None,
    )

    if ativa:
        bloco_ativa = ft.Container(
            border_radius=12 * scale,
            bgcolor="#223F9EDC",
            border=ft.border.all(1, "#2F9EDC"),
            padding=ft.padding.symmetric(horizontal=16 * scale, vertical=12 * scale),
            content=ft.Row(
                spacing=12 * scale,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.PLAY_CIRCLE, color=BLUE, size=24 * scale),
                    ft.Column(
                        spacing=3 * scale,
                        expand=True,
                        controls=[
                            ft.Text(ativa["atividade"], color=WHITE, size=14 * scale, weight="bold"),
                            ft.Text(
                                f"{LABEL_TIPO.get(ativa.get('tipo', 'dia'), 'do dia')}  •  "
                                f"{ativa.get('tempo_maximo', 600) // 60} min",
                                color="#AAFFFFFF",
                                size=12 * scale,
                            ),
                        ],
                    ),
                    ft.Container(
                        border_radius=16 * scale,
                        bgcolor=BLUE,
                        padding=ft.padding.symmetric(horizontal=16 * scale, vertical=10 * scale),
                        on_click=lambda e, nome=ativa["atividade"]: on_iniciar(nome),
                        ink=True,
                        content=ft.Text("▶ INICIAR", color=WHITE, size=13 * scale, weight="bold"),
                    ),
                ],
            ),
        )
    else:
        bloco_ativa = ft.Container(
            border_radius=12 * scale,
            bgcolor="#0FFFFFFF",
            padding=ft.padding.symmetric(horizontal=16 * scale, vertical=10 * scale),
            content=ft.Row(
                spacing=14 * scale,
                controls=[
                    ft.Icon(ft.Icons.LOCK_CLOCK, color="#88FFFFFF", size=18 * scale),
                    ft.Text("Nenhuma atividade liberada no momento.", color="#88FFFFFF", size=12 * scale),
                ],
            ),
        )

    alunos_ativos = state.alunos_ativos or []
    linhas_hist = []

    for aluno in alunos_ativos:
        recentes_aluno = [r for r in dados if r["aluno"] == aluno]
        recentes_aluno = list(reversed(recentes_aluno[-4:] if len(recentes_aluno) > 4 else recentes_aluno))

        linhas_hist.append(
            ft.Row(spacing=6 * scale, controls=[
                ft.Icon(ft.Icons.PERSON, color="#AAFFFFFF", size=14 * scale),
                ft.Text(aluno, color="#CCFFFFFF", size=12 * scale, weight="bold"),
            ])
        )

        if not recentes_aluno:
            linhas_hist.append(
                ft.Text("  Nenhuma atividade realizada ainda.", color="#66FFFFFF", size=11 * scale)
            )
        else:
            for r in recentes_aluno:
                linhas_hist.append(
                    ft.Container(
                        border_radius=8 * scale,
                        bgcolor="#0FFFFFFF",
                        border=ft.border.all(1, "#22FFFFFF"),
                        padding=ft.padding.symmetric(horizontal=14 * scale, vertical=10 * scale),
                        content=ft.Row(
                            spacing=14 * scale,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.CHECK_CIRCLE, color="#4CAF50", size=16 * scale),
                                ft.Text(r["atividade"], color=WHITE, size=12 * scale, expand=True),
                                ft.Text(f"{r['pontuacao']} pts", color="#F9A825", size=12 * scale, weight="bold"),
                                ft.Text(r["data"], color="#77FFFFFF", size=10 * scale),
                            ],
                        ),
                    )
                )

    if not linhas_hist:
        linhas_hist.append(
            ft.Text("Nenhuma atividade realizada ainda.", color="#66FFFFFF", size=12 * scale)
        )

    cards_resumo = []
    for aluno in alunos_ativos:
        regs        = [r for r in dados if r["aluno"].strip() == aluno.strip()]
        total_pts   = sum(r["pontuacao"] for r in regs)
        total_ativ  = len(regs)
        media_pts   = round(total_pts / total_ativ) if total_ativ else 0
        total_acert = sum(r.get("acertos", 0) for r in regs)
        total_erros = sum(r.get("erros", 0) for r in regs)

        cards_resumo.append(ft.Container(
            border_radius=12 * scale,
            bgcolor="#12FFFFFF",
            border=ft.border.all(1, "#22FFFFFF"),
            padding=ft.padding.symmetric(horizontal=14 * scale, vertical=10 * scale),
            content=ft.Column(
                spacing=6 * scale,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(spacing=6 * scale, alignment=ft.MainAxisAlignment.CENTER, controls=[
                        ft.Icon(ft.Icons.PERSON, color=BLUE, size=14 * scale),
                        ft.Text(aluno, color=WHITE, size=12 * scale, weight="bold"),
                    ]),
                    ft.Divider(color="#22FFFFFF", thickness=1),
                    ft.Row(spacing=4 * scale, alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                        ft.Column(spacing=2 * scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text(f"{total_pts}", color="#F9A825", size=16 * scale, weight="bold"),
                            ft.Text("Pontos", color="#AAFFFFFF", size=9 * scale),
                        ]),
                        ft.Container(width=1, height=30 * scale, bgcolor="#22FFFFFF"),
                        ft.Column(spacing=2 * scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text(f"{total_ativ}", color=WHITE, size=16 * scale, weight="bold"),
                            ft.Text("Atividades", color="#AAFFFFFF", size=9 * scale),
                        ]),
                        ft.Container(width=1, height=30 * scale, bgcolor="#22FFFFFF"),
                        ft.Column(spacing=2 * scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text(f"{media_pts}", color=WHITE, size=16 * scale, weight="bold"),
                            ft.Text("Média", color="#AAFFFFFF", size=9 * scale),
                        ]),
                        ft.Container(width=1, height=30 * scale, bgcolor="#22FFFFFF"),
                        ft.Column(spacing=2 * scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text(f"{total_acert}", color="#4CAF50", size=16 * scale, weight="bold"),
                            ft.Text("Acertos", color="#AAFFFFFF", size=9 * scale),
                        ]),
                        ft.Container(width=1, height=30 * scale, bgcolor="#22FFFFFF"),
                        ft.Column(spacing=2 * scale, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text(f"{total_erros}", color="#FF5252", size=16 * scale, weight="bold"),
                            ft.Text("Erros", color="#AAFFFFFF", size=9 * scale),
                        ]),
                    ]),
                ],
            ),
        ))

    col_esquerda = ft.Container(
        expand=3,
        height=595 * scale,
        content=ft.Column(
            spacing=14 * scale,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(spacing=8 * scale, controls=[
                    ft.Icon(ft.Icons.BOLT, color="#F9A825", size=20 * scale),
                    ft.Text("Atividade Liberada", color=WHITE, size=18 * scale, weight="bold"),
                ]),
                bloco_ativa,
                ft.Divider(color="#22FFFFFF", thickness=1),
                ft.Row(spacing=8 * scale, controls=[
                    ft.Icon(ft.Icons.HISTORY, color=ORANGE_BG, size=20 * scale),
                    ft.Text("Últimas Atividades Realizadas", color=WHITE, size=16 * scale, weight="bold"),
                ]),
                *linhas_hist,
            ],
        ),
    )

    col_direita = ft.Container(
        expand=2,
        height=595 * scale,
        content=ft.Column(
            spacing=14 * scale,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(spacing=8 * scale, alignment=ft.MainAxisAlignment.CENTER, controls=[
                    ft.Icon(ft.Icons.INSIGHTS, color=BLUE, size=20 * scale),
                    ft.Text("Resumo de Desempenho", color=WHITE, size=14 * scale, weight="bold"),
                ]),
                *cards_resumo,
            ],
        ),
    )

    return ft.Container(
        width=1010 * scale,
        height=625 * scale,
        border_radius=16 * scale,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        padding=ft.padding.symmetric(horizontal=16 * scale, vertical=14 * scale),
        content=ft.Row(
            spacing=12 * scale,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                col_esquerda,
                ft.Container(width=1, height=595 * scale, bgcolor="#15FFFFFF"),
                col_direita,
            ],
        ),
    )


# ============================================================
#  MENU PRINCIPAL
# ============================================================

def menu(page: ft.Page, navegar: dict):
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

        def _menu_click(e): menu(page, navegar)
        def _atividades(e): tela_atividades(page, navegar)
        def _historico(e):  tela_historico(page, navegar)
        def _ranking(e):    tela_ranking(page, navegar)
        def _sair(e):       navegar["login"]()
        def _iniciar(nome): navegar["iniciar_atividade"](nome)

        pv = painel_verde(scale, _atividades, _historico, _ranking, _sair, on_menu=_menu_click)
        montar_layout_aluno(page, scale, img_w, img_h, pv, _painel_atividades(scale, _iniciar))

    page.on_resize = lambda e: build()
    build()
