#!/bin/bash
# Script de réparation InfluxDB pour AirCarto

echo "🔧 === Réparation InfluxDB AirCarto ==="
echo

# 1. Vérifier et démarrer InfluxDB
echo "1️⃣ Démarrage d'InfluxDB..."
sudo systemctl start influxdb
sudo systemctl enable influxdb
sleep 3

# 2. Vérifier le statut
echo "2️⃣ Vérification du statut..."
systemctl is-active influxdb

# 3. Vérifier les logs
echo "3️⃣ Derniers logs InfluxDB:"
journalctl -u influxdb --no-pager -n 5

# 4. Attendre qu'InfluxDB soit prêt
echo "4️⃣ Attente du démarrage complet..."
for i in {1..30}; do
    if curl -s http://localhost:8086/health > /dev/null 2>&1; then
        echo "✅ InfluxDB est prêt!"
        break
    fi
    echo -n "."
    sleep 1
done

# 5. Vérifier la configuration
echo
echo "5️⃣ Test de la configuration..."
curl -s http://localhost:8086/health | jq '.' 2>/dev/null || echo "InfluxDB répond mais JSON manquant"

# 6. Redémarrer le service AirCarto
echo "6️⃣ Redémarrage du service AirCarto..."
sudo systemctl restart aircarto
sleep 2

# 7. Test final
echo "7️⃣ Test final de l'état du système..."
curl -s http://localhost:5000/health | jq '.' 2>/dev/null || echo "Service AirCarto non disponible"

echo
echo "🎉 Réparation terminée!"
echo "Testez maintenant: curl http://localhost:5000/health" 