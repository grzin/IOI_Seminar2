import pygame
import random
import math
import cv2
import mediapipe as mp

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
MAX_SPEED = 2
PERCEPTION_RADIUS = 200
SEPARATION_DISTANCE = 50
TURN_RATE = 1  # Controls how quickly the velocity aligns with the desired direction
EDGE_THRESHOLD = 50  # Distance from the edge where the repelling force is applied
EDGE_FORCE = 0.15  # Magnitude of the repelling force

# Initialize webcam
cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

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
        self.rand = random.randint(0, 360)
        self.assigned_landmark = random.randint(0, 20)
        self.hand_number = random.randint(0, 10)


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

def draw_fish(screen, position, velocity, frame_count):
    angle = math.degrees(math.atan2(-velocity.y, velocity.x)) 
    
    fish_surface = pygame.Surface((60, 40), pygame.SRCALPHA)  # Increase the size of the surface
    fish_surface.fill((0, 0, 0, 0)) 
    
    # Animate fins by changing their positions slightly over time
    fin_offset = math.sin(frame_count * 0.15) * 6
    tail_offset = math.sin(frame_count * 0.1) * 6
    
    # Draw fins (triangles)
    fin_color = (235, 117, 10)
    pygame.draw.polygon(fish_surface, fin_color, [(26 + fin_offset, 12), (14, 0 + fin_offset * -1), (20, 20)])  # Left fin
    pygame.draw.polygon(fish_surface, fin_color, [(26 + fin_offset, 28), (14, 40 - fin_offset * -1), (20, 20)])  # Right fin
    pygame.draw.polygon(fish_surface, fin_color, [(0, 10 + tail_offset), (0, 30 - tail_offset), (40, 20)])  # Tail fin

    pygame.draw.ellipse(fish_surface, (255, 147, 20), (0, 10, 40, 20))  # Increase the size of the body
    rotated_surface = pygame.transform.rotate(fish_surface, angle)
    rotated_rect = rotated_surface.get_rect(center=(int(position.x), int(position.y)))

    screen.blit(rotated_surface, rotated_rect)


def main():
    running = True
    clock = pygame.time.Clock()
    scatter = 1
    frame_count = 0
    landmark_history = {4: [], 8: [], 12: [], 16: [], 20: []}
    scatter_timer = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  
                    scatter = (scatter + 1) % 3
                    

        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())

        screen.fill(OCEAN)

           # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            break
        
        # Rotate the frame 90 degrees clockwise
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Convert the frame to RGB (OpenCV uses BGR by default)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Resize the frame to fit the Pygame window
        frame = cv2.resize(frame, (HEIGHT, WIDTH))

        results = hands.process(frame)
        hand_pos = None

        # Create a Pygame surface from the frame
        frame_surface = pygame.surfarray.make_surface(frame)

        # Display the frame
        screen.blit(frame_surface, (0, 0))
        

        for entity in flock:
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                temp = hand_landmarks.landmark[entity.assigned_landmark]
                hand_pos = pygame.Vector2(temp.y * WIDTH, temp.x * HEIGHT)
                if len(results.multi_hand_landmarks) == 1 and frame_count > 150:
                    for idx in [4, 8, 12, 16, 20]:
                        landmark = hand_landmarks.landmark[idx]
                        landmark_history[idx].append(pygame.Vector2(landmark.x * WIDTH, landmark.y * HEIGHT))
                        if len(landmark_history[idx]) > 5:
                            landmark_history[idx].pop(0)
                    
                    if all(len(landmark_history[idx]) == 5 for idx in [4, 8, 12, 16, 20]):
                        diffs = [landmark_history[idx][-1].distance_to(landmark_history[idx][0]) for idx in [4, 8, 12, 16, 20]]
                        if all(diff > 50 for diff in diffs):
                            scatter = 2
                            scatter_timer = 150

                if len(results.multi_hand_landmarks) > 1:
                    hand_landmarks = results.multi_hand_landmarks[entity.hand_number % len(results.multi_hand_landmarks)]
                    temp = hand_landmarks.landmark[entity.assigned_landmark]
                    hand_pos = pygame.Vector2(temp.y * WIDTH, temp.x * HEIGHT)
            entity.update(flock, hand_pos, scatter if not hand_pos is None else 0) 
            draw_fish(screen, entity.position, entity.velocity, frame_count - entity.rand)
        
        
        if scatter_timer > 0:
            scatter_timer -= 1
            scatter = 2
        else:
            scatter = 1

        # Update the display
        pygame.display.flip()
        clock.tick(60)
        frame_count += 1

    # Release the webcam and close windows
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()



if __name__ == "__main__":
    main()
