# ✅ Guide de vérification - My Pico en vraies données

## 🔍 1. Vérifier que le serveur reçoit des données

Sur votre Raspberry Pi :

```bash
# Voir les logs du serveur en temps réel
sudo journalctl -u aircarto-server.service -f

# Ou si vous lancez le serveur manuellement :
cd /home/noagia/aircarto-server
python3 server.py

# Vous devriez voir des messages comme :
# "📊 Données reçues: 650 ppm de aircarto_001"
```

## 🔍 2. Tester les API directement

```bash
# Tester la santé du serveur
curl http://localhost:5000/health

# Tester les dernières données
curl http://localhost:5000/api/data/latest

# Tester les statistiques
curl http://localhost:5000/api/stats

# Tester l'historique
curl http://localhost:5000/api/data/history?hours=24
```

## 🔍 3. Vérifier la base de données InfluxDB

```bash
# Lancer le diagnostic InfluxDB
cd /home/noagia/aircarto-server
python3 diagnose_influxdb.py
```

## 🔍 4. Vérifier la connexion du Pico

Sur votre Pico, dans le code :

```python
# Assurez-vous que l'URL du serveur est correcte
SERVER_URL = "http://[IP_DU_PI]:5000/api/co2"

# Et que le Pico envoie bien des données :
data = {
    "device_id": "aircarto_001",
    "co2_ppm": co2_value,
    "air_quality": air_quality,
    "location": "salon"
}
```

## 🔍 5. Interface web - Indicateurs à surveiller

Dans votre navigateur sur `http://[IP_DU_PI]:5000` :

### ✅ Signes que ça fonctionne :
- **Point vert** "En ligne" dans la navbar
- **Valeur numérique** au lieu de "---"
- **Badge coloré** avec qualité d'air
- **Graphique** avec des vraies courbes
- **Horodatage** récent

### ❌ Signes de problème :
- **Point rouge** "Déconnecté" 
- **"---"** comme valeur CO2
- **"En attente du Pico..."** en permanence
- **Graphique vide** ou "Pas de données"

## 🛠️ Dépannage rapide

### Si le serveur ne reçoit rien :
1. Vérifiez que le Pico est connecté au WiFi
2. Vérifiez l'IP du serveur dans le code Pico
3. Testez avec `ping` depuis le Pico vers le Pi

### Si InfluxDB ne fonctionne pas :
```bash
# Redémarrer InfluxDB
sudo systemctl restart influxdb
sudo systemctl status influxdb

# Ou avec Docker :
cd /home/noagia/aircarto-server
docker-compose restart influxdb
```

### Si l'interface n'affiche rien :
1. Ouvrez la console développeur (F12)
2. Regardez les erreurs dans l'onglet Console
3. Vérifiez l'onglet Network pour voir les appels API

## 📊 Ajouter des données de test (si besoin)

Si vous voulez tester l'interface avec des données :

```bash
cd /home/noagia/aircarto-server
python3 add_demo_data.py
```

Puis supprimez ces données une fois le vrai Pico connecté.

## 🎯 Configuration Pico recommandée

```python
import urequests
import ujson
import time

SERVER_URL = "http://[IP_DU_PI]:5000/api/co2"

def send_data(co2_ppm):
    try:
        data = {
            "device_id": "aircarto_001",
            "co2_ppm": co2_ppm,
            "air_quality": get_air_quality(co2_ppm),
            "location": "salon",
            "timestamp": time.time()
        }
        
        response = urequests.post(
            SERVER_URL,
            headers={'Content-Type': 'application/json'},
            data=ujson.dumps(data)
        )
        
        if response.status_code == 200:
            print(f"✅ Données envoyées: {co2_ppm} ppm")
        else:
            print(f"❌ Erreur serveur: {response.status_code}")
            
        response.close()
        
    except Exception as e:
        print(f"❌ Erreur réseau: {e}")

# Envoyer toutes les 30 secondes
while True:
    co2_value = read_co2_sensor()  # Votre fonction de lecture
    send_data(co2_value)
    time.sleep(30)
``` 