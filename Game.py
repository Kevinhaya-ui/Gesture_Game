import pygame
import sys
import main  
import math
import random

pygame.init()

SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Kevin Afkar Haya - 5024251016")
clock = pygame.time.Clock()

# ==========================================
# KELAS PLAYER (Karakter Utama)
# ==========================================
class Player:
    def __init__(self):
        self.sprite_sheet = pygame.image.load("Assets/keafhaa.png").convert_alpha()
        
        self.sprite_attack = pygame.image.load("Assets/keafhaa_attacking.png").convert_alpha()
        self.sprite_attack = pygame.transform.scale(self.sprite_attack, (32, 32))
        
        self.frame_width = 64
        self.frame_height = 64
        
        self.animations = {
            "down": [],  
            "left": [],  
            "right": [], 
            "up": []     
        }
        
        directions = ["down", "left", "right", "up"]
        for row in range(4):
            direction_name = directions[row]
            for col in range(4):
                cut_rect = pygame.Rect(col * self.frame_width, row * self.frame_height, self.frame_width, self.frame_height)
                single_frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA).convert_alpha()
                single_frame.blit(self.sprite_sheet, (0, 0), cut_rect)
                single_frame = pygame.transform.scale(single_frame, (32, 32))
                self.animations[direction_name].append(single_frame)
        
        self.current_direction = "down" 
        self.current_frame = 0          
        self.rect = self.animations["down"][0].get_rect() #kotak frame deteksi tabrakan
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        self.exact_x = float(self.rect.x)
        self.exact_y = float(self.rect.y)
        
        self.move_speed = 3.0        
        self.animation_speed = 0.1    
        self.frame_timer = 0.0        
        self.is_moving = False
        
        self.is_attacking = False
        self.attack_timer = 0
        self.attack_duration = 30
    
    def trigger_attack(self):
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = self.attack_duration        

    def update(self, direction):
        self.is_moving = False
        
        if self.is_attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.is_attacking = False
            return
        
        if direction is not None:
            self.is_moving = True
            self.current_direction = direction 
            
            if direction == "up":
                self.exact_y -= self.move_speed
            elif direction == "down":
                self.exact_y += self.move_speed
            elif direction == "left":
                self.exact_x -= self.move_speed
            elif direction == "right":
                self.exact_x += self.move_speed
            
            self.exact_x = max(0, min(self.exact_x, SCREEN_WIDTH - self.rect.width))
            self.exact_y = max(0, min(self.exact_y, SCREEN_HEIGHT - self.rect.height))
            
            self.rect.x = int(self.exact_x)
            self.rect.y = int(self.exact_y)

        if self.is_moving:
            self.frame_timer += self.animation_speed
            if self.frame_timer >= 1.0:
                self.frame_timer = 0.0
                self.current_frame = (self.current_frame + 1) % 4
        else:
            self.current_frame = 0
            self.frame_timer = 0.0

    def draw(self, surface, is_battle=False):
        if self.is_attacking:
            current_image = self.sprite_attack
            if self.current_direction == "left":
                current_image = pygame.transform.flip(current_image, True, False)
        else:
            current_image = self.animations[self.current_direction][self.current_frame]
            
        if is_battle:
            bigger_image = pygame.transform.scale(current_image, (56, 56))
            draw_rect = bigger_image.get_rect(center=self.rect.center)
            surface.blit(bigger_image, draw_rect)
        else:
            surface.blit(current_image, self.rect)

# ==========================================
# KELAS COMPANION (Vanola)
# ==========================================
class Companion:
    def __init__(self, sprite_path):
        self.sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
        self.frame_width = 64
        self.frame_height = 64
        self.animations = {"down": [], "left": [], "right": [], "up": []}
        
        directions = ["down", "left", "right", "up"]
        for row in range(4):
            direction_name = directions[row]
            for col in range(4):
                cut_rect = pygame.Rect(col * self.frame_width, row * self.frame_height, self.frame_width, self.frame_height)
                single_frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA).convert_alpha()
                single_frame.blit(self.sprite_sheet, (0, 0), cut_rect)
                single_frame = pygame.transform.scale(single_frame, (32, 32))
                self.animations[direction_name].append(single_frame)
        
        self.current_direction = "down" 
        self.current_frame = 0          
        self.rect = self.animations["down"][0].get_rect()
        
        self.exact_x = 0.0
        self.exact_y = 0.0
        
        self.move_speed = 3.0 
        self.animation_speed = 0.1    
        self.frame_timer = 0.0        
        self.is_moving = False
        
        self.history_positions = []
        self.follow_delay = 15 

    def set_initial_position(self, start_x, start_y):
        self.exact_x = float(start_x)
        self.exact_y = float(start_y)
        self.rect.x = int(self.exact_x)
        self.rect.y = int(self.exact_y)
        self.history_positions = [(self.exact_x, self.exact_y, "down")] * self.follow_delay

    def update(self, leader_x, leader_y, leader_direction, leader_is_moving):
        if leader_is_moving:
            self.history_positions.append((leader_x, leader_y, leader_direction))
            
        if len(self.history_positions) > self.follow_delay:
            target_x, target_y, target_dir = self.history_positions.pop(0)
            
            if (self.exact_x != target_x) or (self.exact_y != target_y):
                self.is_moving = True
                self.current_direction = target_dir
                
                self.exact_x = target_x
                self.exact_y = target_y
                self.rect.x = int(self.exact_x)
                self.rect.y = int(self.exact_y)
            else:
                self.is_moving = False
        else:
            self.is_moving = False

        if self.is_moving:
            self.frame_timer += self.animation_speed
            if self.frame_timer >= 1.0:
                self.frame_timer = 0.0
                self.current_frame = (self.current_frame + 1) % 4
        else:
            self.current_frame = 0
            self.frame_timer = 0.0

    def draw(self, surface, is_battle=False):
        current_image = self.animations[self.current_direction][self.current_frame]
        if is_battle:
            bigger_image = pygame.transform.scale(current_image, (56, 56))
            draw_rect = bigger_image.get_rect(center=self.rect.center)
            surface.blit(bigger_image, draw_rect)
        else:
            surface.blit(current_image, self.rect)

# ==========================================
# KELAS HOME (Sistem Menu & UI)
# ==========================================
class Home:
    def __init__(self):
        self.state = "menu"
        
        self.background3    = pygame.image.load("Assets/swampmap.png").convert_alpha()
        # PERBAIKAN: SCREEN WIDTH sekarang menggunakan garis bawah agar tidak error syntax
        self.swamp_map      = pygame.transform.scale(self.background3, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.transition_img = pygame.image.load("Assets/transition.png").convert_alpha()
        self.transition_img = pygame.transform.scale(self.transition_img, (683, 683))
        self.transition_rect = self.transition_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        self.background2    = pygame.image.load("Assets/battlemap.png").convert_alpha()
        self.battle_map     = pygame.transform.scale(self.background2, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.background     = pygame.image.load("Assets/homeui.png").convert_alpha()
        self.background     = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.aboutpage      = pygame.image.load("Assets/AboutPage.png").convert_alpha()
        self.aboutpage      = pygame.transform.scale(self.aboutpage, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.map_1          = pygame.image.load("Assets/Gameplay_map1.png").convert_alpha()
        self.map_1          = pygame.transform.scale(self.map_1, (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.gate_rect = pygame.Rect(1050, 0, 250, 100) 

        self.start = pygame.image.load("Assets/StartButton.png").convert_alpha()
        self.start_hover = pygame.image.load("Assets/StartButtonPressed.png").convert_alpha()
        self.start_rect = self.start.get_rect()
        self.start_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        self.about = pygame.image.load("Assets/AboutButton.png").convert_alpha()
        self.about_hover = pygame.image.load("Assets/AboutButtonPressed.png").convert_alpha()
        self.about_rect = self.about.get_rect()
        self.about_rect.x = 420
        self.about_rect.y = 550
        
        self.exit = pygame.image.load("Assets/ExitButton.png").convert_alpha()
        self.exit_hover = pygame.image.load("Assets/ExitButtonPressed.png").convert_alpha()
        self.exit_rect = self.exit.get_rect()
        self.exit_rect.x = 420
        self.exit_rect.y = 710
        
        self.cursor = pygame.image.load("Assets/cursor.png").convert_alpha()
        self.cursor = pygame.transform.scale(self.cursor, (50, 50))
        self.cursor_rect = self.cursor.get_rect()
        
        self.exact_x = SCREEN_WIDTH // 2
        self.exact_y = SCREEN_HEIGHT // 2
        
    def cursor_update(self, hand_x, hand_y):
        margin_x = 0.2
        margin_y = 0.2
        
        target_x = (hand_x - margin_x) / (1.0 - 2 * margin_x) * SCREEN_WIDTH
        target_y = (hand_y - margin_y) / (1.0 - 2 * margin_y) * SCREEN_HEIGHT

        self.exact_x += (target_x - self.exact_x) * 0.15
        self.exact_y += (target_y - self.exact_y) * 0.15

        self.exact_x = max(0, min(self.exact_x, SCREEN_WIDTH - self.cursor_rect.width))
        self.exact_y = max(0, min(self.exact_y, SCREEN_HEIGHT - self.cursor_rect.height))
        
        self.cursor_rect.x = int(self.exact_x)
        self.cursor_rect.y = int(self.exact_y)
        
    def draw(self, surface, player_obj=None):
        if self.state == "menu":
            surface.blit(self.background, (0, 0))

            if self.cursor_rect.colliderect(self.start_rect):
                surface.blit(self.start_hover, self.start_rect)
            else:
                surface.blit(self.start, self.start_rect)
                
            if self.cursor_rect.colliderect(self.about_rect):
                surface.blit(self.about_hover, self.about_rect)
            else:
                surface.blit(self.about, self.about_rect)
                
            if self.cursor_rect.colliderect(self.exit_rect):
                surface.blit(self.exit_hover, self.exit_rect)
            else:
                surface.blit(self.exit, self.exit_rect)     
            
        elif self.state == "about":
            surface.blit(self.aboutpage, (0, 0))

# ==========================================
# KELAS ENEMY (Kroco Monster 1 & 2)
# ==========================================
class Enemy:
    def __init__(self, target_obj):
        monster_type = random.choice([1, 2])
        
        
        self.sprite_sheet = pygame.image.load(f"Assets/Monster{monster_type}.png").convert_alpha()
        
        self.frame_width = self.sprite_sheet.get_width() // 4
        self.frame_height = self.sprite_sheet.get_height() // 4
        
        self.animations = {"down": [], "left": [], "right": [], "up": []}
        
        directions = ["down", "left", "right", "up"]
        for row in range(4):
            direction_name = directions[row]
            for col in range(4):
                cut_rect = pygame.Rect(col * self.frame_width, row * self.frame_height, self.frame_width, self.frame_height)
                single_frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA).convert_alpha()
                single_frame.blit(self.sprite_sheet, (0, 0), cut_rect)
                single_frame = pygame.transform.scale(single_frame, (48, 48))
                self.animations[direction_name].append(single_frame)

        self.current_direction = "down"
        self.current_frame = 0
        self.rect = self.animations["down"][0].get_rect()
        
        self.target = target_obj 
        self.speed = 1.5 
        self.animation_speed = 0.15
        self.frame_timer = 0.0
        
        spawn_edge = random.choice(["top", "bottom", "left", "right"])
        if spawn_edge == "top":
            self.exact_x = random.uniform(0, SCREEN_WIDTH)
            self.exact_y = -60
        elif spawn_edge == "bottom":
            self.exact_x = random.uniform(0, SCREEN_WIDTH)
            self.exact_y = SCREEN_HEIGHT + 60
        elif spawn_edge == "left":
            self.exact_x = -60
            self.exact_y = random.uniform(0, SCREEN_HEIGHT)
        else: 
            self.exact_x = SCREEN_WIDTH + 60
            self.exact_y = random.uniform(0, SCREEN_HEIGHT)

        self.rect.x = int(self.exact_x)
        self.rect.y = int(self.exact_y)

    def update(self):
        dx = self.target.exact_x - self.exact_x
        dy = self.target.exact_y - self.exact_y
        distance = math.hypot(dx, dy)
        
        if distance != 0:
            self.exact_x += (dx / distance) * self.speed
            self.exact_y += (dy / distance) * self.speed
            
            if abs(dx) > abs(dy):
                self.current_direction = "right" if dx > 0 else "left"
            else:
                self.current_direction = "down" if dy > 0 else "up"

            self.frame_timer += self.animation_speed
            if self.frame_timer >= 1.0:
                self.frame_timer = 0.0
                self.current_frame = (self.current_frame + 1) % 4
                
        self.rect.x = int(self.exact_x)
        self.rect.y = int(self.exact_y)

    def draw(self, surface):
        current_image = self.animations[self.current_direction][self.current_frame]
        surface.blit(current_image, self.rect)

# ==========================================
# KELAS BOSS (Musuh Terakhir - Raksasa & Kuat)
# ==========================================
class Boss:
    def __init__(self, target_obj):
        self.sprite_sheet = pygame.image.load("Assets/Boss.png").convert_alpha()
        
        self.frame_width = self.sprite_sheet.get_width() // 4
        self.frame_height = self.sprite_sheet.get_height() // 4
        
        self.animations = {"down": [], "left": [], "right": [], "up": []}
        
        directions = ["down", "left", "right", "up"]
        for row in range(4):
            direction_name = directions[row]
            for col in range(4):
                cut_rect = pygame.Rect(col * self.frame_width, row * self.frame_height, self.frame_width, self.frame_height)
                single_frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA).convert_alpha()
                single_frame.blit(self.sprite_sheet, (0, 0), cut_rect)
                
               
                single_frame = pygame.transform.scale(single_frame, (128, 128))
                self.animations[direction_name].append(single_frame)

        self.current_direction = "down"
        self.current_frame = 0
        self.rect = self.animations["down"][0].get_rect()
        
        self.target = target_obj 
        self.speed = 1.0           
        self.hp = 15               
        self.animation_speed = 0.1
        self.frame_timer = 0.0
        
        # Bos muncul secara dramatis dari area atas tengah map rawa
        self.exact_x = SCREEN_WIDTH // 2 - 48
        self.exact_y = -100
        self.rect.x = int(self.exact_x)
        self.rect.y = int(self.exact_y)

    def update(self):
        dx = self.target.exact_x - self.exact_x
        dy = self.target.exact_y - self.exact_y
        distance = math.hypot(dx, dy)
        
        if distance != 0:
            self.exact_x += (dx / distance) * self.speed
            self.exact_y += (dy / distance) * self.speed
            
            if abs(dx) > abs(dy):
                self.current_direction = "right" if dx > 0 else "left"
            else:
                self.current_direction = "down" if dy > 0 else "up"

            self.frame_timer += self.animation_speed
            if self.frame_timer >= 1.0:
                self.frame_timer = 0.0
                self.current_frame = (self.current_frame + 1) % 4
                
        self.rect.x = int(self.exact_x)
        self.rect.y = int(self.exact_y)

    def draw(self, surface):
        current_image = self.animations[self.current_direction][self.current_frame]
        surface.blit(current_image, self.rect)

# ==========================================
# INITIALIZATION & SIKLUS UTAMA
# ==========================================
home_screen = Home()
player = Player() 

vanola = Companion("Assets/vanola.png")
vanola.set_initial_position(player.exact_x, player.exact_y)

enemies_list = []      
spawn_timer = 0        
spawn_interval = 120   

total_spawned = 0      
max_monsters = 20      
wave_cleared = False  
transition_timer = 0 

# Objek penampung bos akhir
final_boss = None
boss_spawned = False

main.start()

running = True
prev_action = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if home_screen.state == "about":
                    home_screen.state = "menu" 
            elif event.key == pygame.K_ESCAPE:
                if home_screen.state in ["gameplay", "battle", "transition", "swamp"]:
                    home_screen.state = "menu"

    hx = main.gesture_state['hand_x']
    hy = main.gesture_state['hand_y']
    active = main.gesture_state["active"]
    action = main.gesture_state["action"]
    direction = main.gesture_state["direction"] 
    
    if active:
        home_screen.cursor_update(hx, hy)
        
        if home_screen.state in ["gameplay", "battle", "swamp"]:
            player.update(direction) 
            vanola.update(player.exact_x, player.exact_y, player.current_direction, player.is_moving)
            
            # --- LOGIKA TOMBOL ATTACK GESTUR "PEACE" ---
            if action == "attack" and prev_action != "attack":
                player.trigger_attack()
                attack_hitbox = player.rect.inflate(80, 80)
                
                # A. JIKA DI BATTLE MAP (Membunuh Kroco)
                if home_screen.state == "battle":
                    surviving_enemies = []
                    for enemy in enemies_list:
                        if not attack_hitbox.colliderect(enemy.rect):
                            surviving_enemies.append(enemy)
                        else:
                            print("M kill") 
                    enemies_list = surviving_enemies
                
                # B. JIKA DI SWAMP MAP (Mengurangi Darah Bos)
                elif home_screen.state == "swamp" and final_boss is not None:
                    if attack_hitbox.colliderect(final_boss.rect):
                        final_boss.hp -= 1
                        print(f"JURUS TEBASAN! HP Boss Berkurang! Sisa HP: {final_boss.hp}")
                        if final_boss.hp <= 0:
                            print("💥 FINAL BOSS KALAH! GAME TAMAT! 💥")
                            final_boss = None # Bos hilang dari layar
        
    if action == "parry" and prev_action != "parry":
        if home_screen.state == "menu":
            if home_screen.cursor_rect.colliderect(home_screen.start_rect):
                player.exact_x = SCREEN_WIDTH // 2
                player.exact_y = SCREEN_HEIGHT // 2
                player.rect.x = int(player.exact_x)
                player.rect.y = int(player.exact_y)
                vanola.set_initial_position(player.exact_x, player.exact_y)
                
                # Reset data pertempuran dan bos saat mulai ulang dari menu
                enemies_list.clear() 
                total_spawned = 0
                wave_cleared = False
                final_boss = None
                boss_spawned = False
                
                home_screen.state = "gameplay" 
            elif home_screen.cursor_rect.colliderect(home_screen.about_rect):
                home_screen.state = "about"
            elif home_screen.cursor_rect.colliderect(home_screen.exit_rect):
                running = False

    prev_action = action

    # ==========================================
    # PROSES RENDERING & LOGIKA MAP
    # ==========================================
    if home_screen.state == "gameplay":
        screen.blit(home_screen.map_1, (0, 0))
        vanola.draw(screen)  
        player.draw(screen)  
        
        if player.rect.colliderect(home_screen.gate_rect):
            print("Pindah ke Battle Map!")
            home_screen.state = "battle"
            player.exact_x = SCREEN_WIDTH // 2
            player.exact_y = SCREEN_HEIGHT - 150
            player.rect.x = int(player.exact_x)
            player.rect.y = int(player.exact_y)
            vanola.set_initial_position(player.exact_x, player.exact_y)
            
            enemies_list.clear()
            total_spawned = 0
            wave_cleared = False

    elif home_screen.state == "battle":
        screen.blit(home_screen.battle_map, (0, 0))
        
        if not wave_cleared:
            spawn_timer += 1
            if spawn_timer >= spawn_interval:
                if total_spawned < max_monsters:
                    new_enemy = Enemy(target_obj=vanola)
                    enemies_list.append(new_enemy)
                    total_spawned += 1 
                spawn_timer = 0 
            
            if total_spawned >= max_monsters and len(enemies_list) == 0:
                print("STAGE CLEARED! MENAMPILKAN GAMBAR TRANSISI!")
                wave_cleared = True 
                home_screen.state = "transition"
                transition_timer = 0 

        for enemy in enemies_list:
            enemy.update()
            enemy.draw(screen)
            
        vanola.draw(screen, is_battle=True)
        player.draw(screen, is_battle=True)
        
    elif home_screen.state == "transition":
        screen.fill((0, 0, 0)) # Bersihkan latar belakang menjadi hitam
        screen.blit(home_screen.transition_img, home_screen.transition_rect)
        
        transition_timer += 1
        if transition_timer >= 180:
            print("WAKTU HABIS! PINDAH KE RAWA-RAWA!")
            home_screen.state = "swamp"
            
            player.exact_x = SCREEN_WIDTH // 2
            player.exact_y = SCREEN_HEIGHT - 150
            player.rect.x = int(player.exact_x)
            player.rect.y = int(player.exact_y)
            vanola.set_initial_position(player.exact_x, player.exact_y)

    elif home_screen.state == "swamp":
        screen.blit(home_screen.swamp_map, (0, 0))
        
        # --- MEKANIKA SPAWN BOSS AKHIR ---
        if not boss_spawned:
            final_boss = Boss(target_obj=vanola) # Bos muncul dan fokus mengincar Vanola!
            boss_spawned = True
            
        # Jika bos masih hidup, gerakkan dan tampilkan di layar
        if final_boss is not None:
            final_boss.update()
            final_boss.draw(screen)
        
        vanola.draw(screen)  
        player.draw(screen)
        
    else:
        home_screen.draw(screen) 
        screen.blit(home_screen.cursor, home_screen.cursor_rect)

    # --- RENDER LAYAR WEBCAM PIP ---
    cam_frame = main.gesture_state["frame"]
    if cam_frame is not None:
        cam_surface = pygame.image.frombuffer(cam_frame.tobytes(), (cam_frame.shape[1], cam_frame.shape[0]), "RGB")
        cam_surface = pygame.transform.scale(cam_surface, (320, 240))
        pygame.draw.rect(cam_surface, (255, 255, 255), cam_surface.get_rect(), 3)
        screen.blit(cam_surface, (20, SCREEN_HEIGHT - 240 - 20))
        
    pygame.display.flip()
    clock.tick(60) 
    
main.stop()    
pygame.quit()
sys.exit()