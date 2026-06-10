from flask import Flask, render_template
from config import Config
from controllers.accueil import bp_accueil
from controllers.api import bp_api
from controllers.effectifs import bp_effectifs
from controllers.Prescription import bp_prescription


app = Flask(__name__)
app.config.from_object(Config)

# Enregistrement des contrôleurs (blueprints)
app.register_blueprint(bp_accueil)
app.register_blueprint(bp_api)
app.register_blueprint(bp_effectifs)
app.register_blueprint(bp_prescription)

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
