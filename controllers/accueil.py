from flask import Blueprint, render_template, session
from models.db import Session

bp_accueil = Blueprint("accueil", __name__)

@bp_accueil.route("/")
def index():
    """Page d'accueil"""
    db_session = Session()  # Attention : j'ai renommé en db_session (voir plus bas)
    try:
        # On utilise render_template pour renvoyer le fichier HTML
        return render_template('accueil.html')
    finally:
        db_session.close()