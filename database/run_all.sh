#!/bin/bash
# =============================================================
# Script de lancement complet (Replica Set + Init DB)
# Usage: sudo bash run_all.sh
# =============================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================="
echo " HCR4 - Lancement complet MongoDB"
echo "============================================="

# Vérifier que MongoDB est installé
if ! command -v mongod &> /dev/null; then
    echo "[ERREUR] MongoDB n'est pas installé."
    echo "Exécutez d'abord : sudo bash $SCRIPT_DIR/install_mongodb.sh"
    exit 1
fi

echo "MongoDB trouvé : $(mongod --version | head -1)"
echo ""

# Étape 1: Configurer le Replica Set
echo "--- Étape 1/2 : Configuration du Replica Set ---"
bash "$SCRIPT_DIR/setup_replicaset.sh"
echo ""

# Étape 2: Initialiser la base de données
echo "--- Étape 2/2 : Initialisation de la base ---"
mongosh --port 27017 "$SCRIPT_DIR/init_database.js"
echo ""

echo "============================================="
echo " Tout est prêt !"
echo "============================================="
echo ""
echo "Commandes utiles :"
echo "  mongosh                                    # Se connecter au primary"
echo "  mongosh --port 27017 --eval 'rs.status()'  # Statut replica set"
echo "  mongosh --eval 'use hcr4_ordonnances; db.utilisateurs.find()'  # Lister utilisateurs"
echo "  bash $SCRIPT_DIR/stop_replicaset.sh        # Arrêter tout"
