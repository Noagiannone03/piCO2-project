# 🔧 Correction rapide - Erreur 500 API

## 🎯 Problème identifié
L'erreur 500 sur `/api/data/latest` vient de l'accès aux propriétés des records InfluxDB qui peuvent être `None` ou manquantes.

## 🚀 Solution immédiate

### **Sur votre Raspberry Pi :**

```bash
# 1. Aller dans le dossier serveur
cd /home/noagia/aircarto-server

# 2. Diagnostiquer le problème
python3 debug_api.py

# 3. Sauvegarder l'ancien serveur
cp server.py server.py.broken

# 4. Éditer le serveur pour corriger l'erreur
nano server.py
```

### **Dans nano, remplacer la fonction `get_latest_data()` (vers ligne 106):**

```python
@app.route('/api/data/latest')
def get_latest_data():
    """Récupère les dernières données avec gestion d'erreur robuste"""
    try:
        if not query_api:
            logger.error("❌ InfluxDB query_api non disponible")
            return jsonify({"error": "InfluxDB not available", "devices": []}), 503
        
        # Requête simple sans grouping
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "co2_measurement")
            |> filter(fn: (r) => r._field == "co2_ppm")
            |> last()
        '''
        
        result = query_api.query(query=query)
        
        devices = []
        for table in result:
            for record in table.records:
                try:
                    # Accès sécurisé aux propriétés
                    device_data = {
                        "device_id": record.get("device_id") or "aircarto_001",
                        "location": record.get("location") or "salon", 
                        "co2_ppm": int(record.get_value()) if record.get_value() is not None else 0,
                        "air_quality": record.get("air_quality") or "unknown",
                        "timestamp": record.get_time().isoformat() if record.get_time() else datetime.utcnow().isoformat()
                    }
                    devices.append(device_data)
                    logger.info(f"✅ Device récupéré: {device_data['device_id']} - {device_data['co2_ppm']} ppm")
                    
                except Exception as record_error:
                    logger.error(f"❌ Erreur processing record: {record_error}")
                    continue
        
        return jsonify({"devices": devices})
        
    except Exception as e:
        logger.error(f"❌ Erreur lecture: {e}")
        return jsonify({"error": str(e), "devices": []}), 500
```

### **5. Redémarrer le serveur :**

```bash
# Redémarrer le service
sudo systemctl restart aircarto-server.service

# Vérifier les logs
sudo journalctl -u aircarto-server.service -f
```

## 🧪 Test rapide

```bash
# Tester l'API corrigée
curl http://localhost:5000/api/data/latest

# Devrait retourner quelque chose comme :
# {"devices": []} ou {"devices": [{"device_id": "aircarto_001", ...}]}
```

## 🔧 Alternative : Script de correction automatique

Créer un script pour appliquer le correctif :

```bash
# Sur le Pi
cat > fix_server.py << 'EOF'
#!/usr/bin/env python3
import re

# Lire le fichier serveur
with open('server.py', 'r') as f:
    content = f.read()

# Pattern pour trouver la fonction get_latest_data
pattern = r'@app\.route\(\'/api/data/latest\'\)\ndef get_latest_data\(\):.*?return jsonify\(.*?\), 500'

# Nouvelle fonction corrigée
new_function = '''@app.route('/api/data/latest')
def get_latest_data():
    """Récupère les dernières données avec gestion d'erreur robuste"""
    try:
        if not query_api:
            return jsonify({"error": "InfluxDB not available", "devices": []}), 503
        
        # Requête simple sans grouping
        query = f\'\'\'
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "co2_measurement")
            |> filter(fn: (r) => r._field == "co2_ppm")
            |> last()
        \'\'\'
        
        result = query_api.query(query=query)
        
        devices = []
        for table in result:
            for record in table.records:
                try:
                    device_data = {
                        "device_id": record.get("device_id") or "aircarto_001",
                        "location": record.get("location") or "salon", 
                        "co2_ppm": int(record.get_value()) if record.get_value() is not None else 0,
                        "air_quality": record.get("air_quality") or "unknown",
                        "timestamp": record.get_time().isoformat() if record.get_time() else datetime.utcnow().isoformat()
                    }
                    devices.append(device_data)
                except:
                    continue
        
        return jsonify({"devices": devices})
        
    except Exception as e:
        logger.error(f"❌ Erreur lecture: {e}")
        return jsonify({"error": str(e), "devices": []}), 500'''

# Remplacer la fonction
content_fixed = re.sub(pattern, new_function, content, flags=re.DOTALL)

# Sauvegarder
with open('server.py', 'w') as f:
    f.write(content_fixed)

print("✅ Serveur corrigé !")
EOF

# Exécuter le correctif
python3 fix_server.py
```

## 📊 Ajouter des données de test

Si vous n'avez pas encore de données du Pico :

```bash
# Ajouter des données de démo pour tester
python3 add_demo_data.py

# Puis tester l'interface
# Elle devrait maintenant afficher les données
```

## ✅ Vérification finale

1. **Interface web** : `http://[IP_PI]:5000` 
   - Point vert "En ligne"
   - Valeurs numériques CO2
   - Graphique avec courbes

2. **API directement** :
   ```bash
   curl http://localhost:5000/api/data/latest
   curl http://localhost:5000/api/stats
   ```

3. **Logs serveur** :
   ```bash
   sudo journalctl -u aircarto-server.service -n 20
   ```

## 🎯 Cause du problème

L'ancienne version utilisait `record["device_id"]` qui plante si la clé n'existe pas.
La nouvelle version utilise `record.get("device_id")` qui retourne `None` si la clé n'existe pas, puis `or "aircarto_001"` pour une valeur par défaut.

**L'interface devrait maintenant fonctionner parfaitement ! 🚀** 