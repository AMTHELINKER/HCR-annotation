# =============================================================
# Application Streamlit — Point d'entrée frontend et Routage
# =============================================================

import streamlit as st

# Page config (doit être le premier appel Streamlit)
st.set_page_config(
    page_title="HCR4 — Ordonnances Médicales",
    page_icon="Rx",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injection du thème CSS premium
from frontend.styles import inject as inject_styles
inject_styles()

# Gestion de la session
if "user" not in st.session_state:
    st.session_state.user = None

# Si non connecté, afficher la page de connexion
if st.session_state.user is None:
    from frontend.components import login
    login.render()
else:
    # Récupérer les infos de l'utilisateur
    role = st.session_state.user["role"]
    nom = st.session_state.user["nom"]
    
    # Sidebar partagée et épurée
    with st.sidebar:
        # Profil en haut
        st.markdown(f"<div style='text-align: center; padding: 20px 0;'>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='margin-bottom: 0; font-family: Outfit;'>{nom}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #94a3b8; font-size: 0.9rem;'>Rôle : {role.capitalize()}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Pousser le bouton de déconnexion en bas en utilisant un espaceur
        st.markdown("<div style='height: 65vh;'></div>", unsafe_allow_html=True)
        
        # Bouton déconnexion en bas
        if st.button("Déconnexion", icon=":material/logout:", use_container_width=True, type="primary"):
            st.session_state.user = None
            st.rerun()
            
    # Routage vers le bon tableau de bord
    if role == "admin":
        from frontend.views import admin
        admin.render()
    elif role == "medecin":
        from frontend.views import medecin
        medecin.render()
    elif role == "patient":
        from frontend.views import patient
        patient.render()
    elif role == "pharmacie":
        from frontend.views import pharmacie
        pharmacie.render()
