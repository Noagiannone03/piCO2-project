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
import ntptime
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

def firebase_request(method, path, data=None, max_retries=3):
    """Effectue une requête vers Firebase avec retry automatique"""
    url = f"{FIREBASE_BASE_URL}/{path}"
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(max_retries):
        try:
            # Petit délai entre les tentatives
            if attempt > 0:
                print(f"🔄 Tentative {attempt + 1}/{max_retries}")
                time.sleep(min(2 ** attempt, 10))  # Backoff exponentiel
            
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
                print(f"❌ Firebase HTTP {response.status_code}: {response.text}")
                response.close()
                if attempt == max_retries - 1:
                    return None
                continue
                
        except OSError as e:
            # Erreurs réseau spécifiques
            error_msg = str(e)
            if "104" in error_msg or "ECONNRESET" in error_msg:
                print(f"🌐 Connexion réinitialisée (tentative {attempt + 1})")
            elif "29312" in error_msg or "SSL_CONN_EOF" in error_msg:
                print(f"🔒 Erreur SSL (tentative {attempt + 1})")
            else:
                print(f"❌ Erreur réseau: {e} (tentative {attempt + 1})")
            
            if attempt == max_retries - 1:
                print(f"❌ Échec après {max_retries} tentatives")
                return None
                
        except Exception as e:
            print(f"❌ Erreur Firebase: {e} (tentative {attempt + 1})")
            if attempt == max_retries - 1:
                return None
    
    return None

def get_geolocation():
    """Récupère la géolocalisation via IP avec fallback"""
    # Essayer plusieurs services de géolocalisation
    services = [
        "http://ip-api.com/json/",
        "http://ipinfo.io/json",
        "http://httpbin.org/ip"  # Service de test simple
    ]
    
    for service_url in services:
        try:
            print(f"🌍 Test géolocalisation: {service_url}")
            response = urequests.get(service_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                response.close()
                print(f"✅ Service géolocalisation OK: {service_url}")
                
                # Traitement selon le service
                if "ip-api.com" in service_url and data.get('status') == 'success':
                    return {
                        "lat": data.get('lat', 43.2965),
                        "lng": data.get('lon', 5.3698),
                        "address": f"{data.get('city', 'Marseille')}, {data.get('country', 'France')}"
                    }
                elif "ipinfo.io" in service_url:
                    loc = data.get('loc', '43.2965,5.3698').split(',')
                    return {
                        "lat": float(loc[0]),
                        "lng": float(loc[1]),
                        "address": f"{data.get('city', 'Marseille')}, {data.get('country', 'France')}"
                    }
                else:
                    # Service de test réussi, utiliser valeurs par défaut
                    print("✅ Connectivité Internet OK")
                    break
            else:
                response.close()
                print(f"❌ Service {service_url}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur service {service_url}: {e}")
            continue
    
    # Valeurs par défaut (Marseille)
    print("🏠 Utilisation géolocalisation par défaut: Marseille")
    return {
        "lat": 43.2965,
        "lng": 5.3698,
        "address": "Marseille, France"
    }

def diagnose_network():
    """Diagnostic réseau complet"""
    try:
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            print("❌ WiFi non connecté")
            return False
        
        config = wlan.ifconfig()
        ip, subnet, gateway, dns = config
        
        print("🔍 === DIAGNOSTIC RÉSEAU ===")
        print(f"📱 IP Pico: {ip}")
        print(f"🌐 Masque: {subnet}")
        print(f"🚪 Passerelle: {gateway}")
        print(f"🔍 DNS: {dns}")
        print(f"📶 RSSI: {wlan.status('rssi')} dBm")
        print(f"📡 SSID: {wlan.config('essid')}")
        
        # Test ping passerelle (simulation)
        print(f"🏓 Test passerelle {gateway}...")
        try:
            import socket
            s = socket.socket()
            s.settimeout(5)
            result = s.connect_ex((gateway, 80))
            s.close()
            
            if result == 0:
                print("✅ Passerelle accessible")
                return True
            else:
                print(f"❌ Passerelle inaccessible (code: {result})")
                return False
                
        except Exception as e:
            print(f"❌ Test passerelle échoué: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur diagnostic: {e}")
        return False

def configure_dns():
    """Configure des DNS publics si nécessaire"""
    try:
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            current_config = wlan.ifconfig()
            ip, subnet, gateway, dns = current_config
            
            # Essayer différents DNS
            dns_servers = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]  # Google, Cloudflare, OpenDNS
            
            for new_dns in dns_servers:
                if new_dns != dns:  # Seulement si différent
                    print(f"🔧 Test DNS: {dns} → {new_dns}")
                    
                    try:
                        # Reconfigurer avec nouveau DNS
                        wlan.ifconfig((ip, subnet, gateway, new_dns))
                        time.sleep(3)
                        
                        # Test rapide
                        test_response = urequests.get("http://8.8.8.8", timeout=10)
                        if test_response.status_code == 200:
                            test_response.close()
                            print(f"✅ DNS {new_dns} fonctionne!")
                            return True
                        test_response.close()
                        
                    except Exception as e:
                        print(f"❌ DNS {new_dns} échoué: {e}")
                        continue
            
            print("❌ Aucun DNS ne fonctionne")
            return False
            
    except Exception as e:
        print(f"❌ Erreur configuration DNS: {e}")
    
    return False

def register_device_firebase():
    """Enregistre le device dans Firebase avec retry intelligent"""
    global device_registered
    
    print("📝 Enregistrement Firebase...")
    if mascot:
        mascot.draw_config_screen("firebase_register", "Enregistrement", "Firebase...")
    else:
        display_status("Enregistrement", "Firebase...")
    
    # Test de connectivité avant Firebase
    if not test_internet_connectivity():
        print("❌ Pas de connectivité Internet pour Firebase")
        
        # Essayer de reconfigurer les DNS
        print("🔧 Tentative reconfiguration DNS...")
        if configure_dns():
            print("🔄 Nouveau test après DNS...")
            time.sleep(3)
            if not test_internet_connectivity():
                print("❌ Toujours pas de connectivité après DNS")
                return False
        else:
            return False
    
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
        print("❌ Device non enregistré, impossible d'envoyer vers Firebase")
        return False
    
    # Vérifier la connectivité WiFi
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("❌ WiFi déconnecté, impossible d'envoyer")
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

def sync_time():
    """Synchronise l'heure avec NTP"""
    ntp_servers = ['pool.ntp.org', 'fr.pool.ntp.org', 'europe.pool.ntp.org']
    
    for server in ntp_servers:
        try:
            print(f"🕐 Synchronisation NTP avec {server}...")
            ntptime.host = server
            ntptime.settime()
            print(f"✅ Heure synchronisée avec {server}!")
            
            # Vérifier que la synchronisation a fonctionné
            t = time.localtime()
            if t[0] > 2020:  # Année cohérente
                return True
            else:
                print(f"⚠️ Date suspecte après sync: {t[0]}")
                continue
                
        except Exception as e:
            print(f"❌ Erreur NTP {server}: {e}")
            continue
    
    print("❌ Échec synchronisation NTP sur tous les serveurs")
    return False

def get_current_timestamp():
    """Obtient un timestamp correct même sans RTC"""
    # Calculer un timestamp approximatif basé sur l'uptime
    # En supposant que l'appareil a démarré récemment
    
    # Timestamp approximatif pour août 2025
    base_timestamp = 1756339200  # 28 août 2025 00:00:00 UTC
    
    # Ajouter l'uptime depuis le démarrage
    uptime_seconds = int(time.time() - startup_time)
    current_timestamp = base_timestamp + uptime_seconds
    
    return current_timestamp

def time_to_iso():
    """Convertit le timestamp actuel en format ISO pour Firebase"""
    try:
        # Essayer d'abord la synchronisation NTP
        t = time.localtime()
        
        # Si l'année est correcte (>= 2024), utiliser l'heure système
        if t[0] >= 2024:
            print(f"✅ Utilisation heure système: {t[2]:02d}/{t[1]:02d}/{t[0]} {t[3]:02d}:{t[4]:02d}")
            return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
        
        # Sinon, utiliser notre timestamp calculé
        print("⚠️ Heure système incorrecte, utilisation timestamp calculé")
        calculated_timestamp = get_current_timestamp()
        t = time.localtime(calculated_timestamp)
        
        print(f"🕐 Timestamp calculé: {t[2]:02d}/{t[1]:02d}/{t[0]} {t[3]:02d}:{t[4]:02d}")
        return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
        
    except Exception as e:
        print(f"❌ Erreur timestamp: {e}")
        # Fallback sur timestamp calculé
        calculated_timestamp = get_current_timestamp()
        t = time.localtime(calculated_timestamp) 
        return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"

# =====================================================
# GESTION WIFI & CONFIGURATION
# =====================================================

def test_internet_connectivity():
    """Test la connectivité Internet avec méthodes optimisées"""
    # Tests par ordre de fiabilité (IP directes d'abord)
    test_configs = [
        # Tests IP directes (plus rapides, pas de DNS)
        {"url": "http://1.1.1.1", "desc": "Cloudflare DNS", "timeout": 8},
        {"url": "http://8.8.8.8", "desc": "Google DNS", "timeout": 8},
        {"url": "http://208.67.222.222", "desc": "OpenDNS", "timeout": 8},
        # Tests avec noms de domaine (si IP directes échouent)
        {"url": "http://httpbin.org/ip", "desc": "Service test HTTP", "timeout": 12},
        {"url": "http://example.com", "desc": "Example.com", "timeout": 12}
    ]
    
    for test in test_configs:
        try:
            print(f"🌐 Test {test['desc']}: {test['url']}")
            response = urequests.get(test['url'], timeout=test['timeout'])
            
            if response.status_code == 200:
                response.close()
                print(f"✅ Internet OK via {test['desc']}")
                
                # Si c'est un test IP directe qui réussit, on s'arrête là
                if test['url'].startswith('http://1.1.1.1') or test['url'].startswith('http://8.8.8.8') or test['url'].startswith('http://208.67.222.222'):
                    print(f"🚀 Connectivité confirmée, arrêt des tests")
                
                return True
            else:
                print(f"⚠️ HTTP {response.status_code} pour {test['desc']}")
                response.close()
                
        except OSError as e:
            error_code = str(e)
            if "-2" in error_code:
                print(f"❌ DNS/Résolution: {test['desc']} (erreur -2)")
            elif "110" in error_code or "ETIMEDOUT" in error_code:
                print(f"❌ Timeout: {test['desc']} (pas de réponse)")
            elif "113" in error_code or "EHOSTUNREACH" in error_code:
                print(f"❌ Host inaccessible: {test['desc']}")
            else:
                print(f"❌ Erreur réseau {test['desc']}: {e}")
        except Exception as e:
            print(f"❌ Erreur {test['desc']}: {e}")
    
    print("❌ Aucune connectivité Internet détectée")
    return False

def connect_wifi(ssid=None, password=None):
    """Tente de se connecter au WiFi avec test de connectivité"""
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
        gateway = wlan.ifconfig()[2]
        dns = wlan.ifconfig()[3]
        
        print(f"✅ WiFi connecté! IP: {ip}")
        print(f"🌐 Passerelle: {gateway}, DNS: {dns}")
        
        # Test de connectivité Internet
        print("🔍 Test de connectivité Internet...")
        if mascot:
            mascot.draw_internet_test_screen()
        else:
            display_status("Test Internet", "Vérification...")
        
        internet_ok = test_internet_connectivity()
        
        if internet_ok:
            wifi_connected = True
            
            # Synchroniser l'heure via NTP après connexion Internet réussie
            print("🕐 Synchronisation de l'heure...")
            if mascot:
                mascot.draw_config_screen("ntp_sync", "Synchronisation", "Heure NTP...")
            else:
                display_status("Synchronisation", "Heure NTP...")
            
            ntp_success = sync_time()
            if ntp_success:
                current_time = time.localtime()
                print(f"✅ Heure synchronisée: {current_time[2]:02d}/{current_time[1]:02d}/{current_time[0]} {current_time[3]:02d}:{current_time[4]:02d}")
            else:
                print("⚠️ Synchronisation NTP échouée, utilisation heure locale")
            
            # Sauvegarder config WiFi
            config = load_config()
            config['wifi'] = {'ssid': ssid, 'password': password}
            save_config(config)
            
            if mascot:
                mascot.draw_config_screen("wifi_success", "WiFi + Internet OK!")
                time.sleep(2)
            else:
                display_status("WiFi + Internet OK", "Connecte")
                time.sleep(2)
            
            return True
        else:
            print("⚠️ WiFi connecté mais pas d'Internet")
            wifi_connected = False
            
            if mascot:
                mascot.draw_config_screen("internet_fail", "WiFi OK", "Pas d'Internet")
                time.sleep(3)
            else:
                display_status("WiFi OK", "Pas d'Internet")
                time.sleep(3)
            
            return False
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
    
    # Affichage simple de la configuration
    if mascot:
        mascot.draw_config_screen("initial_setup", "Configuration", "Première utilisation")
        time.sleep(5)
    else:
        display_status("Configuration", "Premier boot")
        time.sleep(5)
    
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

    # Garder l'écran de configuration simple
    # (pas d'affichage d'IP ou autres infos parasites)
    
    return ap, ip

def create_config_portal(ap_ip):
    """Crée le portail de configuration WiFi"""
    global ap_mode
    
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
            body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 450px; margin: 50px auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .container {{ background: white; padding: 40px 30px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.15); text-align: center; }}
            h1 {{ color: #34C759; margin-bottom: 1rem; font-size: 1.8rem; }}
            .success {{ font-size: 4rem; margin: 20px 0; animation: bounce 2s infinite; }}
            .redirect {{ background: #f0f8ff; padding: 20px; border-radius: 12px; margin: 25px 0; border: 2px solid #e2e8f0; }}
            .countdown {{ font-size: 2rem; font-weight: bold; color: #667eea; margin: 15px 0; }}
            .progress-bar {{ background: #e2e8f0; height: 6px; border-radius: 3px; margin: 20px 0; overflow: hidden; }}
            .progress-fill {{ background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; border-radius: 3px; animation: progressFill 5s linear; }}
            @keyframes bounce {{ 0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }} 40% {{ transform: translateY(-10px); }} 60% {{ transform: translateY(-5px); }} }}
            @keyframes progressFill {{ from {{ width: 0%; }} to {{ width: 100%; }} }}
            .device-id {{ background: #667eea; color: white; padding: 12px 20px; border-radius: 8px; font-weight: bold; letter-spacing: 1px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">🎉</div>
            <h1>Configuration WiFi réussie!</h1>
            
            <div class="device-id">Device ID: {DEVICE_ID}</div>
            
            <p><strong>Votre Pico se connecte maintenant à Internet...</strong></p>
            
            <div class="progress-bar">
                <div class="progress-fill"></div>
        </div>
            
            <div class="countdown" id="countdown">5</div>
            
            <div class="redirect">
                <p>🌐 <strong>Redirection automatique vers:</strong></p>
                <p><a href="{WEBSITE_URL}/config.html?id={DEVICE_ID}" target="_blank">{WEBSITE_URL}/config.html</a></p>
                <p style="font-size: 0.9rem; color: #666; margin-top: 10px;">
                    Page de finalisation de la configuration
                </p>
            </div>
            
            <p style="font-size: 0.9rem; color: #888;"><em>Redirection dans quelques secondes...</em></p>
        </div>
        
        <script>
            let countdown = 5;
            const countdownElement = document.getElementById('countdown');
            
            const timer = setInterval(() => {{
                countdown--;
                countdownElement.textContent = countdown;
                
                if (countdown <= 0) {{
                    clearInterval(timer);
                    countdownElement.textContent = "Redirection...";
                    window.location.href = "{WEBSITE_URL}/config.html?id={DEVICE_ID}";
                }}
            }}, 1000);
            
            // Redirection de secours après 6 secondes
            setTimeout(() => {{
                window.location.href = "{WEBSITE_URL}/config.html?id={DEVICE_ID}";
            }}, 6000);
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
                    
                    # Fermer connexion proprement
                    try:
                        conn.close()
                    except:
                        pass
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
            
            # Fermer connexion dans tous les cas
            try:
                if conn:
                    conn.close()
            except:
                pass
            
        except Exception as e:
            print(f"❌ Erreur serveur: {e}")
            # Fermer connexion en cas d'erreur
            try:
                if conn:
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
    
    # Gestion des statuts Firebase
    if firebase_status:
        firebase_icon = "☁️"  # Cloud pour Firebase OK
    else:
        firebase_icon = "❌"  # Erreur Firebase
        
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
                
                # Diagnostic réseau avant de passer en mode config
                print("🔍 Diagnostic réseau complet...")
                wlan = network.WLAN(network.STA_IF)
                
                if wlan.isconnected():
                    print("⚠️ WiFi connecté mais problème Internet")
                    
                    # Diagnostic complet
                    gateway_ok = diagnose_network()
                    
                    if gateway_ok:
                        print("🔧 Passerelle OK, problème DNS/Internet")
                        
                        # Essayer de réparer DNS
                        if configure_dns():
                            print("🔄 Test après réparation DNS...")
                            time.sleep(5)
                            
                            if test_internet_connectivity():
                                print("✅ Connectivité restaurée via DNS!")
                            else:
                                print("❌ DNS réparé mais toujours pas d'Internet")
                                print("🔄 Tentative reconnexion complète...")
                                
                                # Forcer reconnexion WiFi
                                config = load_config()
                                if config.get('wifi'):
                                    wlan.disconnect()
                                    time.sleep(2)
                                    wlan.active(False)
                                    time.sleep(2)
                                    wlan.active(True)
                                    time.sleep(2)
                                    
                                    if connect_wifi():
                                        print("✅ Reconnexion WiFi réussie!")
                                    else:
                                        print("❌ Échec reconnexion, mode config")
                                        ap, ip = start_configuration_mode()
                                        wifi_configured = create_config_portal(ip)
                                if not wifi_configured:
                                    return
                    else:
                        print("❌ Problème passerelle/routeur")
                        print("🔄 Reconnexion WiFi nécessaire...")
                        
                        # Forcer reconnexion
                        config = load_config()
                        if config.get('wifi'):
                            wlan.disconnect()
                            time.sleep(3)
                            
                            if connect_wifi():
                                print("✅ Reconnexion réussie!")
                            else:
                                print("❌ Reconnexion échouée, mode config")
                                ap, ip = start_configuration_mode()
                                wifi_configured = create_config_portal(ip)
                                if not wifi_configured:
                                    return
                else:
                    print("❌ WiFi non connecté, mode reconfig")
                    ap, ip = start_configuration_mode()
                    wifi_configured = create_config_portal(ip)
                    
                    if not wifi_configured:
                        return
        
        # Vérifier si device déjà enregistré
        if not config.get('registered'):
            print("📝 Première connexion - Enregistrement Firebase")
            
            # Essayer l'enregistrement Firebase avec retry
            firebase_attempts = 0
            max_firebase_attempts = 3
            
            while firebase_attempts < max_firebase_attempts:
                firebase_attempts += 1
                print(f"🔄 Tentative Firebase {firebase_attempts}/{max_firebase_attempts}")
                
                if register_device_firebase():
                    break
                elif firebase_attempts < max_firebase_attempts:
                    print(f"⏳ Attente avant nouvelle tentative...")
                    time.sleep(10)
                else:
                    print("❌ ÉCHEC CRITIQUE: Impossible d'enregistrer sur Firebase!")
                    print("🚨 Le capteur ne peut pas fonctionner sans Firebase")
                    print("🔄 Redémarrage nécessaire pour réessayer...")
                    
                    if mascot:
                        mascot.draw_config_screen("firebase_critical", "ERREUR Firebase", "Redémarrage requis")
                        time.sleep(5)
                    else:
                        display_status("ERREUR Firebase", "Redémarrage requis")
                        time.sleep(5)
                    
                    # Redémarrer le système
                    import machine
                    machine.reset()
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
                
                # Tenter reconnexion automatique
                print("🔄 Tentative de reconnexion WiFi...")
                for retry in range(3):
                    if connect_wifi():
                        print("✅ Reconnexion WiFi réussie!")
                        break
                    else:
                        print(f"❌ Échec reconnexion {retry + 1}/3")
                        time.sleep(5)
                
                if not wlan.isconnected():
                    print("❌ Impossible de se reconnecter, attente...")
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
                print(f"🔍 Debug: device_registered = {device_registered}")
                
                # Envoi Firebase obligatoire
                firebase_success = send_measurement_firebase(co2_ppm, status)
                last_firebase_success = firebase_success
                
                if not firebase_success:
                    print("❌ ERREUR: Impossible d'envoyer vers Firebase!")
                    print("🔄 Tentative de ré-enregistrement...")
                    if register_device_firebase():
                        print("✅ Ré-enregistrement réussi, retry envoi...")
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
            
            # Petit délai supplémentaire pour éviter la surcharge réseau
            time.sleep(1)
            
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