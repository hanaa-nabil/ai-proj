import pygame
import sys
import random
import heapq
from collections import deque
import time

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 500,500
GRID_SIZE = 50
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
FPS = 3

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)

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
            # Use A* path if available
            next_pos = path[1]  # path[0] is current position
        else:
            # Manual movement
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
        # Prevent 180-degree turns
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.direction = new_direction

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Game with A* Pathfinding")
        self.clock = pygame.time.Clock()
        self.reset_game()
        
    def reset_game(self):
        self.snake = Snake()
        self.food = self.generate_food()
        self.score = 0
        self.game_over = False
        self.path = None
        self.auto_mode = True       # set true for a* false for manual
    
    def generate_food(self):
        while True:
            food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if food not in self.snake.body:
                return food
    
    def heuristic(self, a, b):
        # Manhattan distance
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def get_neighbors(self, pos):
        neighbors = []
        for dx, dy in directions:
            new_pos = ((pos[0] + dx) % GRID_WIDTH, (pos[1] + dy) % GRID_HEIGHT)
            # Check if the position is not occupied by the snake body (except tail which will move)
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
        
        # If no path is found, try to find the safest move
        return self.find_fallback_path(start)
    
    def find_fallback_path(self, start):
        # Find a path to the furthest position from the snake body
        best_distance = -1
        best_neighbor = None
        
        for neighbor in self.get_neighbors(start):
            # Calculate how far this neighbor is from all snake body parts
            min_distance = float('inf')
            for segment in self.snake.body:
                dist = self.heuristic(neighbor, segment)
                min_distance = min(min_distance, dist)
            
            if min_distance > best_distance:
                best_distance = min_distance
                best_neighbor = neighbor
        
        if best_neighbor:
            return [start, best_neighbor]
        
        # If all else fails, just return the current position (game will likely end)
        return [start]
    
    def update(self):
        if self.game_over:
            return
        
        if self.auto_mode:
            # Calculate new path every time
            self.path = self.a_star_search()
        
        self.snake.move(self.path)
        
        # Check if snake ate the food
        if self.snake.get_head() == self.food:
            self.snake.grow = True
            self.food = self.generate_food()
            self.score += 1
            self.path = None  # Recalculate path
        
        # Check collision with itself
        if self.snake.check_collision():
            self.game_over = True
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw the grid
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRAY, (0, y), (WIDTH, y))
        
        # Draw the food
        food_rect = pygame.Rect(
            self.food[0] * GRID_SIZE,
            self.food[1] * GRID_SIZE,
            GRID_SIZE, GRID_SIZE
        )
        pygame.draw.rect(self.screen, RED, food_rect)
        
        # Draw the snake
        for i, segment in enumerate(self.snake.body):
            segment_rect = pygame.Rect(
                segment[0] * GRID_SIZE,
                segment[1] * GRID_SIZE,
                GRID_SIZE, GRID_SIZE
            )
            color = GREEN if i > 0 else BLUE  # Different color for head
            pygame.draw.rect(self.screen, color, segment_rect)
        
        # Draw path if available and in auto mode
        if self.path and self.auto_mode:
            for i in range(1, len(self.path)):
                pygame.draw.line(
                    self.screen,
                    WHITE,
                    (self.path[i-1][0] * GRID_SIZE + GRID_SIZE // 2,
                     self.path[i-1][1] * GRID_SIZE + GRID_SIZE // 2),
                    (self.path[i][0] * GRID_SIZE + GRID_SIZE // 2,
                     self.path[i][1] * GRID_SIZE + GRID_SIZE // 2),
                    2
                )
        
        # Draw score
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        mode_text = font.render(f"Mode: {'Auto' if self.auto_mode else 'Manual'}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(mode_text, (WIDTH - 160, 10))
        
        if self.game_over:
            game_over_text = font.render("Game Over! Press R to restart", True, WHITE)
            text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(game_over_text, text_rect)
        
        pygame.display.flip()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.snake.change_direction(UP)
                elif event.key == pygame.K_DOWN:
                    self.snake.change_direction(DOWN)
                elif event.key == pygame.K_LEFT:
                    self.snake.change_direction(LEFT)
                elif event.key == pygame.K_RIGHT:
                    self.snake.change_direction(RIGHT)
                elif event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                elif event.key == pygame.K_a:
                    # Toggle auto mode
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