"""
AirCarto Mascotte - Chat Pixel Art pour écran OLED
Animations et sprites pour différents états du système
"""

import time
import network
from machine import Pin

class AirCartoMascot:
    def __init__(self, oled):
        self.oled = oled
        self.animation_frame = 0
        self.animation_time = 0
        
        # Chat adorable avec tête ronde et emoji-style - 18x18 parfait !
        self.cat_sprites = {
            'normal': [
                # Chat normal ultra mignon style emoji
                0b000001111111000000,  # sommet tête ronde
                0b000111111111110000,  # oreilles + front
                0b001111111111111000,  # tête ronde parfaite
                0b011111111111111100,  # contour visage
                0b111111111111111110,  # joues pleines
                0b111110111011111110,  # yeux mignons ● ●
                0b111111111111111110,  # entre yeux-nez
                0b111111101111111110,  # petit nez •
                0b111111000111111110,  # bouche souriante ‿
                0b111111111111111110,  # menton rond
                0b011111111111111100,  # cou
                0b001111111111111000,  # poitrine
                0b000111111111110000,  # corps
                0b000011111111100000,  # ventre
                0b000001111111000000,  # pattes
                0b000000111110000000,  # queue
                0b000000011100000000,  # bout queue
                0b000000000000000000
            ],
            'sleeping': [
                # Chat qui dort - style emoji zen
                0b000001111111000000,
                0b000111111111110000,
                0b001111111111111000,
                0b011111111111111100,
                0b111111111111111110,
                0b111100000000111110,  # yeux fermés ⌐⌐
                0b111111111111111110,
                0b111111101111111110,  # petit nez
                0b111111000111111110,  # bouche zen
                0b111111111111111110,
                0b011111111111111100,
                0b001111111111111000,
                0b000111111111110000,
                0b000011111111100000,
                0b000001111111000000,
                0b000000111110000000,
                0b000000011100000000,
                0b000000000000000000
            ],
            'happy': [
                # Chat super content - style emoji joyeux
                0b000001111111000000,
                0b000111111111110000,
                0b001111111111111000,
                0b011111111111111100,
                0b111111111111111110,
                0b111110111011111110,  # yeux joyeux ● ●
                0b111111111111111110,
                0b111111101111111110,  # petit nez
                0b111100000000111110,  # GRAND sourire ‿‿
                0b111111111111111110,
                0b011111111111111100,
                0b001111111111111000,
                0b000111111111110000,
                0b000011111111100000,
                0b000001111111000000,
                0b000000111110000000,
                0b000000011100000000,
                0b000000000000000000
            ],
            'worried': [
                # Chat inquiet - style emoji soucieux
                0b000001111111000000,
                0b000111111111110000,
                0b001111111111111000,
                0b011111111111111100,
                0b111111111111111110,
                0b111100101010111110,  # yeux soucieux ◔ ◔
                0b111111111111111110,
                0b111111101111111110,  # petit nez
                0b111111010111111110,  # bouche inquiète ︶
                0b111111111111111110,
                0b011111111111111100,
                0b001111111111111000,
                0b000111111111110000,
                0b000011111111100000,
                0b000001111111000000,
                0b000000111110000000,
                0b000000011100000000,
                0b000000000000000000
            ],
            'alert': [
                # Chat en alerte - style emoji surpris
                0b000101111111010000,  # oreilles dressées !
                0b000111111111110000,
                0b001111111111111000,
                0b011111111111111100,
                0b111111111111111110,
                0b111100111110111110,  # yeux alertes ○ ○
                0b111111111111111110,
                0b111111101111111110,  # petit nez
                0b111110000011111110,  # bouche surprise ◯
                0b111111111111111110,
                0b011111111111111100,
                0b001111111111111000,
                0b000111111111110000,
                0b000011111111100000,
                0b000001111111000000,
                0b000000111110000000,
                0b000000011100000000,
                0b000000000000000000
            ],
            'waking': [
                # Chat qui se réveille - style emoji ensommeillé
                0b000001111111000000,
                0b000111111111110000,
                0b001111111111111000,
                0b011111111111111100,
                0b111111111111111110,
                0b111100111010111110,  # un œil fermé ⌐ ●
                0b111111111111111110,
                0b111111101111111110,  # petit nez
                0b111111010111111110,  # bâillement ◡
                0b111111111111111110,
                0b011111111111111100,
                0b001111111111111000,
                0b000111111111110000,
                0b000011111111100000,
                0b000001111111000000,
                0b000000111110000000,
                0b000000011100000000,
                0b000000000000000000
            ]
        }
        
        # États d'animation
        self.current_state = 'normal'
        self.animation_frames = []
        self.frame_index = 0
        self.last_frame_time = time.ticks_ms()
        
    def draw_sprite(self, x, y, sprite_data, size=18):
        """Dessine un sprite sur l'écran (18x18 - parfaitement emoji!)"""
        sprite_size = len(sprite_data)
        
        for row in range(sprite_size):
            if row < len(sprite_data):
                byte_data = sprite_data[row]
                
                for col in range(size):
                    if x + col < 128 and y + row < 64:  # Vérifier les limites de l'écran
                        if byte_data & (1 << (size - 1 - col)):
                            self.oled.pixel(x + col, y + row, 1)
    
    def draw_cat_sprite(self, x, y, sprite_name):
        """Dessine un sprite de chat 18x18 style emoji parfait"""
        if sprite_name in self.cat_sprites:
            self.draw_sprite(x, y, self.cat_sprites[sprite_name], 18)
    
    def draw_startup_animation(self, frame):
        """Animation de démarrage avec texte "My Pico" et chat"""
        self.oled.fill(0)
        
        # Animation du texte "My Pico" qui apparaît lettre par lettre
        text = "My Pico"
        chars_to_show = min(frame // 10, len(text))
        displayed_text = text[:chars_to_show]
        
        # Centrer le texte
        text_x = (128 - len(displayed_text) * 8) // 2
        self.oled.text(displayed_text, text_x, 20)
        
        # Chat sympa qui cligne des yeux pendant l'animation
        cat_state = 'normal' if (frame // 20) % 2 == 0 else 'waking'
        self.draw_cat_sprite(55, 35, cat_state)  # Centré pour 18x18
        
        # Petites étoiles qui apparaissent
        if frame > 30:
            for i in range((frame - 30) // 5):
                star_x = 20 + i * 15
                star_y = 10 + (i % 2) * 5
                if star_x < 120:
                    self.draw_star(star_x, star_y)
        
        self.oled.show()
        return frame < 80  # Animation dure ~8 secondes
    
    def draw_star(self, x, y):
        """Dessine une petite étoile"""
        self.oled.pixel(x, y, 1)
        self.oled.pixel(x-1, y, 1)
        self.oled.pixel(x+1, y, 1)
        self.oled.pixel(x, y-1, 1)
        self.oled.pixel(x, y+1, 1)
    
    def draw_sleeping_animation(self, frame):
        """Animation du chat qui dort pendant le préchauffage - SIMPLIFIE"""
        self.oled.fill(0)
        
        # Titre modifié
        self.oled.text("ca se reveille ici", 5, 5)
        
        # Chat qui dort avec animation de respiration
        breathing = (frame // 15) % 2
        cat_y = 25 + breathing  # Mouvement de respiration
        
        self.draw_cat_sprite(55, cat_y, 'sleeping')  # Centré pour 18x18
        
        # ZZZ qui apparaissent
        zzz_frames = frame // 20
        if zzz_frames >= 1:
            self.oled.text("Z", 75, 20)
        if zzz_frames >= 2:
            self.oled.text("Z", 80, 15)
        if zzz_frames >= 3:
            self.oled.text("Z", 85, 10)
        
        # JUSTE LE COMPTEUR DE SECONDES - pas de barre
        remaining = max(0, 30 - (frame // 4))  # ~4 frames par seconde
        # Centrer le compteur sous la mascotte
        countdown_text = f"{remaining}s"
        text_x = (128 - len(countdown_text) * 8) // 2
        self.oled.text(countdown_text, text_x, 50)
        
        self.oled.show()
        return frame < 120  # Animation de préchauffage
    
    def draw_waking_animation(self):
        """Animation du chat qui se réveille"""
        for frame in range(20):
            self.oled.fill(0)
            self.oled.text("Systeme pret!", 25, 10)
            
            # Chat qui s'étire et se réveille
            if frame < 10:
                sprite = 'sleeping'
            elif frame < 15:
                sprite = 'waking'
            else:
                sprite = 'happy'
            
            self.draw_cat_sprite(55, 25, sprite)  # Centré pour 18x18
            
            # Exclamation de réveil
            if frame > 10:
                self.oled.text("!", 70, 20)
            
            self.oled.show()
            time.sleep(0.2)
    
    def animate_reaction(self, reaction_type):
        """Animations de réaction selon les événements - MASCOTTE DESCENDUE"""
        if reaction_type == "wifi_connect":
            # Chat content de la connexion WiFi
            for frame in range(15):
                self.oled.fill(0)
                self.oled.text("WiFi connecte!", 20, 5)
                # Mascotte descendue et collée au texte
                self.draw_cat_sprite(45, 18, 'happy')
                
                # Petits coeurs qui apparaissent
                if frame > 5:
                    self.draw_heart(25, 40)
                if frame > 10:
                    self.draw_heart(75, 38)
                
                self.oled.show()
                time.sleep(0.15)
                
        elif reaction_type == "wifi_error":
            # Chat inquiet pour les erreurs WiFi
            for frame in range(10):
                self.oled.fill(0)
                self.oled.text("WiFi erreur!", 25, 10)
                # Mascotte descendue et collée au texte
                sprite = 'worried' if frame % 2 == 0 else 'normal'
                self.draw_cat_sprite(45, 23, sprite)
                
                # Points d'interrogation de confusion
                if frame % 2 == 0:
                    self.oled.text("?", 30, 45)
                    self.oled.text("?", 80, 43)
                
                self.oled.show()
                time.sleep(0.3)
                
        elif reaction_type == "co2_danger":
            # Chat alerte pour CO2 élevé
            for frame in range(12):
                self.oled.fill(0)
                self.oled.text("CO2 ELEVE!", 30, 10)
                # Mascotte descendue et collée au texte
                sprite = 'alert' if frame % 2 == 0 else 'worried'
                self.draw_cat_sprite(45, 23, sprite)
                
                # Animation de danger
                if frame % 2 == 0:
                    self.oled.text("!", 25, 45)
                    self.oled.text("!", 80, 43)
                
                self.oled.show()
                time.sleep(0.25)
    
    def draw_heart(self, x, y):
        """Dessine un petit coeur"""
        # Coeur 5x4 pixels
        heart = [
            0b01010,
            0b11111,
            0b11111,
            0b01110,
            0b00100
        ]
        
        for row in range(5):
            byte_data = heart[row]
            for col in range(5):
                if byte_data & (1 << (4 - col)):
                    self.oled.pixel(x + col, y + row, 1)
    
    def draw_config_screen(self, step, message, extra_info="", show_config=True):
        """Écran de configuration - N'affiche QUE si première connexion ou internet perdu"""
        self.oled.fill(0)
        
        # N'afficher l'écran de config QUE si nécessaire
        if show_config and (step == "initial_setup" or step == "internet_lost" or step == "first_boot"):
            # Écran de configuration principal
            self.oled.text("Pour configurer", 10, 15)
            self.oled.text("votre My Pico,", 12, 25)
            self.oled.text("rendez-vous sur", 8, 35)
            self.oled.text("mypico.fr", 28, 45)
        else:
            # Pour les autres cas, affichage simple du message
            if message:
                self.oled.text(message, 5, 25)
            if extra_info:
                self.oled.text(extra_info, 5, 35)
        
        self.oled.show()
    
    def draw_internet_test_screen(self):
        """Écran de test internet simplifié"""
        self.oled.fill(0)
        
        # Message Houston centré
        self.oled.text("ici houston", 25, 20)
        self.oled.text("on cherche", 25, 30)
        self.oled.text("la wifi", 35, 40)
        
        # Petits points d'attente animés
        dots = "." * ((time.ticks_ms() // 500) % 4)
        self.oled.text(dots, 75, 40)
        
        self.oled.show()

def draw_main_display_with_mascot(oled, mascot, co2_ppm, status, emoji, wifi_status, server_status, display_config=None):
    """Interface principale avec configuration dynamique personnalisable"""
    
    # Configuration par défaut si pas fournie
    if display_config is None:
        display_config = {
            'header_text': 'My Pico',
            'show_wifi_status': True,
            'show_time': False,
            'show_air_quality_text': True,
            'wifi_display_mode': 'bars'
        }
    
    oled.fill(0)
    
    # En-tête personnalisable
    header_text = display_config.get('header_text', 'My Pico')
    # Centrer le texte selon sa longueur
    header_x = max(0, (128 - len(header_text) * 8) // 2)
    oled.text(header_text, header_x, 0)
    
    # Zone de statut (ligne du haut droite)
    status_line = ""
    
    # Affichage WiFi configurable
    if display_config.get('show_wifi_status', True):
        try:
            wlan = network.WLAN(network.STA_IF)
            rssi = wlan.status('rssi') if wlan.isconnected() else -100
            wifi_mode = display_config.get('wifi_display_mode', 'bars')
            wifi_display = get_wifi_display_for_mascot(wifi_mode, rssi, wifi_status)
            status_line += wifi_display
        except:
            status_line += "?"
    
    # Affichage heure si activé
    if display_config.get('show_time', False):
        if status_line:  # Ajouter un séparateur si il y a déjà du contenu
            status_line += " "
        status_line += get_current_time_display_for_mascot()
    
    # Icône Firebase/Serveur
    firebase_icon = "S" if server_status else "X"
    if status_line:
        status_line += " " + firebase_icon
    else:
        status_line = firebase_icon
    
    # Afficher la ligne de statut en haut à droite
    status_x = max(85, 128 - len(status_line) * 6)  # Ajuster selon la longueur
    oled.text(status_line, status_x, 0)
    
    oled.hline(0, 8, 128, 1)
    
    if co2_ppm is not None:
        # MESURE PPM - centrée et bien visible
        ppm_text = f"{co2_ppm} ppm"
        text_x = (128 - len(ppm_text) * 8) // 2
        oled.text(ppm_text, text_x, 20)
        
        # Affichage qualité d'air configurable
        if display_config.get('show_air_quality_text', True):
            # STATUT - centré sous les PPM
            status_x = (128 - len(status) * 8) // 2
            oled.text(status, status_x, 35)
        
    else:
        # Erreur capteur
        oled.text("CAPTEUR ERREUR", 15, 25)
    
    oled.show()


def get_wifi_display_for_mascot(mode, rssi, wifi_connected):
    """Génère l'affichage WiFi pour la mascotte selon le mode choisi"""
    if not wifi_connected:
        return "X" if mode == 'icon' else "OFF"
    
    if mode == 'bars':
        if rssi >= -50:
            return "||||"  # 4 barres
        elif rssi >= -60:
            return "|||"   # 3 barres  
        elif rssi >= -70:
            return "||"    # 2 barres
        elif rssi >= -80:
            return "|"     # 1 barre
        else:
            return ""      # Aucune barre
    elif mode == 'icon':
        return "W"
    else:  # mode == 'text'
        if rssi >= -50:
            return "EXC"
        elif rssi >= -60:
            return "BON"
        elif rssi >= -70:
            return "MOY"
        elif rssi >= -80:
            return "FAIB"
        else:
            return "TRES"


def get_current_time_display_for_mascot():
    """Retourne l'heure actuelle formatée pour l'affichage mascotte"""
    try:
        t = time.localtime()
        if t[0] >= 2024:  # Heure valide
            return f"{t[3]:02d}:{t[4]:02d}"
        else:
            # Utiliser uptime approximatif - temps depuis démarrage en heures:minutes
            uptime_seconds = int(time.time())
            uptime_minutes = uptime_seconds // 60
            hours = (uptime_minutes // 60) % 24  # Modulo 24 pour format heure
            mins = uptime_minutes % 60
            return f"{hours:02d}:{mins:02d}"
    except:
        return "--:--"

def get_co2_tip(co2_ppm, animation_time):
    """Retourne un petit conseil discret selon le niveau de CO2"""
    
    # Conseils courts et discrets
    if co2_ppm < 600:
        tips = ["Excellent", "Parfait", "Ideal", "Top"]
        return tips[(animation_time // 120) % len(tips)]
    
    elif co2_ppm < 1000:
        tips = ["Correct", "OK", "Bien", "Normal"]
        return tips[(animation_time // 120) % len(tips)]
    
    elif co2_ppm < 1500:
        tips = ["Aerez", "Ventilez", "Ouvrez", "Air frais"]
        return tips[(animation_time // 100) % len(tips)]
    
    else:
        tips = ["URGENT", "AEREZ!", "DANGER", "SORTEZ"]
        return tips[(animation_time // 80) % len(tips)]

def draw_tip_text(oled, tip_text):
    """Affiche un petit tip discret en bas à droite"""
    # Juste un petit texte discret, pas de gros pavé !
    tip_x = 128 - len(tip_text) * 6 - 2  # Aligné à droite
    oled.text(tip_text, tip_x, 56) 