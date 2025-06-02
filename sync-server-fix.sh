#!/bin/bash

# 🚀 Script de synchronisation serveur My Pico - Correction erreur 500
echo "🌱 My Pico - Synchronisation du serveur corrigé..."

# Configuration
PI_USER="noagia"
PI_HOST="192.168.1.145"  # Remplacez par l'IP de votre Pi
PI_PATH="/home/noagia/aircarto-server"

# Vérifier la connexion au Pi
echo "🔍 Test de connexion au Pi..."
if ! ping -c 1 -W 5 $PI_HOST > /dev/null 2>&1; then
    echo "❌ Impossible de joindre le Pi à l'adresse $PI_HOST"
    echo "💡 Vérifiez l'IP ou utilisez le script suivant manuellement :"
    echo ""
    echo "# Sur votre Pi, exécutez :"
    echo "cd /home/noagia/aircarto-server"
    echo "cp server.py server.py.backup"
    echo "nano server.py"
    echo "# Puis copiez le contenu corrigé depuis ce Mac"
    echo "sudo systemctl restart aircarto-server.service"
    exit 1
fi

# Synchroniser le serveur corrigé
echo "📤 Synchronisation du serveur.py corrigé..."
scp aircarto-server/server.py $PI_USER@$PI_HOST:$PI_PATH/

if [ $? -eq 0 ]; then
    echo "✅ Serveur transféré avec succès"
    
    # Redémarrer le service sur le Pi
    echo "🔄 Redémarrage du service aircarto-server..."
    ssh $PI_USER@$PI_HOST "sudo systemctl restart aircarto-server.service"
    
    if [ $? -eq 0 ]; then
        echo "✅ Service redémarré avec succès"
        
        # Vérifier le statut
        echo "📊 Vérification du statut..."
        ssh $PI_USER@$PI_HOST "sudo systemctl status aircarto-server.service --no-pager -l"
        
        # Test de l'API
        echo "🧪 Test de l'API corrigée..."
        sleep 3
        curl -s "http://$PI_HOST:5000/api/data/latest" | head -200
        echo ""
        
        echo "🎯 Correction appliquée ! Testez votre interface web :"
        echo "   http://$PI_HOST:5000"
        
    else
        echo "❌ Erreur lors du redémarrage du service"
        ssh $PI_USER@$PI_HOST "sudo journalctl -u aircarto-server.service -n 10 --no-pager"
    fi
    
else
    echo "❌ Erreur lors du transfert du fichier"
    echo "💡 Essayez la synchronisation manuelle ou vérifiez la connexion SSH"
fi

echo ""
echo "🔧 En cas de problème, logs disponibles avec :"
echo "   ssh $PI_USER@$PI_HOST 'sudo journalctl -u aircarto-server.service -f'" 