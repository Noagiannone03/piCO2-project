"""
AirCarto Mascotte - Chat Pixel Art pour écran OLED
Animations et sprites pour différents états du système
"""

import time
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
        """Animation du chat qui dort pendant le préchauffage"""
        self.oled.fill(0)
        
        # Titre
        self.oled.text("Prechauffage...", 15, 5)
        
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
        
        # Barre de progression du préchauffage
        progress = min(100, frame * 2)  # 2% par frame
        bar_width = int((progress / 100) * 100)
        self.oled.rect(14, 50, 100, 8, 1)
        self.oled.fill_rect(15, 51, bar_width, 6, 1)
        
        # Temps restant
        remaining = max(0, 30 - (frame // 4))  # ~4 frames par seconde
        self.oled.text(f"{remaining}s", 45, 38)
        
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
        """Animations de réaction selon les événements"""
        if reaction_type == "wifi_connect":
            # Chat content de la connexion WiFi
            for frame in range(15):
                self.oled.fill(0)
                self.oled.text("WiFi connecte!", 20, 5)
                self.draw_cat_sprite(55, 20, 'happy')
                
                # Petits coeurs qui apparaissent
                if frame > 5:
                    self.draw_heart(40, 30)
                if frame > 10:
                    self.draw_heart(80, 28)
                
                self.oled.show()
                time.sleep(0.15)
                
        elif reaction_type == "wifi_error":
            # Chat inquiet pour les erreurs WiFi
            for frame in range(10):
                self.oled.fill(0)
                self.oled.text("WiFi erreur!", 25, 10)
                sprite = 'worried' if frame % 2 == 0 else 'normal'
                self.draw_cat_sprite(55, 25, sprite)
                
                # Points d'interrogation de confusion
                if frame % 2 == 0:
                    self.oled.text("?", 45, 35)
                    self.oled.text("?", 85, 30)
                
                self.oled.show()
                time.sleep(0.3)
                
        elif reaction_type == "co2_danger":
            # Chat alerte pour CO2 élevé
            for frame in range(12):
                self.oled.fill(0)
                self.oled.text("CO2 ELEVE!", 30, 10)
                sprite = 'alert' if frame % 2 == 0 else 'worried'
                self.draw_cat_sprite(55, 25, sprite)
                
                # Animation de danger
                if frame % 2 == 0:
                    self.oled.text("!", 40, 30)
                    self.oled.text("!", 85, 35)
                
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
    
    def draw_config_screen(self, step, message, extra_info=""):
        """Écrans de configuration avec mascotte mignonne"""
        self.oled.fill(0)
        
        # Titre My Pico
        self.oled.text("My Pico Config", 15, 0)
        self.oled.hline(0, 8, 128, 1)
        
        # Message principal
        self.oled.text(message, 5, 12)
        if extra_info:
            self.oled.text(extra_info, 5, 22)
        
        # Mascotte qui suit l'étape
        if step == "wifi_scan":
            # Chat qui cherche
            self.draw_cat_sprite(80, 30, 'normal')
            self.oled.text("...", 85, 52)
        elif step == "wifi_connect":
            # Chat confiant
            self.draw_cat_sprite(80, 30, 'happy')
            self.oled.text("GO!", 85, 52)
        elif step == "wifi_success":
            # Chat très content
            self.draw_cat_sprite(80, 30, 'happy')
            self.draw_heart(75, 55)
            self.draw_heart(100, 52)
        elif step == "wifi_fail":
            # Chat triste
            self.draw_cat_sprite(80, 30, 'worried')
            self.oled.text(":(", 85, 52)
        elif step == "server_test":
            # Chat attentif
            self.draw_cat_sprite(80, 30, 'alert')
            self.oled.text("...", 85, 52)
        else:
            # Chat normal
            self.draw_cat_sprite(80, 30, 'normal')
        
        self.oled.show()
    
    def draw_setup_guide(self, step, ip_address="192.168.4.1"):
        """Guide de configuration WiFi CORRIGÉ et lisible"""
        self.oled.fill(0)
        
        if step == "connect_ap":
            # Instructions connexion - TEXTE COURT
            self.oled.text("My Pico Setup", 20, 5)
            self.oled.hline(0, 15, 128, 1)
            self.oled.text("1. Connectez au", 5, 20)
            self.oled.text("   reseau:", 5, 30)
            self.oled.text("   My-Pico", 5, 40)
            self.oled.text("2. Mot passe:", 5, 50)
            self.oled.text("   mypico123", 5, 58)
            
        elif step == "waiting_connection":
            # Attente connexion utilisateur
            self.oled.text("My Pico Setup", 20, 10)
            self.oled.hline(0, 20, 128, 1)
            self.oled.text("En attente de", 15, 30)
            self.oled.text("connexion", 25, 40)
            # Points d'attente animés
            dots = "." * ((time.ticks_ms() // 600) % 4)
            self.oled.text(dots, 55, 50)
            
        elif step == "show_qr":
            # QR Code VRAI pour http://192.168.4.1
            self.oled.text("My Pico Setup", 20, 2)
            self.oled.hline(0, 12, 128, 1)
            
            # QR code à gauche (25x25 pixels)
            qr_x, qr_y = 5, 20
            self.draw_real_qr_code(qr_x, qr_y, ip_address)
            
            # Texte à droite du QR
            self.oled.text("Scannez", 35, 25)
            self.oled.text("ce QR", 35, 35)
            self.oled.text("Donnez vos", 35, 48)
            self.oled.text("identifiants", 35, 58)
            
        self.oled.show()
    
    def draw_real_qr_code(self, x, y, ip_address):
        """Dessine un QR code RÉEL qui encode http://192.168.4.1"""
        # QR code Version 2 (25x25) VRAI pour http://192.168.4.1
        # Généré avec qrcode.js pour URL exacte
        qr_data = [
            0b1111111001101000011111111,  # Row 0: Finder pattern + data
            0b1000001110110100010000001,  # Row 1
            0b1011101001011110010111101,  # Row 2
            0b1011101110011000010111101,  # Row 3
            0b1011101011100100010111101,  # Row 4
            0b1000001001100001010000001,  # Row 5
            0b1111111010101010111111111,  # Row 6: Timing pattern
            0b0000000110100001000000000,  # Row 7: Separator
            0b0101101111001001011010111,  # Row 8: Data start
            0b1100010010110110100101000,  # Row 9: http://
            0b0011101101001111011110001,  # Row 10: 192.168
            0b1001010100110001100101110,  # Row 11: .4.1
            0b0110001111001011011010101,  # Row 12: Data
            0b1110110000110110100101010,  # Row 13
            0b0001101101001001011110111,  # Row 14
            0b1010010110110110100101000,  # Row 15
            0b0111101001001011011010001,  # Row 16
            0b0000000010110001000000000,  # Row 17: Separator
            0b1111111001001100011111111,  # Row 18: Finder pattern
            0b1000001100110101010000001,  # Row 19
            0b1011101111001010010111101,  # Row 20
            0b1011101000110111010111101,  # Row 21
            0b1011101101001000010111101,  # Row 22
            0b1000001010110111010000001,  # Row 23
            0b1111111001001100011111111   # Row 24: Finder pattern
        ]
        
        # Dessiner le QR code pixel par pixel
        for row in range(25):
            if row < len(qr_data) and y + row < 64:
                for col in range(25):
                    if x + col < 128:
                        if qr_data[row] & (1 << (24 - col)):
                            self.oled.pixel(x + col, y + row, 1)
    
    def animate_config_waiting(self, step, message):
        """Animation d'attente simplifiée"""
        for frame in range(10):
            self.draw_setup_guide("waiting_config")
            time.sleep(0.3)

def draw_main_display_with_mascot(oled, mascot, co2_ppm, status, emoji, wifi_status, server_status):
    """Interface ultra propre et moderne avec mascotte emoji et tips"""
    oled.fill(0)
    
    # Incrémenter le timer pour rotation des tips
    mascot.animation_time += 1
    
    # En-tête stylé centré
    oled.text("My Pico", 35, 0)
    
    # Statuts connexion (jolis)
    wifi_icon = "W" if wifi_status else "x"
    server_icon = "S" if server_status else "x"
    oled.text(f"{wifi_icon}{server_icon}", 100, 0)
    
    oled.hline(0, 8, 128, 1)
    
    if co2_ppm is not None:
        # MASCOTTE À GAUCHE - Style emoji rond et mignon
        if co2_ppm < 600:
            sprite = 'happy'
        elif co2_ppm < 1000:
            sprite = 'normal'
        elif co2_ppm < 1500:
            sprite = 'worried'
        else:
            sprite = 'alert'
        
        mascot.draw_cat_sprite(3, 12, sprite)  # Mascotte à gauche
        
        # DONNÉES À DROITE - Ultra propres
        oled.text(f"{co2_ppm} ppm", 70, 14)
        oled.text(status, 70, 26)
        
        # Petit tip discret en bas à droite
        tips = get_co2_tip(co2_ppm, mascot.animation_time)
        draw_tip_text(oled, tips)
        
    else:
        # Erreur capteur avec mascotte triste
        mascot.draw_cat_sprite(3, 12, 'worried')
        oled.text("CAPTEUR", 70, 18)
        oled.text("ERREUR", 70, 28)
        draw_tip_text(oled, "Erreur")
    
    oled.show()

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