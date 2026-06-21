import requests
from services.cache import avec_cache

class AmeliAPI:
    """Service d'accès à l'API data.ameli.fr."""

    BASE_URL = "https://data.ameli.fr/api/explore/v2.1/catalog/datasets"
 
    def __init__(self, timeout=10):
        self._timeout = timeout
        self._session = requests.Session()

    @avec_cache(duree_vie_seconde=300)
    def get_effectifs(self, profession, departement_code, annee):
        """Effectifs pour une profession, un département et une année.
        Retourne une liste de dictionnaires {annee, effectif, densite}.
        """
        where = (
            f"profession_sante=\"{profession}\" AND "
            f"departement=\"{departement_code}\" AND "
            f"year(annee)={annee} AND "
            f"libelle_classe_age=\"Tout âge\" AND "
            f"libelle_sexe=\"tout sexe\""
        )
        return self._requete(
            "demographie-effectifs-et-les-densites",
            {"select": "annee,effectif,densite", "where": where, "limit": 100},
        )
    
    def _build_honoraires_where(self, niv1, niv2, niv3, departement_code, annee=None, profession=None):
        """Construit le filtre WHERE de manière robuste."""
        clauses = []
        
        if departement_code:
            # L'API Ameli exige 2 ou 3 chiffres (ex: "01" pour l'Ain, pas "1")
            code_propre = str(departement_code).zfill(2)
            clauses.append(f'departement="{code_propre}"')
            
        if niv1:
            clauses.append(f'type_honoraires_niveau_1="{niv1}"')
        if niv2:
            clauses.append(f'type_honoraires_niveau_2="{niv2}"')
        if niv3:
            clauses.append(f'type_honoraires_niveau_3="{niv3}"')
            
        if annee:
            clauses.append(f"year(annee)={annee}")
            
        if profession:
            # Gère le piège du singulier/pluriel automatique
            if not profession.endswith('s') and profession not in ["Autres médecins", "Anesthésistes-réanimateurs"]:
                clauses.append(f'(profession_sante="{profession}" OR profession_sante="{profession}s")')
            else:
                clauses.append(f'profession_sante="{profession}"')
            
        return " AND ".join(clauses) if clauses else "1=1"

    @avec_cache(duree_vie_seconde=300)
    def get_honoraires(self, niv1, niv2, niv3, departement_code, annee, profession=None):
        """Récupère les honoraires d'une année spécifique."""
        where = self._build_honoraires_where(niv1, niv2, niv3, departement_code, annee, profession)

        bruts = self._requete(
            "honoraires-detailles",
            {
                "select": "year(annee), profession_sante, SUM(montant_honoraires) as montant_honoraires",
                "where": where,
                "group_by": "profession_sante, year(annee)",
                "order_by": "profession_sante",
                "limit": 100,
            },
        )
        
        liste_noeuds = bruts.get("results", bruts) if isinstance(bruts, dict) else bruts
        
        resultats_propres = []
        for item in liste_noeuds:
            resultats_propres.append({
                "annee": annee,
                "profession_sante": item.get("profession_sante", "Inconnu"),
                "montant_honoraires": item.get("montant_honoraires")
            })
            
        return resultats_propres

    # NOTE : il existait ici deux définitions de get_evolution_honoraires
    # (un reste de conflit de merge non résolu jusqu'au bout). En Python,
    # seule la dernière définition d'une méthode portant le même nom est
    # gardée, ce qui faisait planter tous les appels avec 5 arguments en
    # utilisant silencieusement l'ancienne version à 2 arguments. On ne garde
    # que la version moderne, cohérente avec get_honoraires ci-dessus
    # (même dataset "honoraires-detailles", même filtre via _build_honoraires_where).
    @avec_cache(duree_vie_seconde=600)
    def get_evolution_honoraires(self, niv1, niv2, niv3, departement_code, profession=None):
        """Récupère l'évolution temporelle pour Chart.js (triée par ordre chronologique)."""
        where = self._build_honoraires_where(
            niv1=niv1, 
            niv2=niv2, 
            niv3=niv3, 
            departement_code=departement_code, 
            annee=None,
            profession=profession
        )

        bruts = self._requete(
            "honoraires-detailles",
            {
                "select": "annee, profession_sante, montant_honoraires",
                "where": where,
                "limit": 100,
            },
        )
        
        liste_noeuds = bruts.get("results", bruts) if isinstance(bruts, dict) else bruts
        
        evolution_propre = []
        if isinstance(liste_noeuds, list):
            for item in liste_noeuds:
                annee_brute = item.get("annee")
                if annee_brute:
                    evolution_propre.append({
                        "annee": int(str(annee_brute)[:4]), # Extrait "2022" de "2022-01-01"
                        "profession_sante": item.get("profession_sante", "Inconnu"),
                        "montant_honoraires": float(item.get("montant_honoraires") or 0.0)
                    })
                    
        evolution_propre.sort(key=lambda x: x["annee"])
        return evolution_propre

    @avec_cache(duree_vie_seconde=600)
    def get_evolution_effectifs(self, profession, departement_code):
        """Effectifs sur toutes les années disponibles (pour un graphique)."""
        where = (f"profession_sante=\"{profession}\" AND "
            f"departement=\"{departement_code}\" AND "
            f"libelle_classe_age=\"Tout âge\" AND "
            f"libelle_sexe=\"tout sexe\""
        )
        return self._requete(
            "demographie-effectifs-et-les-densites",
            {"select": "annee,effectif,densite", "where": where,
            "order_by": "annee", "limit": 100},
        )

    def _requete(self, dataset, params):
        """Méthode privée : effectue une requête GET et gère les erreurs."""
        url = f"{self.BASE_URL}/{dataset}/records"
        try:
            resp = self._session.get(url, params=params, timeout=self._timeout)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except requests.RequestException as e:
            print(f"[AmeliAPI] Erreur : {e}")
        return []
    
    @avec_cache(duree_vie_seconde=300)
    def get_prescriptions(self, profession, departement_code, annee, poste):
        where = (
            f"profession_sante=\"{profession}\" AND "
            f"departement=\"{departement_code}\" AND "
            f"year(annee)={annee} AND "
            f"poste_prescription={poste}"
        )
        return self._requete(
            "prescriptions",
        {"select": "annee, poste_prescription, libelle_poste_prescription, montant_total_prescription, montant_moyen_prescription", "where": where, "limit": 100},
        )
    
    @avec_cache(duree_vie_seconde=600)
    def get_evolution_prescriptions(self, profession, departement_code, poste):
        where = (
            f"profession_sante=\"{profession}\" AND "
            f"departement=\"{departement_code}\" AND "
            f"poste_prescription={poste}"
        )
        return self._requete(
            "prescriptions",
        {"select": "annee, poste_prescription, libelle_poste_prescription, montant_total_prescription, montant_moyen_prescription", "where": where,
            "order_by": "annee", "limit": 100},
        )