import streamlit as st
from backend.services.auth_service import authenticate
import time

def render():
    st.markdown("""
        <style>
        .login-box {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: rgba(255,255,255,0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            text-align: center;
        }
        .login-header {
            font-family: 'Outfit', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            color: white;
            margin-bottom: 30px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # We use empty containers to center the login box
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<div class='login-header'>HCR4 Connexion</div>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Adresse Email", placeholder="nom@exemple.com")
            password = st.text_input("Mot de Passe", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Se connecter", use_container_width=True)
            
            if submit:
                if not email or not password:
                    st.error("Veuillez remplir tous les champs.")
                else:
                    with st.spinner("Authentification..."):
                        # Small delay for UX
                        time.sleep(0.5)
                        user_info = authenticate(email, password)
                        if user_info:
                            st.session_state["user"] = user_info
                            st.rerun()
                        else:
                            st.error("Identifiants incorrects.")
        
        st.markdown("</div>", unsafe_allow_html=True)
