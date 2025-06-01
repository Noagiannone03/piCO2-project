# 🐱 Guide Mascotte AirCarto

## 🎭 **3 Versions disponibles**

### 1. **Version Bitmap Améliorée** (`aircarto_mascot_improved.py`)
- ✅ **Plus jolie** → Sprites 16x16 redessinés
- ✅ **Animations fluides** → Rebonds, tremblements
- ✅ **Expressions détaillées** → Yeux et bouche variables
- ❌ **Plus complexe** → Fichier plus gros

**Messages :**
- `"Ronron!"` → CO2 excellent
- `"C'est bon!"` → CO2 correct  
- `"DANGER!"` → CO2élevé

### 2. **Version Simple ASCII** (`simple_mascot.py`)
- ✅ **Ultra simple** → Caractères de base
- ✅ **Léger** → Prend peu de place
- ✅ **Mignon** → Style emoticon
- ❌ **Moins détaillé** → Expressions basiques

**Expressions :**
- `(^.^)` → Content
- `(o.o)` → Inquiet
- `(@.@)` → Paniqué
- `(?.?)` → Confus

### 3. **Version Originale** (`aircarto_mascot.py`)
- ⚠️ **Basique** → Premier essai
- ❌ **Sprites moches** → À améliorer

## 🎨 **Comment choisir ?**

### **Débutant** → Version Simple ASCII
```python
from simple_mascot import SimpleMascot, draw_simple_display
mascot = SimpleMascot(oled)
# Dans la boucle principale :
draw_simple_display(oled, mascot, co2_ppm, status, wifi_connected, server_success)
```

### **Intermédiaire** → Version Bitmap Améliorée
```python
from aircarto_mascot_improved import AirCartoMascotImproved, draw_main_display_with_mascot_v2
mascot = AirCartoMascotImproved(oled)
# Dans la boucle principale :
draw_main_display_with_mascot_v2(oled, mascot, co2_ppm, status, emoji, wifi_connected, server_success)
```

## 🛠️ **Créer ses propres sprites**

### **Méthode Piskel (Recommandée)**
1. **Site** : https://www.piskelapp.com/
2. **Nouveau sprite** → 16x16 pixels
3. **Dessiner** → Utiliser les outils de pixel art
4. **Export** → JSON puis convertir

### **Méthode Bitmap Converter**
1. **Site** : https://tools.withcode.uk/bitmap/
2. **Upload image** → 16x16 pixels max
3. **Black & White** → Pour OLED
4. **Copy code** → Format tableau

### **Template pour nouveau sprite**
```python
"mon_sprite": [
    0b0000000000000000,  # Ligne 0
    0b0000011111100000,  # Ligne 1
    0b0001111111111000,  # Ligne 2
    # ... 13 lignes suivantes
    0b0000011111100000,  # Ligne 15
],
```

## ✏️ **Personnaliser les messages**

### **Messages par niveau CO2**
```python
def get_custom_messages(self, co2_ppm):
    if co2_ppm < 400:
        return random.choice(["Parfait!", "Top!", "Super!"])
    elif co2_ppm < 600:
        return random.choice(["OK", "Bien", "Cool"])
    # etc...
```

### **Expressions personnalisées**
```python
# ASCII simple
"(^_^)"  # Très content
"(>.<)"  # Stress
"(=.=)"  # Fatigué
"(o_O)"  # Surpris
```

## 🎮 **Ajouter des animations**

### **Nouveau mouvement**
```python
def animate_dance(self):
    """Animation de danse quand CO2 excellent"""
    if self.current_state == "dance":
        # Bouger de gauche à droite
        self.x += (self.frame % 4 - 2)
```

### **Nouveaux événements**
```python
def animate_reaction(self, event):
    if event == "first_boot":
        self.current_state = "wave"  # Saluer
    elif event == "night_mode":
        self.current_state = "sleep"  # Dormir
```

## 📝 **Exemples d'usage**

### **Integration simple**
```python
# Dans aircarto_complete.py, fonction main()
try:
    from simple_mascot import SimpleMascot, draw_simple_display
    mascot = SimpleMascot(oled)
    use_mascot = True
    print("✅ Mascotte simple activée!")
except ImportError:
    use_mascot = False

# Dans la boucle principale
if use_mascot:
    draw_simple_display(oled, mascot, co2_ppm, status, wifi_connected, server_success)
else:
    draw_main_display(co2_ppm, status, emoji, wifi_connected, server_success)
```

### **Fallback intelligent**
```python
# Essayer la meilleure version en premier
try:
    from aircarto_mascot_improved import AirCartoMascotImproved as Mascot
    display_func = draw_main_display_with_mascot_v2
except ImportError:
    try:
        from simple_mascot import SimpleMascot as Mascot
        display_func = draw_simple_display
    except ImportError:
        use_mascot = False
```

## 🎯 **Idées d'amélioration**

- **Saisons** → Bonnet en hiver, lunettes en été
- **Météo** → Parapluie si humidité élevée  
- **Notifications** → Clignoter si message serveur
- **Mini-jeux** → Chat qui court après des particules CO2
- **Humeurs** → Content le matin, fatigué le soir
- **Interactions** → Réagir aux variations rapides

---

**🐱 Amusez-vous bien avec votre mascotte !** 😸 