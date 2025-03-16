import pygame

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Traffic Simulation MVP")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
GRASS_GREEN = (100, 200, 100)
BUILDING_COLORS = [
    (180, 180, 180),  # Light gray
    (160, 140, 120),  # Tan
    (120, 110, 100),  # Brown
    (100, 130, 170),  # Blue-gray
    (150, 150, 170)   # Lavender-gray
]

# Road dimensions
ROAD_WIDTH = 100
LANE_WIDTH = 40
LANE_MARKER_WIDTH = 5
LANE_MARKER_LENGTH = 30
LANE_MARKER_GAP = 20

# Lane positions for different directions
LANES = {
    'north': {'in': (WIDTH//2, HEIGHT//2 - 70), 'out': (WIDTH//2, 50), 'direction': 'down', 
              'queue': [(WIDTH//2, 100), (WIDTH//2, 150), (WIDTH//2, 200), (WIDTH//2, 250)]},
    'south': {'in': (WIDTH//2, HEIGHT//2 + 70), 'out': (WIDTH//2, HEIGHT - 50), 'direction': 'up',
              'queue': [(WIDTH//2, HEIGHT - 100), (WIDTH//2, HEIGHT - 150), (WIDTH//2, HEIGHT - 200), (WIDTH//2, HEIGHT - 250)]},
    'east': {'in': (WIDTH//2 + 70, HEIGHT//2), 'out': (WIDTH - 50, HEIGHT//2), 'direction': 'left',
             'queue': [(WIDTH - 100, HEIGHT//2), (WIDTH - 150, HEIGHT//2), (WIDTH - 200, HEIGHT//2), (WIDTH - 250, HEIGHT//2)]},
    'west': {'in': (WIDTH//2 - 70, HEIGHT//2), 'out': (50, HEIGHT//2), 'direction': 'right',
             'queue': [(100, HEIGHT//2), (150, HEIGHT//2), (200, HEIGHT//2), (250, HEIGHT//2)]}
}

# Intermediate positions for smoother movement
INTERMEDIATE_POSITIONS = {
    'north_to_intersection': [(WIDTH//2, HEIGHT//2 - 50), (WIDTH//2, HEIGHT//2 - 30)],
    'south_to_intersection': [(WIDTH//2, HEIGHT//2 + 50), (WIDTH//2, HEIGHT//2 + 30)],
    'east_to_intersection': [(WIDTH//2 + 50, HEIGHT//2), (WIDTH//2 + 30, HEIGHT//2)],
    'west_to_intersection': [(WIDTH//2 - 50, HEIGHT//2), (WIDTH//2 - 30, HEIGHT//2)],
    'intersection_to_north': [(WIDTH//2, HEIGHT//2 - 30), (WIDTH//2, HEIGHT//2 - 50)],
    'intersection_to_south': [(WIDTH//2, HEIGHT//2 + 30), (WIDTH//2, HEIGHT//2 + 50)],
    'intersection_to_east': [(WIDTH//2 + 30, HEIGHT//2), (WIDTH//2 + 50, HEIGHT//2)],
    'intersection_to_west': [(WIDTH//2 - 30, HEIGHT//2), (WIDTH//2 - 50, HEIGHT//2)]
}

# Vehicle colors
VEHICLE_COLORS = [
    (200, 0, 0),    # Red
    (0, 0, 200),    # Blue
    (200, 200, 0),  # Yellow
    (0, 200, 0),    # Green
    (200, 0, 200),  # Purple
    (0, 200, 200),  # Cyan
    (200, 100, 0),  # Orange
    (100, 100, 100) # Gray
]

# Simulation settings
EPISODE_LENGTH = 1000  # Length of an episode in ticks
DEBUG_MODE = True
SLOW_MODE = True  # Slow down simulation for better visibility

# Vehicle spawn settings
MAX_VEHICLES_PER_LANE = 4
TOTAL_VEHICLES = 20 