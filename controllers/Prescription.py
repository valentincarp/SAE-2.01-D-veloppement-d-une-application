from flask import Blueprint, render_template, request
from models.db import Session
from models.dimensions import ProfessionSante, Departement, Region, TypePrescription
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
        regions = session.query(Region).order_by(Region.libelle).all()
        professions = session.query(ProfessionSante).order_by(ProfessionSante.libelle).all()
        types_prescriptions = session.query(TypePrescription).order_by(TypePrescription.libelle).all()
        if not profession_id or not departement_id or not annee:
            return render_template("prescriptions.html",
            regions=regions, professions=professions, types_prescriptions=types_prescriptions,
            prof=None, resultats=None)
        resultats = api.get_prescriptions(prof.libelle, dept.code, annee, poste_prescription)
        evolution = api.get_evolution_prescriptions(prof.libelle, dept.code, poste_prescription)

        return render_template("prescriptions.html",
            prof=prof, dept=dept, annee=annee,
            resultats=resultats, evolution=evolution,
            regions=regions, professions=professions, types_prescriptions=types_prescriptions)
    finally:
        session.close()