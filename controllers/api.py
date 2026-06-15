from flask import Blueprint, jsonify, request
from models.db import Session
from models.dimensions import Departement
from services.ameli_api import AmeliAPI

bp_api = Blueprint("api", __name__, url_prefix="/api")
api = AmeliAPI()

@bp_api.route("/departements/<int:region_id>")
def departements(region_id):
    """Retourne les départements d'une région au format JSON."""
    session = Session()
    try:
        depts = (session.query(Departement)
        .filter_by(region_id=region_id)
        .order_by(Departement.code).all())
        return jsonify([{"id": d.id, "code": d.code, "libelle": d.libelle} for d in depts])
    finally:
        session.close()

@bp_api.route("/densites")
def densites():
    """Retourne les densités de tous les départements pour une profession et une année."""
    profession = request.args.get("profession")
    annee = request.args.get("annee", type=int)

    session = Session()
    try:
        # On récupère tous les départements de la base
        departements = session.query(Departement).all()
        resultats = []
        for dept in departements:
            # Pour chaque département on appelle l'API ameli
            data = api.get_effectifs(profession, dept.code, annee)
            if data:
                resultats.append({
                    "code": dept.code,
                    "libelle": dept.libelle,
                    "densite": data[0].get("densite", 0)
                })
        return jsonify(resultats)
    finally:
        session.close()