"""
Debug MH-Z19C - Diagnostic du capteur CO2
Ce script teste la communication avec le capteur MH-Z19C
"""

from machine import Pin, UART
import time

print("🔧 === Diagnostic MH-Z19C === 🔧")

# Configuration UART
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
print(f"UART configuré: {uart}")

def hex_dump(data):
    """Affiche les données en hexadécimal"""
    if data:
        return " ".join([f"{b:02X}" for b in data])
    return "Aucune donnée"

def test_uart_basic():
    """Test basique de l'UART"""
    print("\n1️⃣ Test UART de base...")
    
    # Vider le buffer
    while uart.any():
        uart.read()
    
    # Envoyer une commande simple
    test_cmd = bytearray([0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79])
    print(f"Envoi: {hex_dump(test_cmd)}")
    
    uart.write(test_cmd)
    
    # Attendre et lire la réponse
    time.sleep(0.2)  # Délai plus long
    
    if uart.any():
        response = uart.read()
        print(f"Reçu: {hex_dump(response)}")
        print(f"Longueur: {len(response)} bytes")
        return response
    else:
        print("❌ Aucune réponse du capteur")
        return None

def test_different_baudrates():
    """Teste différents baudrates"""
    print("\n2️⃣ Test différents baudrates...")
    
    baudrates = [9600, 4800, 19200, 38400]
    
    for baudrate in baudrates:
        print(f"\nTest baudrate {baudrate}...")
        uart.init(baudrate=baudrate, tx=Pin(8), rx=Pin(9))
        
        # Vider le buffer
        while uart.any():
            uart.read()
        
        # Commande lecture CO2
        cmd = bytearray([0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79])
        uart.write(cmd)
        time.sleep(0.2)
        
        if uart.any():
            response = uart.read()
            print(f"✅ Réponse à {baudrate}: {hex_dump(response)}")
            if len(response) >= 9 and response[0] == 0xFF:
                print(f"🎯 Baudrate {baudrate} semble fonctionner!")
                return baudrate
        else:
            print(f"❌ Pas de réponse à {baudrate}")
    
    return None

def test_wiring_check():
    """Suggestions de vérification du câblage"""
    print("\n3️⃣ Vérification câblage...")
    print("Connexions actuelles:")
    print("Pin 11 (GPIO 8) → RX capteur")
    print("Pin 12 (GPIO 9) → TX capteur") 
    print("Pin 39 (VSYS) → VCC capteur")
    print("Pin 33 (GND) → GND capteur")
    print("\n⚠️ Vérifications importantes:")
    print("1. TX Pico → RX Capteur")
    print("2. RX Pico → TX Capteur") 
    print("3. Alimentation 5V (VSYS) pas 3.3V")
    print("4. GND commun")

def test_alternative_commands():
    """Teste d'autres commandes MH-Z19C"""
    print("\n4️⃣ Test commandes alternatives...")
    
    # Remettre baudrate standard
    uart.init(baudrate=9600, tx=Pin(8), rx=Pin(9))
    
    commands = {
        "Read CO2 (standard)": [0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79],
        "Read CO2 (alt)": [0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79],
        "Get status": [0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79],
    }
    
    for cmd_name, cmd_bytes in commands.items():
        print(f"\nTest: {cmd_name}")
        
        # Vider buffer
        while uart.any():
            uart.read()
        
        cmd = bytearray(cmd_bytes)
        uart.write(cmd)
        time.sleep(0.3)  # Délai plus long
        
        if uart.any():
            response = uart.read()
            print(f"Réponse: {hex_dump(response)}")
            
            # Analyser la réponse
            if len(response) >= 9:
                if response[0] == 0xFF and response[1] == 0x86:
                    co2 = response[2] * 256 + response[3]
                    print(f"🎯 CO2 détecté: {co2} ppm")
                else:
                    print(f"Format inattendu: header = {response[0]:02X} {response[1]:02X}")
            else:
                print(f"Réponse trop courte: {len(response)} bytes")
        else:
            print("Pas de réponse")

def main():
    print("Démarrage diagnostic MH-Z19C...")
    print("Le capteur doit être alimenté et avoir préchauffé pendant 3 minutes minimum")
    
    # Test 1: Communication de base
    response = test_uart_basic()
    
    if response is None:
        print("\n❌ Aucune communication détectée")
        test_wiring_check()
        test_different_baudrates()
    else:
        print("\n✅ Communication détectée!")
        
        # Analyser la réponse
        if len(response) >= 9:
            print(f"Header: {response[0]:02X} {response[1]:02X}")
            if response[0] == 0xFF and response[1] == 0x86:
                co2 = response[2] * 256 + response[3]
                print(f"🎯 CO2: {co2} ppm")
                print("✅ Capteur fonctionne correctement!")
            else:
                print("❌ Format de réponse incorrect")
                test_alternative_commands()
        else:
            print("❌ Réponse trop courte")
            test_alternative_commands()

if __name__ == "__main__":
    main() 