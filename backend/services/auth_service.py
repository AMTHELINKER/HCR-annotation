# =============================================================
# Service d'Authentification — Sécurité et hachage
# =============================================================
import bcrypt
from backend.db.repositories import UtilisateurRepo, PharmacieRepo

def hash_password(password: str) -> str:
    """Hache un mot de passe en texte clair avec bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe clair correspond au hash en base."""
    if not hashed_password or not plain_password:
        return False
    # Fallback pour les mots de passe non hachés (s'il en reste)
    if plain_password == hashed_password:
        return True
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

def authenticate(email: str, password: str) -> dict:
    """
    Tente de connecter un utilisateur ou une pharmacie.
    
    Returns:
        Un dictionnaire avec les infos de session (id, role, nom, email) ou None si échec.
    """
    # 1. Chercher dans les utilisateurs (admin, medecin, patient)
    user = UtilisateurRepo.find_by_email(email)
    if user:
        if verify_password(password, user.get("motDePasse", "")):
            return {
                "id": str(user["_id"]),
                "role": user["role"],
                "nom": user["nom"],
                "email": user["email"]
            }
    
    # 2. Chercher dans les pharmacies
    pharma = PharmacieRepo.find_by_email(email)
    if pharma:
        if verify_password(password, pharma.get("motDePasse", "")):
            return {
                "id": str(pharma["_id"]),
                "role": "pharmacie",
                "nom": pharma["nom"],
                "email": pharma["email"]
            }
            
    return None
