#!/bin/bash
# Script d'installation AirCarto Server v2.0
# Compatible Raspberry Pi OS / Debian

echo "🌱 === Installation AirCarto Server === 🌱"
echo "📊 Serveur de données CO2 avec InfluxDB"
echo ""

# Vérifier si on est root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Ne pas exécuter en tant que root!"
    echo "💡 Utilisez: bash install.sh"
    exit 1
fi

# Détection OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    echo "📋 OS détecté: $OS"
else
    echo "❌ OS non supporté"
    exit 1
fi

# Mise à jour système
echo ""
echo "🔄 Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# Installation des dépendances système
echo ""
echo "📦 Installation des dépendances..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    nginx \
    certbot \
    python3-certbot-nginx

# Installation InfluxDB
echo ""
echo "📊 Installation InfluxDB..."

# Ajouter le dépôt InfluxDB
curl -s https://repos.influxdata.com/influxdata-archive_compat.key | sudo apt-key add -
echo "deb https://repos.influxdata.com/debian stable main" | sudo tee /etc/apt/sources.list.d/influxdb.list

sudo apt update
sudo apt install -y influxdb2

# Démarrer InfluxDB
sudo systemctl enable influxdb
sudo systemctl start influxdb

echo "⏳ Attente démarrage InfluxDB..."
sleep 10

# Configuration InfluxDB
echo ""
echo "⚙️  Configuration InfluxDB..."

# Vérifier si InfluxDB est prêt
if curl -s http://localhost:8086/health | grep -q "pass"; then
    echo "✅ InfluxDB démarré!"
    
    # Configuration initiale (si pas déjà fait)
    INFLUX_SETUP_OUTPUT=$(influx setup \
        --username aircarto \
        --password aircarto2024 \
        --org aircarto \
        --bucket co2_data \
        --token aircarto-token-2024 \
        --force 2>&1 || true)
    
    if echo "$INFLUX_SETUP_OUTPUT" | grep -q "has been setup"; then
        echo "✅ InfluxDB configuré!"
    else
        echo "ℹ️  InfluxDB déjà configuré"
    fi
else
    echo "❌ InfluxDB ne démarre pas!"
    echo "🔧 Vérifiez les logs: sudo journalctl -u influxdb"
    exit 1
fi

# Créer le répertoire de travail
echo ""
echo "📁 Création du répertoire AirCarto..."
AIRCARTO_DIR="$HOME/aircarto-server"
mkdir -p "$AIRCARTO_DIR"

# Si on est dans le repo, copier les fichiers
if [ -f "server.py" ]; then
    echo "📋 Copie des fichiers du projet..."
    cp -r * "$AIRCARTO_DIR/"
else
    echo "⬇️  Téléchargement des fichiers..."
    cd "$AIRCARTO_DIR"
    # Ici on devrait télécharger depuis GitHub ou autre
    echo "⚠️  Placez les fichiers server.py, requirements.txt, etc. dans $AIRCARTO_DIR"
fi

cd "$AIRCARTO_DIR"

# Créer environnement virtuel Python
echo ""
echo "🐍 Configuration environnement Python..."
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances Python
echo "📦 Installation dépendances Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Créer le service systemd
echo ""
echo "🔧 Configuration service système..."

sudo tee /etc/systemd/system/aircarto-server.service > /dev/null <<EOF
[Unit]
Description=AirCarto Server - CO2 Data Server
After=network.target influxdb.service
Requires=influxdb.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$AIRCARTO_DIR
Environment=PATH=$AIRCARTO_DIR/venv/bin
ExecStart=$AIRCARTO_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 server:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Recharger systemd et démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable aircarto-server
sudo systemctl start aircarto-server

# Configuration Nginx (optionnel)
echo ""
read -p "🌐 Configurer Nginx reverse proxy? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⚙️  Configuration Nginx..."
    
    sudo tee /etc/nginx/sites-available/aircarto > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Fichiers statiques
    location /static {
        alias $AIRCARTO_DIR/static;
        expires 1d;
    }
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/aircarto /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    echo "✅ Nginx configuré!"
fi

# Créer script de gestion
echo ""
echo "📝 Création scripts de gestion..."

tee "$HOME/aircarto-manage.sh" > /dev/null <<EOF
#!/bin/bash
# Script de gestion AirCarto

case "\$1" in
    start)
        echo "🚀 Démarrage AirCarto..."
        sudo systemctl start aircarto-server
        ;;
    stop)
        echo "🛑 Arrêt AirCarto..."
        sudo systemctl stop aircarto-server
        ;;
    restart)
        echo "🔄 Redémarrage AirCarto..."
        sudo systemctl restart aircarto-server
        ;;
    status)
        echo "📊 Status AirCarto:"
        sudo systemctl status aircarto-server
        ;;
    logs)
        echo "📋 Logs AirCarto:"
        sudo journalctl -u aircarto-server -f
        ;;
    update)
        echo "⬆️  Mise à jour AirCarto..."
        cd $AIRCARTO_DIR
        git pull || echo "⚠️  Pas de repo Git"
        source venv/bin/activate
        pip install -r requirements.txt
        sudo systemctl restart aircarto-server
        ;;
    backup)
        echo "💾 Sauvegarde données InfluxDB..."
        influx backup -t aircarto-token-2024 ~/aircarto-backup-\$(date +%Y%m%d)
        ;;
    *)
        echo "🌱 AirCarto Server - Commandes disponibles:"
        echo "  start    - Démarrer le serveur"
        echo "  stop     - Arrêter le serveur"
        echo "  restart  - Redémarrer le serveur"
        echo "  status   - Voir le statut"
        echo "  logs     - Voir les logs en temps réel"
        echo "  update   - Mettre à jour le serveur"
        echo "  backup   - Sauvegarder les données"
        ;;
esac
EOF

chmod +x "$HOME/aircarto-manage.sh"

# Test de fonctionnement
echo ""
echo "🧪 Test du serveur..."
sleep 5

if curl -s http://localhost:5000/health | grep -q "running"; then
    echo "✅ Serveur fonctionne!"
else
    echo "❌ Problème serveur - Vérifiez les logs:"
    echo "   sudo journalctl -u aircarto-server"
fi

# Affichage des informations finales
echo ""
echo "🎉 === Installation terminée! === 🎉"
echo ""
echo "📍 URLs d'accès:"
echo "   🏠 Dashboard: http://$(hostname -I | awk '{print $1}'):5000"
echo "   📊 Graphiques: http://$(hostname -I | awk '{print $1}'):5000/charts"
echo "   🔧 Health: http://$(hostname -I | awk '{print $1}'):5000/health"
echo ""
echo "📡 Configuration capteurs:"
echo "   URL API: http://$(hostname -I | awk '{print $1}'):5000/api/co2"
echo "   Méthode: POST"
echo "   Format: JSON"
echo ""
echo "🛠️  Commandes utiles:"
echo "   Gérer le serveur: ~/aircarto-manage.sh [start|stop|restart|status|logs]"
echo "   Logs serveur: sudo journalctl -u aircarto-server -f"
echo "   Logs InfluxDB: sudo journalctl -u influxdb -f"
echo ""
echo "📊 InfluxDB:"
echo "   Interface: http://$(hostname -I | awk '{print $1}'):8086"
echo "   Organisation: aircarto"
echo "   Bucket: co2_data"
echo "   Token: aircarto-token-2024"
echo ""
echo "🔧 Prochaines étapes:"
echo "   1. Configurez vos capteurs AirCarto"
echo "   2. Modifier SERVER_URL dans aircarto_complete.py"
echo "   3. Testez l'envoi de données"
echo ""
echo "💡 Aide: Consultez le README.md pour plus d'infos" 