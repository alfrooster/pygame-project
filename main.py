import pygame
import os
import random
import csv
import button
from pygame import mixer

mixer.init()
pygame.init()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.75)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Game')

#set framerate
clock = pygame.time.Clock()
FPS = 60

#game variables
GRAVITY = 0.75
SCROLL_THL = 300
SCROLL_THR = 600
ROWS = 15
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 48
MAX_LEVELS = 2
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False
start_intro = False
delay = 0

#define player action variables
moving_left = False
moving_right = False
shoot = False

#load music and sounds
pygame.mixer.music.load('audio/music.wav')
pygame.mixer.music.set_volume(0.4)
pygame.mixer.music.play(-1, 0.0, 5000)
shot_fx = pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.4)
jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.4)
vomit_fx = pygame.mixer.Sound('audio/vomit.wav')
vomit_fx.set_volume(0.5)
melee_hit_fx = pygame.mixer.Sound('audio/melee_hit.wav')
melee_hit_fx.set_volume(0.4)
splash_fx = pygame.mixer.Sound('audio/splash.wav')
splash_fx.set_volume(0.5)
bullet_hit_fx = pygame.mixer.Sound('audio/bullet_hit.wav')
bullet_hit_fx.set_volume(0.5)
saw_fx = pygame.mixer.Sound('audio/saw.wav')
saw_fx.set_volume(0.5)
laser_fx = pygame.mixer.Sound('audio/laser.wav')
laser_fx.set_volume(0.5)

#load images
#button images
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()
#background
ship_img = pygame.image.load('img/Background/ship_interior.png').convert_alpha()
ship_img = pygame.transform.scale(ship_img, (int(ship_img.get_width() * 2), int(ship_img.get_height() * 2)))
stars_img = pygame.image.load('img/Background/stars.png').convert_alpha()
stars_img = pygame.transform.scale(stars_img, (int(stars_img.get_width() * 2), int(stars_img.get_height() * 2)))
#store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img/Tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
vomit_img = pygame.image.load('img/icons/vomit.png').convert_alpha()

#define colors
BG = (0, 0, 40)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
PINK = (235, 65, 54)
BLACK = (0, 0, 0)

#define font
font = pygame.font.SysFont('Eras Demi ITC', 48)
font2 = pygame.font.SysFont('Sans Serif', 48)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_bg():
    screen.fill(BG)
    width = ship_img.get_width()
    for x in range(7):
        screen.blit(stars_img, ((x * width) - bg_scroll * 0.8, 0))
        screen.blit(ship_img, ((x * width) - bg_scroll * 0.9, 0))

#function to reset level
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    projectile_group.empty()
    decoration_group.empty()
    trap_group.empty()
    saw_group.empty()
    exit_group.empty()

    #create empty tile list
    data = []
    for row in range(ROWS):
        r =[-1] * COLS
        data.append(r)

    return data


class Creature(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, health):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.shoot_cooldown = 0
        self.trap_cooldown = 0
        self.health = health
        self.max_health = self.health
        self.kill_count = 0
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        #ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 500, 120)
        if char_type == "big_monster":
            self.punch = pygame.Rect(0, 0, 170, 120)
        else:
            self.punch = pygame.Rect(0, 0, 120, 90)
        self.idling = False
        self.idling_counter = 0
        self.vomit_cooldown = 0
        self.melee_cooldown = 0
        self.kill_counted = False

        #load all images for the players
        animation_types = ['Idle', 'Run', 'Jump', 'Death', 'Attack'] 
        for animation in animation_types:
            #reset temporary list of images
            temp_list = []
            #count number of files in folder
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)
        self.img = self.animation_list[self.action][self.frame_index]
        self.rect = self.img.get_rect()
        self.rect.center = (x, y)
        self.width = self.img.get_width()
        self.height = self.img.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        #update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.vomit_cooldown > 0:
            self.vomit_cooldown -= 1
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1
        if self.trap_cooldown > 0:
            self.trap_cooldown -= 1

    def move(self, moving_left, moving_right):
        #reset movement variables
        screen_scroll = 0
        dx = 0
        dy = 0

        #assign movement variables if moving left or right
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1
        
        if self.jump == True and self.in_air == False:
            self.vel_y = -15
            self.jump = False
            self.in_air = True

        #become newton and invent gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y

        #check for collision
        for tile in world.obstacle_list:
            ##pygame.draw.rect(screen, WHITE, tile[1], 1)
            #check collision in the x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height - 0.1):
                dx = 0
                #if the ai has hit a wall then make it turn around
                if self.char_type != 'player':
                    self.direction *= -1
                    self.move_counter = 0
            #same in y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #check if below the ground, i.e. jumping
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                #check if above the ground, i.e. falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        #check for collision with traps
        if pygame.sprite.spritecollide(self, trap_group, False):
            if self.trap_cooldown == 0:
                self.trap_cooldown = 60
                laser_fx.play()
                self.health -= 5
        if pygame.sprite.spritecollide(self, saw_group, False):
            if self.trap_cooldown == 0:
                self.trap_cooldown = 60
                saw_fx.play()
                self.health -= 5

        #check for collision with exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            if self.kill_count >= 0.75 * len(enemy_group):
                dx = 0
                dy = 0
                level_complete = True
            else:
                draw_text("You need to kill 75% of the enemies", font, WHITE, SCREEN_WIDTH // 3, SCREEN_HEIGHT // 2)

        #check if fallen off the map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

        #check if going off the edges of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        #update rectangle position
        self.rect.x += dx
        self.rect.y += dy

        #update scroll based on player position
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THR and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH)\
                or (self.rect.left < SCROLL_THL and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx
                
        return screen_scroll, level_complete

    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 10
            bullet = Bullet(self.rect.centerx + (0.6 * self.rect.size[0] * self.direction), self.rect.centery - 3, self.direction)
            bullet_group.add(bullet)
            shot_fx.play()

    def vomit(self):
        self.vomit_cooldown = 200
        projectile = Projectile(self.rect.centerx + (0.6 * self.rect.size[0] * self.direction), self.rect.centery - 5, self.direction)
        projectile_group.add(projectile)
        self.update_action(4)
        vomit_fx.play()

    def melee(self):
        self.melee_cooldown = 100
        #if player rect collides with punch rect, lower player health
        if self.punch.colliderect(player.rect):
            melee_hit_fx.play()
            if player.alive:
                if self.char_type == "big_monster":
                    player.health -= 3
                else:
                    player.health -= 1


    def ai(self):
        if self.alive:

            if self.idling == False and random.randint(1, 200) == 1:
                self.idling = True
                self.update_action(0)#0: idle
                self.idling_counter = 50
            #check if the ai is near the player
            if self.vision.colliderect(player.rect):
                #don't start idling when player is in vision
                self.idling = False
                #flip the image if facing left
                if self.direction == 1:
                    self.flip = False
                elif self.direction == -1:
                    self.flip = True
                if self.char_type == "ranged_monster":
                    #start vomiting toward where currently facing
                    if self.vomit_cooldown == 0:
                        self.update_action(4)#4: attack
                        #choose which frame of the animation the attack activates
                        if self.frame_index == 4:
                            self.vomit()
                else:
                    #run toward player and melee, when in range                    
                    self.punch.center = (self.rect.centerx + 35 * self.direction, self.rect.centery)
                    ##pygame.draw.rect(screen, RED, self.punch, 1)
                    if self.punch.colliderect(player.rect):
                        if self.melee_cooldown == 0:
                            self.update_action(4)#4: attack
                            #choose which frame of the animation the attack activates
                            if self.frame_index == 4:
                                self.melee()
                    else:
                        if self.direction == 1:
                            ai_moving_right = True
                        else:
                            ai_moving_right = False
                        ai_moving_left = not ai_moving_right
                        self.move(ai_moving_left, ai_moving_right)
                        self.update_action(1)#1: run
                        #update ai vision as the enemy moves
                        self.vision.center = (self.rect.centerx + 250 * self.direction, self.rect.centery - 45)
                        ##pygame.draw.rect(screen, RED, self.vision, 1)
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)#1: run
                    self.move_counter += 1
                    #update ai vision as the enemy moves
                    self.vision.center = (self.rect.centerx + 250 * self.direction, self.rect.centery - 45)
                    ##pygame.draw.rect(screen, RED, self.vision, 1)

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        #scroll
        self.rect.x += screen_scroll
   
        
    def update_animation(self):
        #update animation
        ANIMATION_COOLDOWN = 100
        #update image depending on current frame
        self.img = self.animation_list[self.action][self.frame_index]
        #check if enough time has passed since last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #if animation has run out, reset
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3: #death animation stops at last frame
                self.frame_index = len(self.animation_list[self.action]) - 1
            elif self.action == 4:
                self.action = 0
                self.frame_index = 0
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        #check if new action is different from previous
        if new_action != self.action:
            self.action = new_action
            #update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)
            if self.char_type != 'player' and self.kill_counted == False:
                player.kill_count += 1
                self.kill_counted = True

    def draw(self):
        screen.blit(pygame.transform.flip(self.img, self.flip, False), self.rect)
        ##pygame.draw.rect(screen, WHITE, self.rect, 1)


class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        #iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    #these images are obstacles
                    if tile >= 0 and tile <= 33:
                        self.obstacle_list.append(tile_data)
                    elif tile == 34:
                        saw = Saw(img, x * TILE_SIZE, y * TILE_SIZE)
                        saw_group.add(saw)
                    elif tile == 35:
                        trap = Trap(img, x * TILE_SIZE, y * TILE_SIZE)
                        trap_group.add(trap)
                    elif tile >= 36 and tile <= 41:
                        deco = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(deco)
                    elif tile == 42:
                        player = Creature("player", x * TILE_SIZE, y * TILE_SIZE, 3, 5, 10)
                        health_bar = HealthBar(16, 70, player.health, player.health)
                    elif tile == 43:
                        enemy = Creature("reg_monster", x * TILE_SIZE, y * TILE_SIZE, 5, 2, 10)
                        enemy_group.add(enemy)
                    elif tile == 44:
                        enemy = Creature("ranged_monster", x * TILE_SIZE, y * TILE_SIZE, 4, 4, 10)
                        enemy_group.add(enemy)
                    elif tile == 45:
                        enemy = Creature("big_monster", x * TILE_SIZE, y * TILE_SIZE, 4, 1, 20)
                        enemy_group.add(enemy)
                    elif tile >= 46 and tile <= 47:
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
        return player, health_bar
    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])


class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class Trap(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll


class Saw(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midright = (x + TILE_SIZE, y + TILE_SIZE // 2 + 5)
        self.rect.height = self.image.get_height() - 10
    
    def update(self):
        self.rect.x += screen_scroll


class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll


class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        #update with new health
        self.health = health
        ratio = self.health / self.max_health

        pygame.draw.rect(screen, RED, (self.x, self.y, 275, 40))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, ratio * 275, 40))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 25
        self.image = pygame.transform.scale(bullet_img, (12, 12))
        self.rect = pygame.Rect(0, 0, 12, 12)
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        #move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        ##pygame.draw.rect(screen, WHITE, self.rect, 1)
        #check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        #check if bullet hits wall
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
        #check if bullet hits enemy
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    bullet_hit_fx.play()
                    enemy.health -= 1
                    self.kill()

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 3
        self.image = pygame.transform.scale(vomit_img, (32, 32))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        #move projectile
        self.rect.x += (self.direction * self.speed) + screen_scroll
        ##pygame.draw.rect(screen, WHITE, self.rect, 1)
        #check if projectile has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        #check if projectile hits wall
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                splash_fx.play()
                self.kill()
        #check if projectile hits player
        if pygame.sprite.spritecollide(player, projectile_group, False):
            if player.alive:
                splash_fx.play()
                player.health -= 1
                self.kill()


class ScreenFade():
    def __init__(self, direction, color, speed):
        self.direction = direction
        self.color = color
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:#whole screen fade
            pygame.draw.rect(screen, self.color, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.color, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))

        if self.direction == 2:#vertical screen fade down
            pygame.draw.rect(screen, self.color, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_HEIGHT + 50:
            fade_complete = True

        return fade_complete


#create screen fades
intro_fade = ScreenFade(1, BLACK, 8)
death_fade = ScreenFade(2, PINK, 12)
end_fade = ScreenFade(2, BG, 4)


#create buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

#create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
projectile_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
trap_group = pygame.sprite.Group()
saw_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()



#create empty tile list
world_data = []
for row in range(ROWS):
    r =[-1] * COLS
    world_data.append(r)
#load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=';')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)



run = True
while run:
    clock.tick(FPS)

    if start_game == False:
        #draw menu
        screen.fill(BG)
        if start_button.draw(screen):
            start_game = True
            start_intro = True
        if exit_button.draw(screen):
            run = False
        draw_text('LEFT: A    RIGHT: D    JUMP: W / SPACE    SHOOT: LEFT CLICK / M', font2, WHITE, 100, 120)
    else:

        #update background
        draw_bg()
        #draw world map
        world.draw()

        health_bar.draw(player.health)
        draw_text(f'HP: {player.health}', font, WHITE, 16, 6)

        enemy_count = len(enemy_group)
        draw_text(f'Kills: {player.kill_count}/{enemy_count}', font, WHITE, SCREEN_WIDTH - 270, 6)

        #update and draw groups
        bullet_group.update()
        projectile_group.update()
        trap_group.update()
        saw_group.update()
        decoration_group.update()
        exit_group.update()
        bullet_group.draw(screen)
        projectile_group.draw(screen)
        decoration_group.draw(screen)
        trap_group.draw(screen)
        saw_group.draw(screen)
        exit_group.draw(screen)

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()

        player.update()
        player.draw()

        #show intro
        if start_intro:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0

        #update player actions
        if player.alive:
            if shoot:
                player.shoot()
            if player.in_air:
                player.update_action(2)#2: jump
            elif shoot and player.in_air == False and moving_left == False and moving_right == False:
                player.update_action(4)#4: attack
            elif moving_left or moving_right:
                player.update_action(1)#1: run
            else:
                player.update_action(0)#0: idle
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            #check if level is completed
            if level_complete:
                level += 1
                bg_scroll = 0
                if level <= MAX_LEVELS:
                    start_intro = True
                    world_data = reset_level()
                    #load in level data and create world
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=';')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)
                else:
                    if end_fade.fade():
                        draw_text("Thanks for playing", font, WHITE, SCREEN_WIDTH // 3, SCREEN_HEIGHT // 2)
                        delay += 1
                        if delay >= 240:
                            run = False
        else:
            screen_scroll = 0
            player.move(False, False)
            if death_fade.fade():
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True
                    bg_scroll = 0
                    world_data = reset_level()
                    #load in level data and create world
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=';')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)


    for event in pygame.event.get():
        #quit game
        if event.type == pygame.QUIT:
            run = False
        #key presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if (event.key == pygame.K_w or event.key == pygame.K_SPACE) and player.alive:
                jump_fx.play()
                player.jump = True
            if event.key == pygame.K_m:
                shoot = True
            if event.key == pygame.K_ESCAPE:
                run = False
        #key releases
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_w or event.key == pygame.K_SPACE:
                player.jump = False
            if event.key == pygame.K_m:
                shoot = False
        #mouse
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                shoot = True
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                shoot = False

    pygame.display.update()


pygame.quit()