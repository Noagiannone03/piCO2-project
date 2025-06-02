#!/usr/bin/env python3
"""
Script de diagnostic pour identifier les erreurs API
"""

import requests
import json
from influxdb_client import InfluxDBClient
import traceback

# Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "aircarto-token-2024"
INFLUXDB_ORG = "aircarto"
INFLUXDB_BUCKET = "co2_data"
SERVER_URL = "http://localhost:5000"

def test_influxdb_direct():
    """Test direct d'InfluxDB"""
    print("🔍 Test InfluxDB direct...")
    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        query_api = client.query_api()
        
        # Test de la requête problématique
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "co2_measurement")
            |> filter(fn: (r) => r._field == "co2_ppm")
            |> group(columns: ["device_id"])
            |> last()
        '''
        
        print(f"📊 Exécution de la requête...")
        result = query_api.query(query=query)
        
        print(f"✅ Requête InfluxDB réussie")
        
        devices = []
        for table in result:
            for record in table.records:
                print(f"📋 Record trouvé:")
                print(f"   Device: {record.get('device_id', 'N/A')}")
                print(f"   CO2: {record.get_value()}")
                print(f"   Time: {record.get_time()}")
                print(f"   Air Quality: {record.get('air_quality', 'N/A')}")
                print(f"   Location: {record.get('location', 'N/A')}")
                
                devices.append({
                    "device_id": record.get("device_id"),
                    "location": record.get("location", "unknown"),
                    "co2_ppm": record.get_value(),
                    "air_quality": record.get("air_quality", "unknown"),
                    "timestamp": record.get_time().isoformat() if record.get_time() else None
                })
        
        print(f"📊 {len(devices)} devices trouvés")
        client.close()
        return devices
        
    except Exception as e:
        print(f"❌ Erreur InfluxDB: {e}")
        traceback.print_exc()
        return None

def test_api_endpoints():
    """Test des endpoints API"""
    print("\n🔍 Test des endpoints API...")
    
    endpoints = [
        "/health",
        "/api/data/latest", 
        "/api/stats",
        "/api/data/history?hours=24"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n📡 Test {endpoint}...")
            response = requests.get(f"{SERVER_URL}{endpoint}", timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ JSON valide")
                    if endpoint == "/api/data/latest":
                        print(f"   📊 Devices: {len(data.get('devices', []))}")
                        if data.get('devices'):
                            print(f"   📋 Premier device: {data['devices'][0]}")
                    elif endpoint == "/api/stats":
                        print(f"   📊 Stats: {data}")
                except:
                    print(f"   📄 Contenu: {response.text[:200]}...")
            else:
                print(f"   ❌ Erreur: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def check_data_in_db():
    """Vérifier s'il y a des données dans la DB"""
    print("\n🔍 Vérification des données en base...")
    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        query_api = client.query_api()
        
        # Compter les mesures
        count_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "co2_measurement")
            |> count()
        '''
        
        result = query_api.query(query=count_query)
        
        total_count = 0
        for table in result:
            for record in table.records:
                total_count += record.get_value()
        
        print(f"📊 Total mesures 24h: {total_count}")
        
        # Dernière mesure
        last_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "co2_measurement")
            |> filter(fn: (r) => r._field == "co2_ppm")
            |> last()
        '''
        
        result = query_api.query(query=last_query)
        
        for table in result:
            for record in table.records:
                print(f"📋 Dernière mesure:")
                print(f"   Time: {record.get_time()}")
                print(f"   CO2: {record.get_value()}")
                print(f"   Device: {record.get('device_id')}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erreur vérification DB: {e}")

def fix_api_latest():
    """Proposition de correctif pour /api/data/latest"""
    print("\n🔧 Analyse du problème /api/data/latest...")
    
    # Test avec requête simplifiée
    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        query_api = client.query_api()
        
        # Requête simplifiée sans group
        simple_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "co2_measurement")
            |> filter(fn: (r) => r._field == "co2_ppm")
            |> last()
        '''
        
        result = query_api.query(query=simple_query)
        
        devices = []
        for table in result:
            for record in table.records:
                device_data = {
                    "device_id": record.get("device_id", "aircarto_001"),
                    "location": record.get("location", "salon"),
                    "co2_ppm": int(record.get_value()) if record.get_value() else 0,
                    "air_quality": record.get("air_quality", "unknown"),
                    "timestamp": record.get_time().isoformat() if record.get_time() else None
                }
                devices.append(device_data)
                print(f"✅ Device simplifié: {device_data}")
        
        print(f"📊 Requête simplifiée: {len(devices)} devices")
        client.close()
        return devices
        
    except Exception as e:
        print(f"❌ Erreur requête simplifiée: {e}")
        traceback.print_exc()
        return []

if __name__ == "__main__":
    print("🌱 My Pico - Diagnostic API")
    print("=" * 50)
    
    # Tests séquentiels
    check_data_in_db()
    test_influxdb_direct()
    test_api_endpoints()
    fix_api_latest()
    
    print("\n🎯 Recommandations:")
    print("1. Si InfluxDB direct fonctionne mais pas l'API:")
    print("   → Problème dans le code serveur")
    print("2. Si pas de données en base:")
    print("   → Vérifiez que le Pico envoie des données")
    print("3. Si erreur de requête InfluxDB:")
    print("   → Utilisez la requête simplifiée") 