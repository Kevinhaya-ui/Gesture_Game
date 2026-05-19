import pygame
import sys
import main  

pygame.init()

SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Kevin Afkar Haya - 5024251016")
clock = pygame.time.Clock()

class Player:
    def __init__(self):
        self.sprite_sheet = pygame.image.load("Assets/keafhaa.png").convert_alpha()
        
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
        self.rect = self.animations["down"][0].get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        self.exact_x = float(self.rect.x)
        self.exact_y = float(self.rect.y)
        
        self.move_speed = 25.0         
        self.animation_speed = 0.1    
        self.frame_timer = 0.0         
        self.is_moving = False         

    def update(self, vel_x, vel_y):
        self.is_moving = False
        
        deadzone = 0.02
        
        if abs(vel_x) > deadzone or abs(vel_y) > deadzone:
            self.is_moving = True
            
            if abs(vel_x) > abs(vel_y):
                self.current_direction = "right" if vel_x > 0 else "left"
            else:
                self.current_direction = "down" if vel_y > 0 else "up"
            
            self.exact_x += vel_x * self.move_speed
            self.exact_y += vel_y * self.move_speed
            
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

    def draw(self, surface):
        current_image = self.animations[self.current_direction][self.current_frame]
        surface.blit(current_image, self.rect)



class Home:
    def __init__(self):
        
        self.state = "menu"
        
        self.background = pygame.image.load("Assets/homeui.png").convert_alpha()
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.aboutpage = pygame.image.load("Assets/AboutPage.png").convert_alpha()
        self.aboutpage = pygame.transform.scale(self.aboutpage, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.map_1 = pygame.image.load("Assets/Gameplay_map1.png").convert_alpha()
        self.map_1 = pygame.transform.scale(self.map_1, (SCREEN_WIDTH, SCREEN_HEIGHT))

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
        
    def draw(self, surface, player_obj):
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
            
        elif self.state == "gameplay":
            surface.blit(self.map_1, (0, 0))
            player_obj.draw(surface)

        if self.state != "gameplay":
            surface.blit(self.cursor, self.cursor_rect)

#MAIN DISINI

home_screen = Home()
player = Player() 
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
                    print("Back to Home Screen!")
                    home_screen.state = "menu" 
            
            elif event.key == pygame.K_ESCAPE:
                if home_screen.state == "gameplay":
                    print("Back to Home Screen!")
                    home_screen.state = "menu"

    vx = main.gesture_state['vel_x']
    vy = main.gesture_state['vel_y']
    hx = main.gesture_state['hand_x']
    hy = main.gesture_state['hand_y']
    active = main.gesture_state["active"]
    action = main.gesture_state["action"]
    
    if active:
        home_screen.cursor_update(hx, hy)
        
        if home_screen.state == "gameplay":
            player.update(vx, vy)
        
    
    if action == "parry" and prev_action != "parry":
        if home_screen.state == "menu":
            if home_screen.cursor_rect.colliderect(home_screen.start_rect):
                print("start the Game! Switching to Map 1")
                home_screen.state = "gameplay" 
                
            elif home_screen.cursor_rect.colliderect(home_screen.about_rect):
                print("Show the About Page")
                home_screen.state = "about"
                
            elif home_screen.cursor_rect.colliderect(home_screen.exit_rect):
                print("Exit the Game")
                running = False

    prev_action = action

    home_screen.draw(screen, player)  
    pygame.display.flip()
    clock.tick(60) 
    
main.stop()    
pygame.quit()
sys.exit()