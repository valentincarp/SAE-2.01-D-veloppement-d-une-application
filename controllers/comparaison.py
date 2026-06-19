from flask import Blueprint, render_template, request
from models.db import Session
from models.dimensions import ProfessionSante, Departement, Region
from services.ameli_api import AmeliAPI

bp_comparaison = Blueprint("comparaison", __name__)
api = AmeliAPI()

@bp_comparaison.route("/comparaison")
def comparaison():
    """Affiche la page de comparaison entre 2 départements."""
    profession_id = request.args.get("profession_id", type=int)
    departement1_id = request.args.get("departement1_id", type=int)
    departement2_id = request.args.get("departement2_id", type=int)
    annee = request.args.get("annee", type=int)
    type_comparaison = request.args.get("type_comparaison", default="effectifs")

    session = Session()
    try:
        regions = session.query(Region).order_by(Region.libelle).all()
        professions = session.query(ProfessionSante).order_by(ProfessionSante.libelle).all()
        
        prof = None
        dept1 = None
        dept2 = None
        evolution1 = []
        evolution2 = []
        
        if profession_id and departement1_id and departement2_id and annee:
            prof = session.get(ProfessionSante, profession_id)
            dept1 = session.get(Departement, departement1_id)
            dept2 = session.get(Departement, departement2_id)
            
            if not prof or not dept1 or not dept2:
                return render_template("erreur.html", message="Paramètres invalides."), 400
            
            if type_comparaison == "effectifs":
                evolution1 = api.get_evolution_effectifs(prof.libelle, dept1.code)
                evolution2 = api.get_evolution_effectifs(prof.libelle, dept2.code)
            elif type_comparaison == "honoraires":
                evolution1 = api.get_evolution_honoraires(prof.libelle, dept1.code)
                evolution2 = api.get_evolution_honoraires(prof.libelle, dept2.code)

        return render_template("comparaison.html",
            regions=regions, professions=professions,
            prof=prof, dept1=dept1, dept2=dept2, annee=annee,
            evolution1=evolution1, evolution2=evolution2,
            type_comparaison=type_comparaison)
    finally:
        session.close()