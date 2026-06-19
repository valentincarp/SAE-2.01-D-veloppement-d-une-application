from flask import Blueprint, render_template, request
from models.db import Session
from models.dimensions import ProfessionSante, Departement, Region # N'oublie pas d'importer Region !
from services.ameli_api import AmeliAPI

bp_effectifs = Blueprint("effectifs", __name__)
api = AmeliAPI()

@bp_effectifs.route("/effectifs")
def afficher():
    db_session = Session()
    try:
        # 1. TRAITEMENT SYSTÉMATIQUE : On charge toujours les listes pour les menus déroulants
        regions = db_session.query(Region).order_by(Region.libelle).all()
        professions = db_session.query(ProfessionSante).order_by(ProfessionSante.libelle).all()
        
        # 2. RÉCUPÉRATION DES PARAMÈTRES (peuvent être None lors de la première visite)
        profession_id = request.args.get("profession_id", type=int)
        departement_id = request.args.get("departement_id", type=int)
        annee = request.args.get("annee", type=int)
        
        # Initialisation des variables de résultats par défaut (vide)
        prof = None
        dept = None
        resultats = None
        evolution = None

        # 3. TRAITEMENT CONDITIONNEL : Si l'utilisateur a soumis le formulaire
        if profession_id and departement_id and annee:
            prof = db_session.get(ProfessionSante, profession_id)
            dept = db_session.get(Departement, departement_id)
            
            if prof and dept:
                # On appelle l'API uniquement si les données de base sont valides
                resultats = api.get_effectifs(prof.libelle, dept.code, annee)
                evolution = api.get_evolution_effectifs(prof.libelle, dept.code)

        # 4. ENVOI AU TEMPLATE : On envoie absolument tout (les listes ET les potentiels résultats)
        return render_template("effectifs.html",
            regions=regions, professions=professions, # Indispensable pour le formulaire
            prof=prof, dept=dept, annee=annee,
            resultats=resultats, evolution=evolution)
            
    finally:
        db_session.close()