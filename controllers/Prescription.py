from flask import Blueprint, render_template, request
from models.db import Session
from models.dimensions import ProfessionSante, Departement
from services.ameli_api import AmeliAPI

bp_prescription = Blueprint("prescriptions", __name__)
api = AmeliAPI()

@bp_prescription.route("/prescriptions")
def afficher():
    profession_id = request.args.get("profession_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    annee = request.args.get("annee", type=int)
    poste_prescription = request.args.get("poste_prescription", type=int)

    session = Session()
    try:
        prof = session.get(ProfessionSante, profession_id)
        dept = session.get(Departement, departement_id)
        if not prof or not dept or not annee:
            return render_template("erreur.html", message="Paramètres manquants."), 400
        resultats = api.get_prescriptions(prof.libelle, dept.code, annee, poste_prescription)
        evolution = api.get_evolution_prescriptions(prof.libelle, dept.code, poste_prescription)

        return render_template("prescriptions.html",
            prof=prof, dept=dept, annee=annee,
            resultats=resultats, evolution=evolution)
    finally:
        session.close()