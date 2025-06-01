#!/bin/bash
# Script de synchronisation AirCarto vers Raspberry Pi

PI_IP="192.168.1.42"
PI_USER="noagia"
LOCAL_DIR="."
PI_DIR="~/piCO2-project"

echo "🚀 Synchronisation AirCarto vers Raspberry Pi..."
echo "📡 IP: $PI_IP"

# Synchroniser les fichiers
echo "📋 Synchronisation des fichiers..."
rsync -avz --exclude '.git' --exclude '*.pyc' --exclude '__pycache__' \
    $LOCAL_DIR/ $PI_USER@$PI_IP:$PI_DIR/

if [ $? -eq 0 ]; then
    echo "✅ Synchronisation réussie!"
    
    # Optionnel : redémarrer le serveur
    read -p "🔄 Redémarrer le serveur AirCarto? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Redémarrage du serveur..."
        ssh $PI_USER@$PI_IP "~/aircarto-manage.sh restart"
    fi
else
    echo "❌ Erreur de synchronisation!"
fi 