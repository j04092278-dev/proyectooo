import pygame
import math
import random
import sys

# Inicializar Pygame
pygame.init()

# Configuración de pantalla
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Carreras 3D Extremo")

# Colores
SKY_BLUE = (135, 206, 235)
ROAD_COLOR = (50, 50, 50)
ROAD_MARKING = (255, 255, 255)
GRASS_COLOR = (34, 139, 34)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 215, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Clase para el jugador
class PlayerCar:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.width = 40
        self.height = 70
        self.speed = 0
        self.max_speed = 10
        self.acceleration = 0.1
        self.deceleration = 0.2
        self.steering = 0
        self.max_steering = 3
        self.color = RED
        self.score = 0
        self.lives = 3
        
    def update(self, keys):
        # Aceleración y frenado
        if keys[pygame.K_UP]:
            self.speed = min(self.speed + self.acceleration, self.max_speed)
        elif keys[pygame.K_DOWN]:
            self.speed = max(self.speed - self.deceleration * 2, -self.max_speed / 2)
        else:
            # Desaceleración natural
            if self.speed > 0:
                self.speed = max(self.speed - self.deceleration / 2, 0)
            elif self.speed < 0:
                self.speed = min(self.speed + self.deceleration / 2, 0)
        
        # Dirección
        if keys[pygame.K_LEFT]:
            self.steering = -self.max_steering
        elif keys[pygame.K_RIGHT]:
            self.steering = self.max_steering
        else:
            self.steering = 0
        
        # Movimiento
        self.x += self.steering * (self.speed / self.max_speed)
        
        # Limitar el coche a la carretera
        road_left = WIDTH // 2 - 150
        road_right = WIDTH // 2 + 150
        self.x = max(road_left + self.width // 2, min(self.x, road_right - self.width // 2))
        
    def draw(self, screen):
        # Dibujar el coche del jugador
        pygame.draw.rect(screen, self.color, (self.x - self.width // 2, self.y - self.height // 2, self.width, self.height))
        
        # Detalles del coche
        pygame.draw.rect(screen, BLACK, (self.x - self.width // 2 + 5, self.y - self.height // 2 + 5, self.width - 10, 15))  # Ventana frontal
        pygame.draw.rect(screen, BLACK, (self.x - self.width // 2 + 5, self.y + self.height // 2 - 20, self.width - 10, 15))  # Ventana trasera
        pygame.draw.rect(screen, YELLOW, (self.x - self.width // 2 - 5, self.y - self.height // 2 + 10, 5, 10))  # Luz izquierda
        pygame.draw.rect(screen, YELLOW, (self.x + self.width // 2, self.y - self.height // 2 + 10, 5, 10))  # Luz derecha
        pygame.draw.rect(screen, RED, (self.x - self.width // 2 - 5, self.y + self.height // 2 - 20, 5, 10))  # Luz trasera izquierda
        pygame.draw.rect(screen, RED, (self.x + self.width // 2, self.y + self.height // 2 - 20, 5, 10))  # Luz trasera derecha

# Clase para los coches enemigos
class EnemyCar:
    def __init__(self):
        self.width = 40
        self.height = 70
        self.lane = random.choice([-1, 0, 1])  # -1: izquierda, 0: centro, 1: derecha
        self.x = WIDTH // 2 + self.lane * 50
        self.y = -self.height
        self.speed = random.uniform(3, 7)
        self.color = random.choice([BLUE, (0, 200, 0), (200, 0, 200), (255, 165, 0)])
        
    def update(self):
        self.y += self.speed
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x - self.width // 2, self.y - self.height // 2, self.width, self.height))
        
        # Detalles del coche enemigo
        pygame.draw.rect(screen, BLACK, (self.x - self.width // 2 + 5, self.y - self.height // 2 + 5, self.width - 10, 15))
        pygame.draw.rect(screen, BLACK, (self.x - self.width // 2 + 5, self.y + self.height // 2 - 20, self.width - 10, 15))

# Clase para efectos de partículas
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.life = random.randint(20, 40)
        self.color = random.choice([WHITE, YELLOW, (200, 200, 200)])
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        
    def draw(self, screen):
        alpha = min(255, self.life * 6)
        size = max(1, self.life // 10)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

# Clase para elementos de la carretera
class RoadElement:
    def __init__(self, y):
        self.y = y
        self.width = 10
        self.height = 30
        
    def update(self, speed):
        self.y += speed
        
    def draw(self, screen):
        pygame.draw.rect(screen, ROAD_MARKING, (WIDTH // 2 - self.width // 2, self.y, self.width, self.height))

# Función para dibujar la carretera en perspectiva 3D
def draw_road(screen, player_speed):
    # Dibujar cielo
    screen.fill(SKY_BLUE)
    
    # Dibujar pasto
    pygame.draw.rect(screen, GRASS_COLOR, (0, HEIGHT // 2, WIDTH, HEIGHT // 2))
    
    # Dibujar carretera con perspectiva
    road_width = 300
    road_top_width = 100
    
    # Calcular puntos para la carretera en perspectiva
    points = [
        (WIDTH // 2 - road_top_width // 2, 0),
        (WIDTH // 2 + road_top_width // 2, 0),
        (WIDTH // 2 + road_width // 2, HEIGHT),
        (WIDTH // 2 - road_width // 2, HEIGHT)
    ]
    
    pygame.draw.polygon(screen, ROAD_COLOR, points)
    
    # Dibujar líneas de la carretera
    line_height = 50
    line_spacing = 100
    line_width = 10
    
    for i in range(0, HEIGHT, line_spacing):
        y_pos = (i - pygame.time.get_ticks() // 10 % line_spacing) % HEIGHT
        line_points = [
            (WIDTH // 2 - line_width // 2, y_pos),
            (WIDTH // 2 - line_width // 2, y_pos + line_height),
            (WIDTH // 2 + line_width // 2, y_pos + line_height),
            (WIDTH // 2 + line_width // 2, y_pos)
        ]
        pygame.draw.polygon(screen, ROAD_MARKING, line_points)

# Función para mostrar información en pantalla
def draw_hud(screen, player):
    font = pygame.font.SysFont(None, 36)
    
    # Velocidad
    speed_text = font.render(f"Velocidad: {int(player.speed * 20)} km/h", True, WHITE)
    screen.blit(speed_text, (20, 20))
    
    # Puntuación
    score_text = font.render(f"Puntos: {player.score}", True, WHITE)
    screen.blit(score_text, (20, 60))
    
    # Vidas
    lives_text = font.render(f"Vidas: {player.lives}", True, WHITE)
    screen.blit(lives_text, (20, 100))
    
    # Instrucciones
    instructions_font = pygame.font.SysFont(None, 24)
    instructions = [
        "Flechas: Mover coche",
        "Espacio: Turbo (cuando disponible)",
        "Esc: Salir del juego"
    ]
    
    for i, instruction in enumerate(instructions):
        text = instructions_font.render(instruction, True, WHITE)
        screen.blit(text, (WIDTH - text.get_width() - 20, 20 + i * 30))

# Función principal del juego
def main():
    clock = pygame.time.Clock()
    player = PlayerCar()
    enemy_cars = []
    particles = []
    road_elements = []
    
    # Crear elementos de la carretera
    for i in range(0, HEIGHT, 100):
        road_elements.append(RoadElement(i))
    
    # Variables de juego
    spawn_timer = 0
    game_over = False
    turbo_available = True
    turbo_timer = 0
    
    while True:
        # Manejo de eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_SPACE and turbo_available and not game_over:
                    player.speed = player.max_speed * 1.5
                    turbo_available = False
                    turbo_timer = pygame.time.get_ticks()
                    
                    # Crear partículas de turbo
                    for _ in range(30):
                        particles.append(Particle(player.x, player.y + player.height // 2))
        
        if not game_over:
            # Actualizar jugador
            keys = pygame.key.get_pressed()
            player.update(keys)
            
            # Generar coches enemigos
            spawn_timer += 1
            if spawn_timer >= 60:  # Generar un nuevo coche cada ~1 segundo
                enemy_cars.append(EnemyCar())
                spawn_timer = 0
            
            # Actualizar coches enemigos
            for enemy in enemy_cars[:]:
                enemy.update()
                
                # Verificar colisiones
                if (abs(player.x - enemy.x) < (player.width + enemy.width) // 2 and
                    abs(player.y - enemy.y) < (player.height + enemy.height) // 2):
                    player.lives -= 1
                    enemy_cars.remove(enemy)
                    
                    # Crear partículas de explosión
                    for _ in range(50):
                        particles.append(Particle(enemy.x, enemy.y))
                    
                    if player.lives <= 0:
                        game_over = True
                
                # Eliminar coches que salen de la pantalla
                elif enemy.y > HEIGHT + enemy.height:
                    enemy_cars.remove(enemy)
                    player.score += 10
            
            # Actualizar partículas
            for particle in particles[:]:
                particle.update()
                if particle.life <= 0:
                    particles.remove(particle)
            
            # Actualizar elementos de la carretera
            for element in road_elements:
                element.update(player.speed)
                if element.y > HEIGHT:
                    element.y = -element.height
            
            # Recargar turbo después de 5 segundos
            if not turbo_available and pygame.time.get_ticks() - turbo_timer > 5000:
                turbo_available = True
        
        # Dibujar todo
        draw_road(screen, player.speed)
        
        # Dibujar elementos de la carretera
        for element in road_elements:
            element.draw(screen)
        
        # Dibujar coches enemigos
        for enemy in enemy_cars:
            enemy.draw(screen)
        
        # Dibujar partículas
        for particle in particles:
            particle.draw(screen)
        
        # Dibujar jugador
        player.draw(screen)
        
        # Dibujar HUD
        draw_hud(screen, player)
        
        # Mostrar turbo disponible
        if turbo_available and not game_over:
            font = pygame.font.SysFont(None, 36)
            turbo_text = font.render("TURBO DISPONIBLE (Espacio)", True, YELLOW)
            screen.blit(turbo_text, (WIDTH // 2 - turbo_text.get_width() // 2, HEIGHT - 40))
        
        # Mostrar pantalla de game over
        if game_over:
            font_large = pygame.font.SysFont(None, 72)
            font_small = pygame.font.SysFont(None, 36)
            
            game_over_text = font_large.render("GAME OVER", True, RED)
            score_text = font_small.render(f"Puntuación final: {player.score}", True, WHITE)
            restart_text = font_small.render("Presiona R para reiniciar", True, WHITE)
            
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 + 20))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 70))
            
            # Reiniciar juego si se presiona R
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                # Reiniciar todas las variables del juego
                player = PlayerCar()
                enemy_cars = []
                particles = []
                road_elements = []
                for i in range(0, HEIGHT, 100):
                    road_elements.append(RoadElement(i))
                game_over = False
                turbo_available = True
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()