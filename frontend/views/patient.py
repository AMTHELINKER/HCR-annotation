import streamlit as st
from backend.db.repositories import OrdonnanceRepo, PharmacieRepo
from bson import ObjectId

def render():
    st.markdown("<h2 style='font-family: Outfit;'>Espace Patient</h2>", unsafe_allow_html=True)
    st.markdown("### Mes Ordonnances")
    
    patient_id = st.session_state.user["id"]
    ordonnances = OrdonnanceRepo.find_by_patient(patient_id)
    pharmacies = PharmacieRepo.find_all()
    pharma_options = {str(p["_id"]): p["nom"] for p in pharmacies}
    
    if ordonnances:
        for ordo in ordonnances:
            ordo_id = str(ordo["_id"])
            statut = ordo.get("statut", "inconnu")
            date_crea = ordo['dateCreation'].strftime('%d/%m/%Y') if 'dateCreation' in ordo else "N/A"
            
            with st.expander(f"Ordonnance du {date_crea} - Statut: {statut.upper()}"):
                st.write(f"Médicaments : {len(ordo.get('lignes', []))}")
                
                # Check status
                if statut in ["validee", "digitalisee"]:
                    selected_pharma = st.selectbox(
                        "Envoyer à une pharmacie :", 
                        options=list(pharma_options.keys()), 
                        format_func=lambda x: pharma_options[x],
                        key=f"select_{ordo_id}"
                    )
                    
                    if st.button("Envoyer", key=f"btn_{ordo_id}"):
                        OrdonnanceRepo.send_to_pharmacie(ordo_id, selected_pharma)
                        st.success("Ordonnance envoyée à la pharmacie avec succès !")
                        st.rerun()
                elif statut == "envoyee":
                    pharma_id = ordo.get("pharmacieDestinataireId")
                    nom_pharma = pharma_options.get(str(pharma_id), "Inconnue") if pharma_id else "Inconnue"
                    st.success(f"Déjà envoyée à la pharmacie : {nom_pharma}")
    else:
        st.info("Vous n'avez aucune ordonnance.")
