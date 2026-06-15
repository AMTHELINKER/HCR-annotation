# =============================================================
# Onglet JSON — Réponse brute Roboflow
# =============================================================

import streamlit as st


def render():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-family: Outfit, sans-serif; margin-top: 0;'>Donnees JSON Brutes retournees par Roboflow</h4>", unsafe_allow_html=True)
    st.markdown("Voici l'intégralité de la réponse brute reçue du serveur serverless de Roboflow.")

    if st.session_state.get("raw_result") is not None:
        st.json(st.session_state.raw_result)
    else:
        st.info("Aucune analyse n'a encore été effectuée. Lancez le workflow pour visualiser les données brutes.")

    st.markdown("</div>", unsafe_allow_html=True)
