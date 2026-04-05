"""
views/login_view.py — Tela de login (Flet).

Exibe o card de login sobre a imagem de fundo (Login.png).
Compatível com main.py: expõe  mostrar(page, navegar).
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import flet as ft
import state
from constants import ALUNOS_POR_TURMA, BASE_DIR

# ── Cores ──────────────────────────────────────────────────
BLUE       = "#2F9EDC"
ORANGE_BG  = "#FF7A2F"
INPUT_BG   = "#F4F4F4"
BORDER     = "#D6D6D6"
TEXT_COLOR  = "#333333"

# Caminho da imagem de fundo
IMAGEM_FUNDO = _os.path.join(BASE_DIR, "Login.png")


# ============================================================
#  FUNÇÃO PRINCIPAL — chamada por  main.py → navegar["login"]
# ============================================================

def mostrar(page: ft.Page, navegar: dict):
    page.controls.clear()

    turmas = list(ALUNOS_POR_TURMA.keys())

    # ── Dropdowns ──────────────────────────────────────────
    dd_turma = ft.Dropdown(
        hint_text="Selecionar",
        options=[ft.dropdown.Option(t) for t in turmas],
        border_color=BORDER,
        bgcolor="white",
        filled=True,
        border_radius=18,
        content_padding=ft.padding.symmetric(horizontal=15, vertical=10),
        expand=True,
    )

    dd_aluno1 = ft.Dropdown(
        hint_text="Selecionar",
        options=[],
        border_color=BORDER,
        bgcolor="white",
        filled=True,
        border_radius=18,
        content_padding=ft.padding.symmetric(horizontal=15, vertical=10),
        expand=True,
    )

    dd_aluno2 = ft.Dropdown(
        hint_text="Selecionar",
        options=[],
        border_color=BORDER,
        bgcolor="white",
        filled=True,
        border_radius=18,
        content_padding=ft.padding.symmetric(horizontal=15, vertical=10),
        expand=True,
    )

    lbl_erro = ft.Text("", color="red", size=13, visible=False)

    # ── Callbacks ──────────────────────────────────────────

    def definir_turma(e):
        turma = dd_turma.value
        alunos = ALUNOS_POR_TURMA.get(turma, [])
        opcoes = [ft.dropdown.Option(a) for a in alunos]
        dd_aluno1.options = opcoes
        dd_aluno1.value = None
        dd_aluno2.options = [ft.dropdown.Option("Nenhum")] + list(opcoes)
        dd_aluno2.value = None
        page.update()

    def entrar(e):
        turma  = dd_turma.value
        aluno1 = dd_aluno1.value
        aluno2 = dd_aluno2.value if dd_aluno2.value != "Nenhum" else None
        if not turma: return
        if not aluno1 and not aluno2: return
        if aluno1 and aluno2 and aluno1 == aluno2: return
        state.turma_atual = turma
        state.alunos_ativos = [a for a in (aluno1, aluno2) if a]
        state.modo = "aluno"
        navegar["menu_aluno"]()

    def ir_professor(e):
        campo_senha = ft.TextField(
            hint_text="Digite a senha", password=True, can_reveal_password=True,
            border_radius=18, border_color=BORDER, bgcolor="white",
        )
        erro_senha = ft.Text("", color="red", size=12, visible=False)

        def confirmar_senha(ev):
            if campo_senha.value == state.config.get("senha_professor", "123"):
                dialog.open = False
                page.update()
                state.modo = "professor"
                navegar["menu_professor"]()
            else:
                erro_senha.value = "Senha incorreta."
                erro_senha.visible = True
                page.update()

        def cancelar(ev):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Área do Professor"),
            content=ft.Column(tight=True, spacing=10, controls=[
                ft.Text("Digite a senha para acessar:"), campo_senha, erro_senha,
            ]),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Entrar", on_click=confirmar_senha),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    # ── Card interno ───────────────────────────────────────

    card_content = ft.Column(
        spacing=6,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            # Título com ícone
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.SCHOOL, color="white", size=26),
                    ft.Text("Bem-vindo!", size=24, weight="bold", color="white"),
                ],
            ),
            ft.Text(
                "Selecione sua turma e aluno para começar",
                size=12,
                color="#FFE0CC",
                text_align="center",
            ),
            ft.Divider(color="#44FFFFFF", thickness=1, height=8),

            # TURMA
            ft.Row(spacing=10, controls=[
                ft.Column(expand=2, spacing=4, controls=[
                    ft.Text("TURMA", size=11, weight="bold", color="#FFE0CC"),
                    ft.Container(content=dd_turma, height=48),
                ]),
                ft.Column(expand=1, spacing=4, controls=[
                    ft.Text("", size=11),
                    ft.Container(
                        height=48,
                        content=ft.ElevatedButton(
                            "Definir",
                            color="white",
                            bgcolor="#E05A10",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=14),
                                elevation=2,
                            ),
                            on_click=definir_turma,
                        ),
                    ),
                ]),
            ]),

            # ALUNOS
            ft.Row(spacing=12, controls=[
                ft.Column(expand=1, spacing=4, controls=[
                    ft.Text("ALUNO 1", size=11, weight="bold", color="#FFE0CC"),
                    ft.Container(content=dd_aluno1, height=48),
                ]),
                ft.Column(expand=1, spacing=4, controls=[
                    ft.Text("ALUNO 2", size=11, weight="bold", color="#FFE0CC"),
                    ft.Container(content=dd_aluno2, height=48),
                ]),
            ]),

            lbl_erro,

            # BOTÃO ENTRAR
            ft.Container(
                height=42,
                alignment=ft.Alignment(0, 0),
                content=ft.ElevatedButton(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.LOGIN, color="white", size=18),
                            ft.Text("ENTRAR", color="white", weight="bold", size=15),
                        ],
                    ),
                    bgcolor=BLUE,
                    width=230,
                    height=42,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=25),
                        elevation=4,
                    ),
                    on_click=entrar,
                ),
            ),

            ft.Divider(color="#44FFFFFF", thickness=1, height=6),

            # ÁREA DO PROFESSOR
            ft.TextButton(
                content=ft.Row(spacing=6, alignment=ft.MainAxisAlignment.CENTER, controls=[
                    ft.Icon(ft.Icons.LOCK_PERSON, size=15, color="#FFE0CC"),
                    ft.Text("Área do professor", size=12, color="#FFE0CC"),
                ]),
                on_click=ir_professor,
            ),
        ],
    )

    card = ft.Container(
        width=390,
        padding=ft.padding.symmetric(horizontal=22, vertical=14),
        border_radius=20,
        bgcolor="#E8622A",
        shadow=ft.BoxShadow(blur_radius=24, color="#55000000", offset=ft.Offset(0, 6)),
        content=card_content,
    )

    fundo = ft.Image(src=IMAGEM_FUNDO, fit="cover", expand=True)

    tela = ft.Stack(expand=True, controls=[
        fundo,
        ft.Container(
            expand=True,
            alignment=ft.Alignment(0.6, 1),
            padding=ft.padding.only(right=40, top=270),
            content=card,
        ),
    ])

    page.add(tela)
    page.update()