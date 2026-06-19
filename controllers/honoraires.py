from flask import Blueprint, render_template, request
from models.db import Session
from models.dimensions import Departement, Region, TypeHonoraire, ProfessionSante
from sqlalchemy import and_

bp_honoraires = Blueprint("honoraires", __name__)

@bp_honoraires.route("/honoraires")
def afficher():
    session = Session()
    try:
        #Chargement des données globales pour les listes déroulantes
        regions = session.query(Region).order_by(Region.libelle).all()
        professions = session.query(ProfessionSante).order_by(ProfessionSante.libelle).all()

        #Récupération des IDs du formulaire
        profession_id = request.args.get("profession_id", type=int) # Changé pour correspondre au HTML
        region_id = request.args.get("region_id", type=int)
        departement_id = request.args.get("departement_id", type=int)
        annee = request.args.get("annee", type=int, default=2023)
        
        type_niv1 = request.args.get("type_niv1")
        type_niv2 = request.args.get("type_niv2")
        type_niv3 = request.args.get("type_niv3")

        #Gestion des listes de cascades locales (pour ton HTML)
        honoraires_niv1 = [r[0] for r in session.query(TypeHonoraire.niveau_1).distinct().order_by(TypeHonoraire.niveau_1).all()]
        if len(honoraires_niv1) == 1 and not type_niv1:
            type_niv1 = honoraires_niv1[0]

        honoraires_niv2 = []
        if type_niv1:
            query_niv2 = session.query(TypeHonoraire.niveau_2)\
                                .filter(TypeHonoraire.niveau_1 == type_niv1, TypeHonoraire.niveau_2.isnot(None))\
                                .distinct().order_by(TypeHonoraire.niveau_2).all()
            honoraires_niv2 = [r[0] for r in query_niv2]

        honoraires_niv3 = []
        if type_niv1:
            filtre_niv3 = [TypeHonoraire.niveau_1 == type_niv1, TypeHonoraire.niveau_3.isnot(None)]
            if type_niv2:
                filtre_niv3.append(TypeHonoraire.niveau_2 == type_niv2)
            query_niv3 = session.query(TypeHonoraire.niveau_3).filter(and_(*filtre_niv3)).distinct().order_by(TypeHonoraire.niveau_3).all()
            honoraires_niv3 = [r[0] for r in query_niv3]

        departements = []
        if region_id:
            departements = session.query(Departement).filter(Departement.region_id == region_id).order_by(Departement.libelle).all()

        #Traitement et Requête API Ameli
        dept = None
        resultats = None
        evolution = None

        if profession_id and type_niv1 and type_niv2 and departement_id:
            dept = session.get(Departement, departement_id)
            prof_obj = session.get(ProfessionSante, profession_id)
            
            if dept and prof_obj:
                if type_niv2 == "Dépassements":
                    ameli_niv1 = "Dépassements"
                    ameli_niv2 = None
                else:
                    ameli_niv1 = "Actes" 
                    ameli_niv2 = "Actes cliniques" if type_niv3 == "Moyens" else None

                from services.ameli_api import AmeliAPI
                api = AmeliAPI()
                
                resultats = api.get_honoraires(ameli_niv1, ameli_niv2, None,
                                               dept.code, annee, prof_obj.libelle)

                try:
                    evolution = api.get_evolution_honoraires(ameli_niv1, None, None,
                                                             dept.code, prof_obj.libelle)
                except Exception as e:
                    print("Erreur lors de la récupération de l'évolution :", e)
                    evolution = None

        if isinstance(resultats, dict) and "results" in resultats:
            resultats = resultats["results"]
            
        if isinstance(evolution, dict) and "results" in evolution:
            evolution = evolution["results"]

        #debug
        print("debug tableau :", resultats)
        print("debug graphe :", evolution)
            
        return render_template(
            "honoraires.html",
            regions=regions,
            departements=departements,
            professions=professions,
            honoraires_niv1=honoraires_niv1,
            honoraires_niv2=honoraires_niv2,
            honoraires_niv3=honoraires_niv3,
            profession_id=profession_id,
            region_id=region_id,
            departement_id=departement_id,
            type_niv1=type_niv1,
            type_niv2=type_niv2,
            type_niv3=type_niv3,
            dept=dept,
            annee=annee,
            resultats=resultats,
            evolution=evolution
        )
    finally:
        session.close()