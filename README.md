# 🌱 AirCarto v2.0 - Détecteur CO2 WiFi

**Capteur CO2 intelligent avec Raspberry Pico 2W**
- 📊 Mesures CO2 en temps réel (MH-Z19C)
- 📺 Affichage OLED (SSD1309)
- 📡 Connexion WiFi automatique
- ☁️ Envoi données vers serveur
- 🔧 Configuration WiFi intuitive

## 🚀 Fonctionnalités

### ✨ Configuration WiFi Intelligente
- **Premier démarrage** → Mode configuration automatique
- **Captive Portal** → Interface web pour saisir le WiFi
- **Reconnexion auto** → Se connecte automatiquement au démarrage
- **Mode dégradé** → Fonctionne même sans WiFi

### 📊 Monitoring CO2
- Mesures toutes les 30 secondes
- Qualité d'air : EXCELLENT / BON / MOYEN / MAUVAIS / DANGER
- Affichage graphique sur écran OLED
- Historique et tendances

### 🌐 Connectivité
- Envoi automatique vers serveur
- Interface web de surveillance
- API REST pour intégration
- Gestion des déconnexions

## 🔧 Installation

### 1. Matériel requis

**Raspberry Pico 2W :**
- [Raspberry Pico 2W](https://www.raspberrypi.com/products/raspberry-pi-pico-2/)
- Câble USB-C

**Capteur CO2 MH-Z19C :**
- [MH-Z19C](https://www.winsen-sensor.com/d/files/infrared-gas-sensor/mh-z19c-pins-type-co2-manual-ver1_0.pdf)
- Alimentation 5V

**Écran OLED SSD1309 :**
- SSD1309 128x64 (interface SPI)
- Alimentation 3.3V

### 2. Connexions

```
=== ÉCRAN OLED SSD1309 (SPI) ===
Pin 33 (GND)  → GND écran
Pin 36 (3V3)  → VCC écran
Pin 4 (GPIO 2) → SCK écran
Pin 5 (GPIO 3) → SDA/MOSI écran
Pin 3 (GPIO 1) → RES écran
Pin 7 (GPIO 5) → DC écran
Pin 9 (GPIO 6) → CS écran

=== CAPTEUR CO2 MH-Z19C (UART) ===
Pin 39 (VSYS) → VCC capteur (5V)
Pin 33 (GND)  → GND capteur (partagé)
Pin 12 (GPIO 9) → RX Pico (TX capteur)
Pin 11 (GPIO 8) → TX Pico (RX capteur)
```

### 3. Installation logicielle

1. **Flasher MicroPython sur le Pico 2W**
   ```bash
   # Télécharger MicroPython pour Pico 2W
   # https://micropython.org/download/rp2-pico-w/
   ```

2. **Copier les fichiers sur le Pico**
   ```
   aircarto_complete.py  # Programme principal
   ssd1306.py           # Driver écran OLED
   ```

3. **Renommer le fichier principal**
   ```
   aircarto_complete.py → main.py
   ```

## 🎯 Utilisation

### Premier démarrage (Configuration WiFi)

1. **Alimenter le Pico** → L'écran affiche "Mode Config"

2. **Connecter au WiFi temporaire :**
   - Réseau : `AirCarto-Setup`
   - Mot de passe : `aircarto123`

3. **Configuration automatique :**
   - Une page web s'ouvre automatiquement
   - Sélectionner votre réseau WiFi
   - Saisir le mot de passe
   - Cliquer "Configurer AirCarto"

4. **Redémarrage automatique** → Le Pico se connecte à votre WiFi

### Fonctionnement normal

- **Démarrage** → Connexion WiFi automatique
- **Préchauffage** → 30 secondes de stabilisation capteur
- **Mesures** → CO2 toutes les 30 secondes
- **Affichage** → Valeurs en temps réel sur écran
- **Envoi serveur** → Données transmises automatiquement

### Indicateurs écran

```
📶 WiFi connecté     ❌ WiFi déconnecté
☁️ Serveur OK       📡 Serveur erreur

CO2: 420 ppm
Air: BON

[████████░░░░] Barre de niveau
Up: 1234s           Temps de fonctionnement
```

## 🌐 Serveur de test

### Installation serveur
```bash
# Installer Flask
pip install flask

# Lancer le serveur de test
python test_server.py
```

### Interface web
- **URL** : http://localhost:5000
- **API** : http://localhost:5000/api/co2
- **Auto-refresh** : 30 secondes

### Configuration Pico
Dans `aircarto_complete.py`, modifier :
```python
SERVER_URL = "http://votre-ip:5000/api/co2"
```

## 🔧 Configuration avancée

### Paramètres modifiables

```python
# Intervalle de mesure (secondes)
MEASUREMENT_INTERVAL = 30

# URL du serveur
SERVER_URL = "https://your-server.com/api/co2"

# ID unique du dispositif
"device_id": "aircarto_001"

# Localisation
"location": "salon"
```

### API Serveur

**Endpoint** : `POST /api/co2`

**Format JSON** :
```json
{
  "device_id": "aircarto_001",
  "timestamp": 1234567890,
  "co2_ppm": 420,
  "air_quality": "BON",
  "location": "salon"
}
```

## 🛠️ Dépannage

### Problèmes WiFi

**Symptôme** : Ne se connecte pas au WiFi
**Solution** :
1. Vérifier nom réseau et mot de passe
2. Redémarrer en mode configuration (débrancher/rebrancher)
3. Vérifier portée WiFi

### Problèmes capteur

**Symptôme** : "CAPTEUR ERREUR"
**Solutions** :
1. Vérifier connexions UART
2. Vérifier alimentation 5V
3. Attendre préchauffage complet

### Problèmes écran

**Symptôme** : Écran noir
**Solutions** :
1. Vérifier connexions SPI
2. Vérifier fichier `ssd1306.py`
3. Vérifier alimentation 3.3V

### Reset configuration WiFi

**Méthode 1** : Supprimer le fichier `wifi_config.json` sur le Pico

**Méthode 2** : Maintenir un bouton pendant le démarrage (à implémenter)

## 📊 Interprétation des mesures

| CO2 (ppm) | Qualité | État |
|-----------|---------|------|
| < 400     | EXCELLENT 😊 | Air extérieur |
| 400-600   | BON 🙂 | Air intérieur correct |
| 600-1000  | MOYEN 😐 | Aération recommandée |
| 1000-1500 | MAUVAIS 😟 | Aération nécessaire |
| > 1500    | DANGER 🚨 | Aération urgente |

## 🚀 Évolutions futures

- [ ] Interface web complète
- [ ] Base de données persistante
- [ ] Alertes par email/SMS
- [ ] Capteurs multiples
- [ ] Graphiques historiques
- [ ] Export données CSV
- [ ] Mode veille intelligent
- [ ] Calibration automatique

## 📄 Licence

Projet open-source - Libre d'utilisation et modification

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Partager vos modifications

---

**🌱 AirCarto v2.0** - Pour un air plus sain ! 🌿 