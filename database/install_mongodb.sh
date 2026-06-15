#!/bin/bash
# =============================================================
# Script d'installation de MongoDB 8.0 sur Kali Linux (Debian)
# Projet HCR4 - Système de Gestion des Ordonnances Médicales
# =============================================================
# Note: MongoDB 7.0 utilise une clé GPG SHA1 rejetée par Kali 2026.
#       On utilise MongoDB 8.0 avec trusted=yes comme contournement.
# =============================================================

set -e

echo "============================================="
echo " Installation de MongoDB 8.0 - HCR4"
echo "============================================="

# 1. Nettoyer les anciens dépôts MongoDB
echo "[1/5] Nettoyage des anciens dépôts..."
sudo rm -f /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo rm -f /etc/apt/sources.list.d/mongodb-org-8.0.list
sudo rm -f /usr/share/keyrings/mongodb-server-7.0.gpg
sudo rm -f /usr/share/keyrings/mongodb-server-8.0.gpg

# 2. Importer la clé GPG et ajouter le dépôt MongoDB 8.0
echo "[2/5] Ajout du dépôt MongoDB 8.0..."
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
    sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg

# Utiliser trusted=yes pour contourner le rejet SHA1 de sqv sur Kali 2026
echo "deb [ trusted=yes signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" | \
    sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list

# 3. Mettre à jour les paquets
echo "[3/5] Mise à jour de la liste des paquets..."
sudo apt-get update

# 4. Installer MongoDB
echo "[4/5] Installation de mongodb-org..."
sudo apt-get install -y mongodb-org

# 5. Vérification de l'installation
echo "[5/5] Vérification de l'installation..."
echo ""
echo "--- Versions installées ---"
mongod --version
mongosh --version
echo ""

echo "============================================="
echo " MongoDB 8.0 installé avec succès !"
echo "============================================="
echo ""
echo "Prochaine étape : bash /home/am/AM/HCR4/database/run_all.sh"
