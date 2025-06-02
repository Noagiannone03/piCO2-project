# Commandes manuelles pour synchroniser vers le Raspberry Pi

## Préparation
Remplacez `pi@raspberrypi.local` par l'adresse de votre Pi si différente.

## 1. Synchroniser les nouveaux templates (designs Apple)
```bash
scp -r aircarto-server/templates/ pi@raspberrypi.local:/home/pi/aircarto-project/aircarto-server/
```

## 2. Synchroniser le serveur Python
```bash
scp aircarto-server/server.py pi@raspberrypi.local:/home/pi/aircarto-project/aircarto-server/
scp aircarto-server/requirements.txt pi@raspberrypi.local:/home/pi/aircarto-project/aircarto-server/
```

## 3. Synchroniser le code du capteur (optionnel)
```bash
scp aircarto_complete.py pi@raspberrypi.local:/home/pi/aircarto-project/
scp ssd1306.py pi@raspberrypi.local:/home/pi/aircarto-project/
```

## 4. Redémarrer le serveur sur le Pi
```bash
ssh pi@raspberrypi.local
cd aircarto-project/aircarto-server
sudo pkill -f server.py
python3 server.py
```

## Alternative avec rsync (plus efficace)
```bash
# Sync complet
rsync -avz --progress aircarto-server/ pi@raspberrypi.local:/home/pi/aircarto-project/aircarto-server/
``` 