#!/usr/bin/env python3
"""
Script pour ajouter des données de démonstration dans InfluxDB
Simule des relevés CO2 réalistes sur plusieurs jours
"""

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timedelta
import random
import math

# Configuration (même que server.py)
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "aircarto-token-2024"
INFLUXDB_ORG = "aircarto"
INFLUXDB_BUCKET = "co2_data"

def get_air_quality(co2_ppm):
    """Détermine la qualité de l'air selon le taux de CO2"""
    if co2_ppm < 400:
        return "excellent"
    elif co2_ppm < 600:
        return "good"
    elif co2_ppm < 1000:
        return "medium"
    elif co2_ppm < 1500:
        return "bad"
    else:
        return "danger"

def generate_realistic_co2_data(days=7):
    """Génère des données CO2 réalistes sur plusieurs jours"""
    data_points = []
    start_time = datetime.utcnow() - timedelta(days=days)
    
    for day in range(days):
        for hour in range(24):
            # Pattern réaliste : plus haut la nuit/soirée, plus bas le matin
            base_co2 = 450  # Baseline
            
            # Cycle journalier (plus élevé le soir)
            daily_cycle = 150 * math.sin((hour - 6) * math.pi / 12)
            
            # Variation aléatoire
            random_variation = random.gauss(0, 50)
            
            # Pattern de weekend (moins de variation)
            if (start_time + timedelta(days=day)).weekday() >= 5:  # Weekend
                daily_cycle *= 0.7
            
            # Spikes occasionnels (cuisine, activité...)
            if random.random() < 0.1:  # 10% chance de spike
                spike = random.randint(100, 300)
            else:
                spike = 0
            
            co2_value = max(350, base_co2 + daily_cycle + random_variation + spike)
            co2_value = min(co2_value, 2000)  # Cap à 2000 ppm
            
            # Générer plusieurs points par heure (toutes les 5 minutes)
            for minute in range(0, 60, 5):
                timestamp = start_time + timedelta(days=day, hours=hour, minutes=minute)
                
                # Micro-variations entre les mesures
                micro_variation = random.gauss(0, 10)
                final_co2 = max(350, co2_value + micro_variation)
                
                point = {
                    "time": timestamp,
                    "co2_ppm": round(final_co2),
                    "air_quality": get_air_quality(final_co2),
                    "device_id": "aircarto_001",
                    "location": "salon"
                }
                data_points.append(point)
    
    return data_points

def add_demo_data():
    """Ajoute les données de démonstration à InfluxDB"""
    try:
        # Connexion à InfluxDB
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        print("🔄 Génération des données de démonstration...")
        
        # Générer 7 jours de données
        data_points = generate_realistic_co2_data(7)
        
        print(f"📊 Ajout de {len(data_points)} points de données...")
        
        # Convertir en points InfluxDB et écrire par batch
        batch_size = 1000
        for i in range(0, len(data_points), batch_size):
            batch = data_points[i:i+batch_size]
            influx_points = []
            
            for point in batch:
                influx_point = Point("co2_measurement") \
                    .tag("device_id", point["device_id"]) \
                    .tag("location", point["location"]) \
                    .tag("air_quality", point["air_quality"]) \
                    .field("co2_ppm", float(point["co2_ppm"])) \
                    .time(point["time"])
                
                influx_points.append(influx_point)
            
            write_api.write(bucket=INFLUXDB_BUCKET, record=influx_points)
            print(f"✅ Batch {i//batch_size + 1}/{(len(data_points)-1)//batch_size + 1} ajouté")
        
        print("🎉 Données de démonstration ajoutées avec succès!")
        print(f"📈 {len(data_points)} mesures sur 7 jours")
        print("🌐 Actualisez votre interface web pour voir les données")
        
        # Statistiques
        co2_values = [p["co2_ppm"] for p in data_points]
        print(f"\n📊 Statistiques générées:")
        print(f"   • CO2 minimum: {min(co2_values)} ppm")
        print(f"   • CO2 maximum: {max(co2_values)} ppm")
        print(f"   • CO2 moyen: {sum(co2_values)//len(co2_values)} ppm")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🌱 My Pico - Générateur de données de démonstration")
    print("=" * 50)
    
    success = add_demo_data()
    
    if success:
        print("\n🚀 Prêt! Votre dashboard devrait maintenant afficher des données réalistes.")
        print("🔗 Ouvrez http://localhost:5000 pour voir le résultat")
    else:
        print("\n❌ Échec de l'ajout des données. Vérifiez qu'InfluxDB fonctionne.") 