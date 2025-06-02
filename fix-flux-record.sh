#!/bin/bash

# 🔧 Correction rapide FluxRecord - My Pico
echo "🌱 Correction FluxRecord en cours..."

PI_USER="noagia"
PI_HOST="192.168.1.145"
PI_PATH="/home/noagia/aircarto-server"

# Test connexion
if ping -c 1 -W 3 $PI_HOST > /dev/null 2>&1; then
    echo "📤 Transfert du serveur corrigé..."
    scp aircarto-server/server.py $PI_USER@$PI_HOST:$PI_PATH/
    
    echo "🔄 Redémarrage du service..."
    ssh $PI_USER@$PI_HOST "sudo systemctl restart aircarto-server.service"
    
    echo "🧪 Test de l'API..."
    sleep 2
    curl -s "http://$PI_HOST:5000/api/data/latest"
    echo ""
    echo "✅ Correction FluxRecord appliquée !"
else
    echo "❌ Pi non accessible. Correction manuelle :"
    echo ""
    echo "# Sur le Pi, remplacez dans server.py :"
    echo "record.get(\"device_id\") → record.values.get(\"device_id\")"
    echo "record.get(\"location\") → record.values.get(\"location\")"
    echo "record.get(\"air_quality\") → record.values.get(\"air_quality\")"
    echo ""
    echo "# Puis redémarrez :"
    echo "sudo systemctl restart aircarto-server.service"
fi 