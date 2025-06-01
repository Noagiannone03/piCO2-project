#!/usr/bin/env python3
"""
Script pour corriger l'initialisation InfluxDB dans server.py
Ajoute l'initialisation automatique au chargement du module
"""

import os
import shutil

def fix_server_init():
    """Corrige server.py pour initialiser InfluxDB automatiquement"""
    
    server_file = "server.py"
    backup_file = "server.py.backup"
    
    # Faire une sauvegarde
    shutil.copy2(server_file, backup_file)
    print(f"✅ Sauvegarde créée: {backup_file}")
    
    # Lire le fichier
    with open(server_file, 'r') as f:
        content = f.read()
    
    # Trouver où ajouter l'initialisation
    # On va l'ajouter après la définition de l'app Flask
    
    if "# Auto-initialisation InfluxDB" in content:
        print("⚠️  Le fichier semble déjà corrigé")
        return
    
    # Chercher la ligne avec app = Flask(__name__)
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Ajouter l'initialisation après la création de l'app
        if line.strip().startswith('app = Flask(__name__)'):
            new_lines.append('')
            new_lines.append('# Auto-initialisation InfluxDB pour Gunicorn')
            new_lines.append('# Initialiser InfluxDB au chargement du module')
            new_lines.append('if not influx_client:')
            new_lines.append('    init_result = init_influxdb()')
            new_lines.append('    if init_result:')
            new_lines.append('        logger.info("🔄 InfluxDB initialisé automatiquement")')
            new_lines.append('    else:')
            new_lines.append('        logger.warning("⚠️  InfluxDB non disponible au démarrage")')
            new_lines.append('')
    
    # Écrire le fichier corrigé
    with open(server_file, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print("✅ server.py corrigé pour l'auto-initialisation InfluxDB")
    print("🔄 Redémarrez le service: sudo systemctl restart aircarto-server.service")

if __name__ == "__main__":
    fix_server_init() 