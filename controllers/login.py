from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.db import Session
from models.dimensions import Utilisateur

bp_login = Blueprint("auth", __name__)

@bp_login.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.index"))

    if request.method == "POST":
        identifiant = request.form.get("identifiant")
        password = request.form.get("password")
        
        db_session = Session()
        try:
            user = db_session.query(Utilisateur).filter_by(identifiant=identifiant).first()
            if user and user.check_password(password):
                login_user(user)
                flash("Connexion réussie !", "success")
                # Gère la redirection "next" si l'utilisateur tentait d'accéder à une page protégée
                prochaine_page = request.args.get("next")
                return redirect(prochaine_page or url_for("admin.index"))
            else:
                flash("Identifiant ou mot de passe incorrect.", "danger")
        finally:
            db_session.close()
            
    return render_template("login.html")

@bp_login.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("auth.login"))