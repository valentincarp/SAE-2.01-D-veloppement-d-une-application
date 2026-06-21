from models.db import Session, engine
from models.dimensions import Utilisateur, Base
from dotenv import load_dotenv
import os

load_dotenv()

# Crée la table au cas où elle n'existe pas encore
Base.metadata.create_all(engine)

db_session = Session()

# Vérifie si l'admin éxiste déjà et le créé s'il n'éxiste pas
if not db_session.query(Utilisateur).filter_by(identifiant="admin").first():
    admin = Utilisateur(identifiant="admin")
    admin.set_password(os.getenv('ADMIN_MDP'))
    db_session.add(admin)
    db_session.commit()
    print("Administrateur créé avec succès !")
else:
    print("L'administrateur existe déjà.")

db_session.close()