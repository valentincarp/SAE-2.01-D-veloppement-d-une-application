from flask import Blueprint, render_template
from models.db import Session

bp_a_propos = Blueprint("a_propos", __name__)

@bp_a_propos.route("/a_propos")
def afficher():
    session = Session()
    try:
        return render_template("apropos.html")
    finally:
        session.close()
