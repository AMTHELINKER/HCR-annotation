import streamlit as st
import streamlit.components.v1 as components

def show_sweetalert(title: str, text: str, icon: str = "success"):
    """
    Affiche une notification SweetAlert2.
    icon: 'success', 'error', 'warning', 'info', 'question'
    """
    js = f"""
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            Swal.fire({{
                title: "{title}",
                text: "{text}",
                icon: "{icon}",
                confirmButtonColor: "#6366f1",
                timer: 3000,
                timerProgressBar: true
            }});
        }});
    </script>
    """
    # On utilise un conteneur très petit pour injecter le JS sans gêner l'UI
    components.html(js, height=0, width=0)
