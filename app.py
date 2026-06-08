from flask import Flask
from config import Config
from controllers.accueil import bp_accueil
from controllers.api import bp_api
from controllers.effectifs import bp_effectifs

app = Flask(__name__)
app.config.from_object(Config)

# Enregistrement des contrôleurs (blueprints)
app.register_blueprint(bp_accueil)
app.register_blueprint(bp_api)
app.register_blueprint(bp_effectifs)

if __name__ == "__main__":
    app.run(debug=True)
