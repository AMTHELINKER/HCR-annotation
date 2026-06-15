import streamlit as st
from backend.db.repositories import OrdonnanceRepo, PharmacieRepo, MedicamentRepo

def render():
    st.markdown("<h2 style='font-family: Outfit;'>Espace Pharmacie</h2>", unsafe_allow_html=True)
    
    pharma_id = st.session_state.user["id"]
    
    tab1, tab2 = st.tabs(["Ordonnances Reçues", "Gestion des Stocks"])
    
    with tab1:
        st.markdown("### Ordonnances Reçues")
        ordonnances = OrdonnanceRepo.find_by_pharmacie(pharma_id)
        if ordonnances:
            for ordo in ordonnances:
                date_crea = ordo['dateCreation'].strftime('%d/%m/%Y') if 'dateCreation' in ordo else "N/A"
                with st.expander(f"Ordonnance du {date_crea} - {len(ordo.get('lignes', []))} médicament(s)"):
                    st.write(f"Statut : {ordo.get('statut', 'N/A')}")
                    # Validation du stock pour chaque médicament
                    dispo = PharmacieRepo.check_ordonnance_disponibility(
                        pharma_id, 
                        [l["medicamentId"] for l in ordo.get("lignes", [])]
                    )
                    if dispo["found"]:
                        st.write("Disponibilité en stock :")
                        for d in dispo["results"]:
                            med = MedicamentRepo.find_by_id(d["medicamentId"])
                            nom_med = med["nom"] if med else "Inconnu"
                            st.write(f"- {nom_med} : {'✅ En stock' if d['disponible'] else '❌ Rupture'} (Qté: {d['quantiteStock']})")
        else:
            st.info("Aucune ordonnance reçue pour le moment.")
            
    with tab2:
        st.markdown("### Mon Stock")
        pharma = PharmacieRepo.find_by_id(pharma_id)
        if pharma and "stock" in pharma:
            for item in pharma["stock"]:
                med = MedicamentRepo.find_by_id(item["medicamentId"])
                nom_med = med["nom"] if med else "Inconnu"
                
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"**{nom_med}**")
                qt = col2.number_input(
                    "Quantité", 
                    min_value=0, 
                    value=item.get("quantiteStock", 0), 
                    key=f"stock_{item['medicamentId']}"
                )
                if col3.button("Mettre à jour", key=f"btn_stock_{item['medicamentId']}"):
                    PharmacieRepo.update_stock(pharma_id, item["medicamentId"], qt)
                    st.toast(f"Stock de {nom_med} mis à jour !")
        else:
            st.warning("Aucun stock trouvé pour votre pharmacie.")
