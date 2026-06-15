import bcrypt
from pymongo import MongoClient

print("=== Mise à jour des mots de passe avec Bcrypt ===")

client = MongoClient("mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs-hcr4")
db = client["hcr4_ordonnances"]

def hash_pw(pw):
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# 1. Créer un administrateur
print("Création de l'admin...")
db.utilisateurs.update_one(
    {"email": "admin@hcr4.sn"},
    {"$set": {
        "nom": "Administrateur HCR4",
        "motDePasse": hash_pw("admin123"),
        "role": "admin"
    }},
    upsert=True
)

# 2. Mettre à jour les médecins et patients (mot de passe générique: pass123)
print("Mise à jour des médecins et patients...")
for u in db.utilisateurs.find({"role": {"$in": ["medecin", "patient"]}}):
    if u["motDePasse"].startswith("$2b$12$hashedpassword"):
        db.utilisateurs.update_one({"_id": u["_id"]}, {"$set": {"motDePasse": hash_pw("pass123")}})

# 3. Ajouter des mots de passe aux pharmacies (mot de passe générique: pharma123)
print("Mise à jour des pharmacies...")
for p in db.pharmacies.find():
    if "motDePasse" not in p or p["motDePasse"] == "":
        db.pharmacies.update_one({"_id": p["_id"]}, {"$set": {"motDePasse": hash_pw("pharma123")}})

print("Terminé ! Identifiants par défaut :")
print("  - Admin: admin@hcr4.sn / admin123")
print("  - Medecin: m.diallo@hopital.sn / pass123")
print("  - Patient: a.sow@email.sn / pass123")
print("  - Pharmacie: contact@pharma-centrale.sn / pharma123")
