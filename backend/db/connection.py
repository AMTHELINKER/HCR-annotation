# =============================================================
# Gestionnaire de connexion MongoDB (Singleton)
# =============================================================
# Connexion au Replica Set rs-hcr4 avec failover automatique.
# =============================================================

from pymongo import MongoClient
from backend.config import MONGO_URI, MONGO_DB_NAME

_client = None


def get_client() -> MongoClient:
    """Retourne le MongoClient singleton (thread-safe via pymongo)."""
    global _client
    if _client is None:
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            retryWrites=True,
        )
    return _client


def get_db(db_name: str = None):
    """Retourne l'objet Database pymongo."""
    return get_client()[db_name or MONGO_DB_NAME]


def check_connection() -> dict:
    """Vérifie la connexion et retourne les infos du Replica Set."""
    try:
        client = get_client()
        client.admin.command("ping")
        rs_status = client.admin.command("replSetGetStatus")
        members = [
            {"name": m["name"], "state": m["stateStr"]}
            for m in rs_status.get("members", [])
        ]
        primary = next((m["name"] for m in members if m["state"] == "PRIMARY"), None)
        return {
            "connected": True,
            "primary": primary,
            "members": members,
            "replica_set": rs_status.get("set"),
            "error": None,
        }
    except Exception as e:
        return {
            "connected": False,
            "primary": None,
            "members": [],
            "replica_set": None,
            "error": str(e),
        }
