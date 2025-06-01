"""
AirCarto Mascotte v2 - Sprites améliorés
Sprites plus jolis et plus expressifs pour la mascotte chat
"""

import time
import random

class AirCartoMascotImproved:
    def __init__(self, oled):
        self.oled = oled
        self.x = 96   # Position X (plus à droite)
        self.y = 40   # Position Y 
        self.frame = 0
        self.current_state = "idle"
        self.last_update = time.ticks_ms()
        self.blink_timer = 0
        self.expression = "happy"
        
        # Sprites améliorés 16x16 pixels - Plus mignons !
        self.sprites = {
            # Chat content - yeux ronds
            "happy": [
                0b0000000000000000,  # Ligne 0
                0b0000011111100000,  # Ligne 1 - Haut de la tête
                0b0001111111111000,  # Ligne 2 
                0b0011111111111100,  # Ligne 3
                0b0111111111111110,  # Ligne 4
                0b0111011111101110,  # Ligne 5 - Oreilles
                0b1111011111101111,  # Ligne 6 
                0b1111110110111111,  # Ligne 7 - Yeux
                0b1111110110111111,  # Ligne 8 - Yeux
                0b1111111111111111,  # Ligne 9
                0b1111111001111111,  # Ligne 10 - Nez
                0b1111110000111111,  # Ligne 11 - Bouche souriante
                0b0111111111111110,  # Ligne 12
                0b0011111111111100,  # Ligne 13
                0b0001111111111000,  # Ligne 14
                0b0000011111100000,  # Ligne 15
            ],
            
            # Chat qui cligne
            "blink": [
                0b0000000000000000,
                0b0000011111100000,
                0b0001111111111000,
                0b0011111111111100,
                0b0111111111111110,
                0b0111011111101110,
                0b1111011111101111,
                0b1111111111111111,  # Yeux fermés (lignes pleines)
                0b1111111111111111,  # Yeux fermés
                0b1111111111111111,
                0b1111111001111111,
                0b1111110000111111,
                0b0111111111111110,
                0b0011111111111100,
                0b0001111111111000,
                0b0000011111100000,
            ],
            
            # Chat inquiet
            "worried": [
                0b0000000000000000,
                0b0000011111100000,
                0b0001111111111000,
                0b0011111111111100,
                0b0111111111111110,
                0b0111011111101110,
                0b1111011111101111,
                0b1111100110011111,  # Yeux inquiets (plus petits)
                0b1111110110111111,
                0b1111111111111111,
                0b1111111001111111,
                0b1111111111111111,  # Bouche droite (neutre)
                0b0111111111111110,
                0b0011111111111100,
                0b0001111111111000,
                0b0000011111100000,
            ],
            
            # Chat paniqué
            "panic": [
                0b0000000000000000,
                0b0000011111100000,
                0b0001111111111000,
                0b0011111111111100,
                0b0111111111111110,
                0b0111011111101110,
                0b1111011111101111,
                0b1111001100111111,  # Yeux très petits (stress)
                0b1111100110011111,
                0b1111111111111111,
                0b1111111001111111,
                0b1111100000011111,  # Bouche ouverte (choqué)
                0b0111111111111110,
                0b0011111111111100,
                0b0001111111111000,
                0b0000011111100000,
            ],
            
            # Chat qui dort
            "sleep": [
                0b0000000000000000,
                0b0000011111100000,
                0b0001111111111000,
                0b0011111111111100,
                0b0111111111111110,
                0b0111011111101110,
                0b1111011111101111,
                0b1111111111111111,  # Yeux fermés
                0b1111111111111111,
                0b1111111111111111,
                0b1111111001111111,
                0b1111111001111111,  # Bouche petite (dodo)
                0b0111111111111110,
                0b0011111111111100,
                0b0001111111111000,
                0b0000011111100000,
            ],
        }
        
        # Émoticônes améliorées
        self.emoticons = {
            # Coeur plus joli
            "heart": [
                0b0110011000000000,
                0b1111111100000000,
                0b1111111100000000,
                0b0111111000000000,
                0b0011110000000000,
                0b0001100000000000,
            ],
            
            # Point d'exclamation
            "exclamation": [
                0b0110000000000000,
                0b1111000000000000,
                0b1111000000000000,
                0b1111000000000000,
                0b0110000000000000,
                0b0000000000000000,
                0b1111000000000000,
                0b1111000000000000,
            ],
            
            # Z Z Z (dodo)
            "zzz": [
                0b1111000000000000,
                0b0001000000000000,
                0b0010000000000000,
                0b0100000000000000,
                0b1111000000000000,
                0b0000000000000000,
                0b0110000000000000,
                0b1001000000000000,
            ],
        }

    def draw_sprite(self, sprite_data, x, y):
        """Dessine un sprite à la position donnée"""
        for row, line in enumerate(sprite_data):
            for col in range(16):
                if line & (1 << (15 - col)):
                    if 0 <= x + col < 128 and 0 <= y + row < 64:  # Vérifier les limites
                        self.oled.pixel(x + col, y + row, 1)

    def draw_small_sprite(self, sprite_data, x, y):
        """Dessine un petit sprite (émoticône)"""
        for row, line in enumerate(sprite_data):
            for col in range(8):
                if line & (1 << (15 - col)):
                    if 0 <= x + col < 128 and 0 <= y + row < 64:
                        self.oled.pixel(x + col, y + row, 1)

    def update_expression(self, co2_ppm):
        """Met à jour l'expression selon le CO2"""
        if co2_ppm is None:
            self.expression = "worried"
        elif co2_ppm < 500:
            self.expression = "happy"
        elif co2_ppm < 1000:
            self.expression = "worried"
        else:
            self.expression = "panic"

    def animate_idle(self):
        """Animation de base - clignement occasionnel"""
        current_time = time.ticks_ms()
        
        # Clignement aléatoire
        if current_time - self.blink_timer > 2000:  # Toutes les 2 secondes
            if random.randint(0, 10) > 8:  # 20% de chance
                self.current_state = "blink"
                self.frame = 0
                self.blink_timer = current_time

    def animate_reaction(self, event):
        """Déclenche une animation de réaction"""
        if event == "wifi_connect":
            self.current_state = "happy_bounce"
            self.frame = 0
        elif event == "wifi_error":
            self.current_state = "shake"
            self.frame = 0
        elif event == "co2_danger":
            self.current_state = "panic_wave"
            self.frame = 0

    def update(self, co2_ppm=None, wifi_status=None, server_status=None):
        """Met à jour l'animation de la mascotte"""
        current_time = time.ticks_ms()
        
        # Mettre à jour l'expression
        if co2_ppm is not None:
            self.update_expression(co2_ppm)
        
        # Animation selon l'état
        if self.current_state == "idle":
            self.animate_idle()
        elif self.current_state == "blink":
            if current_time - self.last_update > 300:
                self.current_state = "idle"
        elif self.current_state == "happy_bounce":
            if current_time - self.last_update > 150:
                self.frame += 1
                if self.frame > 4:
                    self.current_state = "idle"
        elif self.current_state == "shake":
            if current_time - self.last_update > 100:
                self.frame += 1
                if self.frame > 6:
                    self.current_state = "idle"
        elif self.current_state == "panic_wave":
            if current_time - self.last_update > 200:
                self.frame += 1
                if self.frame > 8:
                    self.current_state = "idle"
        
        self.last_update = current_time

    def draw(self):
        """Dessine la mascotte sur l'écran"""
        # Position de base
        draw_x = self.x
        draw_y = self.y
        
        # Ajustements selon l'animation
        if self.current_state == "happy_bounce":
            draw_y -= (self.frame % 2) * 2  # Rebond simple
        elif self.current_state == "shake":
            draw_x += (self.frame % 2) * 2 - 1  # Tremblement
        elif self.current_state == "panic_wave":
            draw_x += int(2 * (0.5 - abs(0.5 - (self.frame % 4) / 4)))
        
        # Sélectionner le sprite
        if self.current_state == "blink":
            sprite = "blink"
        elif self.expression == "panic":
            sprite = "panic"
        elif self.expression == "worried":
            sprite = "worried"
        elif self.expression == "happy":
            sprite = "happy"
        else:
            sprite = "happy"
        
        # Dessiner la mascotte
        self.draw_sprite(self.sprites[sprite], draw_x, draw_y)
        
        # Ajouter des émoticônes selon le contexte
        if self.expression == "happy" and self.current_state == "idle":
            if random.randint(0, 200) > 195:  # Rare apparition de coeur
                self.draw_small_sprite(self.emoticons["heart"], draw_x - 12, draw_y - 10)
        elif self.expression == "panic":
            self.draw_small_sprite(self.emoticons["exclamation"], draw_x + 18, draw_y - 8)

    def get_status_message(self, co2_ppm):
        """Messages plus variés selon le CO2"""
        if co2_ppm is None:
            messages = ["Capteur?", "Miaou?", "Bug..."]
        elif co2_ppm < 400:
            messages = ["Ronron!", "Air pur!", "Perfect!", "Top!"]
        elif co2_ppm < 600:
            messages = ["C'est bon!", "Miaou OK", "Cool!"]
        elif co2_ppm < 1000:
            messages = ["Aerer?", "Mouais...", "Bof"]
        elif co2_ppm < 1500:
            messages = ["DANGER!", "MIAOUU!", "Help!"]
        else:
            messages = ["MAYDAY!", "FUITE!", "SOS!"]
        
        return random.choice(messages)

# =====================================================
# AFFICHAGE PRINCIPAL AMÉLIORÉ
# =====================================================

def draw_main_display_with_mascot_v2(oled, mascot, co2_ppm, status, emoji, wifi_status, server_status):
    """Affichage principal avec mascotte améliorée"""
    if not oled:
        return
        
    oled.fill(0)
    
    # En-tête plus joli
    oled.text("AirCarto", 20, 0)
    
    # Statuts connexion avec icônes
    wifi_icon = "W" if wifi_status else "x"
    server_icon = "S" if server_status else "-"
    oled.text(f"{wifi_icon}{server_icon}", 100, 0)
    
    # Ligne de séparation
    oled.hline(0, 8, 128, 1)
    
    # Zone CO2 compacte (gauche)
    if co2_ppm is not None:
        # Grosse valeur CO2
        co2_str = str(co2_ppm)
        oled.text(co2_str, 5, 12)
        oled.text("ppm", 5, 22)
        
        # Statut plus compact
        status_short = status[:6]  # Tronquer
        oled.text(status_short, 5, 32)
        
        # Barre de niveau stylée
        bar_width = min(60, int((co2_ppm / 2000) * 60))
        # Contour
        oled.rect(5, 42, 65, 6, 1)
        # Remplissage selon niveau
        if co2_ppm < 600:
            # Vert (plein)
            oled.fill_rect(6, 43, bar_width, 4, 1)
        elif co2_ppm < 1000:
            # Orange (hachuré)
            for i in range(0, bar_width, 2):
                oled.vline(6 + i, 43, 4, 1)
        else:
            # Rouge (clignotant)
            if time.ticks_ms() % 1000 < 500:
                oled.fill_rect(6, 43, bar_width, 4, 1)
        
    else:
        oled.text("CAPTEUR", 5, 15)
        oled.text("ERREUR", 5, 25)
        oled.rect(5, 35, 40, 8, 1)
        oled.text("X", 20, 37)
    
    # Mettre à jour et dessiner la mascotte
    mascot.update(co2_ppm, wifi_status, server_status)
    mascot.draw()
    
    # Message de la mascotte en bas
    msg = mascot.get_status_message(co2_ppm)
    oled.text(msg, 5, 56)
    
    # Timestamp discret
    uptime = time.ticks_ms() // 1000
    oled.text(f"{uptime}s", 100, 56)
    
    oled.show() 