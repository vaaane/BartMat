import sys
import os

# Adiciona flask_migration/ ao path para que 'blueprints' seja encontrado
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_migration"))

from app import app
