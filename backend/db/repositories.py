# =============================================================
# Repositories — Couche d'accès aux données MongoDB
# =============================================================
# Pattern Repository : chaque classe encapsule les opérations
# CRUD et les requêtes métier d'une collection.
#
# Pour ajouter une nouvelle collection :
#   1. Créer une classe MonNouveauRepo(BaseRepo)
#   2. Définir collection_name = "ma_collection"
#   3. Ajouter les méthodes métier spécifiques
#   4. Exporter dans backend/db/__init__.py
# =============================================================

from datetime import datetime, timezone
from bson import ObjectId
from backend.db.connection import get_db


def _to_oid(value):
    """Convertit une chaîne en ObjectId si nécessaire."""
    return ObjectId(value) if isinstance(value, str) else value


class BaseRepo:
    """Opérations CRUD génériques héritables par tous les repositories."""

    collection_name: str = None

    @classmethod
    def _col(cls):
        return get_db()[cls.collection_name]

    @classmethod
    def find_all(cls, filtre=None, projection=None, limit=0):
        return list(cls._col().find(filtre or {}, projection, limit=limit))

    @classmethod
    def find_by_id(cls, doc_id):
        return cls._col().find_one({"_id": _to_oid(doc_id)})

    @classmethod
    def insert_one(cls, document: dict):
        return cls._col().insert_one(document).inserted_id

    @classmethod
    def insert_many(cls, documents: list):
        return cls._col().insert_many(documents).inserted_ids

    @classmethod
    def update_one(cls, doc_id, update: dict):
        if not any(k.startswith("$") for k in update):
            update = {"$set": update}
        return cls._col().update_one({"_id": _to_oid(doc_id)}, update)

    @classmethod
    def delete_one(cls, doc_id):
        return cls._col().delete_one({"_id": _to_oid(doc_id)})

    @classmethod
    def count(cls, filtre=None):
        return cls._col().count_documents(filtre or {})


# -----------------------------------------------------------------
# Medicament
# -----------------------------------------------------------------

class MedicamentRepo(BaseRepo):
    collection_name = "medicaments"

    @classmethod
    def search_by_name(cls, query: str, limit=10):
        return list(cls._col().find(
            {"nom": {"$regex": query, "$options": "i"}}, limit=limit
        ))

    @classmethod
    def text_search(cls, query: str, limit=10):
        return list(cls._col().find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}},
        ).sort([("score", {"$meta": "textScore"})]).limit(limit))

    @classmethod
    def get_all_names(cls) -> list[str]:
        return [doc["nom"] for doc in cls._col().find({}, {"nom": 1, "_id": 0})]


# -----------------------------------------------------------------
# Utilisateur (Medecin + Patient — héritage par discriminateur)
# -----------------------------------------------------------------

class UtilisateurRepo(BaseRepo):
    collection_name = "utilisateurs"

    @classmethod
    def find_medecins(cls, projection=None):
        return list(cls._col().find({"role": "medecin"}, projection))

    @classmethod
    def find_patients(cls, projection=None):
        return list(cls._col().find({"role": "patient"}, projection))

    @classmethod
    def find_by_email(cls, email: str):
        return cls._col().find_one({"email": email})

    @classmethod
    def authenticate(cls, email: str, mot_de_passe_hash: str):
        return cls._col().find_one({"email": email, "motDePasse": mot_de_passe_hash})

    @classmethod
    def get_patients_of_medecin(cls, medecin_id):
        medecin = cls._col().find_one({"_id": _to_oid(medecin_id)})
        if medecin and medecin.get("patientsIds"):
            return list(cls._col().find({"_id": {"$in": medecin["patientsIds"]}}))
        return []


# -----------------------------------------------------------------
# Ordonnance (avec LigneOrdonnance embarquées)
# -----------------------------------------------------------------

class OrdonnanceRepo(BaseRepo):
    collection_name = "ordonnances"

    @classmethod
    def find_by_patient(cls, patient_id, limit=0):
        return list(cls._col().find(
            {"patientId": _to_oid(patient_id)}
        ).sort("dateCreation", -1).limit(limit))

    @classmethod
    def find_by_medecin(cls, medecin_id, limit=0):
        return list(cls._col().find(
            {"medecinId": _to_oid(medecin_id)}
        ).sort("dateCreation", -1).limit(limit))

    @classmethod
    def find_by_statut(cls, statut: str):
        return list(cls._col().find({"statut": statut}).sort("dateCreation", -1))

    @classmethod
    def create_from_pipeline(cls, medecin_id, patient_id, fichier_original: str,
                              contenu_digitalise: str, lignes: list) -> ObjectId:
        """Crée une ordonnance depuis le pipeline HTR.
        
        Args:
            lignes: [{medicamentId, quantite, posologie, duree}, ...]
        """
        for ligne in lignes:
            if isinstance(ligne.get("medicamentId"), str):
                ligne["medicamentId"] = ObjectId(ligne["medicamentId"])

        return cls.insert_one({
            "dateCreation": datetime.now(timezone.utc),
            "statut": "digitalisee",
            "fichierOriginal": fichier_original,
            "contenuDigitalise": contenu_digitalise,
            "medecinId": _to_oid(medecin_id),
            "patientId": _to_oid(patient_id),
            "lignes": lignes,
        })

    @classmethod
    def update_statut(cls, ordonnance_id, nouveau_statut: str):
        return cls.update_one(ordonnance_id, {"statut": nouveau_statut})

    @classmethod
    def get_with_details(cls, ordonnance_id):
        """Ordonnance enrichie avec noms médecin/patient via aggregation."""
        pipeline = [
            {"$match": {"_id": _to_oid(ordonnance_id)}},
            {"$lookup": {"from": "utilisateurs", "localField": "medecinId",
                         "foreignField": "_id", "as": "medecin"}},
            {"$lookup": {"from": "utilisateurs", "localField": "patientId",
                         "foreignField": "_id", "as": "patient"}},
            {"$unwind": {"path": "$medecin", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$patient", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": "pharmacies", "localField": "pharmacieDestinataireId",
                         "foreignField": "_id", "as": "pharmacie"}},
            {"$unwind": {"path": "$pharmacie", "preserveNullAndEmptyArrays": True}},
        ]
        results = list(cls._col().aggregate(pipeline))
        return results[0] if results else None

    @classmethod
    def send_to_pharmacie(cls, ordonnance_id, pharmacie_id):
        """Envoie l'ordonnance à une pharmacie (met à jour le statut)."""
        return cls.update_one(ordonnance_id, {
            "statut": "envoyee", 
            "pharmacieDestinataireId": _to_oid(pharmacie_id)
        })

    @classmethod
    def find_by_pharmacie(cls, pharmacie_id, limit=0):
        """Retourne les ordonnances reçues par une pharmacie."""
        return list(cls._col().find(
            {"pharmacieDestinataireId": _to_oid(pharmacie_id)}
        ).sort("dateCreation", -1).limit(limit))


# -----------------------------------------------------------------
# Pharmacie (avec DisponibiliteMedicament embarquées)
# -----------------------------------------------------------------

class PharmacieRepo(BaseRepo):
    collection_name = "pharmacies"

    @classmethod
    def find_by_email(cls, email: str):
        """Recherche une pharmacie par email (pour la connexion)."""
        return cls._col().find_one({"email": email})

    @classmethod
    def find_with_medicament(cls, medicament_id):
        """Pharmacies ayant ce médicament disponible en stock."""
        return list(cls._col().find({
            "stock": {"$elemMatch": {
                "medicamentId": _to_oid(medicament_id),
                "disponible": True
            }}
        }))

    @classmethod
    def update_stock(cls, pharmacie_id, medicament_id, quantite: int):
        return cls._col().update_one(
            {"_id": _to_oid(pharmacie_id), "stock.medicamentId": _to_oid(medicament_id)},
            {"$set": {
                "stock.$.quantiteStock": quantite,
                "stock.$.disponible": quantite > 0,
                "stock.$.dateMiseAJour": datetime.now(timezone.utc),
            }}
        )

    @classmethod
    def check_ordonnance_disponibility(cls, pharmacie_id, medicament_ids: list):
        """Vérifie la disponibilité de tous les médicaments d'une ordonnance."""
        pharmacie = cls._col().find_one({"_id": _to_oid(pharmacie_id)})
        if not pharmacie:
            return {"found": False, "results": []}
        stock_map = {s["medicamentId"]: s for s in pharmacie.get("stock", [])}
        results = []
        for mid in medicament_ids:
            entry = stock_map.get(_to_oid(mid), {})
            results.append({
                "medicamentId": _to_oid(mid),
                "disponible": entry.get("disponible", False),
                "quantiteStock": entry.get("quantiteStock", 0),
            })
        return {"found": True, "results": results}
