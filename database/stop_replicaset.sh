#!/bin/bash
# =============================================================
# Arrêt propre des 3 nœuds du Replica Set
# =============================================================

echo "Arrêt des nœuds MongoDB..."

mongosh --port 27017 --quiet --eval "db.adminCommand({shutdown: 1, force: true})" 2>/dev/null && echo "  PRIMARY (27017) arrêté" || echo "  PRIMARY (27017) déjà arrêté"
mongosh --port 27018 --quiet --eval "db.adminCommand({shutdown: 1, force: true})" 2>/dev/null && echo "  SECONDARY (27018) arrêté" || echo "  SECONDARY (27018) déjà arrêté"
mongosh --port 27019 --quiet --eval "db.adminCommand({shutdown: 1, force: true})" 2>/dev/null && echo "  ARBITER (27019) arrêté" || echo "  ARBITER (27019) déjà arrêté"

echo "Tous les nœuds sont arrêtés."
