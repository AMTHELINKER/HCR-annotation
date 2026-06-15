#!/bin/bash
# =============================================================
# Configuration du Replica Set MongoDB (3 nœuds sur la même machine)
# Projet HCR4 - Système de Gestion des Ordonnances Médicales
# =============================================================
# Architecture :
#   - rs0-primary   : port 27017 (PRIMARY)
#   - rs0-secondary : port 27018 (SECONDARY)
#   - rs0-arbiter   : port 27019 (ARBITER)
# =============================================================

set -e

REPLICA_SET_NAME="rs-hcr4"
DATA_DIR="/home/am/AM/HCR4/database/data"
LOG_DIR="/home/am/AM/HCR4/database/logs"
CONFIG_DIR="/home/am/AM/HCR4/database/config"

echo "============================================="
echo " Configuration du Replica Set MongoDB"
echo " Nom: $REPLICA_SET_NAME"
echo "============================================="

# 1. Créer les répertoires de données et logs
echo "[1/5] Création des répertoires..."
mkdir -p "$DATA_DIR/rs0-primary"
mkdir -p "$DATA_DIR/rs0-secondary"
mkdir -p "$DATA_DIR/rs0-arbiter"
mkdir -p "$LOG_DIR"
mkdir -p "$CONFIG_DIR"

# 2. Arrêter toute instance MongoDB existante
echo "[2/5] Arrêt des instances existantes..."
mongosh --port 27017 --eval "db.adminCommand({shutdown: 1})" 2>/dev/null || true
mongosh --port 27018 --eval "db.adminCommand({shutdown: 1})" 2>/dev/null || true
mongosh --port 27019 --eval "db.adminCommand({shutdown: 1})" 2>/dev/null || true
sudo systemctl stop mongod 2>/dev/null || true
sleep 2

# 3. Générer les fichiers de configuration YAML
echo "[3/5] Génération des fichiers de configuration..."

cat > "$CONFIG_DIR/mongod-primary.conf" << EOF
# Configuration du nœud PRIMARY (port 27017)
storage:
  dbPath: $DATA_DIR/rs0-primary

systemLog:
  destination: file
  path: $LOG_DIR/mongod-primary.log
  logAppend: true

net:
  port: 27017
  bindIp: 127.0.0.1

replication:
  replSetName: "$REPLICA_SET_NAME"

processManagement:
  fork: true
  pidFilePath: $LOG_DIR/mongod-primary.pid
EOF

cat > "$CONFIG_DIR/mongod-secondary.conf" << EOF
# Configuration du nœud SECONDARY (port 27018)
storage:
  dbPath: $DATA_DIR/rs0-secondary

systemLog:
  destination: file
  path: $LOG_DIR/mongod-secondary.log
  logAppend: true

net:
  port: 27018
  bindIp: 127.0.0.1

replication:
  replSetName: "$REPLICA_SET_NAME"

processManagement:
  fork: true
  pidFilePath: $LOG_DIR/mongod-secondary.pid
EOF

cat > "$CONFIG_DIR/mongod-arbiter.conf" << EOF
# Configuration du nœud ARBITER (port 27019)
storage:
  dbPath: $DATA_DIR/rs0-arbiter

systemLog:
  destination: file
  path: $LOG_DIR/mongod-arbiter.log
  logAppend: true

net:
  port: 27019
  bindIp: 127.0.0.1

replication:
  replSetName: "$REPLICA_SET_NAME"

processManagement:
  fork: true
  pidFilePath: $LOG_DIR/mongod-arbiter.pid
EOF

# 4. Démarrer les 3 nœuds MongoDB
echo "[4/5] Démarrage des 3 nœuds du Replica Set..."

mongod --config "$CONFIG_DIR/mongod-primary.conf"
echo "  -> PRIMARY démarré sur le port 27017"

mongod --config "$CONFIG_DIR/mongod-secondary.conf"
echo "  -> SECONDARY démarré sur le port 27018"

mongod --config "$CONFIG_DIR/mongod-arbiter.conf"
echo "  -> ARBITER démarré sur le port 27019"

sleep 3

# 5. Initialiser le Replica Set
echo "[5/5] Initialisation du Replica Set..."

mongosh --port 27017 --eval "
rs.initiate({
  _id: '$REPLICA_SET_NAME',
  members: [
    { _id: 0, host: '127.0.0.1:27017', priority: 2 },
    { _id: 1, host: '127.0.0.1:27018', priority: 1 },
    { _id: 2, host: '127.0.0.1:27019', arbiterOnly: true }
  ]
})
"

echo ""
echo "Attente de l'élection du PRIMARY (10 secondes)..."
sleep 10

# Vérification du statut
echo ""
echo "--- Statut du Replica Set ---"
mongosh --port 27017 --eval "rs.status().members.forEach(m => print(m.name + ' => ' + m.stateStr))"

echo ""
echo "============================================="
echo " Replica Set '$REPLICA_SET_NAME' configuré !"
echo "============================================="
echo ""
echo "Connexion : mongosh 'mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=$REPLICA_SET_NAME'"
echo ""
echo "Prochaine étape : exécutez ./init_database.sh"
