import pygame
import random
from config import *
from collision import get_vehicle_position, get_vehicle_direction
from shared import get_screen

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
    # Draw grass background
    pygame.draw.rect(screen, GRASS_GREEN, (0, 0, WIDTH, HEIGHT))
    
    # Draw horizontal road
    pygame.draw.rect(screen, GRAY, (0, HEIGHT//2 - ROAD_WIDTH//2, WIDTH, ROAD_WIDTH))
    
    # Draw vertical road
    pygame.draw.rect(screen, GRAY, (WIDTH//2 - ROAD_WIDTH//2, 0, ROAD_WIDTH, HEIGHT))
    
    # Draw lane dividers - horizontal road
    center_y = HEIGHT // 2
    for x in range(0, WIDTH, LANE_MARKER_LENGTH + LANE_MARKER_GAP):
        if x < WIDTH//2 - ROAD_WIDTH//2 or x > WIDTH//2 + ROAD_WIDTH//2:
            pygame.draw.rect(screen, WHITE, (x, center_y - LANE_MARKER_WIDTH//2, LANE_MARKER_LENGTH, LANE_MARKER_WIDTH))
    
    # Draw lane dividers - vertical road
    center_x = WIDTH // 2
    for y in range(0, HEIGHT, LANE_MARKER_LENGTH + LANE_MARKER_GAP):
        if y < HEIGHT//2 - ROAD_WIDTH//2 or y > HEIGHT//2 + ROAD_WIDTH//2:
            pygame.draw.rect(screen, WHITE, (center_x - LANE_MARKER_WIDTH//2, y, LANE_MARKER_WIDTH, LANE_MARKER_LENGTH))
    
    # Draw intersection box
    pygame.draw.rect(screen, DARK_GRAY, (WIDTH//2 - ROAD_WIDTH//2, HEIGHT//2 - ROAD_WIDTH//2, ROAD_WIDTH, ROAD_WIDTH))
    
    # Draw crosswalks
    crosswalk_width = 5
    crosswalk_gap = 5
    
    # North crosswalk
    for x in range(WIDTH//2 - ROAD_WIDTH//2 + 10, WIDTH//2 + ROAD_WIDTH//2 - 10, crosswalk_width + crosswalk_gap):
        pygame.draw.rect(screen, WHITE, (x, HEIGHT//2 - ROAD_WIDTH//2 - 20, crosswalk_width, 20))
    
    # South crosswalk
    for x in range(WIDTH//2 - ROAD_WIDTH//2 + 10, WIDTH//2 + ROAD_WIDTH//2 - 10, crosswalk_width + crosswalk_gap):
        pygame.draw.rect(screen, WHITE, (x, HEIGHT//2 + ROAD_WIDTH//2, crosswalk_width, 20))
    
    # East crosswalk
    for y in range(HEIGHT//2 - ROAD_WIDTH//2 + 10, HEIGHT//2 + ROAD_WIDTH//2 - 10, crosswalk_width + crosswalk_gap):
        pygame.draw.rect(screen, WHITE, (WIDTH//2 + ROAD_WIDTH//2, y, 20, crosswalk_width))
    
    # West crosswalk
    for y in range(HEIGHT//2 - ROAD_WIDTH//2 + 10, HEIGHT//2 + ROAD_WIDTH//2 - 10, crosswalk_width + crosswalk_gap):
        pygame.draw.rect(screen, WHITE, (WIDTH//2 - ROAD_WIDTH//2 - 20, y, 20, crosswalk_width))

def draw_traffic_lights(ns_light, ew_light):
    """Draw traffic lights on all four sides of the intersection"""
    screen = get_screen()
    
    # North traffic light
    # Traffic light pole
    pygame.draw.rect(screen, BLACK, (WIDTH//2 + ROAD_WIDTH//4, HEIGHT//2 - ROAD_WIDTH//2 - 60, 10, 60))
    # Traffic light housing
    light_box = pygame.Rect(WIDTH//2 + ROAD_WIDTH//4 - 5, HEIGHT//2 - ROAD_WIDTH//2 - 100, 20, 50)
    pygame.draw.rect(screen, BLACK, light_box)
    # Lights
    pygame.draw.ellipse(screen, (100, 0, 0) if ns_light != "red" else RED, 
                       (WIDTH//2 + ROAD_WIDTH//4, HEIGHT//2 - ROAD_WIDTH//2 - 95, 10, 10))  # Red
    pygame.draw.ellipse(screen, (100, 100, 0) if ns_light != "yellow" else YELLOW,
                       (WIDTH//2 + ROAD_WIDTH//4, HEIGHT//2 - ROAD_WIDTH//2 - 80, 10, 10))  # Yellow
    pygame.draw.ellipse(screen, (0, 100, 0) if ns_light != "green" else GREEN,
                       (WIDTH//2 + ROAD_WIDTH//4, HEIGHT//2 - ROAD_WIDTH//2 - 65, 10, 10))  # Green
    
    # South traffic light
    pygame.draw.rect(screen, BLACK, (WIDTH//2 - ROAD_WIDTH//4 - 10, HEIGHT//2 + ROAD_WIDTH//2, 10, 60))
    light_box = pygame.Rect(WIDTH//2 - ROAD_WIDTH//4 - 15, HEIGHT//2 + ROAD_WIDTH//2 + 50, 20, 50)
    pygame.draw.rect(screen, BLACK, light_box)
    pygame.draw.ellipse(screen, (100, 0, 0) if ns_light != "red" else RED,
                       (WIDTH//2 - ROAD_WIDTH//4 - 10, HEIGHT//2 + ROAD_WIDTH//2 + 85, 10, 10))
    pygame.draw.ellipse(screen, (100, 100, 0) if ns_light != "yellow" else YELLOW,
                       (WIDTH//2 - ROAD_WIDTH//4 - 10, HEIGHT//2 + ROAD_WIDTH//2 + 70, 10, 10))
    pygame.draw.ellipse(screen, (0, 100, 0) if ns_light != "green" else GREEN,
                       (WIDTH//2 - ROAD_WIDTH//4 - 10, HEIGHT//2 + ROAD_WIDTH//2 + 55, 10, 10))
    
    # East traffic light
    pygame.draw.rect(screen, BLACK, (WIDTH//2 + ROAD_WIDTH//2, HEIGHT//2 - ROAD_WIDTH//4 - 10, 60, 10))
    light_box = pygame.Rect(WIDTH//2 + ROAD_WIDTH//2 + 50, HEIGHT//2 - ROAD_WIDTH//4 - 15, 50, 20)
    pygame.draw.rect(screen, BLACK, light_box)
    pygame.draw.ellipse(screen, (100, 0, 0) if ew_light != "red" else RED,
                       (WIDTH//2 + ROAD_WIDTH//2 + 85, HEIGHT//2 - ROAD_WIDTH//4 - 10, 10, 10))
    pygame.draw.ellipse(screen, (100, 100, 0) if ew_light != "yellow" else YELLOW,
                       (WIDTH//2 + ROAD_WIDTH//2 + 70, HEIGHT//2 - ROAD_WIDTH//4 - 10, 10, 10))
    pygame.draw.ellipse(screen, (0, 100, 0) if ew_light != "green" else GREEN,
                       (WIDTH//2 + ROAD_WIDTH//2 + 55, HEIGHT//2 - ROAD_WIDTH//4 - 10, 10, 10))
    
    # West traffic light
    pygame.draw.rect(screen, BLACK, (WIDTH//2 - ROAD_WIDTH//2 - 60, HEIGHT//2 + ROAD_WIDTH//4, 60, 10))
    light_box = pygame.Rect(WIDTH//2 - ROAD_WIDTH//2 - 100, HEIGHT//2 + ROAD_WIDTH//4 - 5, 50, 20)
    pygame.draw.rect(screen, BLACK, light_box)
    pygame.draw.ellipse(screen, (100, 0, 0) if ew_light != "red" else RED,
                       (WIDTH//2 - ROAD_WIDTH//2 - 95, HEIGHT//2 + ROAD_WIDTH//4, 10, 10))
    pygame.draw.ellipse(screen, (100, 100, 0) if ew_light != "yellow" else YELLOW,
                       (WIDTH//2 - ROAD_WIDTH//2 - 80, HEIGHT//2 + ROAD_WIDTH//4, 10, 10))
    pygame.draw.ellipse(screen, (0, 100, 0) if ew_light != "green" else GREEN,
                       (WIDTH//2 - ROAD_WIDTH//2 - 65, HEIGHT//2 + ROAD_WIDTH//4, 10, 10))

def draw_vehicle(vehicle, debug_mode=False):
    """Draw a vehicle as a car-like shape instead of a circle"""
    screen = get_screen()
    pos = get_vehicle_position(vehicle)
    direction = get_vehicle_direction(vehicle)
    
    # Draw waiting indicator for vehicles stopped at red light or due to collision
    if vehicle.state == "waiting" or vehicle.stopped_for_collision:
        # Draw a red circle under the vehicle
        indicator_color = (255, 0, 0, 128) if vehicle.state == "waiting" else (255, 165, 0, 128)  # Red for light, orange for collision
        pygame.draw.circle(screen, indicator_color, pos, 15, width=2)
        
        # Draw a small satisfaction indicator
        sat_color = (0, 255, 0) if vehicle.satisfaction > 7 else \
                   (255, 255, 0) if vehicle.satisfaction > 3 else \
                   (255, 0, 0)
        pygame.draw.circle(screen, sat_color, (pos[0], pos[1] - 15), vehicle.satisfaction // 2 + 1)
    
    # Draw the vehicle
    draw_car(pos, vehicle.color, direction, vehicle)
    
    # Draw debug info if enabled
    if debug_mode:
        # Draw route indicator line
        if vehicle.route.index(vehicle.position) < len(vehicle.route) - 1:
            next_pos = vehicle.route[vehicle.route.index(vehicle.position) + 1]
            if next_pos in LANES:
                end_pos = LANES[next_pos]['in']
                pygame.draw.line(screen, DEBUG_COLORS['route_preview'], pos, end_pos, 2)
        
        # Draw vehicle ID and state
        font = pygame.font.SysFont('Arial', FONT_SIZE['vehicle_id'])
        id_text = font.render(f"{id(vehicle) % 1000}", True, BLACK)
        state_text = font.render(f"{vehicle.state}", True, BLACK)
        screen.blit(id_text, (pos[0] - 10, pos[1] - 25))
        screen.blit(state_text, (pos[0] - 15, pos[1] - 15))
        
        # Draw collision detection area
        if vehicle.stopped_for_collision:
            pygame.draw.circle(screen, DEBUG_COLORS['collision_area'], pos, 25, width=1)

def draw_car(pos, color, direction, vehicle):
    """Draw a car-like shape at the given position with the given color and direction"""
    screen = get_screen()
    x, y = pos
    
    # Apply animation offset
    if direction == 'up' or direction == 'down':
        y += vehicle.animation_offset
    else:
        x += vehicle.animation_offset
    
    # Car dimensions - adjusted by vehicle type
    car_length = 20 * vehicle.size_multiplier
    car_width = 12 * vehicle.size_multiplier
    
    # Adjust dimensions for horizontal vs vertical orientation
    if direction == 'left' or direction == 'right':
        car_length, car_width = car_width, car_length
    
    # Create the rectangle for the car body
    car_rect = pygame.Rect(x - car_width//2, y - car_length//2, car_width, car_length)
    
    # Draw the car based on direction
    if direction == 'down':
        # Car body
        pygame.draw.rect(screen, color, car_rect, border_radius=3)
        
        # Windows - different for each vehicle type
        if vehicle.vehicle_type == "car":
            # Car windows (windshield and rear window)
            window_width = car_width - 4
            window_length = 6
            window_rect = pygame.Rect(x - window_width//2, y - car_length//2 + 3, window_width, window_length)
            pygame.draw.rect(screen, (200, 230, 255), window_rect, border_radius=1)
            
            # Rear window
            rear_window = pygame.Rect(x - window_width//2, y + car_length//2 - 8, window_width, 5)
            pygame.draw.rect(screen, (200, 230, 255), rear_window, border_radius=1)
            
        elif vehicle.vehicle_type == "truck":
            # Truck cab
            cab_width = car_width - 2
            cab_length = car_length // 3
            cab_rect = pygame.Rect(x - cab_width//2, y - car_length//2, cab_width, cab_length)
            pygame.draw.rect(screen, (min(color[0] + 30, 255), min(color[1] + 30, 255), min(color[2] + 30, 255)), 
                            cab_rect, border_radius=2)
            
            # Truck windshield
            window_width = cab_width - 4
            window_rect = pygame.Rect(x - window_width//2, y - car_length//2 + 2, window_width, 4)
            pygame.draw.rect(screen, (200, 230, 255), window_rect, border_radius=1)
            
        elif vehicle.vehicle_type == "van":
            # Van windows (larger)
            window_width = car_width - 4
            window_length = car_length // 2
            window_rect = pygame.Rect(x - window_width//2, y - car_length//2 + 3, window_width, window_length)
            pygame.draw.rect(screen, (200, 230, 255), window_rect, border_radius=1)
        
        # Wheels - all vehicle types
        wheel_size = 3 * vehicle.size_multiplier
        pygame.draw.rect(screen, BLACK, (x - car_width//2 - 1, y - car_length//4, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x + car_width//2 - 2, y - car_length//4, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x - car_width//2 - 1, y + car_length//4, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x + car_width//2 - 2, y + car_length//4, wheel_size, wheel_size))
        
        # Add headlights
        headlight_size = 2 * vehicle.size_multiplier
        pygame.draw.rect(screen, (255, 255, 200), (x - car_width//2 + 1, y - car_length//2 + 1, headlight_size, headlight_size))
        pygame.draw.rect(screen, (255, 255, 200), (x + car_width//2 - 3, y - car_length//2 + 1, headlight_size, headlight_size))
    
    elif direction == 'up':
        # Similar to down but flipped
        pygame.draw.rect(screen, color, car_rect, border_radius=3)
        
        # Windows based on vehicle type
        if vehicle.vehicle_type == "car":
            window_width = car_width - 4
            window_length = 6
            window_rect = pygame.Rect(x - window_width//2, y + car_length//2 - 8, window_width, window_length)
            pygame.draw.rect(screen, (200, 230, 255), window_rect, border_radius=1)
            
            # Rear window
            rear_window = pygame.Rect(x - window_width//2, y - car_length//2 + 3, window_width, 5)
            pygame.draw.rect(screen, (200, 230, 255), rear_window, border_radius=1)
        
        # Wheels and headlights (similar to down but positions adjusted)
        wheel_size = 3 * vehicle.size_multiplier
        pygame.draw.rect(screen, BLACK, (x - car_width//2 - 1, y - car_length//4, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x + car_width//2 - 2, y - car_length//4, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x - car_width//2 - 1, y + car_length//4, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x + car_width//2 - 2, y + car_length//4, wheel_size, wheel_size))
        
        # Headlights at the bottom for "up" direction
        headlight_size = 2 * vehicle.size_multiplier
        pygame.draw.rect(screen, (255, 255, 200), (x - car_width//2 + 1, y + car_length//2 - 3, headlight_size, headlight_size))
        pygame.draw.rect(screen, (255, 255, 200), (x + car_width//2 - 3, y + car_length//2 - 3, headlight_size, headlight_size))
    
    elif direction == 'right':
        # Horizontal orientation
        pygame.draw.rect(screen, color, car_rect, border_radius=3)
        
        # Windows and details adjusted for horizontal
        if vehicle.vehicle_type == "car":
            window_height = car_width - 4
            window_width = 6
            window_rect = pygame.Rect(x - car_length//2 + 3, y - window_height//2, window_width, window_height)
            pygame.draw.rect(screen, (200, 230, 255), window_rect, border_radius=1)
        
        # Wheels adjusted for horizontal
        wheel_size = 3 * vehicle.size_multiplier
        pygame.draw.rect(screen, BLACK, (x - car_length//4, y - car_width//2 - 1, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x - car_length//4, y + car_width//2 - 2, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x + car_length//4, y - car_width//2 - 1, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x + car_length//4, y + car_width//2 - 2, wheel_size, wheel_size))
    
    elif direction == 'left':
        # Horizontal orientation facing left
        pygame.draw.rect(screen, color, car_rect, border_radius=3)
        
        # Windows and details adjusted for horizontal
        if vehicle.vehicle_type == "car":
            window_height = car_width - 4
            window_width = 6
            window_rect = pygame.Rect(x + car_length//2 - 8, y - window_height//2, window_width, window_height)
            pygame.draw.rect(screen, (200, 230, 255), window_rect, border_radius=1)
        
        # Wheels adjusted for horizontal
        wheel_size = 3 * vehicle.size_multiplier
        pygame.draw.rect(screen, BLACK, (x - car_length//4, y - car_width//2 - 1, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x - car_length//4, y + car_width//2 - 2, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x + car_length//4, y - car_width//2 - 1, wheel_size, wheel_size))
        pygame.draw.rect(screen, BLACK, (x + car_length//4, y + car_width//2 - 2, wheel_size, wheel_size))

def draw_stats(waiting_count, moving_count, arrived_count, avg_satisfaction, current_episode, current_tick):
    """Draw simulation statistics"""
    screen = get_screen()
    # Create font
    font = pygame.font.SysFont('Arial', FONT_SIZE['stats'])
    
    # Render stats
    stats_text = [
        f"Waiting: {waiting_count}",
        f"Moving: {moving_count}",
        f"Arrived: {arrived_count}",
        f"Avg Satisfaction: {avg_satisfaction:.1f}/10",
        f"Episode: {current_episode}",
        f"Tick: {current_tick}"
    ]
    
    # Draw stats background
    pygame.draw.rect(screen, STATS_PANEL['background'], 
                    (STATS_PANEL['padding'], STATS_PANEL['padding'], 
                     STATS_PANEL['width'], STATS_PANEL['height']), 
                    border_radius=5)
    pygame.draw.rect(screen, STATS_PANEL['border'], 
                    (STATS_PANEL['padding'], STATS_PANEL['padding'], 
                     STATS_PANEL['width'], STATS_PANEL['height']), 
                    width=1, border_radius=5)
    
    # Draw stats
    for i, text in enumerate(stats_text):
        text_surface = font.render(text, True, BLACK)
        screen.blit(text_surface, (STATS_PANEL['padding'] + 5, STATS_PANEL['padding'] + 5 + i * 20))
    
    return waiting_count, moving_count, arrived_count, avg_satisfaction

def draw_debug_info(ns_light, ew_light, active_vehicles, spawn_schedule, current_tick, episode_length, lane_counts):
    """Draw debug information"""
    screen = get_screen()
    font = pygame.font.SysFont('Arial', FONT_SIZE['debug'])
    
    # Prepare debug text
    debug_text = [
        f"NS Light: {ns_light}",
        f"EW Light: {ew_light}",
        f"Active vehicles: {len(active_vehicles)}",
        f"Vehicles to spawn: {len(spawn_schedule)}",
        f"Tick: {current_tick}/{episode_length}",
        f"Press D to toggle debug mode",
        f"Press S to toggle slow mode",
        f"Press E to end episode",
        f"Press N for new episode"
    ]
    
    # Draw debug panel background
    panel_x = WIDTH - DEBUG_PANEL['width'] - DEBUG_PANEL['padding']
    pygame.draw.rect(screen, DEBUG_PANEL['background'], 
                    (panel_x, DEBUG_PANEL['padding'], 
                     DEBUG_PANEL['width'], DEBUG_PANEL['height']), 
                    border_radius=5)
    pygame.draw.rect(screen, DEBUG_PANEL['border'], 
                    (panel_x, DEBUG_PANEL['padding'], 
                     DEBUG_PANEL['width'], DEBUG_PANEL['height']), 
                    width=1, border_radius=5)
    
    # Draw debug text
    for i, text in enumerate(debug_text):
        text_surface = font.render(text, True, BLACK)
        screen.blit(text_surface, (panel_x + 10, DEBUG_PANEL['padding'] + 5 + i * 20))
    
    # Draw lane occupancy
    lane_text = [f"{lane}: {count}/{MAX_VEHICLES_PER_LANE}" for lane, count in lane_counts.items()]
    for i, text in enumerate(lane_text):
        text_surface = font.render(text, True, BLACK)
        screen.blit(text_surface, (panel_x + 10, DEBUG_PANEL['padding'] + 200 + i * 20))
    
    # Draw debug visualization elements
    if DEBUG_MODE:
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

def draw_speed_slider(current_fps):
    """Draw a slider to control simulation speed"""
    screen = get_screen()
    
    # Draw slider background
    slider_rect = pygame.Rect(SPEED_SLIDER['x'], SPEED_SLIDER['y'], 
                             SPEED_SLIDER['width'], SPEED_SLIDER['height'])
    pygame.draw.rect(screen, (200, 200, 200), slider_rect)
    
    # Calculate handle position based on current FPS
    fps_range = SPEED_SLIDER['max_fps'] - SPEED_SLIDER['min_fps']
    handle_pos = SPEED_SLIDER['x'] + (current_fps - SPEED_SLIDER['min_fps']) / fps_range * SPEED_SLIDER['width']
    
    # Draw handle
    handle_rect = pygame.Rect(handle_pos - 5, SPEED_SLIDER['y'] - 5, 10, SPEED_SLIDER['height'] + 10)
    pygame.draw.rect(screen, (100, 100, 100), handle_rect)
    
    # Draw label
    font = pygame.font.SysFont('Arial', 16)
    label = font.render(f"Speed: {int(current_fps)} FPS", True, (0, 0, 0))
    screen.blit(label, (SPEED_SLIDER['x'] - 90, SPEED_SLIDER['y'] - 5))
    
    return handle_rect

def draw_training_slider(current_steps):
    """Draw a slider to control training steps"""
    screen = get_screen()
    
    # Draw slider background
    slider_rect = pygame.Rect(TRAINING_SLIDER['x'], TRAINING_SLIDER['y'], 
                             TRAINING_SLIDER['width'], TRAINING_SLIDER['height'])
    pygame.draw.rect(screen, (200, 200, 200), slider_rect)
    
    # Calculate handle position based on current steps
    steps_range = TRAINING_SLIDER['max_steps'] - TRAINING_SLIDER['min_steps']
    handle_pos = TRAINING_SLIDER['x'] + (current_steps - TRAINING_SLIDER['min_steps']) / steps_range * TRAINING_SLIDER['width']
    
    # Draw handle
    handle_rect = pygame.Rect(handle_pos - 5, TRAINING_SLIDER['y'] - 5, 10, TRAINING_SLIDER['height'] + 10)
    pygame.draw.rect(screen, (50, 150, 50), handle_rect)
    
    # Draw label
    font = pygame.font.SysFont('Arial', 16)
    label = font.render(f"Training: {current_steps} steps", True, (0, 0, 0))
    screen.blit(label, (TRAINING_SLIDER['x'] - 90, TRAINING_SLIDER['y'] - 5))
    
    return handle_rect 