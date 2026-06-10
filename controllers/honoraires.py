from flask import Blueprint, render_template, request
from models.db import Session
from models.dimensions import ProfessionSante, Departement, TypeHonoraire
from services.ameli_api import AmeliAPI

bp_honoraires = Blueprint("honoraires", __name__)
api = AmeliAPI()

@bp_honoraires.route("/honoraires")
def afficher():
    """Affiche les honoraires selon les filtres sélectionnés."""
    # 1. On récupère les paramètres de l'URL (qui valent None au premier affichage)
    profession_id = request.args.get("profession_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    type_honoraire_id = request.args.get("type_honoraire_id", type=int)
    annee = request.args.get("annee", type=int)

    session = Session()
    try:
        # 2. On récupère TOUJOURS les données pour les <select> du formulaire HTML
        toutes_professions = session.query(ProfessionSante).all()
        tous_departements = session.query(Departement).all()
        tous_types_honoraires = session.query(TypeHonoraire).all()
        
        # Variables pour stocker la recherche de l'utilisateur (vides par défaut)
        prof_selectionne = None
        dept_selectionne = None
        hono_selectionne = None
        donnees_api = None

        # 3. SI le formulaire a été soumis (tous les paramètres sont là)
        if profession_id and departement_id and type_honoraire_id and annee:
            prof_selectionne = session.get(ProfessionSante, profession_id)
            dept_selectionne = session.get(Departement, departement_id)
            hono_selectionne = session.get(TypeHonoraire, type_honoraire_id)
            
            if prof_selectionne and dept_selectionne and hono_selectionne:
                # C'est ici qu'on va appeler l'API !
                # Exemple : donnees_api = api.get_honoraires(prof_selectionne.libelle, dept_selectionne.code, annee, hono_selectionne.niveau_1)
                # Dans ton if :
                donnees_api = api.get_honoraires(prof_selectionne.libelle, dept_selectionne.code, annee)                
        
        # 4. On renvoie le template unique de ta page
        return render_template("honoraires.html",
                               professions=toutes_professions,
                               departements=tous_departements,
                               types_honoraires=tous_types_honoraires,
                               prof_sel=prof_selectionne,
                               dept_sel=dept_selectionne,
                               hono_sel=hono_selectionne,
                               annee=annee,
                               resultats=donnees_api)
    finally:
        session.close()