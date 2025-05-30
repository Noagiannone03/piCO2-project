# Raspberry Pico 2W + SSD1309 OLED Display

Ce projet montre comment utiliser un écran OLED SSD1309 (2.42", 128x64 pixels) avec un Raspberry Pico 2W en MicroPython.

## 🔧 Matériel requis

- **Raspberry Pi Pico 2W** (avec MicroPython installé)
- **Écran OLED SSD1309** 2.42" 128x64 pixels (interface I2C)
- **4 fils de connexion** (jumper wires)
- **Breadboard** (optionnel)

## 📋 Spécifications de l'écran

- **Modèle**: SSD1309 OLED
- **Taille**: 2.42 pouces
- **Résolution**: 128x64 pixels
- **Interface**: I2C/SPI (nous utilisons I2C)
- **Connexions utilisées**: 
  - R9, R10, R11, R12 (I2C)
  - R8 (SPI - non utilisé ici)

## 🔌 Schéma de câblage

```
Raspberry Pico 2W    →    SSD1309 OLED
==================        ============
GPIO 4 (Pin 6)       →    SDA (Data)
GPIO 5 (Pin 7)       →    SCL (Clock)  
3.3V (Pin 36)        →    VCC (+3.3V)
GND (Pin 38)         →    GND (Ground)
```

## 📁 Structure des fichiers

```
aircarto-project/
├── main.py          # Code principal du projet
├── ssd1306.py       # Bibliothèque pour écran OLED (compatible SSD1309)
└── README.md        # Ce fichier
```

## 🚀 Installation et utilisation

### 1. Préparer le Raspberry Pico 2W

Assure-toi que ton Pico 2W a **MicroPython** installé :
1. Télécharge le firmware MicroPython pour Pico 2W depuis [micropython.org](https://micropython.org/download/RPI_PICO2/)
2. Maintiens le bouton BOOTSEL et connecte le Pico à l'ordinateur
3. Copie le fichier `.uf2` sur le disque RPI-RP2 qui apparaît

### 2. Transférer les fichiers sur le Pico

Tu as plusieurs options pour transférer les fichiers :

#### **Option A : Avec Thonny IDE (Recommandé pour débuter)**

1. **Installer Thonny** : [thonny.org](https://thonny.org/)
2. **Configurer Thonny** :
   - Ouvre Thonny
   - Va dans `Tools` → `Options` → `Interpreter`
   - Sélectionne "MicroPython (Raspberry Pi Pico)"
   - Sélectionne le port COM de ton Pico
3. **Transférer les fichiers** :
   - Ouvre `ssd1306.py` dans Thonny
   - `File` → `Save as...` → Choisis "Raspberry Pi Pico"
   - Sauvegarde comme `ssd1306.py`
   - Répète pour `main.py`

#### **Option B : Avec rshell**

```bash
# Installer rshell
pip install rshell

# Connecter au Pico
rshell -p /dev/ttyACM0  # Linux/Mac
rshell -p COM3          # Windows

# Copier les fichiers
cp ssd1306.py /pyboard/
cp main.py /pyboard/

# Redémarrer
repl
```

#### **Option C : Avec ampy**

```bash
# Installer ampy
pip install adafruit-ampy

# Copier les fichiers
ampy -p /dev/ttyACM0 put ssd1306.py  # Linux/Mac
ampy -p COM3 put ssd1306.py          # Windows

ampy -p /dev/ttyACM0 put main.py
```

#### **Option D : Avec mpremote (recommandé)**

```bash
# Installer mpremote
pip install mpremote

# Copier les fichiers
mpremote cp ssd1306.py :
mpremote cp main.py :

# Exécuter le code
mpremote exec "exec(open('main.py').read())"
```

#### **Option E : Depuis VS Code avec l'extension Pico-W-Go**

1. Installe l'extension "Pico-W-Go" dans VS Code
2. Ouvre le dossier du projet
3. `Ctrl+Shift+P` → "Pico-W-Go: Upload current file"
4. Ou `Ctrl+Shift+P` → "Pico-W-Go: Upload project"

### 3. Exécuter le code

Une fois les fichiers transférés :

```python
# Dans le terminal de Thonny ou via rshell
exec(open('main.py').read())
```

Ou redémarre simplement le Pico pour que `main.py` s'exécute automatiquement.

## 🔍 Test et dépannage

### Messages de diagnostic

Le code affiche des messages pour t'aider à diagnostiquer les problèmes :

- ✅ **"Périphérique(s) trouvé(s)!"** : L'écran est détecté
- ❌ **"Aucun périphérique I2C détecté!"** : Problème de connexion
- ❌ **"Bibliothèque ssd1306 non trouvée!"** : Fichier manquant

### Problèmes courants

1. **Écran ne s'allume pas** :
   - Vérifie l'alimentation (3.3V et GND)
   - Vérifie que l'écran est bien compatible I2C

2. **Erreur I2C (EIO ou ETIMEDOUT)** :
   - Vérifie les connexions SDA/SCL
   - Essaie de réduire la fréquence I2C : `freq=100000`
   - Ajoute des résistances de pull-up (4.7kΩ) sur SDA et SCL

3. **Adresse I2C incorrecte** :
   - L'écran peut utiliser l'adresse 0x3D au lieu de 0x3C
   - Le code détecte automatiquement l'adresse

### Scanner I2C

Pour vérifier les périphériques connectés :

```python
from machine import Pin, I2C
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
devices = i2c.scan()
print("Périphériques trouvés:", [hex(d) for d in devices])
```

## 📊 Fonctionnalités du code

### Code principal (`main.py`)

- **Détection automatique** de l'écran I2C
- **Test de connexion** avec messages d'erreur détaillés
- **Affichage de texte** simple
- **Animation de clignotement** pour tester l'écran

### Bibliothèque (`ssd1306.py`)

- **Compatible SSD1306/SSD1309** 
- **Support I2C et SPI**
- **Fonctions graphiques** : lignes, rectangles, pixels
- **Contrôle d'affichage** : contraste, inversion, on/off

## 🎯 Prochaines étapes

Pour ton projet AirCarto avec capteur CO2, tu peux :

1. **Ajouter le capteur MH-Z19C** (UART)
2. **Créer une interface utilisateur** sur l'écran
3. **Ajouter la connectivité WiFi** du Pico 2W
4. **Envoyer les données** vers un serveur

## 📚 Ressources utiles

- [Documentation MicroPython](https://docs.micropython.org/)
- [Raspberry Pi Pico SDK](https://www.raspberrypi.org/documentation/pico/getting-started/)
- [Guide Thonny IDE](https://thonny.org/)
- [Pinout Raspberry Pico](https://pinout.xyz/pinout/i2c)

## 🐛 Support

Si tu rencontres des problèmes :

1. Vérifie que MicroPython est bien installé
2. Contrôle les connexions physiques
3. Utilise le scanner I2C pour détecter l'écran
4. Vérifie les messages d'erreur dans la console

---

**Bon développement avec ton projet AirCarto ! 🚀** 