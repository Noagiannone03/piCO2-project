# 🚀 Guide de déploiement rapide AirCarto

## 📋 **Prérequis**
- **Raspberry Pi 3/4** avec Raspberry Pi OS
- **Carte SD** 16GB minimum
- **Connexion internet** pour l'installation

---

## ⚡ **Installation ultra-rapide**

### **1. Préparation du Raspberry Pi**
```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Téléchargement du projet
cd ~
git clone https://github.com/votre-username/aircarto-project.git
cd aircarto-project/aircarto-server
```

### **2. Installation automatique**
```bash
# Rendre le script exécutable
chmod +x install.sh

# Lancer l'installation (15-20 minutes)
bash install.sh
```

**🍺 Allez prendre un café ! Le script fait tout automatiquement.**

### **3. Vérification**
Après installation, vous devriez voir :
```
✅ InfluxDB configuré!
✅ Serveur fonctionne!
🎉 Installation terminée!
```

---

## 🌐 **Accès à l'interface**

### **URLs importantes**
```
📊 Dashboard: http://IP-DU-RASPBERRY:5000
📈 Graphiques: http://IP-DU-RASPBERRY:5000/charts  
🔧 Status: http://IP-DU-RASPBERRY:5000/health
📡 InfluxDB: http://IP-DU-RASPBERRY:8086
```

**💡 Trouvez l'IP de votre Raspberry Pi :**
```bash
hostname -I
```

---

## 📡 **Configuration des capteurs**

### **Modifier le Pico**
Dans `aircarto_complete.py`, ligne 29 :
```python
SERVER_URL = "http://IP-DU-RASPBERRY:5000/api/co2"
```

**Remplacez `IP-DU-RASPBERRY` par l'IP réelle !**

### **Test de connexion**
```bash
# Sur le Raspberry Pi
python3 test_data.py
```

---

## 🛠️ **Commandes utiles**

### **Gestion du serveur**
```bash
# Démarrer/arrêter
~/aircarto-manage.sh start
~/aircarto-manage.sh stop
~/aircarto-manage.sh restart

# Voir les logs
~/aircarto-manage.sh logs

# Status
~/aircarto-manage.sh status
```

### **Dépannage rapide**
```bash
# Vérifier que tout fonctionne
curl http://localhost:5000/health

# Tester l'API
curl -X POST http://localhost:5000/api/co2 \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test","co2_ppm":400,"air_quality":"BON"}'

# Logs InfluxDB
sudo journalctl -u influxdb -f
```

---

## 🎯 **Checklist finale**

- [ ] ✅ Raspberry Pi mis à jour
- [ ] ✅ Script `install.sh` exécuté sans erreur
- [ ] ✅ Dashboard accessible via navigateur
- [ ] ✅ InfluxDB interface accessible
- [ ] ✅ IP du serveur configurée dans le Pico
- [ ] ✅ Test de données effectué avec succès

---

## 🆘 **Problèmes courants**

### **❌ "InfluxDB ne démarre pas"**
```bash
sudo systemctl restart influxdb
sudo journalctl -u influxdb -f
```

### **❌ "Serveur inaccessible"**
```bash
# Vérifier le service
sudo systemctl status aircarto-server

# Redémarrer
sudo systemctl restart aircarto-server
```

### **❌ "Capteurs ne se connectent pas"**
- Vérifiez l'IP dans `SERVER_URL`
- Vérifiez que le port 5000 est ouvert
- Testez avec `test_data.py`

---

## 🎉 **C'est tout !**

Votre serveur AirCarto est maintenant prêt !

**📍 Prochaines étapes :**
1. Configurez vos capteurs Pico
2. Regardez les données arriver en temps réel
3. Explorez les graphiques et statistiques

**💡 Besoin d'aide ?** Consultez le `README.md` complet. 