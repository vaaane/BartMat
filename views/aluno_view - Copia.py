"""
views/aluno_view.py — Menu do aluno, lista de atividades, histórico e ranking.

A função menu() usa a imagem Menu_Aluno.png como fundo com painéis posicionados:
  🟧 Laranja  → Nome da turma + nomes dos alunos
  🟦 Azul     → Mensagem de Bem-vindo
  🟩 Verde    → Botões do menu
  ⬛ Cinza    → Ranking geral dos alunos
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import flet as ft
import state
from constants import LABEL_TIPO, LISTA_ATIVIDADES, ALUNOS_POR_TURMA, BASE_DIR, scrollable
from controllers.historico_controller import buscar_todos_resultados, buscar_detalhes_questoes, contar_tentativas

# ── Cores (MESMAS DO LOGIN) ─────────────────────────────────
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

IMAGEM_MENU = _os.path.join(BASE_DIR, "views", "Menu_Aluno.png")


# ============================================================
#  HELPERS DO MENU
# ============================================================



def _btn_menu(texto, icone, cor_icone, on_click, scale):
    def on_hover(e):
        e.control.bgcolor = "#F7F7F7" if e.data == "true" else WHITE
        e.control.update()

    return ft.Container(
        width=220 * scale,
        height=54 * scale,

        border_radius=16 * scale,
        bgcolor=WHITE,
        border=ft.border.all(1, "#EEEEEE"),

        padding=ft.padding.symmetric(horizontal=16 * scale),

        on_click=on_click,
        on_hover=on_hover,
        ink=True,
        animate=ft.Animation(200, "easeOut"),

        content=ft.Row(
            spacing=12 * scale,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icone, color=cor_icone, size=20 * scale),
                ft.Text(
                    texto,
                    size=14 * scale,
                    weight="w600",
                    color=TEXT_COLOR,
                ),
            ],
        ),
    )










def _painel_laranja(scale):
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


def _painel_azul_mini(scale):
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



def _painel_azul(scale):
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


def _painel_verde(scale, on_atividades, on_historico, on_ranking, on_sair, on_menu=None):
    GAP = 10 * scale
    return ft.Container(
        width=265 * scale,
        height=390 * scale,
        padding=ft.padding.only(left=20 * scale, right=20 * scale, top=40 * scale, bottom=16 * scale),
        content=ft.Column(
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                _btn_menu("Início", ft.Icons.HOME, "#4CAF50", on_menu, scale) if on_menu else ft.Container(),
                ft.Container(height=GAP) if on_menu else ft.Container(),
                _btn_menu("Atividades", ft.Icons.MENU_BOOK,   BLUE,      on_atividades, scale),
                ft.Container(height=GAP),
                _btn_menu("Histórico",  ft.Icons.HISTORY,     ORANGE_BG, on_historico,  scale),
                ft.Container(height=GAP),
                _btn_menu("Ranking",    ft.Icons.LEADERBOARD, "#F9A825", on_ranking,    scale),
                ft.Container(height=GAP),
                ft.Container(
                    width=220 * scale,
                    height=52 * scale,
                    border_radius=14 * scale,
                    bgcolor="#33FFFFFF",
                    on_click=on_sair,
                    ink=True,
                    padding=ft.padding.symmetric(horizontal=16 * scale, vertical=8 * scale),
                    content=ft.Row(
                        spacing=12 * scale,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.LOGOUT, color=WHITE, size=22 * scale),
                            ft.Text("Sair", color=WHITE, size=13 * scale, weight="bold"),
                        ],
                    ),
                ),
                ft.Container(expand=True),
            ],
        ),
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
        bloqueada = not liberada and not feita_por
        # Contar tentativas por aluno (máx 2)
        tentativas_por_aluno = {}
        for r in feita_por_regs:
            tentativas_por_aluno[r["aluno"]] = tentativas_por_aluno.get(r["aluno"], 0) + 1

        # Pode iniciar se liberada E algum aluno tem < 2 tentativas
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
            cor_status   = "#4CAF50"
            can_click    = False
        elif feita_por and liberada and not todos_completaram:
            icone        = ft.Icons.REPLAY
            cor_icone    = GOLD
            status_lines = []
            for r in feita_por_regs:
                status_lines.append(ft.Text(
                    f"🔄 {r['aluno']}: {r['pontuacao']}pts",
                    color=GOLD, size=10 * scale))
            status_lines.append(ft.Text("2ª tentativa disponível", color=GOLD, size=9 * scale))
            cor_status   = GOLD
            can_click    = True
        elif liberada:
            icone        = ft.Icons.PLAY_CIRCLE
            cor_icone    = BLUE
            status_lines = [ft.Text("Liberada", color=BLUE, size=10 * scale)]
            cor_status   = BLUE
            can_click    = True
        else:
            icone        = ft.Icons.LOCK
            cor_icone    = "#66FFFFFF"
            status_lines = [ft.Text("Bloqueada", color="#66FFFFFF", size=10 * scale)]
            cor_status   = "#66FFFFFF"
            can_click    = False

        tempo_txt = (
            f"⏱ {ativa.get('tempo_maximo', 600) // 60} min"
            if liberada and ativa else "⏱ —"
        )

        botao_iniciar = ft.Container(
            border_radius=20 * scale,
            bgcolor=BLUE,
            padding=ft.padding.symmetric(horizontal=16 * scale, vertical=10 * scale),
            on_click=(lambda e, n=nome: on_iniciar(n)) if can_click else None,
            ink=True,

            animate_scale=ft.Animation(300, "easeInOut"),  # 👈

            on_hover=lambda e: (
                setattr(e.control, "scale", 1.05 if e.data == "true" else 1),
                e.control.update()
            ),

            content=ft.Text("▶ INICIAR", color=WHITE, size=13 * scale, weight="bold"),
        )
        def hover_linha(e, bloqueada=bloqueada):
            e.control.bgcolor = "#12FFFFFF" if e.data == "true" else (
                "#0AFFFFFF" if not bloqueada else "#06FFFFFF"
            )
            e.control.update()
        linha = ft.Container(
            border_radius=10 * scale,
            bgcolor="#0AFFFFFF" if not bloqueada else "#06FFFFFF",
            
            on_hover=hover_linha,                    # 👈 ADICIONAR
            animate=ft.Animation(200, "easeOut"),
            
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
        width=1050 * scale,
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
#  TELA DE ATIVIDADES (layout com imagem de fundo)
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

        def _voltar_menu(e): menu(page, navegar)
        def _atividades(e): tela_atividades(page, navegar)
        def _historico(e):  historico(page, navegar)
        def _ranking(e):    ranking(page, navegar)
        def _sair(e):       navegar["login"]()
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

        fundo = ft.Image(src=IMAGEM_MENU, width=img_w, height=img_h, fit="fill")

        layout = ft.Container(
            width=img_w,
            height=img_h,
            content=ft.Stack(
                width=img_w,
                height=img_h,
                controls=[
                    fundo,
                    ft.Container(left=0 * scale,   top=0 * scale,   content=_painel_laranja(scale)),
                    ft.Container(left=670 * scale, top=0 * scale,   content=_painel_azul(scale)),
                    ft.Container(left=0 * scale,   top=210 * scale, content=_painel_verde(scale, _atividades, _historico, _ranking, _sair, on_menu=_voltar_menu)),
                    ft.Container(left=292 * scale, top=60 * scale,  content=_painel_lista_atividades(scale, _iniciar)),
                    ft.Container(left=38 * scale,  top=560 * scale, content=_painel_azul_mini(scale)),
                ],
            ),
        )

        page.add(ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=layout))
        page.update()

    page.on_resize = lambda e: build()
    build()


# ============================================================
#  MENU PRINCIPAL (tela com imagem de fundo)
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
        def _historico(e):  historico(page, navegar)
        def _ranking(e):    ranking(page, navegar)
        def _sair(e):       navegar["login"]()
        def _iniciar(nome): navegar["iniciar_atividade"](nome)

        fundo = ft.Image(src=IMAGEM_MENU, width=img_w, height=img_h, fit="fill")

        layout = ft.Container(
            width=img_w,
            height=img_h,
            content=ft.Stack(
                width=img_w,
                height=img_h,
                controls=[
                    fundo,
                    ft.Container(left=0 * scale,   top=0 * scale,   content=_painel_laranja(scale)),
                    ft.Container(left=670 * scale, top=0 * scale,   content=_painel_azul(scale)),
                    ft.Container(left=0 * scale,   top=210 * scale, content=_painel_verde(scale, _atividades, _historico, _ranking, _sair, on_menu=_menu_click)),
                    ft.Container(left=292 * scale, top=60 * scale, content=_painel_lista_atividades(scale, _iniciar)),
                    ft.Container(left=38 * scale,  top=560 * scale, content=_painel_azul_mini(scale)),
                ],
            ),
        )

        page.add(ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=layout))
        page.update()

    page.on_resize = lambda e: build()
    build()


# ============================================================
#  ATIVIDADES
# ============================================================

def atividades(page: ft.Page, navegar):
    page.controls.clear()

    nomes_atividades = [a["nome"] for a in LISTA_ATIVIDADES]
    dados            = buscar_todos_resultados()

    items = [ft.Text("Atividades Disponíveis", size=25)]

    for atividade in nomes_atividades:
        liberada = any(
            a["atividade"] == atividade and a["turma"] == state.turma_atual
            for a in state.atividades_liberadas
        )
        alunos_que_fizeram = [
            r["aluno"]
            for r in dados
            if r["atividade"] == atividade and r["aluno"] in state.alunos_ativos
        ]

        if alunos_que_fizeram:
            nomes = ", ".join(alunos_que_fizeram)
            items.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=18),
                    ft.Text(f"{atividade}  (já realizada por: {nomes})", color="green"),
                ]),
                padding=ft.padding.symmetric(vertical=2),
            ))
        elif liberada:
            items.append(
                ft.Container(
                    content=ft.TextButton(
                        f"📘 {atividade}  ▶ Iniciar",
                        on_click=(lambda e, nome=ativa["atividade"]: on_iniciar(nome)) if ativa else None,
                        style=ft.ButtonStyle(color="blue"),
                    ),
                    bgcolor=ft.Colors.BLUE_50,
                
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=8),
                )
            )
        else:
            items.append(ft.Row([
                ft.Icon(ft.Icons.LOCK, color="grey", size=16),
                ft.Text(f"{atividade}", color="grey"),
            ]))

    items += [
        ft.Button("Voltar", on_click=lambda e: menu(page, navegar)),
        ft.Button("Sair",   on_click=navegar["login"]),
    ]
    page.add(scrollable(items))
    page.update()


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

        # Melhor nota por atividade
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
                    ft.Container(width=50 * scale, content=ft.Text("T#", color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=70 * scale, content=ft.Text("Final", color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=65 * scale, content=ft.Text("Acertos", color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=60 * scale, content=ft.Text("Erros", color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=70 * scale, content=ft.Text("Tempo", color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=100 * scale, content=ft.Text("Data", color="#AAFFFFFF", size=10 * scale, weight="bold")),
                    ft.Container(width=40 * scale, content=ft.Text("", size=10 * scale)),
                ]),
            )
            blocos.append(header)

            # Agrupar por atividade e numerar tentativas
            contagem = {}
            for r in registros:
                contagem[r["atividade"]] = contagem.get(r["atividade"], 0) + 1
                t_num = contagem[r["atividade"]]
                pts_final = r["pontuacao"]
                is_melhor = pts_final == melhor_por_ativ.get(r["atividade"], -1)

                # Botão para ver detalhes (só se existem dados)
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
                                        ft.Text(f"Sua resposta: {q['resposta_aluno']}", size=12,
                                            color=cor_status, weight="bold"),
                                        ft.Text(f"Correta: {q['resposta_correta']}", size=12, color="#888888"),
                                    ]),
                                ]),
                                ft.Text(f"{q['tentativas']}x", size=12, color="#AAAAAA"),
                                ft.Text(icone_status, size=18),
                            ]),
                        ))

                    acertos_det = sum(1 for q in det if q["acertou"])
                    erros_det = sum(1 for q in det if not q["acertou"])

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

                    dlg = ft.AlertDialog(
                        title=ft.Text(f"📋 {ativ} — {aluno_nome}", size=18, weight="bold"),
                        content=dlg_content,
                    )
                    dlg.actions = [ft.TextButton("Fechar", on_click=lambda ev: _fechar_dlg(dlg))]
                    page.overlay.append(dlg); dlg.open = True; page.update()

                def _fechar_dlg(dlg):
                    dlg.open = False; page.update()

                # Destaque suave na melhor nota
                bg = "#143C4CAF" if is_melhor else "#0AFFFFFF"
                borda = None

                btn_det = ft.Container(
                    width=40 * scale, alignment=ft.Alignment(0, 0),
                    content=ft.IconButton(ft.Icons.VISIBILITY, icon_size=14 * scale,
                        icon_color=BLUE, on_click=_ver_detalhes,
                        tooltip="Ver detalhes das questões"),
                ) if page and tem_detalhes else ft.Container(width=40 * scale)

                linha = ft.Container(
                    border_radius=8 * scale, bgcolor=bg, border=borda,
                    padding=ft.padding.symmetric(horizontal=12 * scale, vertical=7 * scale),
                    content=ft.Row(spacing=4*scale, controls=[
                        ft.Container(width=160 * scale, content=ft.Text(r["atividade"], color=WHITE, size=11 * scale)),
                        ft.Container(width=50 * scale, content=ft.Text(f"T{t_num}", color="#AAFFFFFF", size=11 * scale)),
                        ft.Container(width=70 * scale, content=ft.Text(str(pts_final), color="#F9A825" if is_melhor else WHITE, size=11 * scale, weight="bold" if is_melhor else "normal")),
                        ft.Container(width=65 * scale, content=ft.Text(str(r["acertos"]), color="#4CAF50", size=11 * scale)),
                        ft.Container(width=60 * scale, content=ft.Text(str(r["erros"]), color="#FF5252", size=11 * scale)),
                        ft.Container(width=70 * scale, content=ft.Text(r["tempo"], color=WHITE, size=11 * scale)),
                        ft.Container(width=100 * scale, content=ft.Text(r["data"], color="#77FFFFFF", size=10 * scale)),
                        btn_det,
                    ]),
                )
                blocos.append(linha)

        blocos.append(ft.Container(height=10 * scale))

    if not blocos:
        blocos.append(ft.Text("Nenhum histórico disponível.", color="#66FFFFFF", size=12 * scale))

    return ft.Container(
        width=1050 * scale,
        height=660 * scale,
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
#  TELA DE HISTÓRICO (layout com imagem de fundo)
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

        def _voltar_menu(e): menu(page, navegar)
        def _atividades(e):  tela_atividades(page, navegar)
        def _historico(e):   tela_historico(page, navegar)
        def _ranking(e):     ranking(page, navegar)
        def _sair(e):        navegar["login"]()

        fundo = ft.Image(src=IMAGEM_MENU, width=img_w, height=img_h, fit="fill")

        layout = ft.Container(
            width=img_w,
            height=img_h,
            content=ft.Stack(
                width=img_w,
                height=img_h,
                controls=[
                    fundo,
                    ft.Container(left=0 * scale,   top=0 * scale,   content=_painel_laranja(scale)),
                    ft.Container(left=670 * scale, top=0 * scale,   content=_painel_azul(scale)),
                    ft.Container(left=0 * scale,   top=210 * scale, content=_painel_verde(scale, _atividades, _historico, _ranking, _sair, on_menu=_voltar_menu)),
                    ft.Container(left=292 * scale, top=60 * scale,  content=_painel_historico(scale, page, navegar)),
                    ft.Container(left=38 * scale,  top=560 * scale, content=_painel_azul_mini(scale)),
                ],
            ),
        )

        page.add(ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=layout))
        page.update()

    page.on_resize = lambda e: build()
    build()


# ============================================================
#  HISTÓRICO (versão legada — redireciona para tela_historico)
# ============================================================

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

    total_turma = {
        t: sum(pts.values())
        for t, pts in pts_por_turma.items()
    }

    rank_turmas = sorted(total_turma.items(), key=lambda x: x[1], reverse=True)

    # ───────── LINHA PADRÃO (GERAL) ─────────
    def _rank_line_geral(pos, nome, pts, destaque, turma=""):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(pos, f"{pos}º")
        is_top3 = pos <= 3

        return ft.Container(
            border_radius=10 * scale,
            bgcolor="#143C4CAF" if destaque else "#0AFFFFFF",
            padding=ft.padding.symmetric(horizontal=12 * scale, vertical=8 * scale),
            content=ft.Row(
                spacing=10 * scale,
                controls=[
                    ft.Container(
                        width=40 * scale,
                        content=ft.Text(medal, size=16 * scale if is_top3 else 13 * scale)
                    ),

                    ft.Container(
                        width=160 * scale,
                        content=ft.Text(
                            nome,
                            size=12 * scale,
                            weight="bold" if destaque else "normal",
                            color=BLUE if destaque else WHITE,
                        ),
                    ),

                    ft.Container(
                        width=60 * scale,
                        content=ft.Text(f"Turma{turma}", size=10 * scale, color="#88FFFFFF"),
                    ),

                    ft.Container(expand=True),

                    ft.Container(
                        width=90 * scale,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            controls=[
                                ft.Text(
                                    f"{pts} pts",
                                    size=12 * scale,
                                    weight="bold",
                                    color="#F9A825" if is_top3 else "#CCCCCC",
                                )
                            ],
                        ),
                    ),
                ],
            ),
        )

    # ───────── LINHA PADRÃO (TURMA) ─────────
    def _rank_line(pos, nome, pts, destaque):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(pos, f"{pos}º")

        return ft.Container(
            border_radius=10 * scale,
            bgcolor="#143C4CAF" if destaque else "#0AFFFFFF",
            padding=ft.padding.symmetric(horizontal=12 * scale, vertical=8 * scale),
            content=ft.Row(
                spacing=10 * scale,
                controls=[
                    ft.Container(
                        width=40 * scale,
                        content=ft.Text(medal)
                    ),

                    ft.Container(
                        width=180 * scale,
                        content=ft.Text(
                            nome,
                            size=12 * scale,
                            weight="bold" if destaque else "normal",
                            color=BLUE if destaque else WHITE,
                        ),
                    ),

                    ft.Container(expand=True),

                    ft.Container(
                        width=90 * scale,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            controls=[
                                ft.Text(
                                    f"{pts} pts",
                                    size=12 * scale,
                                    weight="bold",
                                    color="#F9A825",
                                )
                            ],
                        ),
                    ),
                ],
            ),
        )

    # ───────── COLUNA GERAL ─────────
    col_geral = ft.Container(
        expand=True,
        bgcolor="#0AFFFFFF",
        padding=10 * scale,
        border_radius=12 * scale,
        content=ft.Column(
            spacing=6 * scale,
            controls=[
                ft.Text("Ranking Geral", color=WHITE, size=13 * scale, weight="bold"),
                ft.Divider(color="#22FFFFFF"),
                *[
                    _rank_line_geral(i, n, pts, n in alunos_ativos)
                    for i, (n, pts) in enumerate(rank_geral[:10], start=1)
                ]
            ]
        )
    )

    # ───────── COLUNA TURMA ─────────
    rank_turma = rank_por_turma.get(state.turma_atual, [])

    col_turma = ft.Container(
        expand=True,
        bgcolor="#0AFFFFFF",
        padding=10 * scale,
        border_radius=12 * scale,
        content=ft.Column(
            spacing=6 * scale,
            controls=[
                ft.Text(f"Ranking da Turma {state.turma_atual}", color=WHITE, size=13 * scale, weight="bold"),
                ft.Divider(color="#22FFFFFF"),
                *[
                    _rank_line(i, n, pts, n in alunos_ativos)
                    for i, (n, pts) in enumerate(rank_turma[:10], start=1)
                ]
            ]
        )
    )

    col_turmas = ft.Container(
    expand=True,
    bgcolor="#0AFFFFFF",
    padding=10 * scale,
    border_radius=12 * scale,
    content=ft.Column(
        spacing=6 * scale,
        controls=[
            ft.Text("Classificação das Turmas", color=WHITE, size=13 * scale, weight="bold"),
            ft.Divider(color="#22FFFFFF"),
            *[
                ft.Container(
                    border_radius=10 * scale,
                    bgcolor="#143C4CAF" if t == state.turma_atual else "#0AFFFFFF",
                    padding=ft.padding.symmetric(horizontal=12 * scale, vertical=8 * scale),
                    content=ft.Row(
                        spacing=10 * scale,
                        controls=[
                            ft.Container(
                                width=40 * scale,
                                content=ft.Text(
                                    {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}º")
                                ),
                            ),

                            ft.Container(
                                width=120 * scale,
                                content=ft.Text(
                                    f"Turma {t}",
                                    size=12 * scale,
                                    weight="bold" if t == state.turma_atual else "normal",
                                    color=BLUE if t == state.turma_atual else WHITE,
                                ),
                            ),

                            ft.Container(expand=True),

                            ft.Container(
                                width=90 * scale,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.END,
                                    controls=[
                                        ft.Text(
                                            f"{total} pts",
                                            size=12 * scale,
                                            weight="bold",
                                            color="#F9A825",
                                        )
                                    ],
                                ),
                            ),
                        ],
                    ),
                )
                for i, (t, total) in enumerate(rank_turmas, start=1)
            ]
        ],
    ),
)

    return ft.Container(
        width=1050 * scale,
        height=660 * scale,
        padding=ft.padding.symmetric(horizontal=18 * scale, vertical=14 * scale),
        border_radius=16 * scale,
        content=ft.Row(
            spacing=14 * scale,
            controls=[
                col_geral,
                col_turma,
                col_turmas,
            
            ],
        ),
    )










    # ── Helper: linha de ranking GERAL (com destaque top 3 + turma) ─
    
    def _rank_line_geral(pos, nome, pts, is_destaque, turma=""):
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        medal = medals.get(pos, f"{pos}º")

        is_top3 = pos <= 3

        bg = "#143C4CAF" if is_destaque else "#0AFFFFFF"

        return ft.Container(
            border_radius=10 * scale,
            bgcolor=bg,
            padding=ft.padding.symmetric(horizontal=12 * scale, vertical=8 * scale),
            content=ft.Row(
                spacing=14 * scale,
                controls=[
                    ft.Container(
                        width=40 * scale,
                        content=ft.Text(medal, size=16 * scale if is_top3 else 13 * scale)
                    ),

                    ft.Container(
                        width=160 * scale,
                        content=ft.Text(
                            nome,
                            size=12 * scale,
                            weight="bold" if is_destaque else "normal",
                            color=BLUE if is_destaque else WHITE,
                        ),
                    ),

                    ft.Container(
                        width=60 * scale,
                        content=ft.Text(
                            f"T{turma}",
                            size=10 * scale,
                            color="#88FFFFFF",
                        ),
                    ),

                    ft.Container(expand=True),

                    ft.Container(
                        width=90 * scale,
                        alignment=ft.alignment.center_right,
                        content=ft.Text(
                            f"{pts} pts",
                            size=12 * scale,
                            weight="bold",
                            color="#F9A825" if is_top3 else "#CCCCCC",
                        ),
                    ),
                ],
            ),
        )


    # ── Sua posição ──────────────────────────────────────
    cards_posicao = []
    for aluno in alunos_ativos:
        pos_g = posicao_geral(aluno)
        pos_t = posicao_turma(aluno, state.turma_atual)
        pts_g = pts_geral.get(aluno, 0)
        pts_t = pts_por_turma.get(state.turma_atual, {}).get(aluno, 0)

        cards_posicao.append(ft.Container(
            border_radius=10 * scale,
            bgcolor="#1A2F9EDC",
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

    # ── Coluna GERAL ──────────────────────────────────────
    linhas_geral = []
    for i, (n, pts) in enumerate(rank_geral[:10], start=1):
        linhas_geral.append(_rank_line_geral(i, n, pts, n in alunos_ativos, aluno_turma.get(n, "")))

    if not linhas_geral:
        linhas_geral.append(ft.Text("Nenhum resultado.", color="#66FFFFFF", size=11 * scale))

    col_geral = ft.Container(
        expand=True,
        border_radius=12 * scale,
        bgcolor="#0AFFFFFF",
        padding=ft.padding.all(10 * scale),
        content=ft.Column(
            spacing=5 * scale,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(spacing=6 * scale, controls=[
                    ft.Text("🌍", size=13 * scale),
                    ft.Text("Ranking Geral", color=WHITE, size=12 * scale, weight="bold"),
                ]),
                ft.Divider(color="#22FFFFFF", thickness=1),
                *linhas_geral,
            ],
        ),
    )

    # ── Coluna TURMA ─────────────────────────────────────
    rank_minha_turma = rank_por_turma.get(state.turma_atual, [])
    linhas_turma = []
    for i, (n, pts) in enumerate(rank_minha_turma[:10], start=1):
        linhas_turma.append(_rank_line(i, n, pts, n in alunos_ativos))

    if not linhas_turma:
        linhas_turma.append(ft.Text("Nenhum resultado.", color="#66FFFFFF", size=11 * scale))

    col_turma = ft.Container(
        expand=True,
        border_radius=12 * scale,
        bgcolor="#0AFFFFFF",
        padding=ft.padding.all(10 * scale),
        content=ft.Column(
            spacing=5 * scale,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(spacing=6 * scale, controls=[
                    ft.Text("🏫", size=13 * scale),
                    ft.Text(f"Ranking da Turma {state.turma_atual}", color=WHITE, size=12 * scale, weight="bold"),
                ]),
                ft.Divider(color="#22FFFFFF", thickness=1),
                *linhas_turma,
            ],
        ),
    )

    # ── Coluna CLASSIFICAÇÃO DAS TURMAS ──────────────────
    linhas_turmas_classif = []
    for i, (t, total) in enumerate(rank_turmas, start=1):
        destaque = t == state.turma_atual
        medal = medals.get(i, f"{i}º")
        linhas_turmas_classif.append(ft.Container(
            border_radius=8 * scale,
            bgcolor="#1A2F9EDC" if destaque else "#0AFFFFFF",
            padding=ft.padding.symmetric(horizontal=10 * scale, vertical=5 * scale),
            content=ft.Row(spacing=8 * scale, controls=[
                ft.Text(medal, size=13 * scale),
                ft.Text(f"Turma {t}", color=BLUE if destaque else WHITE, size=11 * scale,
                         weight="bold" if destaque else "normal", expand=True),
                ft.Text(f"{total} pts", color="#F9A825" if destaque else "#AAFFFFFF",
                         size=11 * scale, weight="bold"),
            ]),
        ))

    if not linhas_turmas_classif:
        linhas_turmas_classif.append(ft.Text("Nenhum resultado.", color="#66FFFFFF", size=11 * scale))

    col_classif = ft.Container(
        expand=True,
        border_radius=12 * scale,
        bgcolor="#0AFFFFFF",
        padding=ft.padding.all(10 * scale),
        content=ft.Column(
            spacing=5 * scale,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(spacing=6 * scale, controls=[
                    ft.Text("🏆", size=13 * scale),
                    ft.Text("Classif. Turmas", color=WHITE, size=12 * scale, weight="bold"),
                ]),
                ft.Divider(color="#22FFFFFF", thickness=1),
                *linhas_turmas_classif,
            ],
        ),
    )

    return ft.Container(
        width=1050 * scale,
        height=660 * scale,
        border_radius=20 * scale,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        padding=ft.padding.symmetric(horizontal=18 * scale, vertical=14 * scale),
        content=ft.Column(
            spacing=8 * scale,
            controls=[
                # Título
                ft.Row(spacing=8 * scale, controls=[
                    ft.Icon(ft.Icons.LEADERBOARD, color="#F9A825", size=20 * scale),
                    ft.Text("Ranking", color=WHITE, size=16 * scale, weight="bold"),
                ]),
                # Sua posição
                *cards_posicao,
                ft.Divider(color="#22FFFFFF", thickness=1),
                # Três colunas lado a lado
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
#  TELA DE RANKING (layout com imagem de fundo)
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

        def _voltar_menu(e): menu(page, navegar)
        def _atividades(e):  tela_atividades(page, navegar)
        def _historico(e):   tela_historico(page, navegar)
        def _ranking(e):     tela_ranking(page, navegar)
        def _sair(e):        navegar["login"]()

        fundo = ft.Image(src=IMAGEM_MENU, width=img_w, height=img_h, fit="fill")

        layout = ft.Container(
            width=img_w,
            height=img_h,
            content=ft.Stack(
                width=img_w,
                height=img_h,
                controls=[
                    fundo,
                    ft.Container(left=0 * scale,   top=0 * scale,   content=_painel_laranja(scale)),
                    ft.Container(left=670 * scale, top=0 * scale,   content=_painel_azul(scale)),
                    ft.Container(left=0 * scale,   top=210 * scale, content=_painel_verde(scale, _atividades, _historico, _ranking, _sair, on_menu=_voltar_menu)),
                    ft.Container(left=292 * scale, top=60 * scale,  content=_painel_ranking(scale)),
                    ft.Container(left=38 * scale,  top=560 * scale, content=_painel_azul_mini(scale)),
                ],
            ),
        )

        page.add(ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=layout))
        page.update()

    page.on_resize = lambda e: build()
    build()


# ============================================================
#  RANKING (versão legada — redireciona para tela_ranking)
# ============================================================

def ranking(page: ft.Page, navegar):
    tela_ranking(page, navegar)