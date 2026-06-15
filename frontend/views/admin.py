import streamlit as st
import pandas as pd
from backend.db.repositories import UtilisateurRepo, PharmacieRepo
from backend.services.auth_service import hash_password
from frontend.utils import show_sweetalert

# =========================================================
# MODALS POUR UTILISATEURS
# =========================================================
@st.dialog("Ajouter un utilisateur")
def modal_add_user():
    with st.form("create_user_form", clear_on_submit=True):
        new_nom = st.text_input("Nom complet")
        new_email = st.text_input("Email")
        new_pw = st.text_input("Mot de passe", type="password")
        new_role = st.selectbox("Rôle", ["medecin", "patient", "admin"])
        new_spec = st.text_input("Spécialité (si médecin)")
        
        if st.form_submit_button("Enregistrer", type="primary", use_container_width=True):
            if not new_nom or not new_email or not new_pw:
                st.error("Nom, Email et Mot de passe requis.")
            else:
                UtilisateurRepo.insert_one({
                    "nom": new_nom,
                    "email": new_email,
                    "motDePasse": hash_password(new_pw),
                    "role": new_role,
                    "specialite": new_spec if new_role == "medecin" else "",
                    "patientsIds": [],
                    "medecinsIds": []
                })
                st.session_state["swal"] = ("Succès", "Utilisateur créé avec succès", "success")
                st.rerun()

@st.dialog("Modifier un utilisateur")
def modal_edit_user(u_id: str, u_nom: str, u_email: str):
    with st.form(f"edit_user_form_{u_id}"):
        edit_nom = st.text_input("Nom complet", value=u_nom)
        edit_email = st.text_input("Email", value=u_email)
        edit_pw = st.text_input("Nouveau mot de passe (vide = inchangé)", type="password")
        
        if st.form_submit_button("Sauvegarder", type="primary", use_container_width=True):
            update_data = {"nom": edit_nom, "email": edit_email}
            if edit_pw:
                update_data["motDePasse"] = hash_password(edit_pw)
            UtilisateurRepo.update_one(u_id, update_data)
            st.session_state["swal"] = ("Modifié", "L'utilisateur a été mis à jour.", "success")
            st.rerun()

@st.dialog("Supprimer un utilisateur")
def modal_delete_user(u_id: str, u_nom: str):
    st.warning(f"Êtes-vous sûr de vouloir supprimer l'utilisateur **{u_nom}** ? Cette action est irréversible.")
    c1, c2 = st.columns(2)
    if c1.button("Oui, Supprimer", type="primary", use_container_width=True, icon=":material/delete:"):
        if u_id == st.session_state.user["id"]:
            st.error("Vous ne pouvez pas supprimer votre propre compte.")
        else:
            UtilisateurRepo.delete_one(u_id)
            st.session_state["swal"] = ("Supprimé", "L'utilisateur a été supprimé.", "success")
            st.rerun()
    if c2.button("Annuler", use_container_width=True):
        st.rerun()

# =========================================================
# MODALS POUR PHARMACIES
# =========================================================
@st.dialog("Ajouter une pharmacie")
def modal_add_pharma():
    with st.form("create_pharma_form", clear_on_submit=True):
        new_p_nom = st.text_input("Nom de la pharmacie")
        new_p_email = st.text_input("Email (Identifiant)")
        new_p_pw = st.text_input("Mot de passe", type="password")
        new_p_tel = st.text_input("Téléphone")
        new_p_addr = st.text_input("Adresse")
        
        if st.form_submit_button("Enregistrer", type="primary", use_container_width=True):
            if not new_p_nom or not new_p_email or not new_p_pw:
                st.error("Nom, Email et Mot de passe requis.")
            else:
                PharmacieRepo.insert_one({
                    "nom": new_p_nom,
                    "email": new_p_email,
                    "motDePasse": hash_password(new_p_pw),
                    "telephone": new_p_tel,
                    "adresse": new_p_addr,
                    "stock": []
                })
                st.session_state["swal"] = ("Succès", "Pharmacie créée avec succès", "success")
                st.rerun()

@st.dialog("Modifier une pharmacie")
def modal_edit_pharma(p_id: str, p_nom: str, p_email: str, p_tel: str):
    with st.form(f"edit_pharma_form_{p_id}"):
        edit_p_nom = st.text_input("Nom", value=p_nom)
        edit_p_email = st.text_input("Email", value=p_email)
        edit_p_tel = st.text_input("Téléphone", value=p_tel)
        edit_p_pw = st.text_input("Nouveau mot de passe (vide = inchangé)", type="password")
        
        if st.form_submit_button("Sauvegarder", type="primary", use_container_width=True):
            update_data = {
                "nom": edit_p_nom, 
                "email": edit_p_email,
                "telephone": edit_p_tel
            }
            if edit_p_pw:
                update_data["motDePasse"] = hash_password(edit_p_pw)
            PharmacieRepo.update_one(p_id, update_data)
            st.session_state["swal"] = ("Modifiée", "La pharmacie a été mise à jour.", "success")
            st.rerun()

@st.dialog("Supprimer une pharmacie")
def modal_delete_pharma(p_id: str, p_nom: str):
    st.warning(f"Êtes-vous sûr de vouloir supprimer la pharmacie **{p_nom}** ?")
    c1, c2 = st.columns(2)
    if c1.button("Oui, Supprimer", type="primary", use_container_width=True, icon=":material/delete:"):
        PharmacieRepo.delete_one(p_id)
        st.session_state["swal"] = ("Supprimée", "La pharmacie a été supprimée.", "success")
        st.rerun()
    if c2.button("Annuler", use_container_width=True):
        st.rerun()


# =========================================================
# VUE PRINCIPALE
# =========================================================
def render():
    st.markdown("<h2 style='font-family: Outfit;'>Tableau de bord Administrateur</h2>", unsafe_allow_html=True)
    
    # Affichage des alertes SweetAlert planifiées
    if "swal" in st.session_state:
        title, text, icon = st.session_state.pop("swal")
        show_sweetalert(title, text, icon)

    tab_users, tab_pharmas = st.tabs(["Gestion des Utilisateurs", "Gestion des Pharmacies"])
    
    # --- ONGLET UTILISATEURS ---
    with tab_users:
        col_btn, _ = st.columns([1, 4])
        if col_btn.button("Ajouter un utilisateur", icon=":material/person_add:", type="primary", use_container_width=True):
            modal_add_user()

        st.markdown("<br>", unsafe_allow_html=True)
        utilisateurs = UtilisateurRepo.find_all()
        
        if utilisateurs:
            # En-têtes
            h1, h2, h3, h4, h5 = st.columns([3, 3, 2, 2, 2])
            h1.markdown("**Nom**")
            h2.markdown("**Email**")
            h3.markdown("**Rôle**")
            h4.markdown("**Spécialité**")
            h5.markdown("**Actions**")
            st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
            
            for u in utilisateurs:
                u_id = str(u["_id"])
                u_nom = u.get("nom", "")
                c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 2, 2])
                c1.write(u_nom)
                c2.write(u.get("email", ""))
                c3.write(u.get("role", "").capitalize())
                c4.write(u.get("specialite", "-") if u.get("specialite") else "-")
                
                with c5:
                    btn_edit, btn_del = st.columns(2)
                    if btn_edit.button("Editer", icon=":material/edit:", key=f"edit_u_{u_id}", help="Modifier"):
                        modal_edit_user(u_id, u_nom, u.get("email", ""))
                        
                    if btn_del.button("Suppr", icon=":material/delete:", key=f"del_u_{u_id}", help="Supprimer"):
                        modal_delete_user(u_id, u_nom)
                        
                st.markdown("<hr style='margin: 0.2rem 0; opacity: 0.2;'>", unsafe_allow_html=True)
        else:
            st.info("Aucun utilisateur trouvé.")


    # --- ONGLET PHARMACIES ---
    with tab_pharmas:
        col_btn_p, _ = st.columns([1, 4])
        if col_btn_p.button("Ajouter une pharmacie", icon=":material/local_pharmacy:", type="primary", use_container_width=True):
            modal_add_pharma()

        st.markdown("<br>", unsafe_allow_html=True)
        pharmacies = PharmacieRepo.find_all()
        
        if pharmacies:
            h1, h2, h3, h4, h5 = st.columns([3, 3, 2, 3, 2])
            h1.markdown("**Nom**")
            h2.markdown("**Email**")
            h3.markdown("**Téléphone**")
            h4.markdown("**Adresse**")
            h5.markdown("**Actions**")
            st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
            
            for p in pharmacies:
                p_id = str(p["_id"])
                p_nom = p.get("nom", "")
                c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 3, 2])
                c1.write(p_nom)
                c2.write(p.get("email", ""))
                c3.write(p.get("telephone", ""))
                c4.write(p.get("adresse", ""))
                
                with c5:
                    btn_edit_p, btn_del_p = st.columns(2)
                    if btn_edit_p.button("Editer", icon=":material/edit:", key=f"edit_p_{p_id}", help="Modifier"):
                        modal_edit_pharma(p_id, p_nom, p.get("email", ""), p.get("telephone", ""))
                        
                    if btn_del_p.button("Suppr", icon=":material/delete:", key=f"del_p_{p_id}", help="Supprimer"):
                        modal_delete_pharma(p_id, p_nom)
                                
                st.markdown("<hr style='margin: 0.2rem 0; opacity: 0.2;'>", unsafe_allow_html=True)
        else:
            st.info("Aucune pharmacie trouvée.")
