"""
flask_migration/app.py — Factory do app Flask.
Registra blueprints e configura o app.
"""
import sys, os

# Coloca o diretório raiz do projeto no path para que
# todos os blueprints possam importar constants, controllers etc.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask
from blueprints.auth      import auth_bp
from blueprints.aluno     import aluno_bp
from blueprints.professor import professor_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = "chave_secreta_dev_2024"   # trocar em produção

    app.register_blueprint(auth_bp)
    app.register_blueprint(aluno_bp)
    app.register_blueprint(professor_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
