# translate_ppt_deepl_app.py
#
# Application Streamlit pour traduire un fichier PowerPoint (.pptx ou .ppt) du français vers l'anglais
# en utilisant l'API DeepL, tout en préservant la mise en forme (polices, tailles, couleurs, gras, etc.).
#
# ⚙️ Prérequis
# - Python 3.9+
# - Packages : streamlit, python-pptx, requests
#   pip install streamlit python-pptx requests
# - Clé API DeepL via la variable d'environnement DEEPL_API_KEY
#   export DEEPL_API_KEY="votre_clef_deepl"
# - (Optionnel pour .ppt) LibreOffice installé avec la commande `soffice` disponible dans le PATH
#
# ▶️ Lancer :
#   streamlit run translate_ppt_deepl_app.py
#
# 📝 Notes
# - La traduction se fait run par run (éléments de texte formatés) pour préserver la mise en forme.
# - Les tableaux et les notes des diapositives sont pris en charge.
# - Les graphiques/SmartArt/objets intégrés ne sont pas modifiables via python-pptx et ne seront pas traduits.
# - Les fichiers .ppt (ancien format) sont automatiquement convertis en .pptx via LibreOffice si disponible.

import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

import requests
import streamlit as st
from pptx import Presentation
from pptx.shapes.group import GroupShape

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")
DEEPL_API_URL = os.getenv("DEEPL_API_URL")  # Permet de forcer l'URL si besoin

# Détection d'URL selon type de clé : les clés Free contiennent "-free" ; sinon, endpoint payant.
if not DEEPL_API_URL:
    if DEEPL_API_KEY.endswith(":fx") or "-free" in DEEPL_API_KEY:
        DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"
    else:
        DEEPL_API_URL = "https://api.deepl.com/v2/translate"

BATCH_SIZE = 45  # par sécurité, rester < 50 textes par requête

st.set_page_config(page_title="Traduire PowerPoint FR → EN (DeepL)", page_icon="🗂️", layout="centered")
st.title("🗂️ Traduire un PowerPoint FR → EN (DeepL)")
st.write("Téléversez un fichier **.pptx** ou **.ppt**. La mise en forme est préservée ; seul le texte est traduit en anglais.")

with st.expander("Paramètres avancés"):
    tgt_variant = st.selectbox("Variante d'anglais", ["EN-US", "EN-GB"], index=0)
    include_notes = st.checkbox("Traduire les notes des diapositives", value=True)

uploaded = st.file_uploader("Choisir un fichier PowerPoint", type=["pptx", "ppt"]) 

if uploaded is not None:
    if not DEEPL_API_KEY:
        st.error("La variable d'environnement **DEEPL_API_KEY** n'est pas définie.")
        st.stop()

    # Sauvegarder le fichier uploadé dans un dossier temporaire
    tmpdir = Path(tempfile.mkdtemp(prefix="ppt-translate-"))
    in_path = tmpdir / uploaded.name
    with open(in_path, "wb") as f:
        f.write(uploaded.getbuffer())

    # Convertir .ppt → .pptx via LibreOffice si nécessaire
    def convert_ppt_to_pptx(ppt_path: Path) -> Path:
        out_dir = ppt_path.parent
        try:
            result = subprocess.run([
                "soffice", "--headless", "--convert-to", "pptx", "--outdir", str(out_dir), str(ppt_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(result.stderr or result.stdout)
            conv = ppt_path.with_suffix(".pptx")
            if not conv.exists():
                # Certains LibreOffice sortent un nom sans respecter la casse
                candidates = list(out_dir.glob(ppt_path.stem + "*.pptx"))
                if candidates:
                    return candidates[0]
                raise FileNotFoundError("Conversion échouée : fichier .pptx introuvable")
            return conv
        except Exception as e:
            raise RuntimeError(f"Conversion .ppt→.pptx impossible : {e}")

    if in_path.suffix.lower() == ".ppt":
        try:
            st.info("Conversion du .ppt vers .pptx via LibreOffice…")
            in_path = convert_ppt_to_pptx(in_path)
            st.success("Conversion .ppt → .pptx réalisée.")
        except Exception as e:
            st.error(str(e))
            st.stop()

    # Charger la présentation
    prs = Presentation(str(in_path))

    # Utilitaires : itérer sur tous les conteneurs de texte (y compris GroupShapes et Tables)
    def iter_text_frames(shape):
        """Génère tous les text_frames pour un shape (y compris récursif pour groupes et cellules de tableau)."""
        if isinstance(shape, GroupShape):
            for shp in shape.shapes:
                yield from iter_text_frames(shp)
            return

        # Table
        if hasattr(shape, "table") and shape.table is not None:
            for row in shape.table.rows:
                for cell in row.cells:
                    if cell.text_frame is not None:
                        yield cell.text_frame
            return

        # Formes avec texte (auto-shapes, placeholders, text boxes)
        if hasattr(shape, "text_frame") and shape.text_frame is not None:
            yield shape.text_frame

    # Collecter tous les runs de texte pour traduction
    RunRef = Tuple  # alias pour lisibilité: (run_obj, original_text)
    run_refs: List[Tuple[object, str]] = []

    for slide in prs.slides:
        for shape in slide.shapes:
            for tf in iter_text_frames(shape):
                for para in tf.paragraphs:
                    for run in para.runs:
                        txt = run.text
                        if txt is not None and txt.strip() != "":
                            run_refs.append((run, txt))

        # Notes de la diapositive
        if include_notes:
            if slide.has_notes_slide:
                notes = slide.notes_slide
                for shape in notes.shapes:
                    if hasattr(shape, "text_frame") and shape.text_frame is not None:
                        for para in shape.text_frame.paragraphs:
                            for run in para.runs:
                                txt = run.text
                                if txt is not None and txt.strip() != "":
                                    run_refs.append((run, txt))

    total_runs = len(run_refs)
    if total_runs == 0:
        st.warning("Aucun texte détecté à traduire.")
        st.stop()

    st.write(f"Segments à traduire : **{total_runs}** (en conservant la mise en forme)")
    # Traduction par lots via DeepL
    def deepl_translate_batch(texts: List[str], source_lang: str = "FR", target_lang: str = "EN-US") -> List[str]:
        if not texts:
            return []
        # Construire un payload 'application/x-www-form-urlencoded' avec répétition de la clé 'text'
        data: List[Tuple[str, str]] = [
            ("auth_key", DEEPL_API_KEY),
            ("source_lang", source_lang),
            ("target_lang", target_lang),
            ("preserve_formatting", "1"),  # aide à garder la casse/ponctuation
        ]
        data.extend(("text", t) for t in texts)

        # Requêtes + gestion d'erreurs simples
        try:
            resp = requests.post(DEEPL_API_URL, data=data, timeout=60)
            resp.raise_for_status()
            js = resp.json()
            translations = js.get("translations", [])
            return [t.get("text", "") for t in translations]
        except requests.HTTPError as e:
            st.error(f"Erreur DeepL ({e.response.status_code}) : {e.response.text}")
            raise
        except Exception as e:
            st.error(f"Erreur de connexion à l'API DeepL : {e}")
            raise

    # Appliquer la traduction par lots en conservant la mise en forme (remplacement run par run)
    progress = st.progress(0, text="Traduction en cours…")
    for start in range(0, total_runs, BATCH_SIZE):
        batch_refs = run_refs[start:start + BATCH_SIZE]
        batch_texts = [txt for (_run, txt) in batch_refs]
        translated = deepl_translate_batch(batch_texts, source_lang="FR", target_lang=tgt_variant)
        for (run, _orig), new_txt in zip(batch_refs, translated):
            run.text = new_txt
        progress.progress(min(1.0, (start + len(batch_refs)) / total_runs), text=f"{min(start + len(batch_refs), total_runs)}/{total_runs} segments")

    # Enregistrer la présentation traduite
    out_name = Path(in_path.name).with_suffix("")
    out_file = tmpdir / f"{out_name}_EN.pptx"
    prs.save(str(out_file))

    st.success("Traduction terminée. Téléchargez votre fichier ci-dessous.")
    with open(out_file, "rb") as f:
        st.download_button(
            label="⬇️ Télécharger le PowerPoint traduit",
            data=f.read(),
            file_name=out_file.name,
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    # Proposer un bouton pour réinitialiser la session (facilite une autre traduction)
    if st.button("🔁 Traduire un autre fichier"):
        st.experimental_rerun()
