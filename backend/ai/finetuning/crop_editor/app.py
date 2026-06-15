import os
import re
import streamlit as st
from PIL import Image

# Dossier contenant les crops
CROPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../dataset/crops"))

def natural_sort_key(s):
    """Permet de trier 1_1, 1_2, 2_1 correctement au lieu de 1_1, 10_1, 2_1."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def load_images():
    if not os.path.exists(CROPS_DIR):
        return []
    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    files = [f for f in os.listdir(CROPS_DIR) if os.path.splitext(f)[1].lower() in valid_exts]
    return sorted(files, key=natural_sort_key)

st.set_page_config(page_title="Éditeur de Crops", layout="centered")

st.title("✂️ Éditeur de Crops (Médicaments)")

# Initialisation de la session
if "image_list" not in st.session_state:
    st.session_state.image_list = load_images()
    st.session_state.current_index = 0

if not st.session_state.image_list:
    st.success("Aucune image trouvée ou toutes les images ont été traitées !")
    if st.button("Recharger le dossier"):
        st.session_state.image_list = load_images()
        st.session_state.current_index = 0
        st.rerun()
    st.stop()

# Gestion des dépassements d'index
if st.session_state.current_index >= len(st.session_state.image_list):
    st.success("🎉 Vous avez parcouru toutes les images !")
    if st.button("Recommencer au début"):
        st.session_state.current_index = 0
        st.rerun()
    st.stop()
if st.session_state.current_index < 0:
    st.session_state.current_index = 0

# Image courante
current_image_name = st.session_state.image_list[st.session_state.current_index]
current_image_path = os.path.join(CROPS_DIR, current_image_name)

st.write(f"**Image {st.session_state.current_index + 1} sur {len(st.session_state.image_list)}**")

# Affichage de l'image
try:
    img = Image.open(current_image_path)
    # Afficher l'image un peu plus grande
    st.image(img, caption=current_image_name, use_container_width=True)
except Exception as e:
    st.error(f"Erreur lors du chargement de l'image : {e}")
    # Si l'image n'existe plus sur le disque (supprimée manuellement), on la retire
    if not os.path.exists(current_image_path):
        st.session_state.image_list.pop(st.session_state.current_index)
        st.rerun()

st.markdown("---")

# Formulaire d'édition
new_name = st.text_input("Modifier le nom de l'image (conserver l'extension) :", value=current_image_name)

# Boutons d'action
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("⬅️ Précédent", use_container_width=True):
        st.session_state.current_index -= 1
        st.rerun()

with col2:
    if st.button("✅ Enregistrer & Suivant", use_container_width=True, type="primary"):
        # Renommer si modifié
        if new_name != current_image_name:
            new_path = os.path.join(CROPS_DIR, new_name)
            if not os.path.exists(new_path):
                os.rename(current_image_path, new_path)
                st.session_state.image_list[st.session_state.current_index] = new_name
            else:
                st.error("Un fichier avec ce nom existe déjà !")
                st.stop()
        
        # Passer à la suivante
        st.session_state.current_index += 1
        st.rerun()

with col3:
    if st.button("🗑️ Supprimer", use_container_width=True):
        if os.path.exists(current_image_path):
            os.remove(current_image_path)
        # On retire de la liste (pas besoin d'incrémenter l'index, l'élément suivant prend sa place)
        st.session_state.image_list.pop(st.session_state.current_index)
        st.rerun()

with col4:
    if st.button("➡️ Ignorer (Garder tel quel)", use_container_width=True):
        st.session_state.current_index += 1
        st.rerun()
