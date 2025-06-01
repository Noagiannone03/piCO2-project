#!/usr/bin/env python3
"""
AirCarto Server - Serveur de données CO2 avec InfluxDB
Reçoit les données des capteurs Pico et les stocke dans InfluxDB
Interface web pour visualiser les données en temps réel
"""

from flask import Flask, request, jsonify, render_template
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import os
from datetime import datetime, timedelta
import logging

# Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "aircarto-token-2024"  # Token par défaut
INFLUXDB_ORG = "aircarto"
INFLUXDB_BUCKET = "co2_data"

app = Flask(__name__)

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Client InfluxDB
influx_client = None
write_api = None
query_api = None

def init_influxdb():
    """Initialise la connexion InfluxDB"""
    global influx_client, write_api, query_api
    
    try:
        influx_client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        query_api = influx_client.query_api()
        
        # Tester la connexion
        buckets = influx_client.buckets_api().find_buckets()
        logger.info("✅ InfluxDB connecté!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur InfluxDB: {e}")
        return False

@app.route('/')
def index():
    """Page d'accueil avec dashboard"""
    return render_template('index.html')

@app.route('/charts')
def charts():
    """Page avec graphiques détaillés"""
    return render_template('charts.html')

@app.route('/api/co2', methods=['POST'])
def receive_co2_data():
    """Endpoint pour recevoir les données CO2 du Pico"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        # Validation des données
        required_fields = ['device_id', 'co2_ppm', 'air_quality']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        # Créer un point InfluxDB
        point = Point("co2_measurement") \
            .tag("device_id", data['device_id']) \
            .tag("location", data.get('location', 'unknown')) \
            .tag("air_quality", data['air_quality']) \
            .field("co2_ppm", float(data['co2_ppm'])) \
            .time(datetime.utcnow())
        
        # Ajouter des champs optionnels
        if 'temperature' in data:
            point = point.field("temperature", float(data['temperature']))
        if 'humidity' in data:
            point = point.field("humidity", float(data['humidity']))
        
        # Écrire dans InfluxDB
        if write_api:
            write_api.write(bucket=INFLUXDB_BUCKET, record=point)
        
        logger.info(f"📊 Données reçues: {data['co2_ppm']} ppm de {data['device_id']}")
        
        return jsonify({"status": "success", "message": "Data stored"}), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur stockage: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/latest')
def get_latest_data():
    """Récupère les dernières données"""
    try:
        if not query_api:
            return jsonify({"error": "InfluxDB not available"}), 503
        
        # Requête pour les dernières données de chaque device
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "co2_measurement")
            |> filter(fn: (r) => r._field == "co2_ppm")
            |> group(columns: ["device_id"])
            |> last()
        '''
        
        result = query_api.query(query=query)
        
        devices = []
        for table in result:
            for record in table.records:
                devices.append({
                    "device_id": record["device_id"],
                    "location": record.get("location", "unknown"),
                    "co2_ppm": record.get_value(),
                    "air_quality": record.get("air_quality", "unknown"),
                    "timestamp": record.get_time().isoformat()
                })
        
        return jsonify({"devices": devices})
        
    except Exception as e:
        logger.error(f"❌ Erreur lecture: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/history')
def get_history():
    """Récupère l'historique des données"""
    try:
        device_id = request.args.get('device', 'aircarto_001')
        hours = int(request.args.get('hours', 24))
        
        if not query_api:
            return jsonify({"error": "InfluxDB not available"}), 503
        
        # Requête pour l'historique
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -{hours}h)
            |> filter(fn: (r) => r._measurement == "co2_measurement")
            |> filter(fn: (r) => r.device_id == "{device_id}")
            |> filter(fn: (r) => r._field == "co2_ppm")
            |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
            |> yield(name: "mean")
        '''
        
        result = query_api.query(query=query)
        
        data_points = []
        for table in result:
            for record in table.records:
                data_points.append({
                    "time": record.get_time().isoformat(),
                    "co2_ppm": record.get_value()
                })
        
        return jsonify({
            "device_id": device_id,
            "hours": hours,
            "data": data_points
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur historique: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Récupère les statistiques globales"""
    try:
        if not query_api:
            return jsonify({"error": "InfluxDB not available"}), 503
        
        # Statistiques des dernières 24h
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "co2_measurement")
            |> filter(fn: (r) => r._field == "co2_ppm")
        '''
        
        result = query_api.query(query=query)
        
        values = []
        devices = set()
        
        for table in result:
            for record in table.records:
                values.append(record.get_value())
                devices.add(record["device_id"])
        
        if values:
            stats = {
                "total_devices": len(devices),
                "total_measurements": len(values),
                "avg_co2": round(sum(values) / len(values), 2),
                "min_co2": min(values),
                "max_co2": max(values),
                "excellent_count": len([v for v in values if v < 400]),
                "good_count": len([v for v in values if 400 <= v < 600]),
                "medium_count": len([v for v in values if 600 <= v < 1000]),
                "bad_count": len([v for v in values if 1000 <= v < 1500]),
                "danger_count": len([v for v in values if v >= 1500]),
            }
        else:
            stats = {
                "total_devices": 0,
                "total_measurements": 0,
                "avg_co2": 0,
                "min_co2": 0,
                "max_co2": 0,
                "excellent_count": 0,
                "good_count": 0,
                "medium_count": 0,
                "bad_count": 0,
                "danger_count": 0,
            }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ Erreur stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Vérification de l'état du serveur"""
    status = {
        "server": "running",
        "influxdb": "connected" if influx_client else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(status)

if __name__ == '__main__':
    print("🌐 === AirCarto Server v2.0 === 🌐")
    print("📊 Serveur de données CO2 avec InfluxDB")
    
    # Initialiser InfluxDB
    if init_influxdb():
        print("✅ InfluxDB prêt!")
    else:
        print("⚠️  InfluxDB non disponible - Mode dégradé")
    
    print("📍 Interface web: http://localhost:5000")
    print("📡 API endpoint: http://localhost:5000/api/co2")
    print("📈 Graphiques: http://localhost:5000/charts")
    print("🔄 Arrêt: Ctrl+C")
    
    app.run(host='0.0.0.0', port=5000, debug=False) 