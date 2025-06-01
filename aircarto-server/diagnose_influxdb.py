#!/usr/bin/env python3
"""
Script de diagnostic InfluxDB pour AirCarto
Teste la connexion et l'état d'InfluxDB
"""

import os
import subprocess
import sys
from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError

# Configuration InfluxDB
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "aircarto-token-2024"
INFLUXDB_ORG = "aircarto"
INFLUXDB_BUCKET = "co2_data"

def check_influxdb_service():
    """Vérifie si le service InfluxDB est démarré"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'influxdb'], 
                              capture_output=True, text=True)
        status = result.stdout.strip()
        print(f"📊 Service InfluxDB: {status}")
        
        if status != "active":
            print("⚠️  Service InfluxDB non actif. Tentative de démarrage...")
            subprocess.run(['sudo', 'systemctl', 'start', 'influxdb'], check=True)
            print("✅ Service InfluxDB démarré")
        
        return status == "active"
    except Exception as e:
        print(f"❌ Erreur vérification service: {e}")
        return False

def check_influxdb_port():
    """Vérifie si InfluxDB écoute sur le port 8086"""
    try:
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        if ":8086" in result.stdout:
            print("✅ InfluxDB écoute sur le port 8086")
            return True
        else:
            print("❌ InfluxDB n'écoute pas sur le port 8086")
            return False
    except Exception as e:
        print(f"❌ Erreur vérification port: {e}")
        return False

def test_influxdb_connection():
    """Teste la connexion à InfluxDB"""
    try:
        print(f"🔌 Test de connexion à {INFLUXDB_URL}")
        
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        
        # Test de ping
        health = client.health()
        print(f"✅ InfluxDB Health: {health.status}")
        
        # Test des buckets
        buckets_api = client.buckets_api()
        buckets = buckets_api.find_buckets()
        
        print(f"📊 Buckets disponibles:")
        for bucket in buckets.buckets:
            print(f"  - {bucket.name} (org: {bucket.org_id})")
            
        # Vérifier si notre bucket existe
        bucket_names = [b.name for b in buckets.buckets]
        if INFLUXDB_BUCKET in bucket_names:
            print(f"✅ Bucket '{INFLUXDB_BUCKET}' trouvé")
        else:
            print(f"⚠️  Bucket '{INFLUXDB_BUCKET}' non trouvé")
            print("   Création du bucket...")
            try:
                from influxdb_client.client.bucket_api import BucketApi
                bucket_api = BucketApi(client)
                bucket_api.create_bucket(bucket_name=INFLUXDB_BUCKET, org=INFLUXDB_ORG)
                print(f"✅ Bucket '{INFLUXDB_BUCKET}' créé")
            except Exception as e:
                print(f"❌ Erreur création bucket: {e}")
        
        client.close()
        return True
        
    except InfluxDBError as e:
        print(f"❌ Erreur InfluxDB: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False

def check_influxdb_logs():
    """Vérifie les logs d'InfluxDB"""
    try:
        print("📋 Derniers logs InfluxDB:")
        result = subprocess.run(['journalctl', '-u', 'influxdb', '--no-pager', '-n', '10'], 
                              capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"❌ Erreur lecture logs: {e}")

def main():
    print("🔍 === Diagnostic InfluxDB AirCarto ===")
    print()
    
    # 1. Vérifier le service
    print("1️⃣ Vérification du service InfluxDB")
    service_ok = check_influxdb_service()
    print()
    
    # 2. Vérifier le port
    print("2️⃣ Vérification du port 8086")
    port_ok = check_influxdb_port()
    print()
    
    # 3. Tester la connexion
    print("3️⃣ Test de connexion InfluxDB")
    connection_ok = test_influxdb_connection()
    print()
    
    # 4. Afficher les logs si problème
    if not service_ok or not port_ok or not connection_ok:
        print("4️⃣ Logs InfluxDB (pour diagnostic)")
        check_influxdb_logs()
        print()
    
    # Résumé
    print("📋 === RÉSUMÉ ===")
    print(f"Service InfluxDB: {'✅' if service_ok else '❌'}")
    print(f"Port 8086: {'✅' if port_ok else '❌'}")
    print(f"Connexion: {'✅' if connection_ok else '❌'}")
    
    if service_ok and port_ok and connection_ok:
        print("\n🎉 InfluxDB fonctionne correctement!")
        print("   Le problème vient peut-être du serveur Flask.")
        print("   Redémarrez le service AirCarto:")
        print("   sudo systemctl restart aircarto")
    else:
        print("\n⚠️  Problèmes détectés avec InfluxDB")
        print("   Solutions possibles:")
        print("   1. sudo systemctl restart influxdb")
        print("   2. Vérifier la configuration InfluxDB")
        print("   3. Réinstaller InfluxDB si nécessaire")

if __name__ == "__main__":
    main() 