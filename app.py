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
from flask_login import LoginManager
from models.dimensions import Utilisateur
from models.db import Session
from controllers.login import bp_login
from controllers.admin import bp_admin

app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = "testcle"

# Configuration de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login" # Redirection si accès interdit
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    db_session = Session()
    try:
        return db_session.get(Utilisateur, int(user_id))
    finally:
        db_session.close()

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
app.register_blueprint(bp_login)
app.register_blueprint(bp_admin)

api = AmeliAPI()
t = time.time(); api.get_effectifs("...", "75", 2023); print(time.time() - t)
# 1er appel : ~0.5s
t = time.time(); api.get_effectifs("...", "75", 2023); print(time.time() - t)
# 2e appel : ~0.00002s

# Configuration de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login" # Redirection si accès interdit
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    db_session = Session()
    try:
        return db_session.get(Utilisateur, int(user_id))
    finally:
        db_session.close()

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
