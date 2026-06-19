from flask import Flask, render_template
from config import Config
from controllers.accueil import bp_accueil
from controllers.api import bp_api
from controllers.effectifs import bp_effectifs
from controllers.prescription import bp_prescription
from controllers.honoraires import bp_honoraires
from controllers.export import bp_export
from controllers.comparaison import bp_comparaison
from services.ameli_api import AmeliAPI
import time
from controllers.carte import bp_carte
from controllers.effectifs import bp_effectifs
from controllers.apropos import bp_a_propos

app = Flask(__name__)
app.config.from_object(Config)

# Enregistrement des contrôleurs (blueprints)
app.register_blueprint(bp_accueil)
app.register_blueprint(bp_api)
app.register_blueprint(bp_effectifs)
app.register_blueprint(bp_prescription)
app.register_blueprint(bp_honoraires)
app.register_blueprint(bp_export)
app.register_blueprint(bp_comparaison)
app.register_blueprint(bp_carte)
app.register_blueprint(bp_a_propos)

api = AmeliAPI()
t = time.time(); api.get_effectifs("...", "75", 2023); print(time.time() - t)
# 1er appel : ~0.5s
t = time.time(); api.get_effectifs("...", "75", 2023); print(time.time() - t)
# 2e appel : ~0.00002s

@app.errorhandler(404)
def page_non_trouvee(e):
    return render_template("erreur.html",
        message="Page non trouvée."), 404

@app.errorhandler(500)
def erreur_serveur(e):
    return render_template("erreur.html",
        message="Erreur interne. Réessayez plus tard."), 500

if __name__ == "__main__":
    app.run(debug=True)
