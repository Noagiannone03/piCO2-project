@app.route('/api/data/latest')
def get_latest_data():
    """Récupère les dernières données avec gestion d'erreur robuste"""
    try:
        if not query_api:
            logger.error("❌ InfluxDB query_api non disponible")
            return jsonify({"error": "InfluxDB not available", "devices": []}), 503
        
        # Essayer d'abord une requête simplifiée
        try:
            # Requête simple sans grouping
            query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: -24h)
                |> filter(fn: (r) => r._measurement == "co2_measurement")
                |> filter(fn: (r) => r._field == "co2_ppm")
                |> last()
            '''
            
            result = query_api.query(query=query)
            
            devices = []
            for table in result:
                for record in table.records:
                    try:
                        # Accès sécurisé aux propriétés
                        device_data = {
                            "device_id": record.get("device_id") or "aircarto_001",
                            "location": record.get("location") or "salon", 
                            "co2_ppm": int(record.get_value()) if record.get_value() is not None else 0,
                            "air_quality": record.get("air_quality") or "unknown",
                            "timestamp": record.get_time().isoformat() if record.get_time() else datetime.utcnow().isoformat()
                        }
                        devices.append(device_data)
                        logger.info(f"✅ Device récupéré: {device_data['device_id']} - {device_data['co2_ppm']} ppm")
                        
                    except Exception as record_error:
                        logger.error(f"❌ Erreur processing record: {record_error}")
                        continue
            
            if devices:
                return jsonify({"devices": devices})
            else:
                # Pas de données récentes, mais pas d'erreur
                logger.info("ℹ️ Aucune donnée récente trouvée")
                return jsonify({"devices": []})
                
        except Exception as query_error:
            logger.error(f"❌ Erreur requête InfluxDB: {query_error}")
            
            # Fallback: essayer requête encore plus simple
            try:
                fallback_query = f'''
                from(bucket: "{INFLUXDB_BUCKET}")
                    |> range(start: -1h)
                    |> filter(fn: (r) => r._measurement == "co2_measurement")
                    |> limit(n: 1)
                '''
                
                result = query_api.query(query=fallback_query)
                
                devices = []
                for table in result:
                    for record in table.records:
                        try:
                            device_data = {
                                "device_id": "aircarto_001",
                                "location": "salon",
                                "co2_ppm": int(record.get_value()) if record.get_value() else 400,
                                "air_quality": "unknown",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            devices.append(device_data)
                            break
                        except:
                            continue
                
                if devices:
                    logger.info("✅ Fallback query réussie")
                    return jsonify({"devices": devices})
                else:
                    logger.info("ℹ️ Aucune donnée trouvée (fallback)")
                    return jsonify({"devices": []})
                    
            except Exception as fallback_error:
                logger.error(f"❌ Erreur fallback query: {fallback_error}")
                return jsonify({"error": "Database query failed", "devices": []}), 500
        
    except Exception as e:
        logger.error(f"❌ Erreur générale get_latest_data: {e}")
        return jsonify({"error": "Internal server error", "devices": []}), 500

# Également corriger get_stats pour éviter les erreurs similaires
@app.route('/api/stats')
def get_stats():
    """Récupère les statistiques globales avec gestion d'erreur robuste"""
    try:
        if not query_api:
            return jsonify({
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
            }), 200  # Retourner 200 avec stats vides plutôt qu'erreur
        
        try:
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
                    try:
                        value = record.get_value()
                        device_id = record.get("device_id")
                        
                        if value is not None:
                            values.append(float(value))
                        if device_id:
                            devices.add(device_id)
                    except:
                        continue
            
            if values:
                stats = {
                    "total_devices": len(devices),
                    "total_measurements": len(values),
                    "avg_co2": round(sum(values) / len(values), 2),
                    "min_co2": int(min(values)),
                    "max_co2": int(max(values)),
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
            
            logger.info(f"📊 Stats calculées: {len(values)} mesures, {len(devices)} devices")
            return jsonify(stats)
            
        except Exception as query_error:
            logger.error(f"❌ Erreur requête stats: {query_error}")
            # Retourner stats vides en cas d'erreur
            return jsonify({
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
            }), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur générale get_stats: {e}")
        return jsonify({
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
        }), 200 