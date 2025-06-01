"""
AirCarto Mascotte - Système d'animation pour la mascotte chat
Animations réactives basées sur les niveaux de CO2 et événements
"""

import time
import random

class AirCartoMascot:
    def __init__(self, oled):
        self.oled = oled
        self.x = 100  # Position X de la mascotte
        self.y = 45   # Position Y de la mascotte
        self.frame = 0
        self.animation_speed = 0
        self.current_state = "idle"
        self.last_update = time.ticks_ms()
        self.blink_timer = 0
        self.expression = "happy"
        
        # Sprites de la mascotte (16x16 pixels)
        self.sprites = {
            # Chat normal - yeux ouverts
            "idle_1": [
                0b0000011111100000,
                0b0000111111110000,
                0b0001111111111000,
                0b0011111111111100,
                0b0011100110111100,
                0b0111100110011110,
                0b0111111111111110,
                0b0111111001111110,
                0b0111110000111110,
                0b0111111001111110,
                0b0011111111111100,
                0b0001111111111000,
                0b0000111111110000,
                0b0000011111100000,
                0b0000000000000000,
                0b0000000000000000,
            ],
            
            # Chat qui cligne
            "blink": [
                0b0000011111100000,
                0b0000111111110000,
                0b0001111111111000,
                0b0011111111111100,
                0b0011111111111100,
                0b0111111111111110,
                0b0111111111111110,
                0b0111111001111110,
                0b0111110000111110,
                0b0111111001111110,
                0b0011111111111100,
                0b0001111111111000,
                0b0000111111110000,
                0b0000011111100000,
                0b0000000000000000,
                0b0000000000000000,
            ],
            
            # Chat content (CO2 bon)
            "happy": [
                0b0000011111100000,
                0b0000111111110000,
                0b0001111111111000,
                0b0011111111111100,
                0b0011100110111100,
                0b0111100110011110,
                0b0111111111111110,
                0b0111111001111110,
                0b0111110000111110,
                0b0111111001111110,
                0b0011111111111100,
                0b0001111111111000,
                0b0000111111110000,
                0b0000011111100000,
                0b0000001111000000,
                0b0000000110000000,
            ],
            
            # Chat inquiet (CO2 moyen)
            "worried": [
                0b0000011111100000,
                0b0000111111110000,
                0b0001111111111000,
                0b0011111111111100,
                0b0011101101111100,
                0b0111101101011110,
                0b0111111111111110,
                0b0111111001111110,
                0b0111110000111110,
                0b0111110110111110,
                0b0011111111111100,
                0b0001111111111000,
                0b0000111111110000,
                0b0000011111100000,
                0b0000000000000000,
                0b0000000000000000,
            ],
            
            # Chat paniqué (CO2 danger)
            "panic": [
                0b0000011111100000,
                0b0000111111110000,
                0b0001111111111000,
                0b0011111111111100,
                0b0011010010111100,
                0b0111010010011110,
                0b0111111111111110,
                0b0111110110111110,
                0b0111101001011110,
                0b0111110110111110,
                0b0011111111111100,
                0b0001111111111000,
                0b0000111111110000,
                0b0000011111100000,
                0b0000000000000000,
                0b0000000000000000,
            ],
            
            # Chat qui dort (mode veille)
            "sleep": [
                0b0000011111100000,
                0b0000111111110000,
                0b0001111111111000,
                0b0011111111111100,
                0b0011111111111100,
                0b0111111111111110,
                0b0111111111111110,
                0b0111111001111110,
                0b0111110000111110,
                0b0111111001111110,
                0b0011111111111100,
                0b0001111111111000,
                0b0000111111110000,
                0b0000011111100000,
                0b0000001010100000,
                0b0000000101000000,
            ],
        }
        
        # Petites animations d'émoticônes
        self.emoticons = {
            "heart": [  # Coeur (air excellent)
                0b0110011000000000,
                0b1111111100000000,
                0b1111111100000000,
                0b0111111000000000,
                0b0011110000000000,
                0b0001100000000000,
            ],
            "exclamation": [  # Point d'exclamation (danger)
                0b0011000000000000,
                0b0011000000000000,
                0b0011000000000000,
                0b0011000000000000,
                0b0000000000000000,
                0b0011000000000000,
            ],
            "question": [  # Point d'interrogation (erreur)
                0b0111100000000000,
                0b1100110000000000,
                0b0001100000000000,
                0b0011000000000000,
                0b0000000000000000,
                0b0011000000000000,
            ]
        }

    def draw_sprite(self, sprite_data, x, y):
        """Dessine un sprite à la position donnée"""
        for row, line in enumerate(sprite_data):
            for col in range(16):
                if line & (1 << (15 - col)):
                    self.oled.pixel(x + col, y + row, 1)

    def draw_small_sprite(self, sprite_data, x, y):
        """Dessine un petit sprite (émoticône)"""
        for row, line in enumerate(sprite_data):
            for col in range(8):
                if line & (1 << (15 - col)):
                    self.oled.pixel(x + col, y + row, 1)

    def update_expression(self, co2_ppm):
        """Met à jour l'expression selon le CO2"""
        if co2_ppm is None:
            self.expression = "worried"
        elif co2_ppm < 400:
            self.expression = "happy"
        elif co2_ppm < 600:
            self.expression = "happy"
        elif co2_ppm < 1000:
            self.expression = "worried"
        else:
            self.expression = "panic"

    def animate_idle(self):
        """Animation de base - clignement occasionnel"""
        current_time = time.ticks_ms()
        
        # Clignement aléatoire
        if current_time - self.blink_timer > 3000:  # Toutes les 3 secondes
            if random.randint(0, 10) > 7:  # 30% de chance
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
            if current_time - self.last_update > 200:
                self.current_state = "idle"
        elif self.current_state == "happy_bounce":
            if current_time - self.last_update > 100:
                self.frame += 1
                if self.frame > 6:
                    self.current_state = "idle"
        elif self.current_state == "shake":
            if current_time - self.last_update > 80:
                self.frame += 1
                if self.frame > 8:
                    self.current_state = "idle"
        elif self.current_state == "panic_wave":
            if current_time - self.last_update > 150:
                self.frame += 1
                if self.frame > 10:
                    self.current_state = "idle"
        
        self.last_update = current_time

    def draw(self):
        """Dessine la mascotte sur l'écran"""
        # Position de base
        draw_x = self.x
        draw_y = self.y
        
        # Ajustements selon l'animation
        if self.current_state == "happy_bounce":
            draw_y -= abs(3 - self.frame) if self.frame < 6 else 0
        elif self.current_state == "shake":
            draw_x += (self.frame % 2) * 2 - 1
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
            sprite = "idle_1"
        
        # Dessiner la mascotte
        self.draw_sprite(self.sprites[sprite], draw_x, draw_y)
        
        # Ajouter des émoticônes selon le contexte
        if self.expression == "happy" and self.current_state == "idle":
            if random.randint(0, 100) > 95:  # Rare apparition de coeur
                self.draw_small_sprite(self.emoticons["heart"], draw_x - 10, draw_y - 8)
        elif self.expression == "panic":
            self.draw_small_sprite(self.emoticons["exclamation"], draw_x + 18, draw_y - 5)

    def get_status_message(self, co2_ppm):
        """Retourne un message de la mascotte selon le CO2"""
        if co2_ppm is None:
            return "Miaou? Capteur?"
        elif co2_ppm < 400:
            return "Ronron! Air pur!"
        elif co2_ppm < 600:
            return "Miaou! C'est bon!"
        elif co2_ppm < 1000:
            return "Miau... Aerer?"
        elif co2_ppm < 1500:
            return "MIAOUU! Danger!"
        else:
            return "MAYDAY MAYDAY!"

# =====================================================
# INTÉGRATION DANS L'AFFICHAGE PRINCIPAL
# =====================================================

def draw_main_display_with_mascot(oled, mascot, co2_ppm, status, emoji, wifi_status, server_status):
    """Affichage principal avec mascotte"""
    if not oled:
        return
        
    oled.fill(0)
    
    # En-tête compact
    oled.text("AirCarto", 0, 0)
    
    # Statuts connexion (plus compacts)
    wifi_icon = "W" if wifi_status else "X"
    server_icon = "S" if server_status else "-"
    oled.text(f"{wifi_icon}{server_icon}", 110, 0)
    
    oled.hline(0, 8, 128, 1)
    
    # Zone CO2 (côté gauche)
    if co2_ppm is not None:
        # Valeur CO2 (plus petite pour laisser place à la mascotte)
        if co2_ppm < 1000:
            oled.text(f"{co2_ppm}ppm", 0, 12)
        else:
            oled.text(f"{co2_ppm}", 0, 12)
            oled.text("ppm", 0, 22)
        
        # Statut air
        oled.text(status[:8], 0, 32)  # Tronquer si trop long
        
        # Barre de niveau (plus courte)
        bar_width = min(70, int((co2_ppm / 2000) * 70))
        oled.fill_rect(0, 42, bar_width, 4, 1)
        oled.rect(0, 42, 70, 4, 1)
        
    else:
        oled.text("CAPTEUR", 0, 15)
        oled.text("ERREUR", 0, 25)
    
    # Mettre à jour et dessiner la mascotte
    mascot.update(co2_ppm, wifi_status, server_status)
    mascot.draw()
    
    # Message de la mascotte (en bas)
    msg = mascot.get_status_message(co2_ppm)
    oled.text(msg[:18], 0, 56)  # Max 18 caractères
    
    oled.show() 