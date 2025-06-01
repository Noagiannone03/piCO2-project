"""
AirCarto Mascotte Simple - Version ASCII
Alternative simple avec caractères pour écrans plus petits
"""

import time
import random

class SimpleMascot:
    def __init__(self, oled):
        self.oled = oled
        self.x = 90
        self.y = 35
        self.expression = "happy"
        self.blink_timer = 0
        self.last_blink = 0
        
    def update_expression(self, co2_ppm):
        """Expression selon CO2"""
        if co2_ppm is None:
            self.expression = "confused"
        elif co2_ppm < 500:
            self.expression = "happy"
        elif co2_ppm < 1000:
            self.expression = "worried"
        else:
            self.expression = "panic"
    
    def draw(self):
        """Dessine la mascotte avec des caractères"""
        current_time = time.ticks_ms()
        
        # Clignement aléatoire
        is_blinking = False
        if current_time - self.last_blink > 3000:
            if random.randint(0, 10) > 8:
                is_blinking = True
                self.last_blink = current_time
        
        # Dessiner la face selon l'expression
        if self.expression == "happy":
            if is_blinking:
                self.oled.text("(-.-)", self.x, self.y)      # Cligne
            else:
                self.oled.text("(^.^)", self.x, self.y)      # Content
            self.oled.text(" \\./", self.x, self.y + 8)     # Sourire
            
        elif self.expression == "worried":
            if is_blinking:
                self.oled.text("(-.-)", self.x, self.y)
            else:
                self.oled.text("(o.o)", self.x, self.y)      # Inquiet
            self.oled.text(" ___", self.x, self.y + 8)      # Bouche droite
            
        elif self.expression == "panic":
            if is_blinking:
                self.oled.text("(X.X)", self.x, self.y)      # Mort de peur
            else:
                self.oled.text("(@.@)", self.x, self.y)      # Paniqué
            self.oled.text(" oOo", self.x, self.y + 8)      # Bouche ouverte
            
        else:  # confused
            self.oled.text("(?.?)", self.x, self.y)          # Confus
            self.oled.text(" ___", self.x, self.y + 8)
    
    def get_message(self, co2_ppm):
        """Messages courts"""
        if co2_ppm is None:
            return "???"
        elif co2_ppm < 500:
            return "Cool!"
        elif co2_ppm < 1000:
            return "Bof..."
        else:
            return "HELP!"

def draw_simple_display(oled, mascot, co2_ppm, status, wifi_status, server_status):
    """Affichage avec mascotte simple"""
    if not oled:
        return
        
    oled.fill(0)
    
    # Titre
    oled.text("AirCarto", 25, 0)
    
    # Statuts
    icons = ("W" if wifi_status else "x") + ("S" if server_status else "-")
    oled.text(icons, 100, 0)
    
    oled.hline(0, 8, 128, 1)
    
    # CO2 à gauche
    if co2_ppm is not None:
        oled.text(f"{co2_ppm}", 5, 12)
        oled.text("ppm", 5, 22)
        oled.text(status[:6], 5, 32)
    else:
        oled.text("ERROR", 5, 20)
    
    # Mascotte
    mascot.update_expression(co2_ppm)
    mascot.draw()
    
    # Message
    msg = mascot.get_message(co2_ppm)
    oled.text(msg, 5, 56)
    
    oled.show() 