from flask import Blueprint, render_template
from flask_login import login_required
from models.db import Session
from models.dimensions import ProfessionSante, Region, Departement, TypePrescription
from services.ameli_api import AmeliAPI

bp_admin = Blueprint("admin", __name__, url_prefix="/admin")
api = AmeliAPI()

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
        part_hommes_femmes = api.get_part_hommes_femmes()
        
        return render_template("admin.html", 
                               nb_professions=nb_professions,
                               nb_regions=nb_regions,
                               nb_departements=nb_departements,
                               nb_prescriptions=nb_prescriptions,
                               part_hommes_femmes=part_hommes_femmes)
    finally:
        session.close()