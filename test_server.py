#!/usr/bin/env python3
"""
Serveur de test pour AirCarto
Simple serveur Flask pour recevoir et afficher les données CO2
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# Stockage des données en mémoire (pour test)
co2_data = []

@app.route('/')
def index():
    """Page d'accueil avec les dernières données"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AirCarto Server</title>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="30">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { background: #4CAF50; color: white; padding: 20px; border-radius: 10px; text-align: center; }
            .data-card { background: #f9f9f9; border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0; }
            .co2-value { font-size: 24px; font-weight: bold; }
            .timestamp { color: #666; font-size: 12px; }
            .status-excellent { color: #4CAF50; }
            .status-bon { color: #8BC34A; }
            .status-moyen { color: #FF9800; }
            .status-mauvais { color: #FF5722; }
            .status-danger { color: #F44336; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 AirCarto Server</h1>
            <p>Surveillance CO2 en temps réel</p>
        </div>
        
        <h2>📊 Dernières mesures</h2>
    """
    
    if co2_data:
        for data in co2_data[-10:]:  # 10 dernières mesures
            status_class = f"status-{data['air_quality'].lower()}"
            html += f"""
            <div class="data-card">
                <div class="co2-value {status_class}">
                    {data['co2_ppm']} ppm - {data['air_quality']}
                </div>
                <div>Device: {data['device_id']} | Location: {data['location']}</div>
                <div class="timestamp">{data['formatted_time']}</div>
            </div>
            """
    else:
        html += "<p>Aucune donnée reçue pour le moment...</p>"
    
    html += """
        <h2>📈 Statistiques</h2>
        <p>Total mesures: {}</p>
        <p>Dernière mise à jour: Auto-refresh toutes les 30s</p>
    </body>
    </html>
    """.format(len(co2_data))
    
    return html

@app.route('/api/co2', methods=['POST'])
def receive_co2_data():
    """Endpoint pour recevoir les données CO2 du Pico"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        # Ajouter timestamp formaté
        data['formatted_time'] = datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        
        # Stocker les données
        co2_data.append(data)
        
        # Garder seulement les 100 dernières mesures
        if len(co2_data) > 100:
            co2_data.pop(0)
        
        print(f"📊 Données reçues: {data['co2_ppm']} ppm ({data['air_quality']}) de {data['device_id']}")
        
        return jsonify({"status": "success", "message": "Data received"}), 200
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status')
def api_status():
    """Status API"""
    return jsonify({
        "status": "online",
        "total_measurements": len(co2_data),
        "last_measurement": co2_data[-1] if co2_data else None
    })

if __name__ == '__main__':
    print("🌐 Démarrage serveur AirCarto...")
    print("📍 Interface web: http://localhost:5000")
    print("📡 API endpoint: http://localhost:5000/api/co2")
    print("🔄 Arrêt: Ctrl+C")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 