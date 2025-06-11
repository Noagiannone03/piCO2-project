"""
My Pico v3.0 - Capteur CO2 avec auto-enregistrement Firebase
Capteur CO2 MH-Z19C + Écran OLED SSD1309 (SPI) + WiFi + Firebase

Configuration automatique:
1. Premier boot → Mode configuration → Point d'accès WiFi
2. Configuration WiFi → Auto-enregistrement Firebase
3. Envoi automatique des mesures toutes les 30 secondes

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

from machine import Pin, SPI, UART, reset, unique_id
import network
import socket
import time
import json
import urequests
import struct
import os
import ubinascii
from aircarto_mascot import AirCartoMascot, draw_main_display_with_mascot

print("🌱 === My Pico v3.0 - Firebase Ready === 🌱")

# =====================================================
# CONFIGURATION
# =====================================================
DEVICE_ID = "picoAZ12"  # ID unique du Pico (à personnaliser par device)
FIREBASE_PROJECT_ID = "my-pico-cf271"
FIREBASE_API_KEY = "AIzaSyAl_i1UGJ1tVTEAkn8xhSbwe_iKk0eYryk"
FIREBASE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"

WEBSITE_URL = "https://noagiannone03.github.io/piCO2-project"
CONFIG_FILE = "pico_config.json"
FIRST_BOOT_FLAG = "first_boot.flag"

AP_SSID = f"My-Pico-{DEVICE_ID}"
AP_PASSWORD = "mypico123"
MEASUREMENT_INTERVAL = 30  # secondes
RETRY_INTERVAL = 5  # secondes entre tentatives

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
mascot = None
device_registered = False
startup_time = time.time()

# =====================================================
# UTILITAIRES SYSTÈME
# =====================================================

def is_first_boot():
    """Vérifie si c'est le premier démarrage"""
    try:
        with open(FIRST_BOOT_FLAG, 'r'):
            return False
    except:
        return True

def mark_boot_complete():
    """Marque le premier boot comme terminé"""
    with open(FIRST_BOOT_FLAG, 'w') as f:
        f.write(str(time.time()))

def load_config():
    """Charge la configuration sauvegardée"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    """Sauvegarde la configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def get_device_info():
    """Récupère les informations du device"""
    mac = ubinascii.hexlify(network.WLAN().config('mac')).decode()
    
    wlan = network.WLAN(network.STA_IF)
    ip = "0.0.0.0"
    rssi = -100
    ssid = ""
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        rssi = wlan.status('rssi')
        ssid = wlan.config('essid')
    
    return {
        "deviceId": DEVICE_ID,
        "macAddress": mac,
        "ipAddress": ip,
        "wifiSSID": ssid,
        "signalStrength": rssi,
        "firmwareVersion": "3.0.0",
        "uptime": int(time.time() - startup_time),
        "freeMemory": None  # À implémenter si nécessaire
    }

# =====================================================
# FIREBASE INTEGRATION
# =====================================================

def firebase_request(method, path, data=None):
    """Effectue une requête vers Firebase"""
    url = f"{FIREBASE_BASE_URL}/{path}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "POST":
            response = urequests.post(url, json=data, headers=headers)
        elif method == "GET":
            response = urequests.get(url, headers=headers)
        elif method == "PATCH":
            response = urequests.patch(url, json=data, headers=headers)
        else:
            return None
        
        if response.status_code in [200, 201]:
            result = response.json()
            response.close()
            return result
        else:
            print(f"❌ Firebase error {response.status_code}: {response.text}")
            response.close()
            return None
            
    except Exception as e:
        print(f"❌ Firebase request error: {e}")
        return None

def get_geolocation():
    """Récupère la géolocalisation via IP"""
    try:
        # Service gratuit de géolocalisation IP
        response = urequests.get("http://ip-api.com/json/")
        if response.status_code == 200:
            data = response.json()
            response.close()
            
            if data.get('status') == 'success':
                return {
                    "lat": data.get('lat'),
                    "lng": data.get('lon'),
                    "address": f"{data.get('city', '')}, {data.get('country', '')}"
                }
        else:
            response.close()
    except Exception as e:
        print(f"❌ Geolocation error: {e}")
    
    # Valeurs par défaut (Marseille)
    return {
        "lat": 43.2965,
        "lng": 5.3698,
        "address": "Marseille, France"
    }

def register_device_firebase():
    """Enregistre le device dans Firebase"""
    global device_registered
    
    print("📝 Enregistrement Firebase...")
    if mascot:
        mascot.draw_config_screen("firebase_register", "Enregistrement", "Firebase...")
    else:
        display_status("Enregistrement", "Firebase...")
    
    device_info = get_device_info()
    location = get_geolocation()
    
    # Données du device
    device_data = {
        "fields": {
            "info": {
                "mapValue": {
                    "fields": {
                        "deviceId": {"stringValue": DEVICE_ID},
                        "name": {"stringValue": f"My Pico {DEVICE_ID}"},
                        "type": {"stringValue": "pico-co2"},
                        "owner": {"nullValue": None},
                        "location": {
                            "mapValue": {
                                "fields": {
                                    "lat": {"doubleValue": location["lat"]},
                                    "lng": {"doubleValue": location["lng"]},
                                    "address": {"stringValue": location["address"]},
                                    "indoor": {"booleanValue": True}
                                }
                            }
                        },
                        "isPublic": {"booleanValue": False},
                        "isRegistered": {"booleanValue": True},
                        "isConfigured": {"booleanValue": False},
                        "registeredAt": {"timestampValue": time_to_iso()},
                        "lastSeen": {"timestampValue": time_to_iso()},
                        "status": {"stringValue": "online"}
                    }
                }
            },
            "settings": {
                "mapValue": {
                    "fields": {
                        "measurementInterval": {"integerValue": str(MEASUREMENT_INTERVAL)},
                        "sharePublicly": {"booleanValue": False},
                        "alertThresholds": {
                            "mapValue": {
                                "fields": {
                                    "warning": {"integerValue": "1000"},
                                    "danger": {"integerValue": "1500"}
                                }
                            }
                        }
                    }
                }
            },
            "network": {
                "mapValue": {
                    "fields": {
                        "macAddress": {"stringValue": device_info["macAddress"]},
                        "ipAddress": {"stringValue": device_info["ipAddress"]},
                        "wifiSSID": {"stringValue": device_info["wifiSSID"]},
                        "signalStrength": {"integerValue": str(device_info["signalStrength"])}
                    }
                }
            },
            "calibration": {
                "mapValue": {
                    "fields": {
                        "lastCalibration": {"nullValue": None},
                        "calibrationOffset": {"integerValue": "0"},
                        "calibrationNote": {"stringValue": ""}
                    }
                }
            }
        }
    }
    
    # Créer le document device
    result = firebase_request("POST", f"devices?documentId={DEVICE_ID}", device_data)
    
    if result:
        print("✅ Device enregistré dans Firebase!")
        device_registered = True
        
        # Sauvegarder l'état d'enregistrement
        config = load_config()
        config['registered'] = True
        config['registered_at'] = time.time()
        save_config(config)
        
        if mascot:
            mascot.draw_config_screen("firebase_success", "Enregistré!", "Device configuré")
            time.sleep(2)
        else:
            display_status("Enregistré!", "Device configuré")
            time.sleep(2)
        
        return True
    else:
        print("❌ Échec enregistrement Firebase")
        if mascot:
            mascot.draw_config_screen("firebase_error", "Erreur Firebase", "Réessayer...")
            time.sleep(2)
        else:
            display_status("Erreur Firebase", "Réessayer...")
            time.sleep(2)
        
        return False

def send_measurement_firebase(co2_ppm, status):
    """Envoie une mesure vers Firebase"""
    if not device_registered:
        return False
    
    device_info = get_device_info()
    
    measurement_data = {
        "fields": {
            "deviceId": {"stringValue": DEVICE_ID},
            "timestamp": {"timestampValue": time_to_iso()},
            "co2_ppm": {"integerValue": str(co2_ppm)},
            "air_quality": {"stringValue": status.lower()},
            "isPublic": {"booleanValue": False},  # Par défaut non public
            "metadata": {
                "mapValue": {
                    "fields": {
                        "firmware_version": {"stringValue": device_info["firmwareVersion"]},
                        "uptime_seconds": {"integerValue": str(device_info["uptime"])},
                        "wifi_rssi": {"integerValue": str(device_info["signalStrength"])}
                    }
                }
            }
        }
    }
    
    # Ajouter dans la sous-collection measurements
    result = firebase_request("POST", f"measurements/{DEVICE_ID}/data", measurement_data)
    
    if result:
        print(f"✅ Mesure envoyée: {co2_ppm} ppm")
        
        # Mettre à jour le lastSeen du device
        update_device_status()
        return True
    else:
        print("❌ Échec envoi mesure")
        return False

def update_device_status():
    """Met à jour le statut du device (lastSeen, status)"""
    update_data = {
        "fields": {
            "info": {
                "mapValue": {
                    "fields": {
                        "lastSeen": {"timestampValue": time_to_iso()},
                        "status": {"stringValue": "online"}
                    }
                }
            }
        }
    }
    
    firebase_request("PATCH", f"devices/{DEVICE_ID}?updateMask.fieldPaths=info.lastSeen&updateMask.fieldPaths=info.status", update_data)

def time_to_iso():
    """Convertit le timestamp actuel en format ISO pour Firebase"""
    t = time.localtime()
    return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"

# =====================================================
# GESTION WIFI & CONFIGURATION
# =====================================================

def connect_wifi(ssid=None, password=None):
    """Tente de se connecter au WiFi"""
    global wifi_connected
    
    # Charger config si pas de paramètres fournis
    if not ssid or not password:
        config = load_config()
        if not config.get('wifi'):
            return False
        ssid = config['wifi']['ssid']
        password = config['wifi']['password']
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    print(f"🔌 Connexion à {ssid}...")
    if mascot:
        mascot.draw_config_screen("wifi_connect", "Connexion WiFi", ssid)
    else:
        display_status("Connexion WiFi", ssid)
    
    wlan.connect(ssid, password)
    
    # Attendre la connexion (max 15s)
    timeout = 15
    while timeout > 0 and not wlan.isconnected():
        time.sleep(1)
        timeout -= 1
        
        if timeout % 3 == 0:  # Mise à jour écran
            if mascot:
                mascot.draw_config_screen("wifi_connect", "Connexion WiFi", f"{ssid} ({timeout}s)")
            else:
                display_status("Connexion WiFi", f"{ssid} ({timeout}s)")
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"✅ WiFi connecté! IP: {ip}")
        wifi_connected = True
        
        # Sauvegarder config WiFi
        config = load_config()
        config['wifi'] = {'ssid': ssid, 'password': password}
        save_config(config)
        
        if mascot:
            mascot.draw_config_screen("wifi_success", "WiFi connecté!", ip)
            time.sleep(2)
        else:
            display_status("WiFi connecté", ip)
            time.sleep(2)
        
        return True
    else:
        print("❌ Connexion WiFi échouée")
        wifi_connected = False
        
        if mascot:
            mascot.draw_config_screen("wifi_fail", "WiFi échoué", "Vérifiez config")
            time.sleep(2)
        else:
            display_status("WiFi échoué", "Vérifiez config")
            time.sleep(2)
        
        return False

def start_configuration_mode():
    """Démarre le mode configuration avec point d'accès"""
    global ap_mode
    
    print("📡 Mode configuration - Premier boot")
    
    # Affichage des instructions de configuration
    if mascot:
        mascot.draw_config_screen("initial_setup", "Configuration", "Première utilisation")
        time.sleep(3)
        mascot.draw_config_screen("connect_instructions", "Connectez-vous à:", WEBSITE_URL)
        time.sleep(5)
    else:
        display_status("Configuration", "Premier boot")
        time.sleep(2)
        display_status("Connectez-vous à:", WEBSITE_URL)
        time.sleep(3)
    
    # Créer point d'accès
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASSWORD)
    
    while not ap.active():
        time.sleep(1)
    
    ip = ap.ifconfig()[0]
    print(f"✅ Point d'accès créé: {AP_SSID}")
    print(f"🔑 Mot de passe: {AP_PASSWORD}")
    print(f"🌐 IP: {ip}")
    
    ap_mode = True
    
    # Afficher les infos de connexion
    if mascot:
        mascot.draw_config_screen("show_ap_info", f"WiFi: {AP_SSID}", f"Page: {ip}")
    else:
        display_status(f"WiFi: {AP_SSID}", f"Page: {ip}")
    
    return ap, ip

def create_config_portal(ap_ip):
    """Crée le portail de configuration WiFi"""
    
    config_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>My Pico {DEVICE_ID} - Configuration</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 400px; margin: 20px auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .container {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); }}
            h1 {{ color: #2d3748; text-align: center; margin-bottom: 25px; }}
            .device-id {{ background: #f7fafc; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 25px; border: 2px solid #e2e8f0; }}
            .device-id strong {{ color: #667eea; font-size: 18px; }}
            input, select {{ width: 100%; padding: 12px; margin: 10px 0; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 14px; }}
            input:focus, select:focus {{ border-color: #667eea; outline: none; }}
            button {{ width: 100%; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }}
            button:hover {{ transform: translateY(-2px); }}
            .instructions {{ background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .step {{ margin: 8px 0; display: flex; align-items: center; }}
            .step-num {{ background: #667eea; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; margin-right: 10px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌱 My Pico Configuration</h1>
            
            <div class="device-id">
                <strong>Device ID: {DEVICE_ID}</strong><br>
                <small>Notez cet ID pour l'ajout sur {WEBSITE_URL}</small>
            </div>
            
            <div class="instructions">
                <strong>📋 Instructions:</strong>
                <div class="step"><span class="step-num">1</span>Configurez le WiFi ci-dessous</div>
                <div class="step"><span class="step-num">2</span>Allez sur {WEBSITE_URL}</div>
                <div class="step"><span class="step-num">3</span>Ajoutez le device avec l'ID: {DEVICE_ID}</div>
            </div>
            
            <form action="/configure" method="POST">
                <label>🔌 Réseau WiFi:</label>
                <select name="ssid" required>
                    <option value="">-- Sélectionnez --</option>
                    %NETWORKS%
                </select>
                
                <label>🔑 Mot de passe:</label>
                <input type="password" name="password" placeholder="Mot de passe WiFi" required>
                
                <button type="submit">🚀 Configurer et démarrer</button>
            </form>
        </div>
        
        <script>
            setTimeout(() => location.reload(), 20000); // Auto-refresh
        </script>
    </body>
    </html>
    """
    
    success_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Configuration réussie!</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; background: #f0f8ff; text-align: center; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #4CAF50; }}
            .success {{ font-size: 64px; margin: 20px 0; }}
            .redirect {{ background: #e8f4fd; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✅</div>
            <h1>Configuration réussie!</h1>
            <p><strong>My Pico {DEVICE_ID} se connecte maintenant...</strong></p>
            
            <div class="redirect">
                <p>🌐 <strong>Étape suivante:</strong></p>
                <p>Allez sur <a href="{WEBSITE_URL}/config/{DEVICE_ID}" target="_blank">{WEBSITE_URL}</a></p>
                <p>pour ajouter votre Pico à votre compte</p>
            </div>
            
            <p><em>Vous pouvez fermer cette page.</em></p>
        </div>
        
        <script>
            // Redirection automatique après 8 secondes
            setTimeout(() => {{
                window.location.href = "{WEBSITE_URL}/config/{DEVICE_ID}";
            }}, 8000);
        </script>
    </body>
    </html>
    """
    
    def scan_networks():
        try:
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            networks = wlan.scan()
            
            options = ""
            seen = set()
            
            for net in networks:
                ssid = net[0].decode('utf-8')
                if ssid and ssid not in seen:
                    signal = net[3]
                    security = "🔒" if net[4] > 0 else "🔓"
                    options += f'<option value="{ssid}">{security} {ssid} ({signal}dBm)</option>\n'
                    seen.add(ssid)
            
            return options
        except:
            return '<option value="">Erreur scan</option>'
    
    # Serveur web
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 80))
    s.listen(5)
    
    print(f"🌐 Serveur config: http://{ap_ip}")
    
    while ap_mode:
        conn = None
        try:
            conn, addr = s.accept()
            request = conn.recv(1024).decode('utf-8')
            
            if "POST /configure" in request:
                # Traitement configuration
                data_line = request.split('\n')[-1]
                params = {}
                
                for param in data_line.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        key = key.replace('%40', '@').replace('+', ' ')
                        value = value.replace('%40', '@').replace('+', ' ').replace('%21', '!')
                        params[key] = value
                
                if 'ssid' in params and 'password' in params:
                    ssid = params['ssid']
                    password = params['password']
                    
                    print(f"💾 Configuration reçue: {ssid}")
                    
                    # Réponse de succès
                    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{success_page}"
                    conn.send(response.encode())
                    conn.close()
                    conn = None
                    
                    # Fermer serveur et AP
                    try:
                        s.close()
                    except:
                        pass
                    
                    # Sauvegarder config et tenter connexion
                    config = load_config()
                    config['wifi'] = {'ssid': ssid, 'password': password}
                    save_config(config)
                    
                    ap = network.WLAN(network.AP_IF)
                    ap.active(False)
                    ap_mode = False
                    
                    time.sleep(2)
                    
                    # Tenter la connexion
                    if connect_wifi(ssid, password):
                        return True
                    else:
                        return False
                
            else:
                # Page principale
                networks = scan_networks()
                page = config_page.replace('%NETWORKS%', networks)
                
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
        
        if not ap_mode:
            break
    
    try:
        s.close()
    except:
        pass
    
    return False

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
# FONCTIONS AFFICHAGE
# =====================================================

def display_status(title, subtitle=""):
    """Affiche un statut sur l'écran"""
    if oled:
        oled.fill(0)
        oled.text("My Pico v3.0", 5, 0)
        oled.hline(0, 10, 128, 1)
        oled.text(title, 5, 20)
        if subtitle:
            oled.text(subtitle, 5, 35)
        oled.show()

def draw_main_display(co2_ppm, status, emoji, wifi_status, firebase_status):
    """Affiche l'interface principale"""
    if not oled:
        return
        
    oled.fill(0)
    
    # En-tête avec statuts
    oled.text("My Pico", 30, 0)
    
    # Statuts connexion
    wifi_icon = "📶" if wifi_connected else "❌"
    firebase_icon = "☁️" if firebase_status else "📡"
    oled.text(f"{wifi_icon}{firebase_icon}", 85, 0)
    
    oled.hline(0, 10, 128, 1)
    
    # CO2 principal
    if co2_ppm is not None:
        co2_text = f"{co2_ppm} ppm"
        oled.text(co2_text, 15, 20)
        oled.text(f"Air: {status}", 5, 35)
        
        # Barre de niveau
        bar_width = min(120, int((co2_ppm / 2000) * 120))
        oled.fill_rect(4, 45, bar_width, 8, 1)
        oled.rect(4, 45, 120, 8, 1)
        
    else:
        oled.text("CAPTEUR", 25, 25)
        oled.text("ERREUR", 30, 40)
    
    # Device ID en bas
    oled.text(f"ID: {DEVICE_ID}", 0, 56)
    
    oled.show()

# =====================================================
# PROGRAMME PRINCIPAL
# =====================================================

def main():
    global oled, wifi_connected, ap_mode, mascot, device_registered
    
    try:
        # Initialiser l'écran OLED
        print("📺 Initialisation écran...")
        from ssd1306 import SSD1306_SPI
        oled = SSD1306_SPI(128, 64, spi, dc_pin, res_pin, cs_pin)
        print("✅ Écran OK!")
        
        # Initialiser la mascotte
        try:
            mascot = AirCartoMascot(oled)
            print("✅ Mascotte OK!")
            use_mascot = True
            
            # Animation de démarrage
            frame = 0
            while mascot.draw_startup_animation(frame):
                frame += 1
                time.sleep(0.1)
                
        except ImportError:
            print("⚠️ Mascotte indisponible")
            use_mascot = False
            display_status("Démarrage...", f"My Pico {DEVICE_ID}")
            time.sleep(2)
        
        # Vérifier si premier boot
        first_boot = is_first_boot()
        config = load_config()
        
        print(f"🔍 Premier boot: {first_boot}")
        print(f"📁 Config existante: {bool(config.get('wifi'))}")
        
        if first_boot or not config.get('wifi'):
            print("🆕 Configuration initiale requise")
            
            # Mode configuration
            ap, ip = start_configuration_mode()
            wifi_configured = create_config_portal(ip)
            
            if not wifi_configured:
                print("❌ Configuration annulée")
                return
                
            # Marquer comme configuré
            mark_boot_complete()
            
        else:
            print("🔌 Tentative connexion WiFi existant...")
            if not connect_wifi():
                print("❌ Échec connexion, mode reconfig")
                ap, ip = start_configuration_mode()
                wifi_configured = create_config_portal(ip)
                
                if not wifi_configured:
                    return
        
        # Vérifier si device déjà enregistré
        if not config.get('registered'):
            print("📝 Première connexion - Enregistrement Firebase")
            if not register_device_firebase():
                print("❌ Échec enregistrement Firebase")
                return
        else:
            device_registered = True
            print("✅ Device déjà enregistré")
        
        # Préchauffage capteur
        print("🌡️ Préchauffage capteur...")
        if use_mascot and mascot:
            # Animation de préchauffage
            frame = 0
            while mascot.draw_sleeping_animation(frame):
                frame += 1
                time.sleep(0.25)
            mascot.draw_waking_animation()
        else:
            for i in range(6):
                display_status("Préchauffage", f"{(6-i)*5}s")
                time.sleep(5)
        
        print("✅ Système prêt pour les mesures!")
        
        # Boucle principale des mesures
        last_firebase_success = True
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
            
            # Animations selon les changements
            if use_mascot and mascot and co2_ppm is not None:
                if last_co2_level is None:
                    last_co2_level = co2_ppm
                elif co2_ppm > 1500 and last_co2_level <= 1500:
                    mascot.animate_reaction("co2_danger")
                last_co2_level = co2_ppm
            
            if co2_ppm is not None:
                print(f"CO2: {co2_ppm} ppm - {status}")
                
                # Envoi Firebase
                firebase_success = send_measurement_firebase(co2_ppm, status)
                last_firebase_success = firebase_success
            else:
                print("❌ Erreur lecture CO2")
                last_firebase_success = False
            
            # Affichage
            if use_mascot and mascot:
                draw_main_display_with_mascot(oled, mascot, co2_ppm, status, emoji, wifi_connected, last_firebase_success)
            else:
                draw_main_display(co2_ppm, status, emoji, wifi_connected, last_firebase_success)
            
            # Attendre prochaine mesure
            time.sleep(MEASUREMENT_INTERVAL)
            
    except ImportError as e:
        print(f"❌ Librairie manquante: {e}")
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt utilisateur")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        import sys
        sys.print_exception(e)

if __name__ == "__main__":
    main() 