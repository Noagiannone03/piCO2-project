#!/bin/bash

# Script de synchronisation My Pico vers Raspberry Pi
# Usage: ./sync-to-pi.sh [IP_DU_PI] [UTILISATEUR]

# Configuration par défaut (à modifier selon votre Pi)
PI_IP="${1:-raspberrypi.local}"
PI_USER="${2:-pi}"
PI_PROJECT_PATH="/home/${PI_USER}/aircarto-project"

echo "🚀 Synchronisation My Pico vers ${PI_USER}@${PI_IP}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Vérification de la connexion
echo "📡 Test de connexion..."
if ! ping -c 1 "$PI_IP" > /dev/null 2>&1; then
    echo "❌ Impossible de joindre $PI_IP"
    echo "💡 Vérifiez que le Pi est allumé et connecté au réseau"
    exit 1
fi

echo "✅ Connexion OK"

# Création du dossier de destination si nécessaire
echo "📁 Préparation des dossiers..."
ssh "${PI_USER}@${PI_IP}" "mkdir -p ${PI_PROJECT_PATH}/aircarto-server/templates"

# Synchronisation des fichiers serveur (nouveaux designs inclus)
echo "🎨 Synchronisation des templates (nouveaux designs Apple)..."
rsync -avz --progress \
    ./aircarto-server/templates/ \
    "${PI_USER}@${PI_IP}:${PI_PROJECT_PATH}/aircarto-server/templates/"

echo "🖥️ Synchronisation du serveur Python..."
rsync -avz --progress \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    ./aircarto-server/server.py \
    ./aircarto-server/requirements.txt \
    ./aircarto-server/docker-compose.yml \
    "${PI_USER}@${PI_IP}:${PI_PROJECT_PATH}/aircarto-server/"

echo "📱 Synchronisation du code Pico (capteur)..."
rsync -avz --progress \
    ./aircarto_complete.py \
    ./ssd1306.py \
    ./main_spi.py \
    ./debug_mhz19c.py \
    "${PI_USER}@${PI_IP}:${PI_PROJECT_PATH}/"

echo "📚 Synchronisation de la documentation..."
rsync -avz --progress \
    ./README.md \
    "${PI_USER}@${PI_IP}:${PI_PROJECT_PATH}/"

echo ""
echo "✨ Synchronisation terminée !"
echo "🎯 Prochaines étapes sur le Raspberry Pi :"
echo ""
echo "   1️⃣  Connectez-vous au Pi :"
echo "       ssh ${PI_USER}@${PI_IP}"
echo ""
echo "   2️⃣  Naviguez vers le projet :"
echo "       cd ${PI_PROJECT_PATH}/aircarto-server"
echo ""
echo "   3️⃣  Redémarrez le serveur :"
echo "       sudo pkill -f server.py"
echo "       python3 server.py"
echo ""
echo "   4️⃣  Ou utilisez Docker (recommandé) :"
echo "       docker-compose down && docker-compose up -d"
echo ""
echo "🌐 Interface accessible sur : http://${PI_IP}:5000"
echo "📊 Analyses détaillées sur : http://${PI_IP}:5000/charts" 