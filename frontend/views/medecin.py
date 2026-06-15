import streamlit as st
from backend.db.repositories import OrdonnanceRepo
from backend.services.matching_service import load_reference_names
from backend.config import DEFAULT_QUALITY_THRESHOLD
from frontend.components import tab_analyzer

def render():
    st.markdown("<h2 style='font-family: Outfit;'>Espace Médecin</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Digitaliser une Ordonnance", "Historique des Prescriptions"])
    
    with tab1:
        st.markdown("### Nouvelle Ordonnance")
        
        # Configuration avancée déplacée hors de la sidebar
        with st.expander("⚙️ Configuration avancée de l'IA (Roboflow & HTR)"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Détection")
                api_url = st.text_input("URL de l'API", value="https://serverless.roboflow.com")
                workspace_name = st.text_input("Workspace", value="deg")
                workflow_id = st.text_input("ID du Workflow", value="detect-count-and-visualize-2")
                use_cache = st.toggle("Activer le Cache", value=True)
            with c2:
                st.markdown("#### HTR & Matching")
                enable_htr = st.toggle("Activer HTR-VT", value=True)
                confidence_threshold = st.slider("Seuil Confiance", 0.0, 1.0, 0.4, 0.05)
                st.markdown("#### Qualité Image")
                quality_threshold = st.slider(
                    "Seuil Qualité Image",
                    min_value=0, max_value=100,
                    value=DEFAULT_QUALITY_THRESHOLD, step=5,
                    help="Score minimum (0-100) que l'image doit atteindre pour poursuivre le pipeline."
                )
                
        meds_db = load_reference_names()
        
        config = {
            "api_url": api_url,
            "workspace_name": workspace_name,
            "workflow_id": workflow_id,
            "use_cache": use_cache,
            "enable_htr": enable_htr,
            "confidence_threshold": confidence_threshold,
            "quality_threshold": quality_threshold,
            "meds_db": meds_db,
        }
        
        tab_analyzer.render(config)
        
    with tab2:
        st.markdown("### Historique")
        medecin_id = st.session_state.user["id"]
        ordonnances = OrdonnanceRepo.find_by_medecin(medecin_id)
        
        if ordonnances:
            for ordo in ordonnances:
                with st.expander(f"Ordonnance du {ordo['dateCreation'].strftime('%d/%m/%Y')} - Statut: {ordo['statut'].upper()}"):
                    lignes = ordo.get("lignes", [])
                    st.write(f"**Nombre de médicaments prescrits :** {len(lignes)}")
        else:
            st.info("Vous n'avez pas encore numérisé d'ordonnances.")
