import pygame

# Display settings
WIDTH = 1200  # Increased from previous size
HEIGHT = 800  # Increased from previous size
FPS = 30
SLOW_FPS = 10

# Speed slider settings
SPEED_SLIDER = {
    'x': 100,
    'y': HEIGHT - 30,
    'width': WIDTH - 200,
    'height': 10,
    'min_fps': 1,
    'max_fps': 60,
    'default_fps': 30,
    'handle_radius': 8,
    'background': (200, 200, 200),
    'handle': (100, 100, 100),
    'active_handle': (50, 50, 50),
    'label_color': (0, 0, 0)
}

# Training steps slider configuration
TRAINING_SLIDER = {
    'x': 100,
    'y': HEIGHT - 60,
    'width': WIDTH - 200,
    'height': 10,
    'min_steps': 100,
    'max_steps': 20000,
    'default_steps': 2000
}

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
GRASS_GREEN = (34, 139, 34)
BUILDING_COLORS = [
    (139, 69, 19),    # Brown
    (160, 82, 45),    # Sienna
    (205, 133, 63),   # Peru
    (210, 180, 140),  # Tan
    (188, 143, 143),  # Rosy brown
]

# Road settings
ROAD_WIDTH = 100
LANE_MARKER_LENGTH = 30
LANE_MARKER_WIDTH = 3
LANE_MARKER_GAP = 20

# Debug colors
DEBUG_COLORS = {
    'lane_entry': (255, 0, 0),      # Red for entry points
    'lane_exit': (0, 0, 255),       # Blue for exit points
    'queue_pos': (0, 180, 0),       # Dark green for queue positions
    'intersection': (255, 255, 0),   # Yellow for intersection center
    'collision_area': (255, 0, 0, 128),  # Transparent red for collision detection
    'route_preview': (0, 255, 255)   # Cyan for route preview
}

# UI settings
FONT_SIZE = {
    'stats': 16,
    'debug': 14,
    'episode': 24,
    'vehicle_id': 10
}

STATS_PANEL = {
    'width': 250,
    'height': 130,
    'padding': 10,
    'background': (240, 240, 240, 200),
    'border': BLACK
}

DEBUG_PANEL = {
    'width': 250,
    'height': 200,
    'padding': 10,
    'background': (240, 240, 240, 200),
    'border': BLACK
}

# Vehicle settings
VEHICLE_TYPES = {
    'car': {'size': 1.0, 'speed': 1.0},
    'truck': {'size': 1.4, 'speed': 0.8},
    'van': {'size': 1.2, 'speed': 0.9}
}

# Simulation settings
DEBUG_MODE = False
SLOW_MODE = False
EPISODE_LENGTH = 1000
MAX_VEHICLES_PER_LANE = 4
TOTAL_VEHICLES = 20

# Lane positions (adjusted for new window size)
LANES = {
    'north': {
        'in': (WIDTH//2 - ROAD_WIDTH//4, 0),
        'out': (WIDTH//2 + ROAD_WIDTH//4, 0),
        'queue': [(WIDTH//2 - ROAD_WIDTH//4, y) for y in range(50, HEIGHT//2 - ROAD_WIDTH//2 - 50, 30)]
    },
    'south': {
        'in': (WIDTH//2 + ROAD_WIDTH//4, HEIGHT),
        'out': (WIDTH//2 - ROAD_WIDTH//4, HEIGHT),
        'queue': [(WIDTH//2 + ROAD_WIDTH//4, y) for y in range(HEIGHT - 50, HEIGHT//2 + ROAD_WIDTH//2 + 50, -30)]
    },
    'east': {
        'in': (WIDTH, HEIGHT//2 + ROAD_WIDTH//4),
        'out': (WIDTH, HEIGHT//2 - ROAD_WIDTH//4),
        'queue': [(x, HEIGHT//2 + ROAD_WIDTH//4) for x in range(WIDTH - 50, WIDTH//2 + ROAD_WIDTH//2 + 50, -30)]
    },
    'west': {
        'in': (0, HEIGHT//2 - ROAD_WIDTH//4),
        'out': (0, HEIGHT//2 + ROAD_WIDTH//4),
        'queue': [(x, HEIGHT//2 - ROAD_WIDTH//4) for x in range(50, WIDTH//2 - ROAD_WIDTH//2 - 50, 30)]
    }
}

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Traffic Simulation MVP")
clock = pygame.time.Clock()

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