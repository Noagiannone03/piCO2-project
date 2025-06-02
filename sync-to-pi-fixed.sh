#!/bin/bash

# Script de synchronisation My Pico vers Raspberry Pi (Structure corrigée)
# Usage: ./sync-to-pi-fixed.sh [IP_DU_PI] [UTILISATEUR]

# Configuration pour la vraie structure du Pi
PI_IP="${1:-raspberrypi.local}"
PI_USER="${2:-noagia}"
PI_PROJECT_PATH="/home/${PI_USER}/aircarto-server"

echo "🚀 Synchronisation My Pico vers ${PI_USER}@${PI_IP}"
echo "📁 Structure corrigée : ${PI_PROJECT_PATH}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Vérification de la connexion
echo "📡 Test de connexion..."
if ! ping -c 1 "$PI_IP" > /dev/null 2>&1; then
    echo "❌ Impossible de joindre $PI_IP"
    echo "💡 Vérifiez que le Pi est allumé et connecté au réseau"
    exit 1
fi

echo "✅ Connexion OK"

# Synchronisation des nouveaux templates (design Apple)
echo "🎨 Synchronisation des templates (nouveaux designs Apple)..."
rsync -avz --progress \
    ./aircarto-server/templates/ \
    "${PI_USER}@${PI_IP}:${PI_PROJECT_PATH}/templates/"

echo "🖥️ Synchronisation du serveur Python..."
rsync -avz --progress \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='venv' \
    --exclude='server.log' \
    ./aircarto-server/server.py \
    ./aircarto-server/requirements.txt \
    ./aircarto-server/docker-compose.yml \
    "${PI_USER}@${PI_IP}:${PI_PROJECT_PATH}/"

echo ""
echo "✨ Synchronisation terminée !"
echo "🎯 Redémarrage du service sur le Pi..."

# Redémarrer le service à distance
ssh "${PI_USER}@${PI_IP}" "sudo systemctl restart aircarto-server.service"

echo ""
echo "🌐 Interface accessible sur : http://${PI_IP}:5000"
echo "📊 Analyses détaillées sur : http://${PI_IP}:5000/charts"
echo ""
echo "🔍 Pour vérifier les logs :"
echo "       ssh ${PI_USER}@${PI_IP}"
echo "       sudo journalctl -u aircarto-server.service -f" 