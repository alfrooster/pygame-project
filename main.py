import pygame
import os
import random
import csv

pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.75)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Game')

#set framerate
clock = pygame.time.Clock()
FPS = 60

#game variables
GRAVITY = 0.75
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
level = 1

#define player action variables
moving_left = False
moving_right = False
shoot = False

#load images
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()

#define colors
BG = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

#define font
font = pygame.font.SysFont('Times New Roman', 30)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_bg():
    screen.fill(BG)
    pygame.draw.line(screen, RED, (0, 500), (SCREEN_WIDTH, 500))
    pygame.draw.line(screen, RED, (300, 320), (SCREEN_WIDTH, 320))

class Creature(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, health):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.shoot_cooldown = 0
        self.health = health
        self.max_health = self.health
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
        self.vision = pygame.Rect(0, 0, 300, 20)
        if char_type == "big_monster":
            self.punch = pygame.Rect(0, 0, 100, 70)
        else:
            self.punch = pygame.Rect(0, 0, 70, 70)
        self.idling = False
        self.idling_counter = 0
        self.vomit_cooldown = 0
        self.melee_cooldown = 0

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

    def move(self, moving_left, moving_right):
        #reset movement variables
        dx = 0
        dy = 0

        #assign movement variables if moving left or right
        if moving_left:
            if self.in_air:
                dx = -self.speed - 3
            else:
                dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            if self.in_air:
                dx = self.speed + 3
            else:
                dx = self.speed
            self.flip = False
            self.direction = 1
        
        if self.jump == True and self.in_air == False:
            self.vel_y = -13
            self.jump = False
            self.in_air = True

        dy += self.vel_y

        #become newton and invent gravity
        self.vel_y += GRAVITY
        if self.vel_y > 12:
            self.vel_y
        dy += self.vel_y

        #check collision with floor
        if self.rect.bottom + dy > 500:
            dy = 500 - self.rect.bottom
            self.in_air = False

        #update rectangle position
        self.rect.x += dx
        self.rect.y += dy

    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 10
            bullet = Bullet(self.rect.centerx + (0.6 * self.rect.size[0] * self.direction), self.rect.centery - 3, self.direction)
            bullet_group.add(bullet)

    def vomit(self):
        self.vomit_cooldown = 200
        projectile = Projectile(self.rect.centerx + (0.6 * self.rect.size[0] * self.direction), self.rect.centery - 5, self.direction)
        projectile_group.add(projectile)
        self.update_action(4)

    def melee(self):
        self.melee_cooldown = 100
        pygame.draw.rect(screen, RED, self.punch)
        #if player rect collides with punch rect, lower player health
        if self.punch.colliderect(player.rect):
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
                #stop running and face the player
                if self.char_type == "ranged_monster":
                    if self.vomit_cooldown == 0:
                        self.update_action(4)#4: attack
                        #choose which frame of the animation the attack activates
                        if self.frame_index == 2:
                            self.vomit()
                    else:
                        self.update_action(0)
                else:
                    #run toward player and melee, when in range                    
                    self.punch.center = (self.rect.centerx + 35 * self.direction, self.rect.centery)
                    if self.punch.colliderect(player.rect):
                        if self.melee_cooldown == 0:
                            self.update_action(4)#4: attack
                            #choose which frame of the animation the attack activates
                            if self.frame_index == 2:
                                self.melee()
                        else:
                            self.update_action(0)
                    else:
                        if self.direction == 1:
                            ai_moving_right = True
                        else:
                            ai_moving_right = False
                        ai_moving_left = not ai_moving_right
                        self.move(ai_moving_left, ai_moving_right)
                        self.update_action(1)#1: run
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
                    self.vision.center = (self.rect.centerx + 150 * self.direction, self.rect.centery)
                    pygame.draw.rect(screen, RED, self.vision)

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
   
        
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

    def draw(self):
        screen.blit(pygame.transform.flip(self.img, self.flip, False), self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 1)


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

        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, ratio * 150, 20))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = pygame.Rect(0, 0, 6, 6)
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        #move bullet
        self.rect.x += (self.direction * self.speed)
        #check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        #check if bullet hits enemy
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 1
                    self.kill()

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 3
        self.image = grenade_img
        self.rect = pygame.rect.Rect((0,0), (6, 6))
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        #move projectile
        self.rect.x += (self.direction * self.speed)
        #check if projectile has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        #check if projectile hits player
        if pygame.sprite.spritecollide(player, projectile_group, False):
            if player.alive:
                player.health -= 1
                self.kill()


#create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
projectile_group = pygame.sprite.Group()



player = Creature("player", 200, 200, 2, 5, 10)
health_bar = HealthBar(10, 40, player.health, player.health)

#enemy = Creature("reg_monster", 600, 266, 2, 2, 10)
#enemy2 = Creature("ranged_monster", 650, 266, 2, 4, 10)
enemy3 = Creature("big_monster", 720, 446, 2, 1, 20)
#enemy_group.add(enemy)
#enemy_group.add(enemy2)
enemy_group.add(enemy3)



run = True
while run:
    clock.tick(FPS)

    draw_bg()

    health_bar.draw(player.health)
    draw_text(f'HP: {player.health}', font, WHITE, 10, 3)

    player.update()
    player.draw()

    for enemy in enemy_group:
        enemy.ai()
        enemy.update()
        enemy.draw()

    #update and draw groups
    bullet_group.update()
    projectile_group.update()
    bullet_group.draw(screen)
    projectile_group.draw(screen)

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
        player.move(moving_left, moving_right)
    else:
        player.move(False, False) #REMEMBER: make it so that after dying movement slows and then stops, like dying while jumping forward you won't just fall straight down

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
                player.jump = True
            if event.key == pygame.K_ESCAPE:
                run = False
        #key releases
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_w or pygame.K_SPACE:
                player.jump = False
        #mouse
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                shoot = True
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                shoot = False

    pygame.display.update()


pygame.quit()