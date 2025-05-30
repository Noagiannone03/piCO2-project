"""
AirCarto - Détecteur CO2 avec Raspberry Pico 2W
Capteur CO2 MH-Z19C + Écran OLED SSD1309 (SPI)
Mise à jour toutes les 4 secondes

Connexions:
=== ÉCRAN OLED SSD1309 (SPI) ===
Pin 33 (GND) → GND
Pin 36 (3V3) → VCC  
Pin 4 (GPIO 2) → SCK
Pin 5 (GPIO 3) → SDA/MOSI
Pin 3 (GPIO 1) → RES
Pin 7 (GPIO 5) → DC
Pin 9 (GPIO 6) → CS

=== CAPTEUR CO2 MH-Z19C (UART) ===
Pin 39 (VSYS) → VCC (5V)
Pin 33 (GND) → GND (partagé)
Pin 12 (GPIO 9) → RX Pico (TX capteur)
Pin 11 (GPIO 8) → TX Pico (RX capteur)
"""

from machine import Pin, SPI, UART
import time
import struct

print("🌱 === AirCarto - Détecteur CO2 === 🌱")

# =====================================================
# CONFIGURATION ÉCRAN OLED (SPI)
# =====================================================
sck_pin = Pin(2)   # Pin 4 = GPIO 2
mosi_pin = Pin(3)  # Pin 5 = GPIO 3
dc_pin = Pin(5)    # Pin 7 = GPIO 5
res_pin = Pin(1)   # Pin 3 = GPIO 1
cs_pin = Pin(6)    # Pin 9 = GPIO 6

# Initialisation SPI
spi = SPI(0, baudrate=1000000, polarity=0, phase=0, 
          sck=sck_pin, mosi=mosi_pin)

# =====================================================
# CONFIGURATION CAPTEUR CO2 MH-Z19C (UART)
# =====================================================
# UART pour communication avec MH-Z19C
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

# =====================================================
# FONCTIONS CAPTEUR CO2
# =====================================================

def read_co2():
    """Lit la valeur CO2 du capteur MH-Z19C"""
    try:
        # Vider le buffer UART
        while uart.any():
            uart.read()
        
        # Commande pour lire CO2
        cmd = bytearray([0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79])
        uart.write(cmd)
        
        # Attendre la réponse
        time.sleep(0.2)
        
        if uart.any():
            response = uart.read()
            
            # Debug: afficher la réponse reçue
            if response and len(response) >= 9:
                # Format correct: FF 86 XX XX YY YY YY YY CC
                if response[0] == 0xFF and response[1] == 0x86:
                    # CO2 est dans les bytes 2 et 3
                    co2_high = response[2]
                    co2_low = response[3] 
                    co2_ppm = co2_high * 256 + co2_low
                    
                    print(f"✅ CO2: {co2_ppm} ppm")
                    return co2_ppm
                else:
                    print(f"❌ Header invalide: {response[0]:02X} {response[1]:02X}")
                    return None
            else:
                print("❌ Réponse trop courte ou vide")
                return None
        else:
            print("❌ Pas de réponse du capteur")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lecture CO2: {e}")
        return None

def get_air_quality_status(co2_ppm):
    """Retourne le statut de qualité de l'air"""
    if co2_ppm is None:
        return "ERREUR", "---"
    elif co2_ppm < 400:
        return "EXCELLENT", "😊"
    elif co2_ppm < 600:
        return "BON", "🙂"
    elif co2_ppm < 1000:
        return "MOYEN", "😐"
    elif co2_ppm < 1500:
        return "MAUVAIS", "😟"
    else:
        return "DANGER", "🚨"

# =====================================================
# FONCTIONS AFFICHAGE
# =====================================================

def draw_header(oled):
    """Dessine l'en-tête AirCarto"""
    oled.text("AirCarto CO2", 20, 0)
    oled.hline(0, 10, 128, 1)  # Ligne horizontale

def draw_co2_display(oled, co2_ppm, status, emoji):
    """Affiche les données CO2 sur l'écran"""
    # Effacer l'écran
    oled.fill(0)
    
    # En-tête
    draw_header(oled)
    
    # Affichage CO2
    if co2_ppm is not None:
        # Valeur PPM (grande)
        co2_text = f"{co2_ppm} ppm"
        oled.text(co2_text, 25, 20)
        
        # Statut
        oled.text(f"Air: {status}", 10, 35)
        
        # Graphique simple (barre de niveau)
        bar_width = min(120, int((co2_ppm / 2000) * 120))  # Max 2000 ppm
        oled.fill_rect(4, 50, bar_width, 8, 1)
        oled.rect(4, 50, 120, 8, 1)  # Contour
        
    else:
        oled.text("CAPTEUR", 30, 25)
        oled.text("ERREUR", 35, 40)
    
    # Horodatage
    oled.text(f"Update: {time.ticks_ms()//1000}s", 0, 56)
    
    # Mettre à jour l'affichage
    oled.show()

def draw_startup_screen(oled):
    """Écran de démarrage"""
    oled.fill(0)
    oled.text("AirCarto v1.0", 15, 10)
    oled.text("Demarrage...", 15, 25)
    oled.text("Capteur CO2", 20, 40)
    oled.text("MH-Z19C", 30, 55)
    oled.show()

# =====================================================
# PROGRAMME PRINCIPAL
# =====================================================

def main():
    try:
        # Initialiser l'écran OLED
        print("📺 Initialisation écran OLED...")
        from ssd1306 import SSD1306_SPI
        oled = SSD1306_SPI(128, 64, spi, dc_pin, res_pin, cs_pin)
        print("✅ Écran OLED prêt!")
        
        # Écran de démarrage
        draw_startup_screen(oled)
        time.sleep(2)
        
        print("🌡️ Initialisation capteur CO2...")
        
        # Laisser le capteur se stabiliser
        print("⏳ Préchauffage capteur (30s)...")
        for i in range(6):
            oled.fill(0)
            oled.text("AirCarto", 25, 10)
            oled.text("Prechauffage", 15, 25)
            oled.text(f"{(6-i)*5}s restantes", 15, 40)
            oled.show()
            time.sleep(5)
        
        print("✅ Capteur prêt!")
        
        # Boucle principale de mesure
        print("🔄 Début des mesures CO2...")
        
        while True:
            # Lire CO2
            print("📊 Lecture CO2...")
            co2_ppm = read_co2()
            
            if co2_ppm is not None:
                print(f"CO2: {co2_ppm} ppm")
            else:
                print("❌ Erreur lecture CO2")
            
            # Déterminer qualité de l'air
            status, emoji = get_air_quality_status(co2_ppm)
            print(f"Qualité air: {status}")
            
            # Afficher sur écran
            draw_co2_display(oled, co2_ppm, status, emoji)
            
            # Attendre 4 secondes avant prochaine mesure
            print("⏱️ Attente 4s...\n")
            time.sleep(4)
            
    except ImportError:
        print("❌ Bibliothèque ssd1306 non trouvée!")
        print("Assure-toi d'avoir le fichier ssd1306.py sur le Pico")
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")

# =====================================================
# LANCEMENT
# =====================================================

if __name__ == "__main__":
    main() 