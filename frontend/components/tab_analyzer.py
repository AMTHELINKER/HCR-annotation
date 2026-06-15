# =============================================================
# Onglet Analyseur — Upload, contrôle qualité, détection, HTR
# =============================================================

import io
import streamlit as st
import pandas as pd
from PIL import Image

from backend.services import detection_service, image_service, htr_service, matching_service
from backend.services import quality_service
from backend.config import SAMPLES_DIR, DEFAULT_QUALITY_THRESHOLD
import os


# ========================= HELPERS =========================

_METRIC_LABELS = {
    "sharpness":  ("Netteté",    "La netteté mesure la précision des contours du texte."),
    "brightness": ("Luminosité", "La luminosité reflète l'exposition globale de l'image."),
    "contrast":   ("Contraste",  "Le contraste indique la distinction entre encre et fond."),
    "noise":      ("Bruit",      "Le bruit estime les parasites visuels de l'image."),
}

_METRIC_ICONS = {
    "sharpness":  "🔍",
    "brightness": "☀️",
    "contrast":   "🎛️",
    "noise":      "📡",
}


def _bar_class(value: float) -> str:
    """Retourne la classe CSS selon le score normalisé."""
    if value >= 60:
        return "good"
    elif value >= 35:
        return "warn"
    return "bad"


def _render_quality_report(report: dict):
    """Affiche le rapport de qualité image avec jauges visuelles."""
    accepted = report["accepted"]
    score = report["global_score"]
    min_score = report["min_score"]
    card_cls = "accepted" if accepted else "rejected"
    score_cls = "pass" if accepted else "fail"

    st.markdown(f"<div class='quality-card {card_cls}'>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-family: Outfit, sans-serif; margin-top: 0;'>Controle Qualité Image</h4>", unsafe_allow_html=True)

    # --- Score global + verdict ---
    col_gauge, col_details = st.columns([1, 2.5])

    with col_gauge:
        verdict_label = "IMAGE ACCEPTÉE" if accepted else "IMAGE REJETÉE"
        st.markdown(f"""
        <div class='quality-gauge'>
            <div class='quality-score {score_cls}'>{score}</div>
            <div class='quality-label'>Score Global / 100</div>
            <div class='quality-verdict {score_cls}'>{verdict_label}</div>
            <div style='font-size:0.75rem; color:#64748b; margin-top:4px;'>Seuil minimum : {min_score}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- Barres par métrique ---
    with col_details:
        for key, data in report["metrics"].items():
            label, tooltip = _METRIC_LABELS.get(key, (key, ""))
            icon = _METRIC_ICONS.get(key, "📊")
            norm = data["normalized"]
            raw = data["raw"]
            bar_cls = _bar_class(norm)
            status_dot = "🟢" if data["status"] == "pass" else "🔴"

            st.markdown(f"""
            <div style='margin-bottom: 12px;'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;'>
                    <span style='font-weight:600; font-size:0.9rem; color:#cbd5e1;'>
                        <span class='metric-icon'>{icon}</span> {label}
                        <span style='font-size:0.7rem; color:#64748b; margin-left:6px;' title='{tooltip}'>(brut: {raw})</span>
                    </span>
                    <span style='font-weight:700; font-size:0.9rem; color:#e2e8f0;'>
                        {norm}/100 {status_dot}
                    </span>
                </div>
                <div class='metric-bar-track'>
                    <div class='metric-bar-fill {bar_cls}' style='width:{norm}%;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ========================= RENDER =========================

def render(config: dict):
    """Affiche l'onglet principal d'analyse d'ordonnances.
    
    Args:
        config: Dict retourné par sidebar.render().
    """
    confidence = config["confidence_threshold"]
    enable_htr = config["enable_htr"]
    meds_db = config["meds_db"]
    quality_threshold = config.get("quality_threshold", DEFAULT_QUALITY_THRESHOLD)

    col_input, col_output = st.columns([2, 3], gap="large")

    # --- Colonne gauche : upload / sélection ---
    with col_input:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-family: Outfit, sans-serif; margin-top: 0;'>Image Source</h4>", unsafe_allow_html=True)

        input_type = st.radio("Méthode d'entrée", ["Téléverser une ordonnance", "Tester avec une image d'exemple"])
        uploaded_image = None

        if input_type == "Téléverser une ordonnance":
            uploaded_file = st.file_uploader("Téléversez l'ordonnance (PNG, JPG, JPEG)...", type=["png", "jpg", "jpeg", "webp"])
            if uploaded_file:
                uploaded_image = Image.open(uploaded_file).convert("RGB")
        else:
            # Chercher les images dans data/samples/ et à la racine du projet
            search_dirs = [SAMPLES_DIR, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))]
            local_samples = {}
            for d in search_dirs:
                if os.path.isdir(d):
                    for f in sorted(os.listdir(d)):
                        if f.lower().endswith((".jpeg", ".jpg", ".png", ".webp")):
                            local_samples[f] = os.path.join(d, f)

            if local_samples:
                selected = st.selectbox("Selectionnez un exemple :", list(local_samples.keys()))
                try:
                    uploaded_image = Image.open(local_samples[selected]).convert("RGB")
                except Exception as e:
                    st.error(f"Erreur image exemple : {e}")
            else:
                st.warning("Aucune image d'exemple trouvee.")

        if uploaded_image:
            st.image(uploaded_image, caption="Ordonnance à analyser", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # === QUALITY GATE ===
        quality_passed = False
        if uploaded_image:
            with st.spinner("Évaluation de la qualité de l'image..."):
                accepted, quality_report = quality_service.is_acceptable(
                    uploaded_image, min_score=quality_threshold
                )
            _render_quality_report(quality_report)

            quality_passed = accepted
            st.session_state["quality_report"] = quality_report

            if not accepted:
                st.error(
                    f"L'image n'atteint pas le seuil de qualité minimum "
                    f"(**{quality_report['global_score']}/{quality_threshold}**). "
                    f"Veuillez fournir une image plus nette et mieux éclairée."
                )

        # Bouton d'analyse : visible uniquement si la qualité est OK
        if uploaded_image and quality_passed:
            analyze_button = st.button("Lancer le pipeline complet", use_container_width=True, type="primary")
        elif not uploaded_image:
            st.info("Veuillez téléverser une image ou choisir un exemple pour démarrer.")
            analyze_button = False
        else:
            analyze_button = False

    # --- Colonne droite : visualisation ---
    with col_output:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-family: Outfit, sans-serif; margin-top: 0;'>Visualisation de Detection</h4>", unsafe_allow_html=True)

        # Session state init
        if "raw_result" not in st.session_state:
            st.session_state.raw_result = None
            st.session_state.source_img = None
            st.session_state.htr_results = {}

        # --- Pipeline execution ---
        if analyze_button and uploaded_image:
            st.session_state.htr_results = {}

            with st.spinner("Etape 1/2 : Detection des medicaments avec Roboflow Workflows..."):
                try:
                    result = detection_service.detect_lines(uploaded_image, config["use_cache"])
                    st.session_state.raw_result = result
                    st.session_state.source_img = uploaded_image
                except Exception as e:
                    st.error(f"Erreur d'appel Roboflow : {e}")

            if st.session_state.raw_result and enable_htr:
                parsed = detection_service.parse_response(st.session_state.raw_result)
                valid_preds = detection_service.filter_predictions(parsed["predictions"], confidence)

                if valid_preds:
                    with st.spinner(f"Etape 2/2 : Transcription HTR-VT de {len(valid_preds)} lignes..."):
                        try:
                            for idx, pred in enumerate(valid_preds):
                                crop = image_service.crop_prediction(uploaded_image, pred)
                                try:
                                    st.session_state.htr_results[idx] = htr_service.transcribe(crop)
                                except Exception as htr_err:
                                    st.session_state.htr_results[idx] = f"Erreur HTR: {htr_err}"
                            st.toast("Pipeline complet execute avec succes !")
                        except Exception as e:
                            st.error(f"Impossible de charger HTR-VT : {e}")

        # --- Render results ---
        if st.session_state.raw_result is not None and st.session_state.source_img is not None:
            parsed = detection_service.parse_response(st.session_state.raw_result)
            predictions = parsed["predictions"]

            visualized_img, detected_count = image_service.draw_predictions(
                st.session_state.source_img, predictions, confidence
            )
            valid_preds = detection_service.filter_predictions(predictions, confidence)
            avg_conf = sum(p.get("confidence", 0) for p in valid_preds) / len(valid_preds) if valid_preds else 0

            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-badge'>
                    <div class='metric-value'>{detected_count}</div>
                    <div class='metric-label'>Lignes Détectées</div>
                </div>
                <div class='metric-badge emerald'>
                    <div class='metric-value'>{avg_conf:.1%}</div>
                    <div class='metric-label'>Confiance Détection</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.image(visualized_img, caption="Ordonnance avec lignes segmentées", use_container_width=True)
        else:
            st.markdown("""
            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center;
                height: 300px; border: 2px dashed rgba(255,255,255,0.05); border-radius: 12px; color: #64748b;'>
                <div style='font-weight: 500; font-size: 1.1rem; color: #cbd5e1;'>Pret pour l'Analyse Medicale</div>
                <div style='text-align: center; max-width: 320px; font-size: 0.85rem; margin-top: 5px;'>
                    Uploadez une ordonnance manuscrite pour détecter les lignes et transcrire le nom des médicaments.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # --- Galerie de Transcription & Matching ---
    if st.session_state.raw_result is not None and st.session_state.source_img is not None:
        _render_gallery(confidence, enable_htr, meds_db)


def _render_gallery(confidence: float, enable_htr: bool, meds_db: list):
    """Sous-composant : galerie interactive de transcription et matching flou."""
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-family: Outfit, sans-serif; margin-top:0;'>Galerie de Transcription & Matching Flou</h3>", unsafe_allow_html=True)
    st.markdown("Modifiez la transcription brute de l'IA en temps réel pour recalculer le médicament le plus proche.")

    parsed = detection_service.parse_response(st.session_state.raw_result)
    valid_preds = detection_service.filter_predictions(parsed["predictions"], confidence)

    if not enable_htr:
        st.info("La reconnaissance d'écriture manuscrite (HTR-VT) est désactivée. Activez-la dans la barre latérale.")
    elif not valid_preds:
        st.warning("Aucune ligne n'a été détectée avec le seuil de confiance actuel.")
    else:
        final_report = []

        for idx, pred in enumerate(valid_preds):
            if idx not in st.session_state.htr_results:
                st.session_state.htr_results[idx] = "Non transcrit"

            crop_img = image_service.crop_prediction(st.session_state.source_img, pred)
            col_num, col_crop, col_trans, col_match = st.columns([0.5, 2.5, 3.5, 3.5])

            with col_num:
                st.markdown(f"<div style='margin-top: 15px;' class='index-bubble'>{idx + 1}</div>", unsafe_allow_html=True)
            with col_crop:
                st.image(crop_img, caption="Segment découpé", use_container_width=True)
            with col_trans:
                user_text = st.text_input(
                    f"Transcription IA (Ligne #{idx+1})",
                    value=st.session_state.htr_results[idx],
                    key=f"trans_input_{idx}"
                )
                st.session_state.htr_results[idx] = user_text
            with col_match:
                matched, score = matching_service.fuzzy_match(user_text, meds_db)
                badge_cls, badge_lbl = matching_service.classify_score(score)
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.02); padding: 8px 12px; border-radius: 8px;
                    border: 1px solid rgba(255,255,255,0.05);'>
                    <div style='font-size:0.75rem; color:#94a3b8;'>MÉDICAMENT ASSOCIE :</div>
                    <div style='font-family:Outfit; font-weight:600; font-size:1.05rem; color:#cbd5e1; margin-top:2px;'>{matched}</div>
                    <div style='margin-top:6px;'>
                        <span class='score-badge {badge_cls}'>Similarité: {score:.1%} ({badge_lbl})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            final_report.append({
                "Ligne": idx + 1,
                "Transcription Brute": user_text,
                "Médicament Correspondant": matched,
                "Indice de Similarité": f"{score:.1%}",
                "Score de Confiance": score,
            })
            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 15px 0;'>", unsafe_allow_html=True)

        # Export
        if final_report:
            st.markdown("<h4 style='font-family: Outfit, sans-serif; margin-top: 15px;'>Synthese de l'Ordonnance Medicale</h4>", unsafe_allow_html=True)
            report_df = pd.DataFrame(final_report)
            st.dataframe(report_df.drop(columns=["Score de Confiance"]), use_container_width=True, hide_index=True)

            csv_buf = io.StringIO()
            report_df.to_csv(csv_buf, index=False)
            st.download_button(
                "Telecharger le rapport d'ordonnance (.csv)",
                csv_buf.getvalue().encode("utf-8"),
                "ordonnance_predite.csv", "text/csv",
                use_container_width=True
            )

    st.markdown("</div>", unsafe_allow_html=True)
