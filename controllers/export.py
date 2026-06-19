import csv
import io
import matplotlib
matplotlib.use("Agg")  # mode sans interface graphique, obligatoire sur un serveur
import matplotlib.pyplot as plt
from flask import Blueprint, request, Response
from models.db import Session
from models.dimensions import ProfessionSante, Departement, TypeHonoraire
from services.ameli_api import AmeliAPI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

bp_export = Blueprint("export", __name__)
api = AmeliAPI()


# ═══════════════════════════════════════════════
# EXPORT EFFECTIFS
# ═══════════════════════════════════════════════

def get_donnees_effectifs(profession_id, departement_id, annee):
    """Récupère prof, dept, effectifs et évolution depuis la base et l'API."""
    session = Session()
    try:
        prof = session.get(ProfessionSante, profession_id)
        dept = session.get(Departement, departement_id)
        resultats = api.get_effectifs(prof.libelle, dept.code, annee)
        evolution = api.get_evolution_effectifs(prof.libelle, dept.code)
        return prof, dept, resultats, evolution
    finally:
        session.close()

@bp_export.route("/export/csv")
def export_csv():
    """Exporte les effectifs au format CSV téléchargeable."""
    profession_id = request.args.get("profession_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    annee = request.args.get("annee", type=int)

    prof, dept, resultats, _ = get_donnees_effectifs(profession_id, departement_id, annee)

    # Création du fichier CSV en mémoire
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # En-tête du CSV
    writer.writerow(["Annee", "Effectif", "Densite"])

    # Une ligne par résultat
    for r in resultats:
        writer.writerow([r.get("annee"), r.get("effectif"), r.get("densite")])

    # utf-8-sig pour que Excel reconnaisse les accents
    response = Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv; charset=utf-8-sig"
    )
    response.headers["Content-Disposition"] = (
        f"attachment; filename=effectifs_{dept.code}_{annee}.csv"
    )
    return response

@bp_export.route("/export/pdf")
def export_pdf():
    """Exporte les effectifs et le graphique d'évolution au format PDF."""
    profession_id = request.args.get("profession_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    annee = request.args.get("annee", type=int)

    prof, dept, resultats, evolution = get_donnees_effectifs(profession_id, departement_id, annee)

    # Génération du graphique avec matplotlib
    annees = [r.get("annee") for r in evolution]
    effectifs = [r.get("effectif") for r in evolution]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(annees, effectifs, color="#2E74B5", linewidth=2)
    ax.set_title("Évolution des effectifs")
    ax.set_xlabel("Année")
    ax.set_ylabel("Effectif")
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.xticks(rotation=45, ha="right")  # années en diagonale pour éviter chevauchement
    plt.tight_layout()

    # Sauvegarde du graphique en mémoire (pas sur le disque)
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close()
    img_buffer.seek(0)

    # Construction du PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Titre du PDF
    titre = f"{prof.libelle} – {dept.code} {dept.libelle} – {annee}"
    elements.append(Paragraph(titre, styles["Title"]))

    # Tableau des données
    data = [["Annee", "Effectif", "Densite"]]
    for r in resultats:
        data.append([r.get("annee"), r.get("effectif"), r.get("densite")])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E74B5")),  # en-tête bleu
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),                  # texte blanc
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),                  # bordures grises
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF4FB")]),
    ]))
    elements.append(table)

    # Ajout du graphique dans le PDF
    elements.append(RLImage(img_buffer, width=500, height=250))

    doc.build(elements)
    buffer.seek(0)

    response = Response(buffer.read(), mimetype="application/pdf")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=effectifs_{dept.code}_{annee}.pdf"
    )
    return response


# ═══════════════════════════════════════════════
# EXPORT PRESCRIPTIONS
# ═══════════════════════════════════════════════

@bp_export.route("/export/csv/prescription")
def export_csv_prescription():
    """Exporte les prescriptions au format CSV téléchargeable."""
    profession_id = request.args.get("profession_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    annee = request.args.get("annee", type=int)
    poste_prescription = request.args.get("poste_prescription", type=int)

    # Récupération des données depuis la base et l'API
    session = Session()
    try:
        prof = session.get(ProfessionSante, profession_id)
        dept = session.get(Departement, departement_id)
        resultats = api.get_prescriptions(prof.libelle, dept.code, annee, poste_prescription)
    finally:
        session.close()

    # Création du CSV en mémoire
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # En-tête du CSV
    writer.writerow(["Annee", "Type prescription", "Libelle poste", "Montant total", "Montant moyen"])

    # Une ligne par résultat
    for r in resultats:
        writer.writerow([
            r.get("annee"),
            r.get("poste_prescription"),
            r.get("libelle_poste_prescription"),
            r.get("montant_total_prescription"),
            r.get("montant_moyen_prescription")
        ])

    # utf-8-sig pour que Excel reconnaisse les accents
    response = Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv; charset=utf-8-sig"
    )
    response.headers["Content-Disposition"] = (
        f"attachment; filename=prescriptions_{dept.code}_{annee}.csv"
    )
    return response

@bp_export.route("/export/pdf/prescription")
def export_pdf_prescription():
    """Exporte les prescriptions et le graphique d'évolution au format PDF."""
    profession_id = request.args.get("profession_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    annee = request.args.get("annee", type=int)
    poste_prescription = request.args.get("poste_prescription", type=int)

    # Récupération des données depuis la base et l'API
    session = Session()
    try:
        prof = session.get(ProfessionSante, profession_id)
        dept = session.get(Departement, departement_id)
        resultats = api.get_prescriptions(prof.libelle, dept.code, annee, poste_prescription)
        evolution = api.get_evolution_prescriptions(prof.libelle, dept.code, poste_prescription)
    finally:
        session.close()

    # Génération du graphique en barres avec matplotlib (comme sur la page web)
    annees = [r.get("annee") for r in evolution]
    montants = [r.get("montant_total_prescription") for r in evolution]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(annees, montants, color="#2E74B5")
    ax.set_title("Évolution des montants de prescription")
    ax.set_xlabel("Année")
    ax.set_ylabel("Montant total (€)")
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Sauvegarde du graphique en mémoire
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close()
    img_buffer.seek(0)

    # Construction du PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Titre du PDF
    titre = f"{prof.libelle} – {dept.code} {dept.libelle} – {annee}"
    elements.append(Paragraph(titre, styles["Title"]))

    # Tableau des données
    data = [["Annee", "Type", "Libelle", "Montant total", "Montant moyen"]]
    for r in resultats:
        data.append([
            r.get("annee"),
            r.get("poste_prescription"),
            r.get("libelle_poste_prescription"),
            f"{r.get('montant_total_prescription')} €",
            f"{r.get('montant_moyen_prescription')} €"
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E74B5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF4FB")]),
    ]))
    elements.append(table)

    # Ajout du graphique dans le PDF
    elements.append(RLImage(img_buffer, width=500, height=250))

    doc.build(elements)
    buffer.seek(0)

    response = Response(buffer.read(), mimetype="application/pdf")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=prescriptions_{dept.code}_{annee}.pdf"
    )
    return response


# ═══════════════════════════════════════════════
# EXPORT HONORAIRES
# ═══════════════════════════════════════════════

@bp_export.route("/export/csv/honoraires")
def export_csv_honoraires():
    """Exporte les honoraires au format CSV téléchargeable."""
    profession_id = request.args.get("profession_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    type_honoraire_id = request.args.get("type_honoraire_id", type=int)
    annee = request.args.get("annee", type=int)

    # Récupération des données depuis la base et l'API
    session = Session()
    try:
        prof = session.get(ProfessionSante, profession_id)
        dept = session.get(Departement, departement_id)
        resultats = api.get_honoraires(prof.libelle, dept.code, annee)
    finally:
        session.close()

    # Création du CSV en mémoire
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # En-tête du CSV
    writer.writerow(["Annee", "Honoraires sans depassement", "Depassements totaux"])

    # Une ligne par résultat — r est toujours un dict car l'API retourne des dicts
    for r in resultats:
        writer.writerow([
            r.get("annee", annee),
            r.get("hono_sans_depassement_totaux", ""),
            r.get("depassements_totaux", "")
        ])

    # utf-8-sig pour que Excel reconnaisse les accents
    response = Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv; charset=utf-8-sig"
    )
    response.headers["Content-Disposition"] = (
        f"attachment; filename=honoraires_{dept.code}_{annee}.csv"
    )
    return response

@bp_export.route("/export/pdf/honoraires")
def export_pdf_honoraires():
    """Exporte les honoraires au format PDF téléchargeable."""
    profession_id = request.args.get("profession_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    type_honoraire_id = request.args.get("type_honoraire_id", type=int)
    annee = request.args.get("annee", type=int)

    # Récupération des données depuis la base et l'API
    session = Session()
    try:
        prof = session.get(ProfessionSante, profession_id)
        dept = session.get(Departement, departement_id)
        resultats = api.get_honoraires(prof.libelle, dept.code, annee)
    finally:
        session.close()

    # Construction du PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Titre du PDF
    titre = f"Honoraires – {prof.libelle} – {dept.code} {dept.libelle} – {annee}"
    elements.append(Paragraph(titre, styles["Title"]))

    # Tableau des données
    data = [["Annee", "Honoraires sans depassement", "Depassements totaux"]]
    for r in resultats:
        # r est un dict retourné par l'API
        data.append([
            r.get("annee", annee),
            f"{r.get('hono_sans_depassement_totaux', '')} €",
            f"{r.get('depassements_totaux', '')} €"
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E74B5")),  # en-tête bleu
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),                  # texte blanc
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),                  # bordures grises
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF4FB")]),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    response = Response(buffer.read(), mimetype="application/pdf")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=honoraires_{dept.code}_{annee}.pdf"
    )
    return response


# ═══════════════════════════════════════════════
# EXPORT COMPARAISON
# ═══════════════════════════════════════════════

@bp_export.route("/export/csv/comparaison")
def export_csv_comparaison():
    """Exporte les données de comparaison entre 2 départements au format CSV."""
    profession_id = request.args.get("profession_id", type=int)
    departement1_id = request.args.get("departement1_id", type=int)
    departement2_id = request.args.get("departement2_id", type=int)
    annee = request.args.get("annee", type=int)
    type_comparaison = request.args.get("type_comparaison", default="effectifs")

    # Récupération des données depuis la base et l'API
    session = Session()
    try:
        prof = session.get(ProfessionSante, profession_id)
        dept1 = session.get(Departement, departement1_id)
        dept2 = session.get(Departement, departement2_id)

        # Récupération de l'évolution selon le type choisi
        if type_comparaison == "effectifs":
            evolution1 = api.get_evolution_effectifs(prof.libelle, dept1.code)
            evolution2 = api.get_evolution_effectifs(prof.libelle, dept2.code)
        else:
            evolution1 = api.get_evolution_honoraires(prof.libelle, dept1.code)
            evolution2 = api.get_evolution_honoraires(prof.libelle, dept2.code)
    finally:
        session.close()

    # Création du CSV en mémoire
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # En-tête et clé selon le type de comparaison
    if type_comparaison == "effectifs":
        writer.writerow(["Annee", f"Effectif {dept1.code}", f"Effectif {dept2.code}"])
        dict1 = {r.get("annee"): r.get("effectif") for r in evolution1}
        dict2 = {r.get("annee"): r.get("effectif") for r in evolution2}
    else:
        writer.writerow(["Annee", f"Honoraires {dept1.code} (€)", f"Honoraires {dept2.code} (€)"])
        dict1 = {r.get("annee"): r.get("hono_sans_depassement_totaux") for r in evolution1}
        dict2 = {r.get("annee"): r.get("hono_sans_depassement_totaux") for r in evolution2}

    # Toutes les années disponibles dans les deux départements
    toutes_annees = sorted(set(list(dict1.keys()) + list(dict2.keys())))
    for an in toutes_annees:
        writer.writerow([an, dict1.get(an, ""), dict2.get(an, "")])

    # utf-8-sig pour que Excel reconnaisse les accents
    response = Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv; charset=utf-8-sig"
    )
    response.headers["Content-Disposition"] = (
        f"attachment; filename=comparaison_{dept1.code}_{dept2.code}_{annee}.csv"
    )
    return response

@bp_export.route("/export/pdf/comparaison")
def export_pdf_comparaison():
    """Exporte la comparaison entre 2 départements avec graphique au format PDF."""
    profession_id = request.args.get("profession_id", type=int)
    departement1_id = request.args.get("departement1_id", type=int)
    departement2_id = request.args.get("departement2_id", type=int)
    annee = request.args.get("annee", type=int)
    type_comparaison = request.args.get("type_comparaison", default="effectifs")

    # Récupération des données depuis la base et l'API
    session = Session()
    try:
        prof = session.get(ProfessionSante, profession_id)
        dept1 = session.get(Departement, departement1_id)
        dept2 = session.get(Departement, departement2_id)

        # Récupération de l'évolution selon le type choisi
        if type_comparaison == "effectifs":
            evolution1 = api.get_evolution_effectifs(prof.libelle, dept1.code)
            evolution2 = api.get_evolution_effectifs(prof.libelle, dept2.code)
            cle = "effectif"
            ylabel = "Effectif"
        else:
            evolution1 = api.get_evolution_honoraires(prof.libelle, dept1.code)
            evolution2 = api.get_evolution_honoraires(prof.libelle, dept2.code)
            cle = "hono_sans_depassement_totaux"
            ylabel = "Montant (€)"
    finally:
        session.close()

    # Génération du graphique avec deux courbes (une par département)
    annees1 = [r.get("annee") for r in evolution1]
    valeurs1 = [r.get(cle) for r in evolution1]
    annees2 = [r.get("annee") for r in evolution2]
    valeurs2 = [r.get(cle) for r in evolution2]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(annees1, valeurs1, color="#2E74B5", linewidth=2, label=f"{dept1.code} - {dept1.libelle}")
    ax.plot(annees2, valeurs2, color="#E74C3C", linewidth=2, label=f"{dept2.code} - {dept2.libelle}")
    ax.set_title(f"Comparaison – {prof.libelle}")
    ax.set_xlabel("Année")
    ax.set_ylabel(ylabel)
    ax.legend()  # légende pour distinguer les deux courbes
    ax.grid(True, linestyle="--", alpha=0.5)

    # Formater l'axe Y pour éviter les grands nombres illisibles
    # ex: 1500000 → 1.5M €, 500000 → 500K €
    # Formater l'axe Y pour éviter les grands nombres illisibles
    if type_comparaison == "honoraires":
        # Conversion en float car l'API peut retourner des strings
        valeurs1 = [float(v) if v is not None else 0 for v in valeurs1]
        valeurs2 = [float(v) if v is not None else 0 for v in valeurs2]
        # Redessiner les courbes avec les valeurs converties
        ax.clear()
        ax.plot(annees1, valeurs1, color="#2E74B5", linewidth=2, label=f"{dept1.code} - {dept1.libelle}")
        ax.plot(annees2, valeurs2, color="#E74C3C", linewidth=2, label=f"{dept2.code} - {dept2.libelle}")
        ax.set_title(f"Comparaison – {prof.libelle}")
        ax.set_xlabel("Année")
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"{x/1_000_000:.1f}M €" if x >= 1_000_000 else f"{x/1_000:.0f}K €")
    )

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Sauvegarde du graphique en mémoire
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close()
    img_buffer.seek(0)

    # Construction du PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Titre du PDF
    titre = f"Comparaison {type_comparaison} – {prof.libelle} – {annee}"
    elements.append(Paragraph(titre, styles["Title"]))

    # Sous-titre avec les deux départements
    sous_titre = f"{dept1.code} {dept1.libelle} vs {dept2.code} {dept2.libelle}"
    elements.append(Paragraph(sous_titre, styles["Heading2"]))

    # Tableau avec les deux départements côte à côte par année
    if type_comparaison == "effectifs":
        dict1 = {r.get("annee"): r.get("effectif") for r in evolution1}
        dict2 = {r.get("annee"): r.get("effectif") for r in evolution2}
        data = [["Annee", f"Effectif {dept1.code}", f"Effectif {dept2.code}"]]
    else:
        dict1 = {r.get("annee"): r.get("hono_sans_depassement_totaux") for r in evolution1}
        dict2 = {r.get("annee"): r.get("hono_sans_depassement_totaux") for r in evolution2}
        data = [["Annee", f"Honoraires {dept1.code} (€)", f"Honoraires {dept2.code} (€)"]]

    toutes_annees = sorted(set(list(dict1.keys()) + list(dict2.keys())))
    for an in toutes_annees:
        data.append([an, dict1.get(an, "N/A"), dict2.get(an, "N/A")])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E74B5")),  # en-tête bleu
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),                  # texte blanc
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),                  # bordures grises
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF4FB")]),
    ]))
    elements.append(table)

    # Ajout du graphique avec les deux courbes
    elements.append(RLImage(img_buffer, width=520, height=280))

    doc.build(elements)
    buffer.seek(0)

    response = Response(buffer.read(), mimetype="application/pdf")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=comparaison_{dept1.code}_{dept2.code}_{annee}.pdf"
    )
    return response