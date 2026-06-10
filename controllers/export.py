import csv
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import Blueprint, request, Response
from models.db import Session
from models.dimensions import ProfessionSante, Departement
from services.ameli_api import AmeliAPI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

bp_export = Blueprint("export", __name__)
api = AmeliAPI()

def get_donnees(profession_id, departement_id, annee):
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
    profession_id = request.args.get("profession_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    annee = request.args.get("annee", type=int)

    prof, dept, resultats, _ = get_donnees(profession_id, departement_id, annee)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Annee", "Effectif", "Densite"])
    for r in resultats:
        writer.writerow([r.get("annee"), r.get("effectif"), r.get("densite")])

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
    profession_id = request.args.get("profession_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    annee = request.args.get("annee", type=int)

    prof, dept, resultats, evolution = get_donnees(profession_id, departement_id, annee)

    # Graphique matplotlib
    annees = [r.get("annee") for r in evolution]
    effectifs = [r.get("effectif") for r in evolution]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(annees, effectifs, color="#2E74B5", linewidth=2)
    ax.set_title("Évolution des effectifs")
    ax.set_xlabel("Année")
    ax.set_ylabel("Effectif")
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close()
    img_buffer.seek(0)

    # PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    titre = f"{prof.libelle} – {dept.code} {dept.libelle} – {annee}"
    elements.append(Paragraph(titre, styles["Title"]))

    # Tableau
    data = [["Annee", "Effectif", "Densite"]]
    for r in resultats:
        data.append([r.get("annee"), r.get("effectif"), r.get("densite")])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E74B5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF4FB")]),
    ]))
    elements.append(table)

    # Graphique
    elements.append(RLImage(img_buffer, width=500, height=250))

    doc.build(elements)
    buffer.seek(0)

    response = Response(buffer.read(), mimetype="application/pdf")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=effectifs_{dept.code}_{annee}.pdf"
    )
    return response