"""
AirCarto - Détecteur CO2 avec Raspberry Pico 2W
Capteur CO2 MH-Z19C + Écran OLED SSD1309 (SPI) + WiFi + Serveur
Mise à jour toutes les 30 secondes avec envoi de données

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

from machine import Pin, SPI, UART, reset
import network
import socket
import time
import json
import urequests
import struct
import os

print("🌱 === AirCarto v2.0 - WiFi Ready === 🌱")

# =====================================================
# CONFIGURATION
# =====================================================
WIFI_CONFIG_FILE = "wifi_config.json"
SERVER_URL = "http://192.168.1.42:5000/api/co2"  # 🔧 IP du Raspberry Pi!
AP_SSID = "AirCarto-Setup"
AP_PASSWORD = "aircarto123"
MEASUREMENT_INTERVAL = 30  # secondes
RETRY_INTERVAL = 5  # secondes entre tentatives de connexion

# =====================================================
# CONFIGURATION MATÉRIEL
# =====================================================
# Écran OLED (SPI)
sck_pin = Pin(2)
mosi_pin = Pin(3)
dc_pin = Pin(5)
res_pin = Pin(1)
cs_pin = Pin(6)
spi = SPI(0, baudrate=1000000, polarity=0, phase=0, sck=sck_pin, mosi=mosi_pin)

# Capteur CO2 (UART)
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

# Variables globales
oled = None
wifi_connected = False
ap_mode = False
mascot = None  # Nouvelle variable pour la mascotte

# =====================================================
# GESTION WIFI & CONFIGURATION
# =====================================================

def load_wifi_config():
    """Charge la configuration WiFi depuis le fichier"""
    try:
        with open(WIFI_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def save_wifi_config(ssid, password):
    """Sauvegarde la configuration WiFi"""
    config = {"ssid": ssid, "password": password}
    with open(WIFI_CONFIG_FILE, 'w') as f:
        json.dump(config, f)
    print(f"✅ WiFi sauvegardé: {ssid}")

def connect_wifi(ssid=None, password=None):
    """Tente de se connecter au WiFi"""
    global wifi_connected
    
    # Si SSID/password fournis directement, les utiliser
    if ssid and password:
        config = {"ssid": ssid, "password": password}
    else:
        # Sinon charger depuis le fichier
        config = load_wifi_config()
        if not config:
            print("❌ Pas de configuration WiFi")
            return False
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    print(f"🔌 Connexion à {config['ssid']}...")
    display_status("Connexion WiFi", config['ssid'])
    
    wlan.connect(config['ssid'], config['password'])
    
    # Attendre la connexion (max 15s)
    timeout = 15
    while timeout > 0 and not wlan.isconnected():
        time.sleep(1)
        timeout -= 1
        print(f"⏳ Tentative... {timeout}s")
        if timeout % 3 == 0:  # Mise à jour écran toutes les 3s
            display_status("Connexion WiFi", f"{config['ssid']} ({timeout}s)")
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"✅ WiFi connecté! IP: {ip}")
        display_status("WiFi connecté", ip)
        wifi_connected = True
        return True
    else:
        print("❌ Connexion WiFi échouée")
        display_status("WiFi échoué", "Vérifiez config")
        wifi_connected = False
        return False

def start_access_point():
    """Démarre le point d'accès pour configuration"""
    global ap_mode
    
    print("📡 Démarrage mode configuration...")
    display_status("Mode Config", "AirCarto-Setup")
    
    # Créer point d'accès
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASSWORD)
    
    while not ap.active():
        time.sleep(1)
    
    print(f"✅ Point d'accès créé: {AP_SSID}")
    print(f"🔑 Mot de passe: {AP_PASSWORD}")
    print(f"🌐 IP: {ap.ifconfig()[0]}")
    
    ap_mode = True
    return ap

def create_captive_portal():
    """Crée le serveur web pour la configuration"""
    
    html_page = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AirCarto - Configuration WiFi</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; background: #f0f8ff; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h1 { color: #2c5282; text-align: center; margin-bottom: 30px; }
            .logo { text-align: center; font-size: 48px; margin-bottom: 20px; }
            input, select { width: 100%; padding: 12px; margin: 10px 0; border: 2px solid #ddd; border-radius: 5px; font-size: 16px; }
            button { width: 100%; padding: 15px; background: #4CAF50; color: white; border: none; border-radius: 5px; font-size: 18px; cursor: pointer; }
            button:hover { background: #45a049; }
            .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .step { margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🌱</div>
            <h1>AirCarto Setup</h1>
            
            <div class="info">
                <strong>📋 Instructions:</strong>
                <div class="step">1. Sélectionnez votre réseau WiFi</div>
                <div class="step">2. Entrez le mot de passe</div>
                <div class="step">3. Cliquez sur "Configurer"</div>
                <div class="step">4. AirCarto se connectera automatiquement</div>
            </div>
            
            <form action="/configure" method="POST">
                <label for="ssid"><strong>🔌 Réseau WiFi:</strong></label>
                <select name="ssid" id="ssid" required>
                    <option value="">-- Sélectionnez un réseau --</option>
                    %NETWORKS%
                </select>
                
                <label for="password"><strong>🔑 Mot de passe:</strong></label>
                <input type="password" name="password" id="password" placeholder="Mot de passe WiFi" required>
                
                <button type="submit">🚀 Configurer AirCarto</button>
            </form>
        </div>
        
        <script>
            // Auto-refresh networks every 10s
            setTimeout(() => location.reload(), 10000);
        </script>
    </body>
    </html>
    """
    
    success_page = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AirCarto - Configuré!</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; background: #f0f8ff; text-align: center; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h1 { color: #4CAF50; }
            .success { font-size: 64px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✅</div>
            <h1>Configuration réussie!</h1>
            <p><strong>AirCarto se connecte à votre WiFi...</strong></p>
            <p>Votre capteur va maintenant fonctionner en mode normal et commencer les mesures CO2.</p>
            <p><em>Vous pouvez fermer cette page et vous déconnecter du réseau AirCarto-Setup.</em></p>
        </div>
        <script>
            setTimeout(() => window.close(), 8000);
        </script>
    </body>
    </html>
    """
    
    def scan_networks():
        """Scanne les réseaux WiFi disponibles"""
        try:
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            networks = wlan.scan()
            
            network_options = ""
            seen_ssids = set()
            
            for net in networks:
                ssid = net[0].decode('utf-8')
                if ssid and ssid not in seen_ssids:
                    signal_strength = net[3]
                    security = "🔒" if net[4] > 0 else "🔓"
                    network_options += f'<option value="{ssid}">{security} {ssid} ({signal_strength}dBm)</option>\n'
                    seen_ssids.add(ssid)
            
            return network_options
        except Exception as e:
            print(f"❌ Erreur scan WiFi: {e}")
            return '<option value="">Erreur scan réseaux</option>'
    
    # Créer serveur web
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 80))
    s.listen(5)
    
    print("🌐 Serveur web démarré sur http://192.168.4.1")
    display_status("Web Config", "192.168.4.1")
    
    while ap_mode:
        conn = None  # Initialiser conn à None
        try:
            conn, addr = s.accept()
            request = conn.recv(1024).decode('utf-8')
            
            print(f"📨 Requête de {addr[0]}")
            
            if "POST /configure" in request:
                # Traitement de la configuration
                lines = request.split('\n')
                data = lines[-1]  # Dernière ligne contient les données POST
                
                params = {}
                for param in data.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        # Décoder les caractères URL
                        key = key.replace('%40', '@').replace('+', ' ')
                        value = value.replace('%40', '@').replace('+', ' ')
                        params[key] = value
                
                if 'ssid' in params and 'password' in params:
                    ssid = params['ssid']
                    password = params['password']
                    
                    print(f"💾 Configuration reçue: {ssid}")
                    
                    # Réponse de succès d'abord
                    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{success_page}"
                    conn.send(response.encode())
                    conn.close()
                    conn = None  # Marquer comme fermé
                    
                    # Sauvegarder la config
                    save_wifi_config(ssid, password)
                    
                    # Arrêter le serveur web et le point d'accès
                    print("🔄 Arrêt du mode configuration...")
                    try:
                        s.close()
                    except:
                        pass
                    
                    # Arrêter le point d'accès
                    ap = network.WLAN(network.AP_IF)
                    ap.active(False)
                    
                    # Attendre un peu
                    time.sleep(2)
                    
                    # Tenter la connexion au nouveau WiFi
                    print("🔌 Connexion au nouveau WiFi...")
                    if connect_wifi(ssid, password):
                        print("✅ Configuration terminée avec succès!")
                        return True  # Succès
                    else:
                        print("❌ Échec de connexion, retour en mode configuration...")
                        # Redémarrer le point d'accès si échec
                        time.sleep(3)
                        start_access_point()
                        return create_captive_portal()  # Récursif
                else:
                    # Paramètres manquants
                    error_response = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n<h1>Erreur: Paramètres manquants</h1>"
                    conn.send(error_response.encode())
                
            else:
                # Page principale
                networks = scan_networks()
                page = html_page.replace('%NETWORKS%', networks)
                
                response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{page}"
                conn.send(response.encode())
            
            if conn:
                conn.close()
                conn = None
            
        except Exception as e:
            print(f"❌ Erreur serveur: {e}")
            if conn:
                try:
                    conn.close()
                except:
                    pass
        
        # Vérifier si on doit sortir de la boucle
        if not ap_mode:
            break
    
    # Fermer le serveur si on arrive ici
    try:
        s.close()
    except:
        pass
    
    return False  # Échec par défaut

# =====================================================
# FONCTIONS CAPTEUR CO2
# =====================================================

def read_co2():
    """Lit la valeur CO2 du capteur MH-Z19C"""
    try:
        while uart.any():
            uart.read()
        
        cmd = bytearray([0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79])
        uart.write(cmd)
        time.sleep(0.2)
        
        if uart.any():
            response = uart.read()
            
            if response and len(response) >= 9:
                if response[0] == 0xFF and response[1] == 0x86:
                    co2_high = response[2]
                    co2_low = response[3] 
                    co2_ppm = co2_high * 256 + co2_low
                    return co2_ppm
        
        return None
            
    except Exception as e:
        print(f"❌ Erreur lecture CO2: {e}")
        return None

def get_air_quality_status(co2_ppm):
    """Retourne le statut de qualité de l'air"""
    if co2_ppm is None:
        return "ERREUR", "❌"
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
# ENVOI DONNÉES SERVEUR
# =====================================================

def send_to_server(co2_ppm, status):
    """Envoie les données au serveur"""
    if not wifi_connected:
        return False
    
    try:
        data = {
            "device_id": "aircarto_001",  # ID unique du dispositif
            "timestamp": time.time(),
            "co2_ppm": co2_ppm,
            "air_quality": status,
            "location": "default"  # À personnaliser
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AirCarto/2.0"
        }
        
        print(f"📡 Envoi au serveur: {co2_ppm} ppm")
        
        # ENVOI RÉEL activé !
        response = urequests.post(SERVER_URL, json=data, headers=headers)
        
        if response.status_code == 200:
            print("✅ Données envoyées!")
            response.close()  # Libérer la mémoire
            return True
        else:
            print(f"❌ Erreur serveur: {response.status_code}")
            response.close()
            return False
        
        # # Simulation désactivée
        # print("✅ Données envoyées! (simulation)")
        # return True
        
    except Exception as e:
        print(f"❌ Erreur envoi: {e}")
        return False

# =====================================================
# FONCTIONS AFFICHAGE
# =====================================================

def display_status(title, subtitle=""):
    """Affiche un statut sur l'écran"""
    if oled:
        oled.fill(0)
        oled.text("AirCarto v2.0", 10, 0)
        oled.hline(0, 10, 128, 1)
        oled.text(title, 10, 20)
        if subtitle:
            oled.text(subtitle, 5, 35)
        oled.show()

def draw_main_display(co2_ppm, status, emoji, wifi_status, server_status):
    """Affiche l'interface principale"""
    if not oled:
        return
        
    oled.fill(0)
    
    # En-tête avec statuts
    oled.text("AirCarto", 35, 0)
    
    # Statuts connexion
    wifi_icon = "📶" if wifi_connected else "❌"
    server_icon = "☁️" if server_status else "📡"
    oled.text(f"{wifi_icon} {server_icon}", 90, 0)
    
    oled.hline(0, 10, 128, 1)
    
    # CO2 principal
    if co2_ppm is not None:
        co2_text = f"{co2_ppm} ppm"
        oled.text(co2_text, 20, 15)
        oled.text(f"Air: {status}", 10, 30)
        
        # Barre de niveau
        bar_width = min(120, int((co2_ppm / 2000) * 120))
        oled.fill_rect(4, 45, bar_width, 8, 1)
        oled.rect(4, 45, 120, 8, 1)
        
    else:
        oled.text("CAPTEUR", 30, 25)
        oled.text("ERREUR", 35, 40)
    
    # Pied de page
    oled.text(f"Up: {time.ticks_ms()//1000}s", 0, 56)
    
    oled.show()

# =====================================================
# PROGRAMME PRINCIPAL
# =====================================================

def main():
    global oled, wifi_connected, ap_mode, mascot
    
    try:
        # Initialiser l'écran OLED
        print("📺 Initialisation écran...")
        from ssd1306 import SSD1306_SPI
        oled = SSD1306_SPI(128, 64, spi, dc_pin, res_pin, cs_pin)
        print("✅ Écran prêt!")
        
        # Initialiser la mascotte
        print("🐱 Initialisation mascotte...")
        try:
            from aircarto_mascot import AirCartoMascot, draw_main_display_with_mascot
            mascot = AirCartoMascot(oled)
            print("✅ Mascotte prête!")
            use_mascot = True
        except ImportError:
            print("⚠️ Mascotte non disponible, mode classique")
            use_mascot = False
        
        display_status("Demarrage...", "AirCarto v2.0")
        time.sleep(2)
        
        # Tentative de connexion WiFi
        print("🔌 Tentative connexion WiFi...")
        wifi_configured = False
        
        if not connect_wifi():
            print("📡 Démarrage mode configuration...")
            ap_mode = True  # S'assurer que ap_mode est défini
            ap = start_access_point()
            wifi_configured = create_captive_portal()
            ap_mode = False  # Réinitialiser après le captive portal
            
            if not wifi_configured:
                print("❌ Configuration WiFi annulée")
                return
        else:
            wifi_configured = True
            # Animation de connexion réussie
            if use_mascot and mascot:
                mascot.animate_reaction("wifi_connect")
        
        # Si on arrive ici, le WiFi est configuré
        if wifi_configured:
            print("✅ WiFi configuré, démarrage du système...")
            display_status("WiFi OK", "Demarrage systeme")
            time.sleep(2)
        
        # Préchauffage capteur
        print("🌡️ Préchauffage capteur...")
        for i in range(6):
            display_status("Prechauffage", f"{(6-i)*5}s restantes")
            time.sleep(5)
        
        print("✅ Système prêt!")
        
        # Boucle principale
        last_server_success = True
        last_co2_level = None
        
        while True:
            print("📊 Nouvelle mesure...")
            
            # Vérifier connexion WiFi
            wlan = network.WLAN(network.STA_IF)
            if not wlan.isconnected():
                print("❌ WiFi déconnecté!")
                wifi_connected = False
                if use_mascot and mascot:
                    mascot.animate_reaction("wifi_error")
                # Tenter reconnexion
                if not connect_wifi():
                    time.sleep(RETRY_INTERVAL)
                    continue
            
            # Lecture CO2
            co2_ppm = read_co2()
            status, emoji = get_air_quality_status(co2_ppm)
            
            # Déclencher animations selon les changements
            if use_mascot and mascot and co2_ppm is not None:
                if last_co2_level is None:
                    last_co2_level = co2_ppm
                elif co2_ppm > 1500 and last_co2_level <= 1500:
                    mascot.animate_reaction("co2_danger")
                last_co2_level = co2_ppm
            
            if co2_ppm is not None:
                print(f"CO2: {co2_ppm} ppm - {status}")
                
                # Envoi au serveur
                server_success = send_to_server(co2_ppm, status)
                last_server_success = server_success
            else:
                print("❌ Erreur lecture CO2")
                last_server_success = False
            
            # Affichage avec ou sans mascotte
            if use_mascot and mascot:
                draw_main_display_with_mascot(oled, mascot, co2_ppm, status, emoji, wifi_connected, last_server_success)
            else:
                draw_main_display(co2_ppm, status, emoji, wifi_connected, last_server_success)
            
            # Attendre prochaine mesure
            time.sleep(MEASUREMENT_INTERVAL)
            
    except ImportError:
        print("❌ Bibliothèque ssd1306 manquante!")
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt utilisateur")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        import sys
        sys.print_exception(e)  # Afficher la stack trace complète

if __name__ == "__main__":
    main() 