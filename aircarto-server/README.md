# 🌱 AirCarto Server v2.0

**Serveur de données CO2 avec InfluxDB et interface web**

## 🎯 **Fonctionnalités**

- 📊 **Base de données InfluxDB** → Stockage optimisé pour données temporelles
- 🌐 **Interface web moderne** → Dashboard temps réel + graphiques
- 📡 **API REST** → Réception données des capteurs Pico
- 📈 **Graphiques avancés** → Chart.js avec 3 types de visualisation
- 💾 **Export CSV** → Téléchargement des données
- 🔄 **Auto-refresh** → Mise à jour automatique des données
- 🛡️ **Service système** → Démarrage automatique
- 🌍 **Nginx ready** → Support reverse proxy

---

## 🚀 **Installation automatique**

### **Raspberry Pi / Debian**
```bash
# 1. Télécharger le projet
git clone <repository-url>
cd aircarto-project/aircarto-server

# 2. Rendre le script exécutable
chmod +x install.sh

# 3. Lancer l'installation
bash install.sh
```

L'installation configure automatiquement :
- ✅ InfluxDB avec base de données
- ✅ Environnement Python + dépendances
- ✅ Service système
- ✅ Nginx (optionnel)

---

## 📋 **Installation manuelle**

### **1. Prérequis**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv curl nginx
```

### **2. InfluxDB**
```bash
# Ajouter dépôt
curl -s https://repos.influxdata.com/influxdata-archive_compat.key | sudo apt-key add -
echo "deb https://repos.influxdata.com/debian stable main" | sudo tee /etc/apt/sources.list.d/influxdb.list

# Installer
sudo apt update && sudo apt install -y influxdb2

# Démarrer
sudo systemctl enable influxdb
sudo systemctl start influxdb

# Configurer
influx setup \
  --username aircarto \
  --password aircarto2024 \
  --org aircarto \
  --bucket co2_data \
  --token aircarto-token-2024
```

### **3. Application Python**
```bash
# Créer environnement
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt

# Test
python server.py
```

---

## ⚙️ **Configuration**

### **Serveur (server.py)**
```python
# Configuration InfluxDB
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "aircarto-token-2024"
INFLUXDB_ORG = "aircarto"
INFLUXDB_BUCKET = "co2_data"
```

### **Capteur Pico (aircarto_complete.py)**
```python
# Changer l'URL du serveur
SERVER_URL = "http://IP-DU-RASPBERRY:5000/api/co2"
```

---

## 🌐 **URLs d'accès**

| Page | URL | Description |
|------|-----|-------------|
| 🏠 **Dashboard** | `http://IP:5000/` | Vue d'ensemble temps réel |
| 📊 **Graphiques** | `http://IP:5000/charts` | Analyses détaillées |
| 🔧 **Health** | `http://IP:5000/health` | Status du serveur |
| 📡 **API CO2** | `http://IP:5000/api/co2` | Endpoint pour capteurs |
| 📈 **InfluxDB** | `http://IP:8086/` | Interface InfluxDB |

---

## 📡 **API Documentation**

### **Envoyer des données CO2**
```http
POST /api/co2
Content-Type: application/json

{
  "device_id": "aircarto_001",
  "co2_ppm": 450,
  "air_quality": "BON",
  "location": "salon",
  "timestamp": 1234567890
}
```

### **Récupérer les dernières données**
```http
GET /api/data/latest
```

### **Historique des données**
```http
GET /api/data/history?device=aircarto_001&hours=24
```

### **Statistiques**
```http
GET /api/stats
```

---

## 🛠️ **Gestion du serveur**

### **Service système**
```bash
# Démarrer
sudo systemctl start aircarto-server

# Arrêter
sudo systemctl stop aircarto-server

# Redémarrer
sudo systemctl restart aircarto-server

# Status
sudo systemctl status aircarto-server

# Logs
sudo journalctl -u aircarto-server -f
```

### **Script de gestion**
```bash
# Utiliser le script généré
~/aircarto-manage.sh start|stop|restart|status|logs|backup
```

---

## 📊 **Interface Web**

### **Dashboard principal**
- 📊 **Statistiques globales** → Capteurs, moyenne, mesures
- 📡 **Capteurs temps réel** → Status et données actuelles
- 🔄 **Auto-refresh** → Mise à jour toutes les 10s
- 📱 **Responsive** → Compatible mobile

### **Page graphiques**
- 📈 **Évolution temporelle** → Courbe CO2 dans le temps
- 🎯 **Répartition qualité** → Donut chart des niveaux
- 📊 **Zones de qualité** → Graphique en aires par heures
- 💾 **Export CSV** → Téléchargement des données

---

## 🔧 **Configuration Nginx**

### **Reverse proxy**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### **HTTPS avec Let's Encrypt**
```bash
sudo certbot --nginx -d your-domain.com
```

---

## 💾 **Sauvegarde et maintenance**

### **Sauvegarde InfluxDB**
```bash
# Sauvegarde manuelle
influx backup -t aircarto-token-2024 ~/backup-$(date +%Y%m%d)

# Script automatique
~/aircarto-manage.sh backup
```

### **Mise à jour**
```bash
# Avec le script
~/aircarto-manage.sh update

# Ou manuellement
cd ~/aircarto-server
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart aircarto-server
```

---

## 🐛 **Dépannage**

### **InfluxDB ne démarre pas**
```bash
# Vérifier les logs
sudo journalctl -u influxdb -f

# Réinitialiser la configuration
sudo rm -rf /var/lib/influxdb
sudo systemctl restart influxdb
```

### **Serveur Python en erreur**
```bash
# Vérifier les logs
sudo journalctl -u aircarto-server -f

# Test manuel
cd ~/aircarto-server
source venv/bin/activate
python server.py
```

### **Connexion des capteurs**
```bash
# Vérifier la connectivité
curl -X POST http://localhost:5000/api/co2 \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test","co2_ppm":400,"air_quality":"BON"}'
```

---

## 📈 **Performance et limites**

### **Capacité**
- ✅ **Capteurs** → Jusqu'à 100 devices simultanés
- ✅ **Données** → 1 mesure/minute/capteur recommandé
- ✅ **Stockage** → InfluxDB optimisé pour millions de points
- ✅ **Web** → Support 10+ utilisateurs simultanés

### **Optimisations**
- **Agrégation** → Données groupées par 5min pour affichage
- **Rétention** → Configurez la rétention InfluxDB selon besoins
- **Cache** → Nginx pour fichiers statiques

---

## 🔐 **Sécurité**

### **Recommandations**
- 🔒 **Firewall** → Restreignez l'accès aux ports nécessaires
- 🛡️ **HTTPS** → Utilisez SSL en production
- 🔑 **Tokens** → Changez les tokens par défaut
- 🚫 **Accès** → Limitez l'accès réseau si possible

### **Ports utilisés**
- **5000** → Serveur Flask (en développement)
- **8086** → InfluxDB
- **80/443** → Nginx (si configuré)

---

## 📞 **Support**

### **Logs utiles**
```bash
# Logs serveur
sudo journalctl -u aircarto-server -f

# Logs InfluxDB
sudo journalctl -u influxdb -f

# Logs Nginx
sudo tail -f /var/log/nginx/error.log
```

### **Tests de connectivité**
```bash
# Test serveur
curl http://localhost:5000/health

# Test InfluxDB
curl http://localhost:8086/health

# Test API
curl -X POST http://localhost:5000/api/co2 \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test","co2_ppm":400,"air_quality":"BON"}'
```

---

## 🆕 **Prochaines versions**

- 📱 **App mobile** → Application iOS/Android
- 🔔 **Notifications** → Alertes SMS/email
- 🌡️ **Multi-capteurs** → Température, humidité
- 🔗 **Intégrations** → Home Assistant, MQTT
- 📊 **Reporting** → Rapports PDF automatiques

---

**🌱 Profitez de votre surveillance CO2 avec AirCarto!** 🎉 