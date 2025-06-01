#!/usr/bin/env python3
"""
Script de test pour AirCarto Server
Génère des données de test et vérifie le bon fonctionnement
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
SERVER_URL = "http://localhost:5000"
API_ENDPOINT = f"{SERVER_URL}/api/co2"

def test_server_health():
    """Test la santé du serveur"""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Serveur en ligne!")
            return True
        else:
            print(f"❌ Serveur répond avec code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur connexion serveur: {e}")
        return False

def generate_test_data(device_id="aircarto_test", location="test_lab"):
    """Génère des données de test réalistes"""
    # Simulation de valeurs CO2 réalistes
    base_co2 = 400 + random.randint(0, 800)  # 400-1200 ppm
    variation = random.randint(-50, 50)
    co2_ppm = max(300, base_co2 + variation)
    
    # Déterminer la qualité de l'air
    if co2_ppm < 400:
        air_quality = "EXCELLENT"
    elif co2_ppm < 600:
        air_quality = "BON"
    elif co2_ppm < 1000:
        air_quality = "MOYEN"
    elif co2_ppm < 1500:
        air_quality = "MAUVAIS"
    else:
        air_quality = "DANGER"
    
    return {
        "device_id": device_id,
        "co2_ppm": co2_ppm,
        "air_quality": air_quality,
        "location": location,
        "timestamp": time.time(),
        "temperature": round(20 + random.uniform(-5, 5), 1),  # Optionnel
        "humidity": round(50 + random.uniform(-20, 20), 1)    # Optionnel
    }

def send_test_data(data):
    """Envoie des données de test au serveur"""
    try:
        response = requests.post(
            API_ENDPOINT,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Données envoyées: {data['co2_ppm']} ppm ({data['air_quality']})")
            return True
        else:
            print(f"❌ Erreur envoi: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur envoi données: {e}")
        return False

def test_api_endpoints():
    """Test tous les endpoints API"""
    print("\n🧪 Test des endpoints API...")
    
    endpoints = [
        ("/health", "Health check"),
        ("/api/data/latest", "Dernières données"),
        ("/api/stats", "Statistiques"),
        ("/api/data/history?device=aircarto_test&hours=1", "Historique"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{SERVER_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description}: OK")
            else:
                print(f"❌ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: {e}")

def run_continuous_test(duration_minutes=5, interval_seconds=30):
    """Lance un test continu d'envoi de données"""
    print(f"\n🔄 Test continu pendant {duration_minutes} minutes...")
    print(f"📊 Envoi toutes les {interval_seconds} secondes")
    
    devices = [
        ("aircarto_test_1", "bureau"),
        ("aircarto_test_2", "salon"),
        ("aircarto_test_3", "cuisine")
    ]
    
    end_time = time.time() + (duration_minutes * 60)
    success_count = 0
    total_count = 0
    
    while time.time() < end_time:
        for device_id, location in devices:
            data = generate_test_data(device_id, location)
            total_count += 1
            
            if send_test_data(data):
                success_count += 1
            
            time.sleep(1)  # Petit délai entre devices
        
        print(f"📊 Succès: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        time.sleep(interval_seconds)
    
    print(f"\n✅ Test terminé! Succès: {success_count}/{total_count}")

def test_single_device():
    """Test simple avec un seul device"""
    print("\n📡 Test envoi données simple...")
    
    data = generate_test_data()
    print(f"📊 Données générées: {json.dumps(data, indent=2)}")
    
    return send_test_data(data)

def stress_test(num_requests=100):
    """Test de charge avec beaucoup de requêtes"""
    print(f"\n🚀 Test de charge: {num_requests} requêtes...")
    
    success = 0
    start_time = time.time()
    
    for i in range(num_requests):
        device_id = f"stress_test_{i % 10}"  # 10 devices différents
        data = generate_test_data(device_id, "stress_test")
        
        if send_test_data(data):
            success += 1
        
        if i % 10 == 0:
            print(f"Progress: {i+1}/{num_requests}")
    
    duration = time.time() - start_time
    print(f"\n✅ Test terminé en {duration:.2f}s")
    print(f"📊 Succès: {success}/{num_requests} ({success/num_requests*100:.1f}%)")
    print(f"⚡ Débit: {num_requests/duration:.2f} req/s")

def main():
    """Menu principal"""
    print("🌱 === AirCarto Server - Tests === 🌱")
    print("📊 Script de test et validation\n")
    
    if not test_server_health():
        print("❌ Serveur non disponible!")
        print("💡 Vérifiez que le serveur est démarré:")
        print("   python server.py")
        print("   ou: sudo systemctl start aircarto-server")
        return
    
    while True:
        print("\n🎯 Choisissez un test:")
        print("1. 📡 Test simple (1 envoi)")
        print("2. 🔄 Test continu (5 min)")
        print("3. 🧪 Test endpoints API")
        print("4. 🚀 Test de charge")
        print("5. 🎲 Génération données aléatoires")
        print("6. ❌ Quitter")
        
        choice = input("\nVotre choix (1-6): ").strip()
        
        if choice == "1":
            test_single_device()
            
        elif choice == "2":
            minutes = input("Durée en minutes (défaut: 5): ").strip()
            minutes = int(minutes) if minutes.isdigit() else 5
            run_continuous_test(minutes)
            
        elif choice == "3":
            test_api_endpoints()
            
        elif choice == "4":
            num = input("Nombre de requêtes (défaut: 100): ").strip()
            num = int(num) if num.isdigit() else 100
            stress_test(num)
            
        elif choice == "5":
            print("\n🎲 Génération 10 données aléatoires...")
            for i in range(10):
                data = generate_test_data(f"random_{i+1}")
                send_test_data(data)
                time.sleep(2)
                
        elif choice == "6":
            print("👋 Au revoir!")
            break
            
        else:
            print("❌ Choix invalide!")

if __name__ == "__main__":
    main() 