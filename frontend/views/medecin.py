import streamlit as st
from backend.db.repositories import OrdonnanceRepo, MedicamentRepo
from backend.services.matching_service import load_reference_names
from backend.config import DEFAULT_QUALITY_THRESHOLD
from frontend.components import tab_analyzer

def render():
    st.markdown("<h2 style='font-family: Outfit;'>Espace Médecin</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Digitaliser une Ordonnance", "Historique des Prescriptions"])
    
    with tab1:
        st.markdown("### Nouvelle Ordonnance")
        
        api_url = "https://serverless.roboflow.com"
        workspace_name = "deg"
        workflow_id = "detect-count-and-visualize-2"
        use_cache = True
        enable_htr = True
        confidence_threshold = 0.4
        quality_threshold = DEFAULT_QUALITY_THRESHOLD
                
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
                    if lignes:
                        st.markdown("#### Médicaments :")
                        for ligne in lignes:
                            med_id = ligne.get("medicamentId")
                            if med_id:
                                med = MedicamentRepo.find_by_id(med_id)
                                nom_med = med["nom"] if med else "Inconnu"
                            else:
                                nom_med = ligne.get("medicament", "Inconnu")
                            
                            st.markdown(f"- **{nom_med}**")
        else:
            st.info("Vous n'avez pas encore numérisé d'ordonnances.")
