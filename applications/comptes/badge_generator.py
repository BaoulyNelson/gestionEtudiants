"""
Génère le badge étudiant FASCH/UEH au format PDF (ReportLab).

Style FIDÈLE à la carte physique Nelson :
  - Fond entièrement BLANC
  - En-tête : logo à gauche | texte centré | "ueh" cursive à droite  (sur blanc)
  - Ligne rouge horizontale sous l'en-tête
  - Blason / cachet officiel en filigrane au centre (site.cachet_officiel)
  - Photo à gauche + "Etudiant" dessous + signature directeur
  - Libellés en ROUGE, valeurs en bleu marine foncé
  - Code-barres en bas à droite
  - Bande JAUNE en pied de page

Dépendances :
    pip install reportlab pillow
"""

import io
from reportlab.lib.units    import mm
from reportlab.lib          import colors
from reportlab.pdfgen       import canvas
from reportlab.lib.utils    import ImageReader
from reportlab.graphics.barcode import code128 as code128_mod
from reportlab.pdfbase.pdfmetrics import stringWidth

# ── Import des modèles ──────────────────────────────────────────────────────
from applications.comptes.models  import Utilisateur

# ── Dimensions CR80 standard ────────────────────────────────────────────────
CARD_W = 85.6 * mm
CARD_H = 54.0 * mm

# ── Palette fidèle à la carte Nelson ────────────────────────────────────────
BLEU_MARINE = colors.HexColor("#1B2A6B")   # texte établissement + valeurs
ROUGE_UEH   = colors.HexColor("#C8102E")   # libellés + ligne accent
JAUNE_UEH   = colors.HexColor("#F5C518")   # bande pied de page
BLANC       = colors.white
GRIS_PHOTO  = colors.HexColor("#CBD5E1")
GRIS_TEXTE  = colors.HexColor("#1E293B")   # valeurs des champs
GRIS_SOUS   = colors.HexColor("#64748B")   # titre directeur

# ── Libellés ─────────────────────────────────────────────────────────────────
NIVEAU_LABELS = {
    "PREPARATOIRE": "Préparatoire",
    "NIVEAU1":      "Niveau I",
    "NIVEAU2":      "Niveau II",
    "NIVEAU3":      "Niveau III",
}
DEPT_LABELS = {
    "COMM":  "Communication Sociale",
    "PSY":   "Psychologie",
    "SOCIO": "Sociologie",
    "TS":    "Travail Social",
}

# ── Mise en page ─────────────────────────────────────────────────────────────
ENTETE_H   =  9 * mm   # zone texte en-tête (sur fond blanc)
LIGNE_R_H  =  1 * mm   # épaisseur ligne rouge
FOOTER_H   =  4 * mm   # bande jaune
PHOTO_X    =  2 * mm
PHOTO_W    = 20 * mm
PHOTO_H    = 25 * mm
# La photo commence juste sous l'en-tête + ligne rouge
PHOTO_Y_TOP = CARD_H - ENTETE_H - LIGNE_R_H   # bord haut de la photo
PHOTO_Y     = PHOTO_Y_TOP - PHOTO_H            # bord bas de la photo
# Zone sous la photo (entre bas de photo et footer) pour signature
SIG_ZONE_H  = PHOTO_Y - FOOTER_H


# ════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════════════════════

def generer_badge_pdf(etudiant) -> bytes:
    """Retourne les octets PDF du badge, style carte physique Nelson."""
    from applications.portail.models import SiteSettings
    site = SiteSettings.get()

    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=(CARD_W, CARD_H))

    # ── Calques de bas en haut ──────────────────────────────────────────────
    _fond_blanc(c)
    _filigrane_blason(c, site)        # cachet_officiel en transparence au centre
    _entete(c, site)                  # texte sur fond blanc
    _ligne_rouge(c)                   # trait rouge sous l'en-tête
    _zone_photo(c, etudiant)          # photo à gauche
    _label_etudiant(c)                # "Etudiant" sous la photo
    _signature_directeur(c, site)     # signature + nom sous la photo
    _infos(c, etudiant)               # champs à droite
    _code_barre(c, etudiant.numero_etudiant)
    _pied_jaune(c, site)              # bande jaune bas

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


# ════════════════════════════════════════════════════════════════════════════
# BLOCS
# ════════════════════════════════════════════════════════════════════════════

def _fond_blanc(c):
    """Fond entièrement blanc — pas de bandeau coloré."""
    c.setFillColor(BLANC)
    c.rect(0, 0, CARD_W, CARD_H, fill=1, stroke=0)


def _filigrane_blason(c, site):
    """
    Le cachet officiel (blason Haïti) en filigrane central,
    comme sur la carte Nelson physique.
    Utilise site.cachet_officiel si disponible, sinon texte "UEH".
    """
    cx = CARD_W / 2
    # Centré verticalement dans la zone corps (entre ligne rouge et footer)
    corps_top = CARD_H - ENTETE_H - LIGNE_R_H
    corps_bot = FOOTER_H
    cy = (corps_top + corps_bot) / 2

    blason_path = _image_path(site.cachet_officiel)
    if blason_path:
        try:
            img  = ImageReader(blason_path)
            size = 22 * mm
            # Dessin transparent via saveState / alpha simulé
            c.saveState()
            # ReportLab ne supporte pas l'alpha direct sur drawImage ;
            # on utilise une superposition blanche semi-opaque APRÈS le dessin.
            c.drawImage(img,
                        cx - size / 2, cy - size / 2,
                        width=size, height=size,
                        preserveAspectRatio=True, anchor='c',
                        mask='auto')
            # Voile blanc pour simuler la transparence (opacité ~15 %)
            c.setFillColorRGB(1, 1, 1, alpha=0.82)
            c.rect(cx - size / 2 - 1*mm, cy - size / 2 - 1*mm,
                   size + 2*mm, size + 2*mm, fill=1, stroke=0)
            c.restoreState()
            return
        except Exception:
            pass

    # Fallback : texte "UEH" très pâle
    c.setFillColorRGB(
        BLEU_MARINE.red, BLEU_MARINE.green, BLEU_MARINE.blue, alpha=0.08
    )
    c.setFont("Helvetica-Bold", 18)
    w = stringWidth("UEH", "Helvetica-Bold", 18)
    c.drawString(cx - w / 2, cy - 3 * mm, "UEH")


def _entete(c, site):
    """
    En-tête sur fond BLANC :
      [logo_small]   Université d'État d'Haïti   ueh (cursif)
                     Faculté des Sciences Humaines
    Exactement comme la carte Nelson.
    """
    top_y = CARD_H          # haut de carte
    zone_h = ENTETE_H       # 9 mm

    # ── Logo à gauche (logo_small ou logo) ──────────────────────────────
    logo_path = _image_path(site.logo) or _image_path(site.logo_small)
    logo_sz   = 7 * mm
    logo_x    = 2 * mm
    logo_y    = top_y - zone_h / 2 - logo_sz / 2
    if logo_path:
        try:
            img = ImageReader(logo_path)
            c.drawImage(img, logo_x, logo_y,
                        width=logo_sz, height=logo_sz,
                        preserveAspectRatio=True, anchor='c', mask='auto')
        except Exception:
            _logo_fallback(c, logo_x, logo_y, logo_sz)
    else:
        _logo_fallback(c, logo_x, logo_y, logo_sz)

    # ── "ueh" cursif à droite ───────────────────────────────────────────
    c.setFillColor(BLEU_MARINE)
    c.setFont("Helvetica-BoldOblique", 13)
    ueh_txt = "ueh"
    ueh_w   = stringWidth(ueh_txt, "Helvetica-BoldOblique", 13)
    c.drawString(CARD_W - ueh_w - 3 * mm,
                 top_y - zone_h / 2 - 2 * mm,
                 ueh_txt)

    # ── Textes centrés ──────────────────────────────────────────────────
    # Ligne 1 : nom_etablissement  (ex : "Université d'État d'Haïti")
    c.setFillColor(BLEU_MARINE)
    t1 = site.nom_etablissement
    f1, s1 = "Helvetica-Bold", 6
    w1 = stringWidth(t1, f1, s1)
    c.setFont(f1, s1)
    c.drawString((CARD_W - w1) / 2, top_y - 4.5 * mm, t1)

    # Ligne 2 : nom_complet  (ex : "Faculté des Sciences Humaines")
    t2 = site.nom_complet
    f2, s2 = "Helvetica", 4.8
    w2 = stringWidth(t2, f2, s2)
    c.setFont(f2, s2)
    c.drawString((CARD_W - w2) / 2, top_y - 8 * mm, t2)


def _logo_fallback(c, x, y, sz):
    """Carré blanc bordé bleu + 'UEH' si pas d'image."""
    c.setStrokeColor(BLEU_MARINE)
    c.setFillColor(BLANC)
    c.rect(x, y, sz, sz, fill=1, stroke=1)
    c.setFillColor(BLEU_MARINE)
    c.setFont("Helvetica-Bold", 4)
    c.drawCentredString(x + sz / 2, y + sz / 2 - 1.5 * mm, "UEH")


def _ligne_rouge(c):
    """Trait rouge horizontal sous l'en-tête — signature visuelle Nelson."""
    y = CARD_H - ENTETE_H - LIGNE_R_H
    c.setFillColor(ROUGE_UEH)
    c.rect(0, y, CARD_W, LIGNE_R_H, fill=1, stroke=0)


def _zone_photo(c, etudiant):
    """Photo à gauche, sous la ligne rouge."""
    px, py = PHOTO_X, PHOTO_Y
    pw, ph = PHOTO_W, PHOTO_H

    c.setFillColor(GRIS_PHOTO)
    c.roundRect(px, py, pw, ph, 1.5 * mm, fill=1, stroke=0)

    photo_path = _image_path(etudiant.utilisateur.photo_profil)
    if photo_path:
        try:
            img = ImageReader(photo_path)
            c.drawImage(img, px, py, pw, ph,
                        preserveAspectRatio=True, anchor='c', mask='auto')
            return
        except Exception:
            pass

    # Silhouette
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.circle(px + pw / 2, py + ph * 0.68, 4 * mm, fill=1, stroke=0)
    c.ellipse(px + 1*mm, py, px + pw - 1*mm, py + ph * 0.55, fill=1, stroke=0)


def _label_etudiant(c):
    """
    "Etudiant" centré sous la photo, en bleu marine,
    exactement comme sur la carte Nelson.
    """
    label_y = PHOTO_Y - 3.5 * mm
    c.setFillColor(BLEU_MARINE)
    c.setFont("Helvetica", 4)
    c.drawCentredString(PHOTO_X + PHOTO_W / 2, label_y, "Etudiant")


def _signature_directeur(c, site):
    """
    Signature + nom directeur sous le label 'Etudiant',
    dans la zone entre la photo et le footer.
    """
    zone_top = PHOTO_Y - 4.5 * mm   # juste sous "Etudiant"
    zone_bot = FOOTER_H + 0.5 * mm
    zone_h   = zone_top - zone_bot

    if zone_h <= 0:
        return

    sig_path = _image_path(site.signature_directeur)
    if sig_path and zone_h > 3 * mm:
        try:
            img_sig  = ImageReader(sig_path)
            sig_draw_h = min(zone_h * 0.6, 6 * mm)
            c.drawImage(img_sig,
                        PHOTO_X,
                        zone_bot + zone_h - sig_draw_h,
                        width=PHOTO_W, height=sig_draw_h,
                        preserveAspectRatio=True, anchor='sw', mask='auto')
        except Exception:
            pass

    if site.nom_directeur_etudes:
        c.setFillColor(GRIS_TEXTE)
        c.setFont("Helvetica-Bold", 3.5)
        c.drawString(PHOTO_X, zone_bot + 2.2 * mm, site.nom_directeur_etudes)
    if site.titre_directeur_etudes:
        c.setFillColor(GRIS_SOUS)
        c.setFont("Helvetica", 3.0)
        c.drawString(PHOTO_X, zone_bot + 0.3 * mm, site.titre_directeur_etudes)


def _infos(c, etudiant):
    """
    Zone infos à droite de la photo.

    Structure (fidèle à Nelson) :
      Nom complet          — gras, bleu marine, grand
      ─────────────────    — séparateur rouge
      Département          — rouge italique
      ─────────────────    — séparateur fin
      [libellé rouge]  [valeur gris foncé]   × 5 lignes
    """
    u  = etudiant.utilisateur
    ix = PHOTO_X + PHOTO_W + 3 * mm    # début zone infos
    iy = CARD_H - ENTETE_H - LIGNE_R_H - 3 * mm   # départ sous ligne rouge

    # ── Nom complet ──────────────────────────────────────────────────────
    c.setFillColor(BLEU_MARINE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(ix, iy, u.get_full_name())

    # ── Séparateur rouge ─────────────────────────────────────────────────
    iy -= 2.5 * mm
    c.setStrokeColor(ROUGE_UEH)
    c.setLineWidth(0.7)
    c.line(ix, iy, CARD_W - 2 * mm, iy)

    # ── Département ──────────────────────────────────────────────────────
    dept_nom = "—"
    if etudiant.departement:
        dept_nom = DEPT_LABELS.get(etudiant.departement.code,
                                   etudiant.departement.nom)
    iy -= 3.5 * mm
    c.setFillColor(ROUGE_UEH)
    c.setFont("Helvetica-BoldOblique", 5.5)
    c.drawString(ix, iy, dept_nom)

    # ── Séparateur fin gris ───────────────────────────────────────────────
    iy -= 2 * mm
    c.setStrokeColor(colors.HexColor("#E2E8F0"))
    c.setLineWidth(0.3)
    c.line(ix, iy, CARD_W - 2 * mm, iy)

    # ── 5 lignes d'informations (libellé rouge | valeur bleu foncé) ──────
    # Style Nelson : libellés courts en rouge gras, valeur à droite en noir
    lignes = [
        ("Email",   u.email),
        ("N°",      str(etudiant.numero_etudiant)),
        ("Niveau",  NIVEAU_LABELS.get(etudiant.niveau, etudiant.niveau)),
        ("Né(e)",   _fmt_date(u.date_naissance)),
        ("Tél",     u.numero_telephone or "—"),
    ]

    label_col  = ix
    value_col  = ix + 10 * mm   # colonne valeur
    seuil_bas  = FOOTER_H + 2 * mm
    gap        = 3.6 * mm

    for label, valeur in lignes:
        iy -= gap
        if iy < seuil_bas:
            break

        # Libellé en rouge gras (style "Code Permanent" de Nelson)
        c.setFillColor(ROUGE_UEH)
        c.setFont("Helvetica-Bold", 4.5)
        c.drawString(label_col, iy, label)

        # Valeur en bleu marine / gris foncé
        c.setFillColor(GRIS_TEXTE)
        c.setFont("Helvetica", 4.5)
        c.drawString(value_col, iy, valeur)

        # Trait séparateur très fin
        c.setStrokeColor(colors.HexColor("#F1F5F9"))
        c.setLineWidth(0.2)
        c.line(label_col, iy - 1 * mm, CARD_W - 2 * mm, iy - 1 * mm)


def _code_barre(c, numero):
    """
    Code-barres Code128 en bas à droite,
    au-dessus de la bande jaune — comme le QR de Nelson mais en barcode.
    """
    barre = code128_mod.Code128(
        str(numero),
        barWidth   = 0.48,
        barHeight  = 5 * mm,
        humanReadable = True,
        quiet      = False,
        barFillColor   = colors.black,
        barStrokeColor = colors.black,
    )
    bw = barre.width
    bx = CARD_W - 2 * mm - bw
    by = FOOTER_H + 2.5 * mm
    barre.drawOn(c, bx, by)


def _pied_jaune(c, site):
    """Bande jaune bas de carte, identique à la carte Nelson."""
    c.setFillColor(JAUNE_UEH)
    c.rect(0, 0, CARD_W, FOOTER_H, fill=1, stroke=0)

    # Texte centré en bleu marine sur fond jaune
    c.setFillColor(BLEU_MARINE)
    c.setFont("Helvetica-Bold", 3.2)
    label = f"{site.nom_etablissement} — {site.nom_complet}"
    c.drawCentredString(CARD_W / 2, 1.2 * mm, label)


# ════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ════════════════════════════════════════════════════════════════════════════

def _image_path(champ_image):
    """Retourne le chemin absolu d'un ImageField, ou None."""
    if not champ_image:
        return None
    try:
        return champ_image.path
    except (ValueError, AttributeError, FileNotFoundError):
        return None


def _fmt_date(d):
    if d is None:
        return "—"
    return d.strftime("%d / %m / %Y")