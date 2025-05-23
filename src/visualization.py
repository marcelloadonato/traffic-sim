import pygame
import random
from src.config import *
from src.collision import get_vehicle_position, get_vehicle_direction
from src.shared import get_screen

def draw_buildings(buildings):
    """Draw buildings in the city"""
    screen = get_screen()
    for x, y, width, height, color in buildings:
        # Ensure color values are valid integers
        building_color = tuple(max(0, min(255, int(c))) for c in color)
        
        # Building body
        pygame.draw.rect(screen, building_color, (x, y, width, height))
        
        # Windows
        window_size = 8
        window_gap = 12
        for wx in range(x + 10, x + width - 10, window_gap):
            for wy in range(y + 10, y + height - 10, window_gap):
                # Only draw some windows (random pattern)
                if random.random() > 0.3:  # 70% chance to draw a window
                    pygame.draw.rect(screen, (200, 230, 255), (wx, wy, window_size, window_size))
        
        # Roof
        roof_height = random.randint(5, 15)
        # Calculate roof color by darkening the building color
        roof_color = tuple(max(0, min(255, int(c - 30))) for c in building_color)
        
        if random.random() > 0.5:  # 50% chance for a different roof style
            # Flat roof with edge
            pygame.draw.rect(screen, roof_color, (x, y - roof_height, width, roof_height))
        else:
            # Pitched roof
            pygame.draw.polygon(screen, roof_color, [(x, y), (x + width, y), (x + width//2, y - roof_height)])

def draw_road():
    """Draw the road with lanes and markings"""
    screen = get_screen()
    
    # Create static grass texture if it doesn't exist
    if not hasattr(draw_road, 'grass_surface'):
        draw_road.grass_surface = pygame.Surface((WIDTH, HEIGHT))
        draw_road.grass_surface.fill(GRASS_GREEN)
        # Add subtle texture variations
        for y in range(0, HEIGHT, 20):
            for x in range(0, WIDTH, 20):
                variation = random.randint(-10, 10)
                grass_color = (34 + variation, 139 + variation, 34 + variation)
                pygame.draw.rect(draw_road.grass_surface, grass_color, (x, y, 20, 20))
    
    # Create static road texture if it doesn't exist
    if not hasattr(draw_road, 'road_h') or not hasattr(draw_road, 'road_v'):
        # Horizontal road
        draw_road.road_h = pygame.Surface((WIDTH, ROAD_WIDTH))
        draw_road.road_h.fill(GRAY)
        # Vertical road
        draw_road.road_v = pygame.Surface((ROAD_WIDTH, HEIGHT))
        draw_road.road_v.fill(GRAY)
        
        # Add static asphalt texture
        for i in range(2000):
            # Horizontal road texture
            x = random.randint(0, WIDTH-1)
            y = random.randint(0, ROAD_WIDTH-1)
            color_var = random.randint(-10, 10)
            pygame.draw.circle(draw_road.road_h, (128 + color_var, 128 + color_var, 128 + color_var), (x, y), 1)
            
            # Vertical road texture
            x = random.randint(0, ROAD_WIDTH-1)
            y = random.randint(0, HEIGHT-1)
            color_var = random.randint(-10, 10)
            pygame.draw.circle(draw_road.road_v, (128 + color_var, 128 + color_var, 128 + color_var), (x, y), 1)
    
    # Draw the static textures
    screen.blit(draw_road.grass_surface, (0, 0))
    screen.blit(draw_road.road_h, (0, HEIGHT//2 - ROAD_WIDTH//2))
    screen.blit(draw_road.road_v, (WIDTH//2 - ROAD_WIDTH//2, 0))
    
    # Draw road edges (darker lines)
    pygame.draw.line(screen, DARK_GRAY, (0, HEIGHT//2 - ROAD_WIDTH//2), (WIDTH, HEIGHT//2 - ROAD_WIDTH//2), 3)
    pygame.draw.line(screen, DARK_GRAY, (0, HEIGHT//2 + ROAD_WIDTH//2), (WIDTH, HEIGHT//2 + ROAD_WIDTH//2), 3)
    pygame.draw.line(screen, DARK_GRAY, (WIDTH//2 - ROAD_WIDTH//2, 0), (WIDTH//2 - ROAD_WIDTH//2, HEIGHT), 3)
    pygame.draw.line(screen, DARK_GRAY, (WIDTH//2 + ROAD_WIDTH//2, 0), (WIDTH//2 + ROAD_WIDTH//2, HEIGHT), 3)
    
    # Draw lane dividers - horizontal road
    center_y = HEIGHT // 2
    dash_length = LANE_MARKER_LENGTH
    gap_length = LANE_MARKER_GAP
    
    # Draw dashed lines with shadow effect
    for x in range(0, WIDTH, dash_length + gap_length):
        if x < WIDTH//2 - ROAD_WIDTH//2 or x > WIDTH//2 + ROAD_WIDTH//2:
            # Draw shadow
            pygame.draw.rect(screen, DARK_GRAY, (x, center_y - LANE_MARKER_WIDTH//2 + 1, dash_length, LANE_MARKER_WIDTH))
            # Draw white line
            pygame.draw.rect(screen, WHITE, (x, center_y - LANE_MARKER_WIDTH//2, dash_length, LANE_MARKER_WIDTH))
    
    # Draw lane dividers - vertical road
    center_x = WIDTH // 2
    for y in range(0, HEIGHT, dash_length + gap_length):
        if y < HEIGHT//2 - ROAD_WIDTH//2 or y > HEIGHT//2 + ROAD_WIDTH//2:
            # Draw shadow
            pygame.draw.rect(screen, DARK_GRAY, (center_x - LANE_MARKER_WIDTH//2 + 1, y, LANE_MARKER_WIDTH, dash_length))
            # Draw white line
            pygame.draw.rect(screen, WHITE, (center_x - LANE_MARKER_WIDTH//2, y, LANE_MARKER_WIDTH, dash_length))
    
    # Draw intersection box with crosswalk
    intersection_rect = pygame.Rect(WIDTH//2 - ROAD_WIDTH//2, HEIGHT//2 - ROAD_WIDTH//2, ROAD_WIDTH, ROAD_WIDTH)
    pygame.draw.rect(screen, DARK_GRAY, intersection_rect)
    
    # Draw crosswalks with 3D effect
    crosswalk_width = 5
    crosswalk_gap = 5
    crosswalk_length = 20
    shadow_offset = 1
    
    # North crosswalk
    for x in range(WIDTH//2 - ROAD_WIDTH//2 + 10, WIDTH//2 + ROAD_WIDTH//2 - 10, crosswalk_width + crosswalk_gap):
        # Draw shadow
        pygame.draw.rect(screen, DARK_GRAY, (x + shadow_offset, HEIGHT//2 - ROAD_WIDTH//2 - crosswalk_length + shadow_offset, 
                                           crosswalk_width, crosswalk_length))
        # Draw white stripe
        pygame.draw.rect(screen, WHITE, (x, HEIGHT//2 - ROAD_WIDTH//2 - crosswalk_length, crosswalk_width, crosswalk_length))
    
    # South crosswalk
    for x in range(WIDTH//2 - ROAD_WIDTH//2 + 10, WIDTH//2 + ROAD_WIDTH//2 - 10, crosswalk_width + crosswalk_gap):
        pygame.draw.rect(screen, DARK_GRAY, (x + shadow_offset, HEIGHT//2 + ROAD_WIDTH//2 + shadow_offset, 
                                           crosswalk_width, crosswalk_length))
        pygame.draw.rect(screen, WHITE, (x, HEIGHT//2 + ROAD_WIDTH//2, crosswalk_width, crosswalk_length))
    
    # East crosswalk
    for y in range(HEIGHT//2 - ROAD_WIDTH//2 + 10, HEIGHT//2 + ROAD_WIDTH//2 - 10, crosswalk_width + crosswalk_gap):
        pygame.draw.rect(screen, DARK_GRAY, (WIDTH//2 + ROAD_WIDTH//2 + shadow_offset, y + shadow_offset, 
                                           crosswalk_length, crosswalk_width))
        pygame.draw.rect(screen, WHITE, (WIDTH//2 + ROAD_WIDTH//2, y, crosswalk_length, crosswalk_width))
    
    # West crosswalk
    for y in range(HEIGHT//2 - ROAD_WIDTH//2 + 10, HEIGHT//2 + ROAD_WIDTH//2 - 10, crosswalk_width + crosswalk_gap):
        pygame.draw.rect(screen, DARK_GRAY, (WIDTH//2 - ROAD_WIDTH//2 - crosswalk_length + shadow_offset, y + shadow_offset, 
                                           crosswalk_length, crosswalk_width))
        pygame.draw.rect(screen, WHITE, (WIDTH//2 - ROAD_WIDTH//2 - crosswalk_length, y, crosswalk_length, crosswalk_width))

def draw_traffic_lights(ns_light, ew_light):
    """Draw traffic lights on all four sides of the intersection"""
    screen = get_screen()
    
    def draw_light_housing(x, y, width, height, vertical=True):
        """Helper function to draw a traffic light housing with 3D effect"""
        # Draw main housing shadow
        shadow_offset = 3
        pygame.draw.rect(screen, (30, 30, 30), 
                        (x + shadow_offset, y + shadow_offset, width, height), border_radius=5)
        
        # Draw main housing
        pygame.draw.rect(screen, BLACK, (x, y, width, height), border_radius=5)
        
        # Draw metallic highlight
        highlight_width = 2
        pygame.draw.rect(screen, (60, 60, 60),
                        (x + (0 if vertical else highlight_width), 
                         y + (highlight_width if vertical else 0),
                         width - (0 if vertical else highlight_width*2),
                         height - (highlight_width*2 if vertical else 0)),
                        border_radius=4)
    
    def draw_light(x, y, color, is_active):
        """Helper function to draw a single traffic light with glow effect"""
        light_size = 12
        # Draw glow for active light
        if is_active:
            glow_size = light_size * 2
            glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            for radius in range(int(light_size * 0.7), -1, -1):
                alpha = int(100 * (radius / (light_size * 0.7)))
                pygame.draw.circle(glow_surface, (*color, alpha), (glow_size//2, glow_size//2), radius)
            # Center the glow precisely on the light
            screen.blit(glow_surface, (x - glow_size//2, y - glow_size//2))
        
        # Draw light housing (black ring)
        pygame.draw.circle(screen, BLACK, (x, y), light_size//2 + 1)
        
        # Draw the light
        light_color = color if is_active else (color[0]//3, color[1]//3, color[2]//3)
        pygame.draw.circle(screen, light_color, (x, y), light_size//2)
        
        # Add highlight reflection (slightly offset from center)
        if is_active:
            highlight_pos = (x - light_size//6, y - light_size//6)
            pygame.draw.circle(screen, (255, 255, 255), highlight_pos, 2)
    
    # Traffic light positions and dimensions
    housing_width = 24
    housing_height = 65
    pole_width = 8
    
    # North traffic light (facing south)
    pole_x = WIDTH//2 + ROAD_WIDTH//2 + 40  # Position on the grass to the right of the road
    pole_y = HEIGHT//2 - ROAD_WIDTH//2 - housing_height - 20  # Original height
    pole_base_y = HEIGHT//2 - ROAD_WIDTH//2 - 20  # Move the base up by 60 pixels
    # Draw pole from higher base position
    pygame.draw.rect(screen, BLACK, (pole_x - pole_width//2, pole_base_y, pole_width, pole_y + housing_height - pole_base_y))
    draw_light_housing(pole_x - housing_width//2, pole_y, housing_width, housing_height)
    
    center_x = pole_x
    draw_light(center_x, pole_y + 15, RED, ns_light == "red")
    draw_light(center_x, pole_y + 32, YELLOW, ns_light == "yellow")
    draw_light(center_x, pole_y + 49, GREEN, ns_light == "green")
    
    # East traffic light (facing west)
    pole_x = WIDTH//2 + ROAD_WIDTH//2 + 40  # Light position
    pole_y = HEIGHT//2 + ROAD_WIDTH//2 + 40  # Position on the grass below the road
    pole_base_x = WIDTH//2 + ROAD_WIDTH//2 + 20  # Move the base right by 60 pixels
    # Draw pole from more rightward base position
    pygame.draw.rect(screen, BLACK, (pole_base_x, pole_y - pole_width//2, pole_x - pole_base_x + housing_height, pole_width))
    draw_light_housing(pole_x, pole_y - housing_width//2, housing_height, housing_width, vertical=False)
    
    center_y = pole_y
    draw_light(pole_x + 15, center_y, RED, ew_light == "red")
    draw_light(pole_x + 32, center_y, YELLOW, ew_light == "yellow")
    draw_light(pole_x + 49, center_y, GREEN, ew_light == "green")

def draw_vehicle(vehicle, debug_mode=False):
    """Draw a vehicle on the screen"""
    screen = get_screen()
    
    # Get vehicle position
    if hasattr(vehicle, 'interpolated_position') and vehicle.interpolated_position is not None:
        x, y = vehicle.interpolated_position
    else:
        # Fall back to edge positions if no interpolation
        if vehicle.position == 'north':
            x, y = WIDTH//2, 0
        elif vehicle.position == 'south':
            x, y = WIDTH//2, HEIGHT
        elif vehicle.position == 'east':
            x, y = WIDTH, HEIGHT//2
        elif vehicle.position == 'west':
            x, y = 0, HEIGHT//2
        elif vehicle.position == 'intersection':
            # Use the previous position if at intersection
            current_idx = vehicle.route.index(vehicle.position)
            if current_idx > 0 and isinstance(vehicle.route[current_idx - 1], tuple):
                x, y = vehicle.route[current_idx - 1]
            else:
                return  # Skip drawing if position cannot be determined
        elif isinstance(vehicle.position, tuple):
            x, y = vehicle.position
        else:
            return  # Skip drawing if position cannot be determined
    
    # Get vehicle direction
    direction = get_vehicle_direction(vehicle)
    
    # Determine vehicle color based on type
    if not hasattr(vehicle, 'color') or vehicle.color is None:
        if vehicle.vehicle_type == "car":
            vehicle.color = random.choice([(255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 165, 0), (128, 0, 128)])
        elif vehicle.vehicle_type == "truck":
            vehicle.color = random.choice([(192, 192, 192), (139, 69, 19), (47, 79, 79)])
        else:  # van
            vehicle.color = random.choice([(255, 255, 255), (255, 215, 0), (70, 130, 180)])
    
    # Draw the vehicle
    draw_car((x, y), vehicle.color, direction, vehicle)
    
    # Draw vehicle ID with better visibility
    if debug_mode:
        # Create a background for the ID
        font = pygame.font.Font(None, 24)  # Larger font size
        id_text = str(id(vehicle) % 1000)  # Keep last 3 digits of ID
        text_surface = font.render(id_text, True, WHITE)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        
        # Draw a semi-transparent background for better readability
        padding = 2
        background_rect = pygame.Rect(text_rect.x - padding,
                                    text_rect.y - padding,
                                    text_rect.width + padding * 2,
                                    text_rect.height + padding * 2)
        background_surface = pygame.Surface((background_rect.width, background_rect.height))
        background_surface.fill(BLACK)
        background_surface.set_alpha(160)  # Semi-transparent background
        screen.blit(background_surface, background_rect)
        
        # Draw the ID text
        screen.blit(text_surface, text_rect)

def draw_car(pos, color, direction, vehicle):
    """Draw a car-like shape at the given position with the given color and direction"""
    screen = get_screen()
    x, y = pos
    
    # Car dimensions - adjusted by vehicle type
    car_length = 24 * vehicle.size_multiplier  # Slightly larger base size
    car_width = 14 * vehicle.size_multiplier
    
    # Adjust dimensions for horizontal vs vertical orientation
    if direction == 'left' or direction == 'right':
        car_length, car_width = car_width, car_length
    
    # Draw shadow first (offset by 2 pixels)
    shadow_rect = pygame.Rect(x - car_width//2 + 2, y - car_length//2 + 2, car_width, car_length)
    pygame.draw.rect(screen, (30, 30, 30, 128), shadow_rect, border_radius=3)
    
    # Create the rectangle for the car body
    car_rect = pygame.Rect(x - car_width//2, y - car_length//2, car_width, car_length)
    
    # Draw the car based on direction and type
    if direction == 'down' or direction == 'up':
        # Car body
        pygame.draw.rect(screen, color, car_rect, border_radius=3)
        
        # Add a highlight effect on the side
        highlight_width = 2
        highlight_color = (min(color[0] + 50, 255), min(color[1] + 50, 255), min(color[2] + 50, 255))
        if direction == 'down':
            pygame.draw.rect(screen, highlight_color, 
                           (x - car_width//2, y - car_length//2, highlight_width, car_length), border_radius=2)
        else:
            pygame.draw.rect(screen, highlight_color,
                           (x + car_width//2 - highlight_width, y - car_length//2, highlight_width, car_length), border_radius=2)
        
        # Vehicle type specific details
        if vehicle.vehicle_type == "car":
            # Windshield (with gradient effect)
            window_width = car_width - 4
            window_length = 8
            window_rect = pygame.Rect(x - window_width//2, 
                                    y - car_length//2 + 3 if direction == 'down' else y + car_length//2 - window_length - 3,
                                    window_width, window_length)
            pygame.draw.rect(screen, (100, 150, 255), window_rect, border_radius=1)
            pygame.draw.rect(screen, (200, 230, 255), window_rect, border_radius=1, width=1)
            
            # Side windows
            side_window_length = car_length // 3
            side_window_width = 2
            pygame.draw.rect(screen, (200, 230, 255),
                           (x - car_width//2 - 1, y - side_window_length//2, side_window_width, side_window_length))
            pygame.draw.rect(screen, (200, 230, 255),
                           (x + car_width//2 - 1, y - side_window_length//2, side_window_width, side_window_length))
            
            # Rear window
            rear_window = pygame.Rect(x - window_width//2,
                                    y + car_length//2 - 8 if direction == 'down' else y - car_length//2 + 3,
                                    window_width, 5)
            pygame.draw.rect(screen, (100, 150, 255), rear_window, border_radius=1)
            pygame.draw.rect(screen, (200, 230, 255), rear_window, border_radius=1, width=1)
            
        elif vehicle.vehicle_type == "truck":
            # Truck cab with metallic effect
            cab_width = car_width - 2
            cab_length = car_length // 3
            cab_rect = pygame.Rect(x - cab_width//2, y - car_length//2, cab_width, cab_length)
            cab_color = (min(color[0] + 30, 255), min(color[1] + 30, 255), min(color[2] + 30, 255))
            pygame.draw.rect(screen, cab_color, cab_rect, border_radius=2)
            
            # Truck windshield
            window_width = cab_width - 4
            window_rect = pygame.Rect(x - window_width//2, y - car_length//2 + 2, window_width, 4)
            pygame.draw.rect(screen, (100, 150, 255), window_rect, border_radius=1)
            pygame.draw.rect(screen, (200, 230, 255), window_rect, border_radius=1, width=1)
            
            # Cargo area details
            pygame.draw.line(screen, (50, 50, 50), 
                           (x - car_width//2 + 2, y - car_length//2 + cab_length),
                           (x + car_width//2 - 2, y - car_length//2 + cab_length))
            
        elif vehicle.vehicle_type == "van":
            # Van windows with larger area
            window_width = car_width - 4
            window_length = car_length // 2
            window_rect = pygame.Rect(x - window_width//2, y - car_length//2 + 3, window_width, window_length)
            pygame.draw.rect(screen, (100, 150, 255), window_rect, border_radius=1)
            pygame.draw.rect(screen, (200, 230, 255), window_rect, border_radius=1, width=1)
            
            # Side panel lines
            pygame.draw.line(screen, (50, 50, 50),
                           (x - car_width//2 + 2, y),
                           (x + car_width//2 - 2, y))
        
        # Wheels with better detail
        wheel_size = 4 * vehicle.size_multiplier
        for wheel_x in [x - car_width//2 - 1, x + car_width//2 - wheel_size + 1]:
            for wheel_y in [y - car_length//4, y + car_length//4]:
                # Wheel shadow
                pygame.draw.rect(screen, (20, 20, 20), 
                               (wheel_x + 1, wheel_y + 1, wheel_size, wheel_size))
                # Wheel
                pygame.draw.rect(screen, BLACK,
                               (wheel_x, wheel_y, wheel_size, wheel_size))
                # Wheel hub
                pygame.draw.rect(screen, (80, 80, 80),
                               (wheel_x + 1, wheel_y + 1, wheel_size - 2, wheel_size - 2))
        
        # Headlights with glow effect
        headlight_size = 3 * vehicle.size_multiplier
        for headlight_x in [x - car_width//2 + 2, x + car_width//2 - headlight_size - 2]:
            headlight_y = y - car_length//2 + 2 if direction == 'down' else y + car_length//2 - headlight_size - 2
            # Glow
            pygame.draw.circle(screen, (255, 255, 200, 64),
                             (headlight_x + headlight_size//2, headlight_y + headlight_size//2),
                             headlight_size * 1.5)
            # Headlight
            pygame.draw.rect(screen, (255, 255, 200),
                           (headlight_x, headlight_y, headlight_size, headlight_size))
    
    elif direction == 'right' or direction == 'left':
        # Similar enhancements for horizontal orientation
        pygame.draw.rect(screen, color, car_rect, border_radius=3)
        
        # Add highlight effect on top
        highlight_height = 2
        highlight_color = (min(color[0] + 50, 255), min(color[1] + 50, 255), min(color[2] + 50, 255))
        pygame.draw.rect(screen, highlight_color,
                        (x - car_length//2, y - car_width//2, car_length, highlight_height), border_radius=2)
        
        # Vehicle type specific details (adjusted for horizontal orientation)
        if vehicle.vehicle_type == "car":
            window_height = car_width - 4
            window_width = 8
            window_rect = pygame.Rect(x - car_length//2 + 3 if direction == 'right' else x + car_length//2 - window_width - 3,
                                    y - window_height//2, window_width, window_height)
            pygame.draw.rect(screen, (100, 150, 255), window_rect, border_radius=1)
            pygame.draw.rect(screen, (200, 230, 255), window_rect, border_radius=1, width=1)
        
        # Wheels for horizontal orientation
        wheel_size = 4 * vehicle.size_multiplier
        for wheel_y in [y - car_width//2 - 1, y + car_width//2 - wheel_size + 1]:
            for wheel_x in [x - car_length//4, x + car_length//4]:
                # Wheel shadow
                pygame.draw.rect(screen, (20, 20, 20),
                               (wheel_x + 1, wheel_y + 1, wheel_size, wheel_size))
                # Wheel
                pygame.draw.rect(screen, BLACK,
                               (wheel_x, wheel_y, wheel_size, wheel_size))
                # Wheel hub
                pygame.draw.rect(screen, (80, 80, 80),
                               (wheel_x + 1, wheel_y + 1, wheel_size - 2, wheel_size - 2))
        
        # Headlights for horizontal orientation
        headlight_size = 3 * vehicle.size_multiplier
        for headlight_y in [y - car_width//2 + 2, y + car_width//2 - headlight_size - 2]:
            headlight_x = x - car_length//2 + 2 if direction == 'right' else x + car_length//2 - headlight_size - 2
            # Glow
            pygame.draw.circle(screen, (255, 255, 200, 64),
                             (headlight_x + headlight_size//2, headlight_y + headlight_size//2),
                             headlight_size * 1.5)
            # Headlight
            pygame.draw.rect(screen, (255, 255, 200),
                           (headlight_x, headlight_y, headlight_size, headlight_size))

def draw_debug_info(ns_light, ew_light, active_vehicles, spawn_schedule, current_tick, episode_length, lane_counts):
    """Draw debug information"""
    screen = get_screen()
    
    # Draw lane entry/exit points
    for lane, pos_data in LANES.items():
        # Entry points
        pygame.draw.circle(screen, DEBUG_COLORS['lane_entry'], pos_data['in'], 5)
        # Exit points
        pygame.draw.circle(screen, DEBUG_COLORS['lane_exit'], pos_data['out'], 5)
        # Queue positions
        for pos in pos_data['queue']:
            pygame.draw.circle(screen, DEBUG_COLORS['queue_pos'], pos, 3)
    
    # Draw intersection center marker
    pygame.draw.circle(screen, DEBUG_COLORS['intersection'], (WIDTH//2, HEIGHT//2), 8, width=2) 