import pygame
import random
import math

# asistentovi komentarji: naredi da se ribe prilagodijo roki. se pravi ne samo da se zberejo okoli točke ampak, da se dotikajo prstov in dlani.

pygame.init()

info = pygame.display.Info() # You have to call this before pygame.display.set_mode()
screen_width,screen_height = info.current_w,info.current_h
#WIDTH, HEIGHT = screen_width-50, screen_height-50
WIDTH, HEIGHT = 800, 600

# Colors
OCEAN = (200, 200, 200)

# Flocking parameters
NUM_ENTITIES = 50
MAX_SPEED = 1.5
PERCEPTION_RADIUS = 200
SEPARATION_DISTANCE = 50
TURN_RATE = 1  # Controls how quickly the velocity aligns with the desired direction
EDGE_THRESHOLD = 50  # Distance from the edge where the repelling force is applied
EDGE_FORCE = 0.15  # Magnitude of the repelling force


# Entity class
class Entity:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        self.velocity.scale_to_length(MAX_SPEED)
        self.desired_velocity = self.velocity 
        self.edge_force = pygame.Vector2(0, 0)
        self.separation_force = pygame.Vector2(0, 0)
        self.desired_pos = pygame.Vector2(0, 0)
        self.vel = pygame.Vector2(0, 0)

    def update(self, flock, mouse_pos, scatter):
        average_velocity = pygame.Vector2(0, 0)
        average_position = pygame.Vector2(0, 0)
        average_separation = pygame.Vector2(0, 0)
        num_neighbors_sep = 0
        num_neighbors_per = 0

        for other in flock:
            if other == self:
                continue

            distance = self.distance_to(other)

            if distance < PERCEPTION_RADIUS:
                average_velocity += other.velocity
                average_position += other.position
                num_neighbors_per += 1

            if distance < SEPARATION_DISTANCE:
                diff = self.position - other.position
                diff.scale_to_length(1 / distance)
                average_separation += diff
                num_neighbors_sep += 1

        self.edge_force = self.wrap_edges()        
        

        self.desired_velocity = self.velocity +  self.edge_force

        if num_neighbors_per > 0 :
            average_position += self.position
            average_velocity += self.velocity
            num_neighbors_per += 1
            average_velocity /= num_neighbors_per
            average_position /= (num_neighbors_per)
            self.desired_velocity -= (average_velocity * 0.1)

        if num_neighbors_sep > 0 :
            self.desired_velocity += (average_separation * 1)
            
        self.separation_force = average_separation
        self.desired_pos = average_position
        self.vel = average_velocity

        if scatter == 2:
            direction_from_mouse = self.position - mouse_pos
            if direction_from_mouse.length() > 0:
                direction_from_mouse.scale_to_length(1)  
            self.desired_velocity += direction_from_mouse * 1
        elif scatter == 1:
            direction_to_mouse = mouse_pos - self.position
            if direction_to_mouse.length() > 0:
                direction_to_mouse.scale_to_length(1) 
            self.desired_velocity += direction_to_mouse * 0.5  
        

        if self.desired_velocity.length() > MAX_SPEED:
            self.desired_velocity.scale_to_length(MAX_SPEED)
        self.velocity = self.velocity.lerp(self.desired_velocity, TURN_RATE)

        self.position += self.velocity

    def wrap_edges(self):
        edge_force = pygame.Vector2(0, 0)
        if self.position.x < EDGE_THRESHOLD:
            edge_force.x = EDGE_FORCE * (EDGE_THRESHOLD - self.position.x) / EDGE_THRESHOLD
        elif self.position.x > WIDTH - EDGE_THRESHOLD:
            edge_force.x = -EDGE_FORCE * (self.position.x - (WIDTH - EDGE_THRESHOLD)) / EDGE_THRESHOLD

        if self.position.y < EDGE_THRESHOLD:
            edge_force.y = EDGE_FORCE * (EDGE_THRESHOLD - self.position.y) / EDGE_THRESHOLD
        elif self.position.y > HEIGHT - EDGE_THRESHOLD:
            edge_force.y = -EDGE_FORCE * (self.position.y - (HEIGHT - EDGE_THRESHOLD)) / EDGE_THRESHOLD

        return edge_force

    def distance_to(self, other):
        return math.sqrt((self.position.x - other.position.x) ** 2 + (self.position.y - other.position.y) ** 2)


flock = [Entity(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(NUM_ENTITIES)]

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ribja Simulacija")

def draw_fish(screen, position, velocity):
    angle = math.degrees(math.atan2(-velocity.y, velocity.x)) 
    
    fish_surface = pygame.Surface((30, 20), pygame.SRCALPHA)  
    fish_surface.fill((0, 0, 0, 0)) 
    
    
    # Draw fins (triangles)
    fin_color = (235, 117, 10)
    pygame.draw.polygon(fish_surface, fin_color, [(13, 5), (7, 0), (10, 10)])  # Left fin
    pygame.draw.polygon(fish_surface, fin_color, [(13, 15), (7, 20), (10, 10)])  # Right fin
    pygame.draw.polygon(fish_surface, fin_color, [(0, 5), (0, 15), (20, 10)])  # Tail fin

    pygame.draw.ellipse(fish_surface, (255, 147, 20), (0, 5, 20, 10))
    rotated_surface = pygame.transform.rotate(fish_surface, angle)
    rotated_rect = rotated_surface.get_rect(center=(int(position.x), int(position.y)))

    screen.blit(rotated_surface, rotated_rect)


def main():
    running = True
    clock = pygame.time.Clock()
    scatter = False  
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  
                    scatter = (scatter + 1) % 3

        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())

        screen.fill(OCEAN)

        for entity in flock:
            entity.update(flock, mouse_pos, scatter) 
            draw_fish(screen, entity.position, entity.velocity)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()



if __name__ == "__main__":
    main()
