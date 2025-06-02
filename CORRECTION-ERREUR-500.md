# 🔧 Correction Erreur 500 - My Pico

## 🎯 Problème
L'interface affiche "offline" avec l'erreur :
```
Failed to load resource: the server responded with a status of 500 (INTERNAL SERVER ERROR)
```

## 🚀 Solution immédiate

### **Méthode 1 : Script automatique (recommandé)**

Sur votre Mac :
```bash
cd /Users/noagiannone/Documents/aircarto-project
./sync-server-fix.sh
```

### **Méthode 2 : Correction manuelle**

#### **1. Connexion au Pi**
```bash
ssh noagia@192.168.1.145
cd /home/noagia/aircarto-server
```

#### **2. Sauvegarde de l'ancien serveur**
```bash
cp server.py server.py.backup
```

#### **3. Correction du problème**
```bash
nano server.py
```

**Dans nano, trouvez la ligne 125 environ :**
```python
"device_id": record["device_id"],
```

**Remplacez par :**
```python
"device_id": record.get("device_id") or "aircarto_001",
```

**Également ligne 191 environ :**
```python
devices.add(record["device_id"])
```

**Remplacez par :**
```python
device_id = record.get("device_id")
if device_id:
    devices.add(device_id)
```

#### **4. Redémarrage du service**
```bash
sudo systemctl restart aircarto-server.service
sudo systemctl status aircarto-server.service
```

## 🧪 Test de la correction

```bash
# Test direct de l'API
curl http://localhost:5000/api/data/latest

# Devrait retourner quelque chose comme :
# {"devices": []} ou {"devices": [{"device_id": "aircarto_001", ...}]}
```

## 🔍 Vérification des logs
 
 
```bash
# Voir les logs en temps réel
sudo journalctl -u aircarto-server.service -f

# Voir les dernières 20 lignes
sudo journalctl -u aircarto-server.service -n 20
```

## 🎯 Cause du problème

- **Avant** : `record["device_id"]` → Erreur si la clé n'existe pas
- **Après** : `record.get("device_id")` → Retourne `None` si la clé n'existe pas
- **Sécurité** : `or "aircarto_001"` → Valeur par défaut si `None`

## ✅ Résultat attendu

Après correction, l'interface devrait afficher :
- Point vert "En ligne" au lieu de rouge "Hors ligne"
- Valeurs CO2 réelles ou par défaut (400 ppm)
- Graphiques fonctionnels
- Plus d'erreur 500 dans la console

## 🚨 En cas de problème persistant

### **Diagnostique avancé :**
```bash
# Sur le Pi
python3 debug_api.py

# Test des différents endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/stats
curl http://localhost:5000/api/data/latest
```

### **Redémarrage complet :**
```bash
sudo systemctl stop aircarto-server.service
sudo systemctl start aircarto-server.service
sudo systemctl status aircarto-server.service
```

### **Si InfluxDB pose problème :**
```bash
sudo systemctl restart influxdb
docker-compose restart  # Si utilisation de Docker
```

## 🌱 Interface fonctionnelle

Une fois corrigé, l'interface My Pico devrait être pleinement opérationnelle avec :
- Dashboard principal avec données en temps réel
- Page d'analyse avec graphiques détaillés
- Statistiques environnementales
- Conseils et recommandations

**L'erreur 500 sera définitivement résolue ! 🎉** 