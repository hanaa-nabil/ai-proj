import pygame
import sys
import random
import heapq
from collections import deque

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 700, 500
GRID_SIZE = 20
GRID_WIDTH = (WIDTH - 200) // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
SIDEBAR_WIDTH = 200
FPS = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (50, 205, 50)
RED = (255, 50, 50)
BLUE = (30, 144, 255)
DARK_BLUE = (25, 25, 112)
GRAY = (40, 40, 40)
GOLD = (255, 215, 0)

# Direction vectors
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
directions = [UP, DOWN, LEFT, RIGHT]

class Snake:
    def __init__(self):
        self.body = deque([(GRID_WIDTH // 2, GRID_HEIGHT // 2)])
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.grow = False
        
    def get_head(self):
        return self.body[0]
    
    def move(self, path=None):
        if path and len(path) > 1:
            next_pos = path[1]
        else:
            head_x, head_y = self.get_head()
            dir_x, dir_y = self.direction
            next_pos = ((head_x + dir_x) % GRID_WIDTH, (head_y + dir_y) % GRID_HEIGHT)
        
        self.body.appendleft(next_pos)
        if not self.grow:
            self.body.pop()
        else:
            self.grow = False
            
    def check_collision(self):
        head = self.get_head()
        return head in list(self.body)[1:]
    
    def change_direction(self, new_direction):
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.direction = new_direction

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.is_hovered = False
        
    def draw(self, screen):
        color = (self.color[0]+30, self.color[1]+30, self.color[2]+30) if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=5)
        
        font = pygame.font.SysFont("Arial", 18)
        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Game with A* Pathfinding")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.title_font = pygame.font.SysFont("Arial", 24, bold=True)
        self.normal_font = pygame.font.SysFont("Arial", 18)
        
        # Create buttons
        self.reset_button = Button(WIDTH - 180, HEIGHT - 100, 160, 40, "Reset Game (R)", (128, 0, 128))
        self.toggle_button = Button(WIDTH - 180, HEIGHT - 50, 160, 40, "Toggle AI (A)", BLUE)
        
        self.reset_game()
        
    def reset_game(self):
        self.snake = Snake()
        self.food = self.generate_food()
        self.score = 0
        self.high_score = self.load_high_score()
        self.game_over = False
        self.path = None
        self.auto_mode = False
        
    def load_high_score(self):
        try:
            with open("snake_high_score.txt", "r") as f:
                return int(f.read())
        except:
            return 0
            
    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open("snake_high_score.txt", "w") as f:
                    f.write(str(self.high_score))
            except:
                pass
    
    def generate_food(self):
        while True:
            food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if food not in self.snake.body:
                return food
    
    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def get_neighbors(self, pos):
        neighbors = []
        for dx, dy in directions:
            new_pos = ((pos[0] + dx) % GRID_WIDTH, (pos[1] + dy) % GRID_HEIGHT)
            if new_pos not in list(self.snake.body)[:-1] or (new_pos == self.snake.body[-1] and not self.snake.grow):
                neighbors.append(new_pos)
        return neighbors
    
    def a_star_search(self):
        start = self.snake.get_head()
        goal = self.food
        
        open_set = [(self.heuristic(start, goal), 0, start, [])]
        closed_set = set()
        
        g_score = {start: 0}
        came_from = {}
        
        while open_set:
            _, cost, current, path = heapq.heappop(open_set)
            
            if current in closed_set:
                continue
                
            if current == goal:
                path = path + [current]
                return path
            
            closed_set.add(current)
            
            for neighbor in self.get_neighbors(current):
                if neighbor in closed_set:
                    continue
                    
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, tentative_g_score, neighbor, path + [current]))
        
        return self.find_fallback_path(start)
    
    def find_fallback_path(self, start):
        best_distance = -1
        best_neighbor = None
        
        for neighbor in self.get_neighbors(start):
            min_distance = float('inf')
            for segment in self.snake.body:
                dist = self.heuristic(neighbor, segment)
                min_distance = min(min_distance, dist)
            
            if min_distance > best_distance:
                best_distance = min_distance
                best_neighbor = neighbor
        
        if best_neighbor:
            return [start, best_neighbor]
        return [start]
    
    def update(self):
        if self.game_over:
            return
        
        if self.auto_mode:
            self.path = self.a_star_search()
        
        self.snake.move(self.path)
        
        if self.snake.get_head() == self.food:
            self.snake.grow = True
            self.food = self.generate_food()
            self.score += 1
            self.path = None
        
        if self.snake.check_collision():
            self.game_over = True
            self.save_high_score()
    
    def draw(self):
        self.screen.fill(DARK_BLUE)
        
        # Draw game area
        for x in range(0, WIDTH - SIDEBAR_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRAY, (0, y), (WIDTH - SIDEBAR_WIDTH, y), 1)
        
        # Draw food
        food_rect = pygame.Rect(
            self.food[0] * GRID_SIZE,
            self.food[1] * GRID_SIZE,
            GRID_SIZE, GRID_SIZE
        )
        pygame.draw.rect(self.screen, RED, food_rect)
        pygame.draw.rect(self.screen, GOLD, food_rect, 1)
        
        # Draw snake
        for i, segment in enumerate(self.snake.body):
            segment_rect = pygame.Rect(
                segment[0] * GRID_SIZE,
                segment[1] * GRID_SIZE,
                GRID_SIZE, GRID_SIZE
            )
            color = BLUE if i == 0 else GREEN
            pygame.draw.rect(self.screen, color, segment_rect)
            pygame.draw.rect(self.screen, WHITE if i == 0 else (0, 180, 0), segment_rect, 1)
            
            # Draw eyes on head
            if i == 0:
                eye_size = GRID_SIZE // 5
                # Left eye position
                left_eye_x = segment[0] * GRID_SIZE + GRID_SIZE // 4
                left_eye_y = segment[1] * GRID_SIZE + GRID_SIZE // 4
                # Right eye position
                right_eye_x = segment[0] * GRID_SIZE + 3 * GRID_SIZE // 4
                right_eye_y = segment[1] * GRID_SIZE + GRID_SIZE // 4
                
                pygame.draw.circle(self.screen, WHITE, (left_eye_x, left_eye_y), eye_size)
                pygame.draw.circle(self.screen, WHITE, (right_eye_x, right_eye_y), eye_size)
                pygame.draw.circle(self.screen, BLACK, (left_eye_x, left_eye_y), eye_size // 2)
                pygame.draw.circle(self.screen, BLACK, (right_eye_x, right_eye_y), eye_size // 2)
        
        # Draw path if available and in auto mode
        if self.path and self.auto_mode:
            for i in range(1, len(self.path)):
                pygame.draw.line(
                    self.screen,
                    (255, 255, 255, 128),
                    (self.path[i-1][0] * GRID_SIZE + GRID_SIZE // 2,
                     self.path[i-1][1] * GRID_SIZE + GRID_SIZE // 2),
                    (self.path[i][0] * GRID_SIZE + GRID_SIZE // 2,
                     self.path[i][1] * GRID_SIZE + GRID_SIZE // 2),
                    2
                )
        
        # Draw sidebar
        sidebar_rect = pygame.Rect(WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
        pygame.draw.rect(self.screen, (30, 30, 50), sidebar_rect)
        pygame.draw.line(self.screen, WHITE, (WIDTH - SIDEBAR_WIDTH, 0), (WIDTH - SIDEBAR_WIDTH, HEIGHT), 2)
        
        # Draw info on sidebar
        title_text = self.title_font.render("SNAKE GAME", True, WHITE)
        self.screen.blit(title_text, (WIDTH - SIDEBAR_WIDTH + 20, 20))
        
        score_text = self.normal_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (WIDTH - SIDEBAR_WIDTH + 20, 60))
        
        high_score_text = self.normal_font.render(f"High Score: {self.high_score}", True, GOLD)
        self.screen.blit(high_score_text, (WIDTH - SIDEBAR_WIDTH + 20, 90))
        
        mode_text = self.normal_font.render(f"Mode: {'AI' if self.auto_mode else 'Manual'}", True, WHITE)
        self.screen.blit(mode_text, (WIDTH - SIDEBAR_WIDTH + 20, 130))
        
        # Draw controls info
        controls_header = self.normal_font.render("Controls:", True, WHITE)
        self.screen.blit(controls_header, (WIDTH - SIDEBAR_WIDTH + 20, 180))
        
        controls = ["← → ↑ ↓ : Move Snake", "A: Toggle AI Mode", "R: Reset Game"]
        for i, text in enumerate(controls):
            control_text = self.normal_font.render(text, True, (180, 180, 180))
            self.screen.blit(control_text, (WIDTH - SIDEBAR_WIDTH + 20, 210 + i * 30))
        
        # Draw buttons
        self.reset_button.draw(self.screen)
        self.toggle_button.draw(self.screen)
        
        # Draw game over screen
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.title_font.render("GAME OVER", True, WHITE)
            text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            self.screen.blit(game_over_text, text_rect)
            
            score_text = self.normal_font.render(f"Final Score: {self.score}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
            self.screen.blit(score_text, score_rect)
        
        pygame.display.flip()
    
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        self.reset_button.check_hover(mouse_pos)
        self.toggle_button.check_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Button clicks
            if self.reset_button.is_clicked(mouse_pos, event):
                self.reset_game()
            
            if self.toggle_button.is_clicked(mouse_pos, event):
                self.auto_mode = not self.auto_mode
                if self.auto_mode:
                    self.path = self.a_star_search()
            
            # Key presses
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.snake.change_direction(UP)
                elif event.key == pygame.K_DOWN:
                    self.snake.change_direction(DOWN)
                elif event.key == pygame.K_LEFT:
                    self.snake.change_direction(LEFT)
                elif event.key == pygame.K_RIGHT:
                    self.snake.change_direction(RIGHT)
                elif event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_a:
                    self.auto_mode = not self.auto_mode
                    if self.auto_mode:
                        self.path = self.a_star_search()
    
    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
