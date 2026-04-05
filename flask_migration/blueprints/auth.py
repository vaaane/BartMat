"""blueprints/auth.py — Login, logout e verificação de senha."""
import json, os
from flask import Blueprint, render_template, request, redirect, url_for, session
from constants import ALUNOS_POR_TURMA

auth_bp = Blueprint("auth", __name__)


def _senha_professor():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "dados", "config.json",
    )
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("senha_professor", "123")
    except Exception:
        return "123"


@auth_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login")
def login():
    return render_template(
        "login.html",
        turmas=list(ALUNOS_POR_TURMA.keys()),
        alunos_json=json.dumps(ALUNOS_POR_TURMA, ensure_ascii=False),
        erro=session.pop("erro_login", None),
        erro_prof=session.pop("erro_professor", None),
    )


@auth_bp.route("/entrar_aluno", methods=["POST"])
def entrar_aluno():
    turma  = request.form.get("turma",  "").strip()
    aluno1 = request.form.get("aluno1", "").strip()
    aluno2 = request.form.get("aluno2", "").strip()

    if not turma or not aluno1:
        session["erro_login"] = "Selecione a turma e pelo menos um aluno."
        return redirect(url_for("auth.login"))
    if aluno2 == "Nenhum":
        aluno2 = ""
    if aluno1 and aluno2 and aluno1 == aluno2:
        session["erro_login"] = "Os dois alunos não podem ser iguais."
        return redirect(url_for("auth.login"))

    session["turma"]  = turma
    session["alunos"] = [a for a in (aluno1, aluno2) if a]
    session["modo"]   = "aluno"
    return redirect(url_for("aluno.menu"))


@auth_bp.route("/entrar_professor", methods=["POST"])
def entrar_professor():
    if request.form.get("senha", "") == _senha_professor():
        session["modo"] = "professor"
        return redirect(url_for("professor.dashboard"))
    session["erro_professor"] = "Senha incorreta."
    return redirect(url_for("auth.login") + "#tab-professor")


@auth_bp.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("auth.login"))
