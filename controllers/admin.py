from flask import Blueprint, render_template
from flask_login import login_required
from models.db import Session
from models.dimensions import ProfessionSante, Region, Departement, TypePrescription

bp_admin = Blueprint("admin", __name__, url_prefix="/admin")

@bp_admin.route("/")
@login_required
def index():
    session = Session()
    try:
        # On affiche des statistiques rapides sur le panneau d'administration
        nb_professions = session.query(ProfessionSante).count()
        nb_regions = session.query(Region).count()
        nb_departements = session.query(Departement).count()
        nb_prescriptions = session.query(TypePrescription).count()
        
        return render_template("admin.html", 
                               nb_professions=nb_professions,
                               nb_regions=nb_regions,
                               nb_departements=nb_departements,
                               nb_prescriptions=nb_prescriptions)
    finally:
        session.close()