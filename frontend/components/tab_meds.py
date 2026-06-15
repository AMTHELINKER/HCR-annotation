# =============================================================
# Onglet Base de Médicaments — Liste de référence
# =============================================================

import streamlit as st
import pandas as pd


def render(meds_db: list):
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-family: Outfit, sans-serif; margin-top: 0;'>Liste de Reference des Medicaments</h4>", unsafe_allow_html=True)

    if meds_db:
        st.markdown(f"La base contient **{len(meds_db):,}** entrées uniques.")
        col1, col2, col3 = st.columns(3)
        chunk = len(meds_db) // 3 + 1

        with col1:
            st.dataframe(pd.DataFrame(meds_db[:chunk], columns=["Médicament Reference"]), use_container_width=True)
        with col2:
            st.dataframe(pd.DataFrame(meds_db[chunk:chunk*2], columns=["Médicament Reference"]), use_container_width=True)
        with col3:
            st.dataframe(pd.DataFrame(meds_db[chunk*2:1000], columns=["Médicament Reference"]), use_container_width=True)
            st.caption("Affichage limité aux 1000 premières références dans le 3ème panneau.")
    else:
        st.error("Aucune source de médicaments disponible.")

    st.markdown("</div>", unsafe_allow_html=True)
