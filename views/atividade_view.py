"""
views/atividade_view.py — Motor da atividade com layout visual.
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import time, asyncio, flet as ft, threading
from datetime import datetime
from fractions import Fraction

import state
from constants import FATOR_ATRASO, LABEL_TIPO, LISTA_ATIVIDADES, BASE_DIR, formatar_tempo, scrollable, carregar_perguntas
from controllers.historico_controller import (
    adicionar_resultado, atualizar_resultado, buscar_todos_resultados,
    salvar_detalhes_questoes, contar_tentativas,
    registrar_conquista, buscar_conquistas, verificar_conquista_existente,
    registrar_alerta, verificar_tentativas_suspeitas,
)

def _beep(freq, dur):
    try:
        import winsound
        threading.Thread(target=winsound.Beep, args=(freq, dur), daemon=True).start()
    except Exception:
        pass  # Sem suporte a áudio no ambiente atual

BLUE="#2F9EDC"; ORANGE="#FF7A2F"; WHITE="#FFFFFF"; GREEN="#4CAF50"; RED="#FF5252"
GOLD="#F9A825"; BG_DARK="#1E1E2E"; CARD_BG="#2A2A3C"; CARD_BG2="#33334A"
MAX_TENTATIVAS=2

def _respostas_equivalentes(a,c):
    a,c=a.strip(),c.strip()
    if a==c: return True
    try: return Fraction(a)==Fraction(c)
    except: pass
    try: return abs(float(a)-float(c))<1e-9
    except: return False

def _build_leaderboard(nome_ativ, scale):
    dados=buscar_todos_resultados()
    regs=[r for r in dados if r["atividade"]==nome_ativ]
    mg,td,mt={},{},{}
    for r in regs:
        a,t=r["aluno"],r["turma"]
        if a not in mg or r["pontuacao"]>mg[a]: mg[a]=r["pontuacao"]; td[a]=t
        if t==state.turma_atual:
            if a not in mt or r["pontuacao"]>mt[a]: mt[a]=r["pontuacao"]
    tg=sorted(mg.items(),key=lambda x:x[1],reverse=True)[:3]
    tt=sorted(mt.items(),key=lambda x:x[1],reverse=True)[:3]
    m={1:"🥇",2:"🥈",3:"🥉"}
    l=[ft.Text("🌍 Top 3 Geral",size=11*scale,weight="bold",color=WHITE)]
    for i,(n,p) in enumerate(tg,1):
        d=n in state.alunos_ativos
        l.append(ft.Row(spacing=4*scale,controls=[
            ft.Text(f"  {m[i]} {n}",size=10*scale,color=BLUE if d else "#CCFFFFFF",weight="bold" if d else "normal"),
            ft.Text(f"Turma {td.get(n,'')}",size=8*scale,color="#66FFFFFF"),
            ft.Text(f"— {p} pts",size=10*scale,color=GOLD if d else "#AAFFFFFF")]))
    if not tg: l.append(ft.Text("  (sem dados)",size=10*scale,color="#66FFFFFF"))
    l.append(ft.Divider(color="#22FFFFFF",thickness=1))
    l.append(ft.Text(f"🏫 Top 3 — Turma {state.turma_atual}",size=11*scale,weight="bold",color=WHITE))
    for i,(n,p) in enumerate(tt,1):
        d=n in state.alunos_ativos
        l.append(ft.Text(f"  {m[i]} {n} — {p} pts",size=10*scale,color=BLUE if d else "#CCFFFFFF",weight="bold" if d else "normal"))
    if not tt: l.append(ft.Text("  (sem dados)",size=10*scale,color="#66FFFFFF"))
    return ft.Container(border_radius=12*scale,bgcolor=CARD_BG2,padding=ft.padding.all(10*scale),
        content=ft.Column(spacing=4*scale,controls=l))

def _get_info_anterior(nome):
    dados=buscar_todos_resultados()
    rp=[r for r in dados if r["atividade"]==nome and r["aluno"] in state.alunos_ativos]
    rt=[r for r in dados if r["atividade"]==nome]
    pts_1a=rp[0]["pontuacao"] if rp else 0
    mp=max((r["pontuacao"] for r in rp),default=0)
    mg=0; am=""; tm=""
    for r in rt:
        if r["pontuacao"]>mg: mg=r["pontuacao"]; am=r["aluno"]; tm=r["turma"]
    # Rankings do aluno nesta atividade
    melhor_por_aluno={}
    turma_por_aluno={}
    for r in rt:
        a=r["aluno"]
        if a not in melhor_por_aluno or r["pontuacao"]>melhor_por_aluno[a]:
            melhor_por_aluno[a]=r["pontuacao"]; turma_por_aluno[a]=r["turma"]
    rank_geral=sorted(melhor_por_aluno.items(),key=lambda x:x[1],reverse=True)
    rank_turma=sorted([(a,p) for a,p in melhor_por_aluno.items() if turma_por_aluno.get(a)==state.turma_atual],
        key=lambda x:x[1],reverse=True)
    # Posição do aluno
    pos_geral=None; pos_turma=None
    for al in state.alunos_ativos:
        for i,(n,_) in enumerate(rank_geral,1):
            if n==al: pos_geral=i; break
        for i,(n,_) in enumerate(rank_turma,1):
            if n==al: pos_turma=i; break
    total_geral=len(rank_geral); total_turma=len(rank_turma)
    return pts_1a,mp,mg,am,tm,pos_geral,total_geral,pos_turma,total_turma

def aguardar_liberacao(page,nome,navegar):
    page.controls.clear(); page.bgcolor=BG_DARK
    ref={"r":True}

    # Textos de status dinâmicos para cada atividade
    status_texts={a["nome"]:ft.Text("",size=11,color="#AAFFFFFF") for a in LISTA_ATIVIDADES}

    def _status_lib(a_nome):
        lib=next((x for x in state.atividades_liberadas if x["atividade"]==a_nome and x["turma"]==state.turma_atual),None)
        if not lib: return "⏳ Aguardando", "#AAFFFFFF"
        exp=lib.get("expira_em")
        if exp:
            from datetime import datetime as _dt
            rem=(_dt.fromisoformat(exp)-_dt.now()).total_seconds()
            if rem>0:
                m,s=int(rem//60),int(rem%60)
                return f"🟢 Liberada — expira em {m}:{s:02d}", GREEN
            return "🔴 Expirada", RED
        return "🟢 Liberada", GREEN

    W=page.width or 1366; H=page.height or 768; sc=min(W/1366,H/768)
    cards=[]
    for a in LISTA_ATIVIDADES:
        st,cor=_status_lib(a["nome"])
        txt=ft.Text(st,size=11*sc,color=cor)
        status_texts[a["nome"]]=txt
        destaque=a["nome"]==nome
        cards.append(ft.Container(border_radius=12*sc,bgcolor=CARD_BG if not destaque else "#1A2F9EDC",
            border=ft.border.all(1.5 if destaque else 1, BLUE if destaque else "#22FFFFFF"),
            padding=ft.padding.all(12*sc),
            content=ft.Row(spacing=10*sc,controls=[
                ft.Icon(ft.Icons.LOCK_CLOCK if destaque else ft.Icons.MENU_BOOK,
                    color=BLUE if destaque else "#66FFFFFF",size=18*sc),
                ft.Column(spacing=2,expand=True,controls=[
                    ft.Text(a["nome"],color=WHITE if destaque else "#AAFFFFFF",
                        size=12*sc,weight="bold" if destaque else "normal"),
                    txt]),
            ])))

    def cancelar(e):
        ref["r"]=False
        from views import aluno_view; aluno_view.menu(page,navegar)

    page.add(ft.Container(expand=True,bgcolor=BG_DARK,
        padding=ft.padding.symmetric(horizontal=60*sc,vertical=40*sc),
        content=ft.Column(spacing=16*sc,horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
            ft.Icon(ft.Icons.SCHOOL,size=48*sc,color=BLUE),
            ft.Text("Aguardando liberação",size=20*sc,weight="bold",color=WHITE),
            ft.Text(f"Turma {state.turma_atual}  •  {', '.join(state.alunos_ativos)}",
                size=12*sc,color="#AAFFFFFF"),
            ft.Divider(color="#22FFFFFF",thickness=1),
            ft.Text("Status das atividades:",size=11*sc,color="#88FFFFFF"),
            *cards,
            ft.Container(height=8*sc),
            ft.ElevatedButton("← Voltar ao Menu",on_click=cancelar,
                style=ft.ButtonStyle(bgcolor="#33FFFFFF",color=WHITE,
                    shape=ft.RoundedRectangleBorder(radius=12))),
        ])))
    page.update()

    async def poll():
        while ref["r"]:
            lib=next((a for a in state.atividades_liberadas if a["atividade"]==nome and a["turma"]==state.turma_atual),None)
            if lib: ref["r"]=False; iniciar(page,nome,navegar); return
            # Atualiza status de todas as atividades
            for a in LISTA_ATIVIDADES:
                st,cor=_status_lib(a["nome"])
                if a["nome"] in status_texts:
                    status_texts[a["nome"]].value=st; status_texts[a["nome"]].color=cor
            try: page.update()
            except: return
            await asyncio.sleep(3)

    page.run_task(poll)

def iniciar(page,nome,navegar,modo_teste=False):
    page.controls.clear(); page.padding=0; page.bgcolor=BG_DARK
    info_lib=next((a for a in state.atividades_liberadas if a["atividade"]==nome and a["turma"]==state.turma_atual),None)
    if not info_lib and not modo_teste: aguardar_liberacao(page,nome,navegar); return

    tipo_atividade=info_lib["tipo"] if info_lib else "dia"
    tempo_maximo=info_lib.get("tempo_maximo",600) if info_lib else 600
    fator_atraso=FATOR_ATRASO[tipo_atividade]
    perguntas=carregar_perguntas(nome)
    pts_1a,melhor_proprio,melhor_geral,aluno_melhor,turma_melhor,pos_geral,total_geral,pos_turma,total_turma=_get_info_anterior(nome)
    num_tentativa=contar_tentativas(state.alunos_ativos[0],nome)+1 if state.alunos_ativos else 1
    label_tipo=LABEL_TIPO[tipo_atividade]

    estado={"ajuda_usada":False,"indice":0,"pontuacao":0,"respondidas":0,"acertos":0,
        "erros":0,"tentativas":0,"ja_salvo":False,"atividade_ativa":True,
        "resposta_atual":"","processando":False,"resultado_ids":{}}
    historico_perguntas=[]
    inicio=time.time()

    # Registra a tentativa imediatamente (antes de responder qualquer questão)
    if not modo_teste:
        da_inicio=datetime.now().strftime("%d/%m/%Y %H:%M")
        for _al in state.alunos_ativos:
            _rid=adicionar_resultado({"aluno":_al,"turma":state.turma_atual,"atividade":nome,
                "pontuacao_bruta":0,"pontuacao":0,"tipo_atividade":tipo_atividade,
                "fator_atraso":fator_atraso,"acertos":0,"erros":0,
                "tempo":"0s","data":da_inicio,"atraso":tipo_atividade!="dia"})
            estado["resultado_ids"][_al]=_rid
    timer_text=ft.Text(size=18,weight="bold",color=WHITE)
    mensagem=ft.Text(size=13,color=WHITE)
    barra_progresso=ft.ProgressBar(value=0,color=BLUE,bgcolor="#22FFFFFF")
    progresso_label=ft.Text("",size=11,color="#AAFFFFFF")

    def fator_tentativa():
        t=estado["tentativas"]; return [1.0,0.75,0.5,0.25][min(t,3)] if t<4 else 0.0
    def atualizar_barra():
        total=len(perguntas); f=estado["respondidas"]
        barra_progresso.value=f/total if total>0 else 0
        barra_progresso.color=GREEN if f==total else BLUE
        progresso_label.value=f"{f} questões respondidas"
    def registrar_questao(acertou):
        historico_perguntas.append({"pergunta":perguntas[estado["indice"]]["pergunta"],
            "resposta_aluno":estado["resposta_atual"] or "—",
            "resposta_correta":perguntas[estado["indice"]]["resposta"],
            "tentativas":estado["tentativas"],"acertou":acertou})
    def salvar_resultado():
        if estado["ja_salvo"]: return
        estado["ja_salvo"]=True
        if modo_teste: return
        fim=time.time(); tt=round(fim-inicio); da=datetime.now().strftime("%d/%m/%Y %H:%M")
        pb=estado["pontuacao"]; pf=max(1,int(pb*fator_atraso)) if pb>0 else 0
        for al in state.alunos_ativos:
            dados_finais={"pontuacao_bruta":pb,"pontuacao":pf,"tipo_atividade":tipo_atividade,
                "fator_atraso":fator_atraso,"acertos":estado["acertos"],"erros":estado["erros"],
                "tempo":f"{tt}s","data":da,"atraso":tipo_atividade!="dia"}
            if al in estado["resultado_ids"]:
                rid=estado["resultado_ids"][al]
                atualizar_resultado(rid,dados_finais)
            else:
                rid=adicionar_resultado({"aluno":al,"turma":state.turma_atual,"atividade":nome,**dados_finais})
            salvar_detalhes_questoes(rid,historico_perguntas)

    def _handle_close(e=None):
        def cancelar(ev): dlg.open=False; page.update()
        def confirmar(ev):
            dlg.open=False; page.update()
            estado["atividade_ativa"]=False
            state.fechar_fn=None
            if len(historico_perguntas)<=estado["indice"]: registrar_questao(False)
            salvar_resultado(); page.window.destroy()
        dlg=ft.AlertDialog(modal=True,title=ft.Text("Fechar o sistema"),
            content=ft.Text(
                "Uma atividade está em andamento.\n\n"
                "Ao fechar, o progresso será salvo e esta tentativa será contada.",
                size=13),
            actions=[ft.TextButton("Cancelar",on_click=cancelar),
                ft.ElevatedButton("Fechar e salvar",on_click=confirmar,
                    style=ft.ButtonStyle(bgcolor="#FF5252",color="white"))])
        page.overlay.append(dlg); dlg.open=True; page.update()
    state.fechar_fn=_handle_close

    def proxima():
        if not estado["atividade_ativa"]: return
        if estado["indice"]<len(perguntas)-1:
            estado["indice"]+=1; estado["ajuda_usada"]=False
            estado["tentativas"]=0; estado["processando"]=False; mostrar_pergunta()
        else:
            estado["atividade_ativa"]=False; state.fechar_fn=None; salvar_resultado(); _tela_parabens()

    def _tela_parabens():
        page.controls.clear()
        fim=time.time(); tt=round(fim-inicio); pb=estado["pontuacao"]
        pf=max(1,int(pb*fator_atraso)) if pb>0 else 0
        page.add(scrollable([ft.Container(height=40),
            ft.Icon(ft.Icons.EMOJI_EVENTS,size=64,color="amber"),
            ft.Text("🎉 Parabéns, você respondeu todas as questões!",size=22,weight="bold",text_align="center"),
            ft.Text("A atividade será encerrada.",size=16,color="#AAAAAA",text_align="center"),
            ft.Container(height=8),
            ft.Text(f"Pontuação: {pf} pts  •  Acertos: {estado['acertos']}  •  Tempo: {formatar_tempo(tt)}",
                size=16,text_align="center"),
            ft.Container(height=24),
            ft.ElevatedButton("Ver resultado completo",icon=ft.Icons.BAR_CHART,
                on_click=lambda e:finalizar(),style=ft.ButtonStyle(bgcolor="green",color="white"))]))
        page.update()

    def _verificar_conquistas(pf, tt):
        """Verifica e concede conquistas após uma atividade."""
        novas=[]
        data_agora=datetime.now().strftime("%d/%m/%Y %H:%M")
        for al in state.alunos_ativos:
            hist_al=[r for r in buscar_todos_resultados() if r["aluno"]==al]
            hist_ativ=[r for r in hist_al if r["atividade"]==nome]
            def _conceder(tipo, desc):
                if not verificar_conquista_existente(al,tipo,nome):
                    registrar_conquista({"aluno":al,"turma":state.turma_atual,
                        "atividade":nome,"tipo":tipo,"descricao":desc,"data":data_agora})
                    novas.append(desc)
            # Desempenho
            if estado["erros"]==0 and estado["respondidas"]>0:
                _conceder("sem_erros","Sem erros! ✨")
            todas_1a=all(h["tentativas"]==1 and not h.get("ajuda") for h in historico_perguntas) and len(historico_perguntas)>0 and estado["erros"]==0
            if todas_1a:
                _conceder("nota_maxima","Nota máxima! 🏆")
            if tempo_maximo and tt < tempo_maximo*0.5 and estado["respondidas"]>0:
                _conceder("top_velocidade","Top velocidade! ⚡")
            # Evolução
            if not hist_al:
                _conceder("primeira_atividade","Primeira atividade! 🎉")
            else:
                prev_ativ=[r["pontuacao"] for r in hist_ativ if r["id"]!=max((r["id"] for r in hist_ativ),default=0)]
                if prev_ativ and pf>max(prev_ativ):
                    _conceder("melhorou_nota","Melhorou a nota! 📈")
                max_geral=max((r["pontuacao"] for r in hist_al),default=0)
                if pf>max_geral:
                    _conceder("superou_recorde_pessoal","Novo recorde pessoal! 🌟")
        return novas

    def finalizar(tempo_esgotado=False):
        estado["atividade_ativa"]=False; state.fechar_fn=None; salvar_resultado()
        page.controls.clear()
        page.bgcolor=BG_DARK
        fim=time.time(); tt=round(fim-inicio); pb=estado["pontuacao"]
        pf=max(1,int(pb*fator_atraso)) if pb>0 else 0; lt=LABEL_TIPO[tipo_atividade]

        # Conquistas e alertas
        novas_conquistas=_verificar_conquistas(pf, tt)
        for al in state.alunos_ativos:
            if verificar_tentativas_suspeitas(al, nome):
                registrar_alerta({"aluno":al,"turma":state.turma_atual,"atividade":nome,
                    "motivo":f"3+ tentativas em 10 minutos","data":datetime.now().strftime("%d/%m/%Y %H:%M")})

        W=page.width or 1366; H=page.height or 768; sc=min(W/1366,H/768)

        # Banner de conquistas
        banner_conquistas=[]
        if novas_conquistas:
            chips=[ft.Container(border_radius=12*sc,bgcolor="#22FFD700",
                padding=ft.padding.symmetric(horizontal=10*sc,vertical=4*sc),
                content=ft.Text(c,color=GOLD,size=11*sc,weight="bold")) for c in novas_conquistas]
            banner_conquistas.append(ft.Container(border_radius=12*sc,bgcolor="#1AFFD700",
                border=ft.border.all(1.5,GOLD),padding=ft.padding.all(12*sc),
                content=ft.Column(spacing=6*sc,horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                    ft.Row(spacing=6*sc,alignment=ft.MainAxisAlignment.CENTER,controls=[
                        ft.Text("🏆",size=18*sc),
                        ft.Text("Conquistas desbloqueadas!",color=GOLD,size=13*sc,weight="bold")]),
                    ft.Row(spacing=6*sc,wrap=True,alignment=ft.MainAxisAlignment.CENTER,controls=chips),
                ])))

        # Header
        header_controls=[]
        if tempo_esgotado:
            header_controls.append(ft.Icon(ft.Icons.TIMER_OFF,size=40*sc,color=RED))
            header_controls.append(ft.Text("Tempo esgotado!",size=20*sc,weight="bold",color=RED))
        else:
            header_controls.append(ft.Icon(ft.Icons.EMOJI_EVENTS,size=40*sc,color=GOLD))
            header_controls.append(ft.Text("Resultado Final",size=20*sc,weight="bold",color=WHITE))

        # Stats cards
        stats_row=ft.Row(spacing=12*sc,alignment=ft.MainAxisAlignment.CENTER,controls=[
            ft.Container(border_radius=12*sc,bgcolor=CARD_BG2,padding=ft.padding.all(14*sc),
                content=ft.Column(spacing=2,horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                    ft.Text(f"{pf}",color=GOLD,size=28*sc,weight="bold"),
                    ft.Text("Pontuação",color="#AAFFFFFF",size=10*sc)])),
            ft.Container(border_radius=12*sc,bgcolor=CARD_BG2,padding=ft.padding.all(14*sc),
                content=ft.Column(spacing=2,horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                    ft.Text(f"{estado['acertos']}",color=GREEN,size=28*sc,weight="bold"),
                    ft.Text("Acertos",color="#AAFFFFFF",size=10*sc)])),
            ft.Container(border_radius=12*sc,bgcolor=CARD_BG2,padding=ft.padding.all(14*sc),
                content=ft.Column(spacing=2,horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                    ft.Text(f"{estado['erros']}",color=RED,size=28*sc,weight="bold"),
                    ft.Text("Erros",color="#AAFFFFFF",size=10*sc)])),
            ft.Container(border_radius=12*sc,bgcolor=CARD_BG2,padding=ft.padding.all(14*sc),
                content=ft.Column(spacing=2,horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                    ft.Text(formatar_tempo(tt),color=WHITE,size=22*sc,weight="bold"),
                    ft.Text("Tempo",color="#AAFFFFFF",size=10*sc)])),
            ft.Container(border_radius=12*sc,bgcolor=CARD_BG2,padding=ft.padding.all(14*sc),
                content=ft.Column(spacing=2,horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                    ft.Text(f"{estado['respondidas']}",color=BLUE,size=28*sc,weight="bold"),
                    ft.Text("Respondidas",color="#AAFFFFFF",size=10*sc)])),
        ])

        # Info de atraso
        info_extra=[]
        if modo_teste:
            info_extra.append(ft.Text("🧪 MODO TESTE — resultado não salvo",color=ORANGE,size=12*sc,weight="bold"))
        if fator_atraso<1:
            info_extra.append(ft.Container(border_radius=8*sc,bgcolor="#33FF7A2F",
                padding=ft.padding.all(8*sc),
                content=ft.Text(f"⚠️ Atividade {lt} — fator {int(fator_atraso*100)}%  •  Bruto: {pb} → Final: {pf} pts",
                    color=ORANGE,size=11*sc,weight="bold",text_align="center")))

        # Revisão das questões
        questoes_cards=[]
        for i,h in enumerate(historico_perguntas,1):
            cor_bg="#1A4CAF50" if h["acertou"] else "#1AFF5252"
            borda_cor=GREEN if h["acertou"] else RED
            questoes_cards.append(ft.Container(border_radius=8*sc,bgcolor=cor_bg,
                border=ft.border.all(1,borda_cor),
                padding=ft.padding.symmetric(horizontal=12*sc,vertical=8*sc),
                content=ft.Row(spacing=8*sc,vertical_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                    ft.Text(f"Q{i}",size=11*sc,weight="bold",color="#AAFFFFFF",width=30*sc),
                    ft.Column(spacing=1,expand=True,controls=[
                        ft.Text(h["pergunta"],size=11*sc,color=WHITE),
                        ft.Row(spacing=10*sc,controls=[
                            ft.Text(f"Resp: {h['resposta_aluno']}",size=10*sc,color=GREEN if h["acertou"] else RED,weight="bold"),
                            ft.Text(f"Correta: {h['resposta_correta']}",size=10*sc,color="#88FFFFFF"),
                        ]),
                    ]),
                    ft.Text(f"{h['tentativas']}x",size=10*sc,color="#AAFFFFFF"),
                    ft.Text("✅" if h["acertou"] else "❌",size=14*sc),
                ])))

        # Questões não respondidas
        for i in range(len(historico_perguntas),len(perguntas)):
            questoes_cards.append(ft.Container(border_radius=8*sc,bgcolor="#0AFFFFFF",
                padding=ft.padding.symmetric(horizontal=12*sc,vertical=8*sc),
                content=ft.Row(spacing=8*sc,controls=[
                    ft.Text(f"Q{i+1}",size=11*sc,color="#66FFFFFF",width=30*sc),
                    ft.Text(perguntas[i]["pergunta"],size=11*sc,color="#66FFFFFF",expand=True),
                    ft.Text("⬜",size=14*sc),
                ])))

        # Botões
        botoes=ft.Row(spacing=12*sc,alignment=ft.MainAxisAlignment.CENTER,controls=[
            ft.ElevatedButton("Voltar ao Menu",icon=ft.Icons.HOME,on_click=navegar["menu_aluno"],
                style=ft.ButtonStyle(bgcolor=BLUE,color=WHITE,shape=ft.RoundedRectangleBorder(radius=12))),
            ft.TextButton("Sair",on_click=navegar["login"],style=ft.ButtonStyle(color="#AAFFFFFF")),
        ])

        # Montagem
        conteudo=ft.Column(spacing=12*sc,scroll=ft.ScrollMode.AUTO,expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                ft.Container(height=10*sc),
                *banner_conquistas,
                ft.Row(spacing=10*sc,alignment=ft.MainAxisAlignment.CENTER,controls=header_controls),
                ft.Container(height=4*sc),
                stats_row,
                *info_extra,
                ft.Divider(color="#22FFFFFF",thickness=1),
                ft.Text("📋 Revisão das Questões",size=14*sc,weight="bold",color=WHITE),
                *questoes_cards,
                ft.Container(height=8*sc),
                botoes,
                ft.Container(height=10*sc),
            ])

        page.add(ft.Container(expand=True,bgcolor=BG_DARK,
            padding=ft.padding.symmetric(horizontal=40*sc,vertical=10*sc),content=conteudo))
        page.update()

    async def timer_loop():
        while estado["atividade_ativa"]:
            el=time.time()-inicio; rem=tempo_maximo-el
            if rem<=0:
                estado["atividade_ativa"]=False
                timer_text.value=f"⏱ {formatar_tempo(tempo_maximo)} / {formatar_tempo(tempo_maximo)} — ESGOTADO"
                timer_text.color=RED
                if len(historico_perguntas)<=estado["indice"]: registrar_questao(False)
                finalizar(tempo_esgotado=True); return
            timer_text.color=RED if rem<=120 else WHITE
            a=f"  ⚠️ {int(rem)}s" if rem<=30 else ""
            timer_text.value=f"⏱ {formatar_tempo(el)} / {formatar_tempo(tempo_maximo)}{a}"
            try: page.update()
            except: break
            await asyncio.sleep(1)

    async def avancar_apos_acerto():
        await asyncio.sleep(1.5)
        if estado["atividade_ativa"]: proxima()
    async def avancar_apos_erro():
        await asyncio.sleep(2.0)
        if estado["atividade_ativa"]: proxima()

    def mostrar_pergunta():
        if not estado["atividade_ativa"]: return
        page.controls.clear(); estado["resposta_atual"]=""; estado["processando"]=False
        W=page.width or 1366; H=page.height or 768; scale=min(W/1366,H/768)
        perg=perguntas[estado["indice"]]
        if perg["dificuldade"]==1: niv,base,cdif="Fácil",10,GREEN
        elif perg["dificuldade"]==2: niv,base,cdif="Média",20,GOLD
        else: niv,base,cdif="Difícil",30,RED

        resp_input=ft.TextField(label="Digite sua resposta",autofocus=True,border_color="#44FFFFFF",
            color=WHITE,label_style=ft.TextStyle(color="#88FFFFFF"),cursor_color=WHITE,
            bgcolor="#0AFFFFFF",border_radius=12,on_submit=lambda e:responder(e))
        info_text=ft.Text(size=11*scale,color="#AAFFFFFF")
        pts_total=ft.Text(size=16*scale,weight="bold",color=GOLD)
        alt_text=ft.Text("",size=14*scale,color=WHITE)
        btn_ref=ft.Ref[ft.ElevatedButton]()

        def att_info():
            fa=0.5 if estado["ajuda_usada"] else 1; at=int(base*fator_tentativa()*fa)
            pts_total.value=f"🏆 {estado['pontuacao']} pts"
            info_text.value=f"Valor máx: {base}  •  Vale agora: {at} pts"
        def ajuda(e):
            if estado["ajuda_usada"]: mensagem.value="⚠️ Ajuda já utilizada"; page.update(); return
            estado["ajuda_usada"]=True; estado["tentativas"]=0
            alt_text.value="Opções:  "+"   |   ".join(perg["alternativas"])
            mensagem.value="💡 Alternativas exibidas (-50%)"; att_info(); page.update()
        def responder(e):
            if estado["processando"]: return
            estado["processando"]=True
            if btn_ref.current: btn_ref.current.disabled=True; page.update()
            r=resp_input.value.strip()
            if not r:
                mensagem.value="⚠️ Digite uma resposta"; estado["processando"]=False
                if btn_ref.current: btn_ref.current.disabled=False; page.update(); return
            estado["resposta_atual"]=r; ft_=fator_tentativa(); fa=0.5 if estado["ajuda_usada"] else 1
            if _respostas_equivalentes(r,perg["resposta"]):
                estado["acertos"]+=1; p=max(1,int(base*ft_*fa))
                estado["pontuacao"]+=p; estado["respondidas"]+=1; estado["tentativas"]+=1
                registrar_questao(True); mensagem.value=f"✅ Correto! +{p} pontos"
                mensagem.color=GREEN; _beep(1000,150); page.update(); page.run_task(avancar_apos_acerto)
            else:
                estado["tentativas"]+=1
                if estado["tentativas"]<4:
                    mensagem.value=f"❌ Errado ({estado['tentativas']}/4)"; mensagem.color=RED
                    att_info(); estado["processando"]=False
                    if btn_ref.current: btn_ref.current.disabled=False; page.update()
                else:
                    estado["erros"]+=1; estado["respondidas"]+=1; registrar_questao(False)
                    mensagem.value=f"❌ Errou 4x — Resposta: {perg['resposta']}"
                    mensagem.color=RED; _beep(400,300); page.update(); page.run_task(avancar_apos_erro)

        def conf_encerrar(e):
            dlg=ft.AlertDialog(modal=True,title=ft.Text("Encerrar atividade"),
                content=ft.Text(
                    "Tem certeza que deseja encerrar?\n\n"
                    "O resultado parcial será salvo e esta tentativa será contada.",
                    size=13))
            def f(ev): dlg.open=False; page.update()
            def c(ev):
                dlg.open=False; page.update(); estado["atividade_ativa"]=False
                state.fechar_fn=None
                if len(historico_perguntas)<=estado["indice"]: registrar_questao(False)
                finalizar()
            dlg.actions=[
                ft.TextButton("Cancelar",on_click=f),
                ft.ElevatedButton("Encerrar e salvar",on_click=c,
                    style=ft.ButtonStyle(bgcolor="#FF5252",color="white"))]
            page.overlay.append(dlg); dlg.open=True; page.update()

        atualizar_barra(); att_info()
        p_atual=estado["pontuacao"]

        # ══════════════════════════════════════
        #  PAINEL ESQUERDO — Info + Regras
        # ══════════════════════════════════════
        info_controls=[]

        # 1) MAIOR NOTA GERAL — menor, com turma
        if melhor_geral>0:
            info_controls.append(ft.Container(border_radius=10*scale,
                bgcolor="#33FFD700",border=ft.border.all(1.5,GOLD),
                padding=ft.padding.symmetric(horizontal=10*scale,vertical=6*scale),
                content=ft.Row(spacing=6*scale,alignment=ft.MainAxisAlignment.CENTER,controls=[
                    ft.Text("⭐",size=14*scale),
                    ft.Text(f"{melhor_geral} pts",color=GOLD,size=13*scale,weight="bold"),
                    ft.Text(f"— {aluno_melhor} (Turma {turma_melhor})",color=WHITE,size=11*scale),
                ])))

        # 2) Ranking do aluno nesta atividade
        if pos_geral is not None:
            info_controls.append(ft.Container(border_radius=8*scale,bgcolor=CARD_BG2,
                padding=ft.padding.all(8*scale),
                content=ft.Column(spacing=2,horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                    ft.Text(f"📊 Seu ranking nesta atividade",color="#AAFFFFFF",size=9*scale),
                    ft.Row(spacing=12*scale,alignment=ft.MainAxisAlignment.CENTER,controls=[
                        ft.Text(f"{pos_geral}º/{total_geral} geral",color=GOLD,size=11*scale,weight="bold"),
                        ft.Text(f"{pos_turma}º/{total_turma} turma",color=WHITE,size=11*scale),
                    ]),
                ])))
        else:
            info_controls.append(ft.Container(border_radius=8*scale,bgcolor=CARD_BG2,
                padding=ft.padding.all(8*scale),
                content=ft.Text("📊 Sem ranking — primeira atividade!",color="#AAFFFFFF",
                    size=10*scale,text_align="center")))

        # 3) Tentativa anterior (se 2ª)
        if num_tentativa>=2 and pts_1a>0:
            info_controls.append(ft.Container(border_radius=8*scale,bgcolor=CARD_BG2,
                padding=ft.padding.all(8*scale),
                content=ft.Column(spacing=2,horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                    ft.Text(f"1ª tentativa: {pts_1a} pts",color="#AAFFFFFF",size=10*scale),
                    ft.Text(f"Agora: {p_atual} pts",color=WHITE,size=11*scale,weight="bold"),
                ])))

        # 4) Acertos/Erros
        info_controls.append(ft.Row(spacing=0,alignment=ft.MainAxisAlignment.SPACE_EVENLY,controls=[
            ft.Column(spacing=2,horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                ft.Text(str(estado["acertos"]),color=GREEN,size=20*scale,weight="bold"),
                ft.Text("Acertos",color="#AAFFFFFF",size=9*scale)]),
            ft.Container(width=1,height=30*scale,bgcolor="#22FFFFFF"),
            ft.Column(spacing=2,horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                ft.Text(str(estado["erros"]),color=RED,size=20*scale,weight="bold"),
                ft.Text("Erros",color="#AAFFFFFF",size=9*scale)]),
        ]))

        info_controls.append(ft.Divider(color="#22FFFFFF",thickness=1))

        # 4) Leaderboard
        info_controls.append(_build_leaderboard(nome,scale))
        info_controls.append(ft.Divider(color="#22FFFFFF",thickness=1))

        # 5) REGRAS — bem visível
        pct_atraso = int(fator_atraso * 100)
        regras_text = (
            f"📏 REGRAS DA ATIVIDADE\n\n"
            f"• Dificuldade: Fácil = 10 pts, Média = 20 pts, Difícil = 30 pts\n"
            f"• Cada erro reduz o valor: 100% → 75% → 50% → 25% → 0 pts\n"
            f"• Usar opções (-50% do valor da questão)\n"
            f"• Tipo: {label_tipo} — fator {pct_atraso}%"
        )
        if fator_atraso < 1:
            regras_text += f"\n   ⚠️ Atividade com atraso! Nota final = bruta × {pct_atraso}%"

        info_controls.append(ft.Container(border_radius=10*scale,
            bgcolor="#1A2F9EDC",border=ft.border.all(1,BLUE),
            padding=ft.padding.all(10*scale),
            content=ft.Text(regras_text,color=WHITE,size=9*scale)))

        info_controls.append(ft.Divider(color="#22FFFFFF",thickness=1))

        # 6) Botões
        # Botão rever questões respondidas
        n_resp=len(historico_perguntas)
        if n_resp>0:
            def ver_respondidas(e):
                linhas=[]
                for i,h in enumerate(historico_perguntas,1):
                    cor_r="#2E7D32" if h["acertou"] else "#C62828"
                    linhas.append(ft.Container(border_radius=8,bgcolor="#F5F5F5",
                        border=ft.border.all(1,"#E0E0E0"),
                        padding=ft.padding.symmetric(horizontal=10,vertical=8),
                        content=ft.Column(spacing=3,controls=[
                            ft.Row(spacing=6,controls=[
                                ft.Text(f"Q{i}",color="#666666",size=10,weight="bold",width=24),
                                ft.Text("✅" if h["acertou"] else "❌",size=13),
                                ft.Text(f"{h['tentativas']}x",color="#888888",size=10),
                            ]),
                            ft.Text(h["pergunta"],color="#222222",size=11),
                            ft.Row(spacing=8,controls=[
                                ft.Text(f"Sua resp: {h['resposta_aluno']}",color=cor_r,size=10,weight="bold"),
                                ft.Text(f"Correta: {h['resposta_correta']}",color="#555555",size=10),
                            ]),
                        ])))
                def fechar_dlg(ev): dlg_r.open=False; page.update()
                dlg_r=ft.AlertDialog(modal=True,
                    title=ft.Text(f"📋 Questões respondidas ({n_resp})"),
                    content=ft.Container(width=420,height=400,
                        content=ft.Column(spacing=8,scroll=ft.ScrollMode.AUTO,controls=linhas)),
                    actions=[ft.ElevatedButton("Fechar",on_click=fechar_dlg)])
                page.overlay.append(dlg_r); dlg_r.open=True; page.update()
            info_controls.append(ft.Container(border_radius=10*scale,bgcolor="#0A2F9EDC",
                padding=ft.padding.symmetric(horizontal=12*scale,vertical=6*scale),
                on_click=ver_respondidas,ink=True,
                content=ft.Row(spacing=6*scale,alignment=ft.MainAxisAlignment.CENTER,controls=[
                    ft.Icon(ft.Icons.LIST_ALT,color=BLUE,size=14*scale),
                    ft.Text(f"Ver respondidas ({n_resp})",color=BLUE,size=10*scale,weight="bold")])))

        info_controls.append(ft.Container(border_radius=10*scale,bgcolor="#33FF5252",
            padding=ft.padding.symmetric(horizontal=12*scale,vertical=8*scale),
            on_click=conf_encerrar,ink=True,
            content=ft.Row(spacing=6*scale,alignment=ft.MainAxisAlignment.CENTER,controls=[
                ft.Icon(ft.Icons.STOP_CIRCLE,color=RED,size=16*scale),
                ft.Text("Encerrar atividade",color=RED,size=11*scale,weight="bold")])))

        painel_esq=ft.Container(expand=2,border_radius=16*scale,bgcolor=CARD_BG,
            padding=ft.padding.all(14*scale),clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(spacing=8*scale,scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=info_controls))

        # ══════════════════════════════════════
        #  PAINEL DIREITO — Pergunta
        # ══════════════════════════════════════
        painel_dir=ft.Container(expand=3,border_radius=16*scale,bgcolor=CARD_BG,
            padding=ft.padding.all(20*scale),clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(spacing=14*scale,scroll=ft.ScrollMode.AUTO,controls=[
                ft.Row(spacing=8*scale,controls=[
                    ft.Container(border_radius=20*scale,bgcolor=cdif,
                        padding=ft.padding.symmetric(horizontal=12*scale,vertical=4*scale),
                        content=ft.Text(niv,color=WHITE,size=11*scale,weight="bold")),
                    info_text]),
                ft.Container(border_radius=12*scale,bgcolor="#15FFFFFF",
                    padding=ft.padding.all(18*scale),
                    content=ft.Text(perg["pergunta"],size=22*scale,color=WHITE,weight="bold")),
                alt_text,resp_input,
                ft.Row(spacing=10*scale,controls=[
                    ft.ElevatedButton("Responder",on_click=responder,ref=btn_ref,
                        style=ft.ButtonStyle(bgcolor=BLUE,color=WHITE,shape=ft.RoundedRectangleBorder(radius=12))),
                    ft.TextButton("💡 Mostrar opções (-50%)",on_click=ajuda,style=ft.ButtonStyle(color=GOLD))]),
                mensagem]))

        # BARRA TOPO
        bt=ft.Container(height=65*scale,bgcolor=ORANGE,
            padding=ft.padding.symmetric(horizontal=20*scale,vertical=8*scale),
            content=ft.Row(vertical_alignment=ft.CrossAxisAlignment.CENTER,controls=[
                ft.Container(border_radius=10*scale,bgcolor="#33000000",
                    padding=ft.padding.symmetric(horizontal=14*scale,vertical=6*scale),content=timer_text),
                ft.Container(width=16*scale),
                ft.Column(spacing=2*scale,expand=True,controls=[
                    ft.Text(nome,color=WHITE,size=15*scale,weight="bold"),
                    ft.Text(f"👤 {', '.join(state.alunos_ativos)}  •  Turma {state.turma_atual}",
                        color="#DDFFFFFF",size=10*scale)]),
                ft.Container(border_radius=10*scale,bgcolor="#33000000",
                    padding=ft.padding.symmetric(horizontal=14*scale,vertical=6*scale),content=pts_total)]))
        bp=ft.Container(height=28*scale,bgcolor="#15FFFFFF",
            padding=ft.padding.symmetric(horizontal=20*scale,vertical=4*scale),
            content=ft.Row(spacing=10*scale,vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[ft.Container(expand=True,content=barra_progresso),progresso_label]))
        ac=ft.Container(padding=ft.padding.only(left=16*scale,right=16*scale,top=8*scale,bottom=8*scale),
            expand=True,content=ft.Row(spacing=14*scale,expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,controls=[painel_esq,painel_dir]))

        page.add(ft.Column(spacing=0,expand=True,controls=[bt,bp,ac])); page.update()

    page.run_task(timer_loop); mostrar_pergunta()
