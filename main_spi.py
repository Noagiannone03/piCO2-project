"""
Raspberry Pico 2W + SSD1309 OLED Display - Version SPI
Écran OLED 2.42" 128x64 pixels - Interface SPI

Connexions utilisées par l'utilisateur :
- GND sur pin 33 (GPIO 28 - mais on peut utiliser n'importe quel GND)
- VCC sur pin 37 (3V3_EN)  
- SCK sur pin 4 (GPIO 2)
- SDA sur pin 5 (GPIO 3) - en fait MOSI pour SPI
- RES sur pin 3 (GPIO 1) - Reset
- DC sur pin 7 (GPIO 5) - Data/Command  
- CS sur pin 9 (GPIO 6) - Chip Select
"""

from machine import Pin, SPI
import time

print("=== Test Raspberry Pico 2W + SSD1309 OLED (SPI) ===")

# Configuration SPI selon tes connexions
sck_pin = Pin(2)   # Pin 4 = GPIO 2
mosi_pin = Pin(3)  # Pin 5 = GPIO 3 (ton SDA)
dc_pin = Pin(5)    # Pin 7 = GPIO 5 (Data/Command)
res_pin = Pin(1)   # Pin 3 = GPIO 1 (Reset)
cs_pin = Pin(6)    # Pin 9 = GPIO 6 (Chip Select)

print(f"Configuration SPI:")
print(f"- SCK (Clock): GPIO {sck_pin}")
print(f"- MOSI (Data): GPIO {mosi_pin}")
print(f"- DC: GPIO {dc_pin}")
print(f"- RES: GPIO {res_pin}")
print(f"- CS: GPIO {cs_pin}")

# Initialisation SPI
try:
    spi = SPI(0, baudrate=1000000, polarity=0, phase=0, 
              sck=sck_pin, mosi=mosi_pin)
    
    print("✅ SPI initialisé avec succès")
    
    # Importer la bibliothèque SSD1306 (compatible SSD1309)
    try:
        from ssd1306 import SSD1306_SPI
        
        # Configuration de l'écran
        WIDTH = 128
        HEIGHT = 64
        
        print("Initialisation de l'écran OLED...")
        
        # Initialiser l'écran OLED en mode SPI
        oled = SSD1306_SPI(WIDTH, HEIGHT, spi, dc_pin, res_pin, cs_pin)
        
        # Effacer l'écran
        oled.fill(0)
        
        # Afficher du texte
        oled.text("Pico 2W SPI", 0, 0)
        oled.text("SSD1309 OLED", 0, 15)
        oled.text("Mode SPI OK!", 0, 30)
        oled.text("AirCarto", 0, 45)
        
        # Mettre à jour l'affichage
        oled.show()
        
        print("✅ Texte affiché sur l'écran OLED!")
        print("Si tu vois le texte, l'écran fonctionne en SPI!")
        
        # Animation simple - clignotement
        for i in range(5):
            time.sleep(1)
            oled.invert(1)  # Inverser les couleurs
            time.sleep(0.5)
            oled.invert(0)  # Retour normal
            print(f"Clignotement {i+1}/5")
            
        print("🎉 Test terminé avec succès!")
            
    except ImportError:
        print("❌ Bibliothèque ssd1306 non trouvée!")
        print("Assure-toi d'avoir le fichier ssd1306.py sur le Pico")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de l'écran: {e}")
        print("Vérifications à faire :")
        print("1. Toutes les connexions sont bien faites")
        print("2. L'écran est alimenté (3.3V)")
        print("3. L'écran supporte bien le mode SPI")
        
except Exception as e:
    print(f"❌ Erreur SPI: {e}")
    print("Vérifications à faire :")
    print("1. SCK sur pin 4 (GPIO 2)")
    print("2. MOSI sur pin 5 (GPIO 3)")  
    print("3. Connexions physiques correctes")

print("\n" + "="*50)
print("Si ça ne marche pas, essaie la version I2C :")
print("1. Déconnecte RES, DC, CS")
print("2. Connecte seulement VCC, GND, SDA, SCL")
print("3. Lance main.py (version I2C)")
print("="*50) 