import pygame
import random
import os

# Inicializar Pygame
pygame.init()

# Configuración de pantalla
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SpaceMax Defender: Power Edition")

# Rutas de recursos
current_path = os.path.dirname(__file__)
assets_path = os.path.join(current_path, 'assets')
img_path = os.path.join(assets_path, 'images')

# Cargar imágenes y escalarlas
player_img = pygame.transform.scale(
    pygame.image.load(os.path.join(img_path, 'player.jpg')).convert_alpha(), (60, 60)
)

enemy_imgs = [
    pygame.transform.scale(pygame.image.load(os.path.join(img_path, 'enemy1.png')).convert_alpha(), (50, 50)),
    pygame.transform.scale(pygame.image.load(os.path.join(img_path, 'enemy2.png')).convert_alpha(), (50, 50)),
    pygame.transform.scale(pygame.image.load(os.path.join(img_path, 'enemy3.png')).convert_alpha(), (50, 50))
]

ghost_img = enemy_imgs[2]  # Fantasma

bullet_img = pygame.transform.scale(
    pygame.image.load(os.path.join(img_path, 'bullet.jpg')).convert_alpha(), (10, 20)
)

background = pygame.transform.scale(
    pygame.image.load(os.path.join(img_path, 'background.jpg')).convert(), (WIDTH, HEIGHT)
)

power_img = pygame.transform.scale(
    pygame.image.load(os.path.join(img_path, 'multi.jpg')).convert_alpha(), (30, 30)
)

# (Opcional) Imagen de explosión simple, si no está se usa un círculo rojo
explosion_img = None
try:
    explosion_img = pygame.transform.scale(
        pygame.image.load(os.path.join(img_path, 'kabum.jpg')).convert_alpha(), (30, 30)
    )
except:
    print("⚠️ No se encontró 'explosion.png'. Usaré efecto alternativo.")

# Reloj
clock = pygame.time.Clock()
# ===================== CLASES ========================

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10
        self.speed = 8
        self.lives = 3
        self.score = 0
        self.power_level = 1
        self.power_timer = 0
        self.invincible = False
        self.invincible_timer = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed

        # Invencibilidad temporal
        if self.invincible and pygame.time.get_ticks() > self.invincible_timer:
            self.invincible = False

        # Disparo múltiple se reinicia después de 10 segundos
        if self.power_level > 1 and pygame.time.get_ticks() > self.power_timer:
            self.power_level = 1

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        self.image = enemy_imgs[type]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
        self.direction = 1

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.right >= WIDTH or self.rect.left <= 0:
            self.direction *= -1
            self.rect.y += 30

class Ghost(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = ghost_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = -50
        self.speed_y = random.randint(3, 7)

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT:
            self.kill()

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed):
        super().__init__()
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        self.image = power_img
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 3
        self.type = random.choice(['x2', 'x3', 'shield', 'life', 'bomb'])

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        if explosion_img:
            self.image = explosion_img
        else:
            self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 0, 0), (15, 15), 15)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.timer = pygame.time.get_ticks() + 300

    def update(self):
        if pygame.time.get_ticks() > self.timer:
            self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(enemy_imgs[1], (120, 100))
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.y = 20
        self.speed = 3
        self.health = 10
        self.direction = 1

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.direction *= -1
# ===================== INICIALIZACIÓN DE GRUPOS Y OBJETOS ========================

all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
ghosts = pygame.sprite.Group()
bullets = pygame.sprite.Group()
powers = pygame.sprite.Group()
explosions = pygame.sprite.Group()
boss_group = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

def spawn_enemies():
    for row in range(3):
        for col in range(8):
            enemy = Enemy(100 + col * 70, 50 + row * 60, row)
            all_sprites.add(enemy)
            enemies.add(enemy)

spawn_enemies()

# ===================== VARIABLES DE JUEGO ========================

spawn_ghost_timer = 0
spawn_power_timer = 0
score_checkpoint = 0
game_over = False

# ===================== BUCLE PRINCIPAL ========================

running = True
while running:
    clock.tick(60)
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over:
                for i in range(player.power_level):
                    offset = (i - player.power_level // 2) * 15
                    bullet = Bullet(player.rect.centerx + offset, player.rect.top, -10)
                    all_sprites.add(bullet)
                    bullets.add(bullet)

            if event.key == pygame.K_r and game_over:
                # Reiniciar todo
                player.lives = 3
                player.score = 0
                player.power_level = 1
                player.invincible = False
                player.rect.centerx = WIDTH // 2
                enemies.empty()
                ghosts.empty()
                bullets.empty()
                powers.empty()
                boss_group.empty()
                explosions.empty()
                all_sprites.empty()
                all_sprites.add(player)
                spawn_enemies()
                game_over = False
                score_checkpoint = 0

    if not game_over:
        # =================== Aparición de fantasmas ===================
        if current_time > spawn_ghost_timer:
            ghost = Ghost()
            ghosts.add(ghost)
            all_sprites.add(ghost)
            spawn_ghost_timer = current_time + random.randint(2000, 4000)

        # =================== Aparición de poderes ===================
        if current_time > spawn_power_timer:
            x = random.randint(50, WIDTH - 50)
            power = PowerUp((x, 0))
            powers.add(power)
            all_sprites.add(power)
            spawn_power_timer = current_time + random.randint(7000, 12000)

        # =================== Actualizar todo ===================
        all_sprites.update()

        # =================== Colisiones balas-enemigos ===================
        hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
        for hit in hits:
            player.score += 100
            explosion = Explosion(hit.rect.center)
            all_sprites.add(explosion)
            explosions.add(explosion)

        # =================== Colisiones balas-jefe ===================
        for boss in boss_group:
            if pygame.sprite.spritecollide(boss, bullets, True):
                boss.health -= 1
                if boss.health <= 0:
                    boss.kill()
                    player.score += 500
                    explosion = Explosion(boss.rect.center)
                    all_sprites.add(explosion)
                    explosions.add(explosion)

        # =================== Colisiones jugador-enemigos ===================
        if not player.invincible:
            if pygame.sprite.spritecollide(player, enemies, True) or pygame.sprite.spritecollide(player, ghosts, True):
                player.lives -= 1
                player.invincible = True
                player.invincible_timer = current_time + 2000
                if player.lives <= 0:
                    game_over = True

        # =================== Colisiones jugador-powerups ===================
        hits = pygame.sprite.spritecollide(player, powers, True)
        for hit in hits:
            if hit.type == 'x2':
                player.power_level = min(player.power_level + 1, 3)
                player.power_timer = current_time + 10000
            elif hit.type == 'shield':
                player.invincible = True
                player.invincible_timer = current_time + 5000
            elif hit.type == 'life':
                player.lives = min(player.lives + 1, 5)
            elif hit.type == 'bomb':
                for e in enemies:
                    e.kill()
                    explosion = Explosion(e.rect.center)
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                for g in ghosts:
                    g.kill()
                    explosion = Explosion(g.rect.center)
                    all_sprites.add(explosion)
                    explosions.add(explosion)

        # =================== Dificultad progresiva ===================
        if player.score >= score_checkpoint + 500:
            spawn_enemies()
            score_checkpoint += 500

        # =================== Jefe ===================
        if player.score > 0 and player.score % 1000 == 0 and len(boss_group) == 0:
            boss = Boss()
            boss_group.add(boss)
            all_sprites.add(boss)

    # =================== Dibujar ===================
    screen.blit(background, (0, 0))
    all_sprites.draw(screen)

    # Texto
    font = pygame.font.Font(None, 36)
    text = font.render(f"Score: {player.score}  Lives: {player.lives}  Power: x{player.power_level}", True, (255, 255, 255))
    screen.blit(text, (10, 10))

    if game_over:
        font_big = pygame.font.Font(None, 72)
        over_text = font_big.render("GAME OVER", True, (255, 0, 0))
        screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2 - 50))
        restart_text = font.render("Presiona R para reiniciar", True, (255, 255, 255))
        screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 20))

    pygame.display.flip()

pygame.quit()
