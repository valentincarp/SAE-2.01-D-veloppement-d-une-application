from flask import Blueprint, render_template
from models.db import Session
from models.dimensions import ProfessionSante
from services.ameli_api import AmeliAPI

bp_carte = Blueprint("carte", __name__)
api = AmeliAPI()

@bp_carte.route("/carte")
def afficher():
    # On ouvre une connexion à la base de données
    session = Session()
    try:
        # On récupère toutes les professions triées par ordre alphabétique
        # pour remplir la liste déroulante du formulaire
        professions = session.query(ProfessionSante).order_by(ProfessionSante.libelle).all()
        
        # On envoie les professions au template carte.html pour les afficher
        return render_template("carte.html", professions=professions)
    finally:
        # On ferme toujours la connexion même si une erreur survient
        session.close()