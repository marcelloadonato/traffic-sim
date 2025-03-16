import pygame
import random
from config import *
from collision import get_vehicle_position, get_vehicle_direction
from shared import get_screen

def draw_buildings(buildings):
    """Draw buildings in the city"""
    screen = get_screen()
    for x, y, width, height, color in buildings:
        # Building body
        pygame.draw.rect(screen, color, (x, y, width, height))
        
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
        if random.random() > 0.5:  # 50% chance for a different roof style
            # Flat roof with edge
            pygame.draw.rect(screen, (min(color[0] - 30, 255), min(color[1] - 30, 255), min(color[2] - 30, 255)), 
                            (x, y - roof_height, width, roof_height))
        else:
            # Pitched roof
            pygame.draw.polygon(screen, (min(color[0] - 30, 255), min(color[1] - 30, 255), min(color[2] - 30, 255)),
                              [(x, y), (x + width, y), (x + width//2, y - roof_height)])

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
    """Draw two traffic lights - one for NS and one for EW"""
    screen = get_screen()
    # North-South traffic light (right side of intersection)
    # Traffic light pole
    pygame.draw.rect(screen, BLACK, (WIDTH//2 + ROAD_WIDTH//2 + 10, HEIGHT//2 - ROAD_WIDTH//2 - 60, 10, 60))
    
    # Traffic light housing
    light_box = pygame.Rect(WIDTH//2 + ROAD_WIDTH//2 + 5, HEIGHT//2 - ROAD_WIDTH//2 - 100, 20, 50)
    pygame.draw.rect(screen, BLACK, light_box)
    
    # Red light
    red_light = pygame.Rect(WIDTH//2 + ROAD_WIDTH//2 + 10, HEIGHT//2 - ROAD_WIDTH//2 - 95, 10, 10)
    pygame.draw.ellipse(screen, (100, 0, 0) if ns_light != "red" else RED, red_light)
    
    # Yellow light
    yellow_light = pygame.Rect(WIDTH//2 + ROAD_WIDTH//2 + 10, HEIGHT//2 - ROAD_WIDTH//2 - 80, 10, 10)
    pygame.draw.ellipse(screen, (100, 100, 0) if ns_light != "yellow" else YELLOW, yellow_light)
    
    # Green light
    green_light = pygame.Rect(WIDTH//2 + ROAD_WIDTH//2 + 10, HEIGHT//2 - ROAD_WIDTH//2 - 65, 10, 10)
    pygame.draw.ellipse(screen, (0, 100, 0) if ns_light != "green" else GREEN, green_light)
    
    # East-West traffic light (bottom side of intersection)
    # Traffic light pole
    pygame.draw.rect(screen, BLACK, (WIDTH//2 - ROAD_WIDTH//2 - 60, HEIGHT//2 + ROAD_WIDTH//2 + 10, 60, 10))
    
    # Traffic light housing
    light_box = pygame.Rect(WIDTH//2 - ROAD_WIDTH//2 - 100, HEIGHT//2 + ROAD_WIDTH//2 + 5, 50, 20)
    pygame.draw.rect(screen, BLACK, light_box)
    
    # Red light
    red_light = pygame.Rect(WIDTH//2 - ROAD_WIDTH//2 - 95, HEIGHT//2 + ROAD_WIDTH//2 + 10, 10, 10)
    pygame.draw.ellipse(screen, (100, 0, 0) if ew_light != "red" else RED, red_light)
    
    # Yellow light
    yellow_light = pygame.Rect(WIDTH//2 - ROAD_WIDTH//2 - 80, HEIGHT//2 + ROAD_WIDTH//2 + 10, 10, 10)
    pygame.draw.ellipse(screen, (100, 100, 0) if ew_light != "yellow" else YELLOW, yellow_light)
    
    # Green light
    green_light = pygame.Rect(WIDTH//2 - ROAD_WIDTH//2 - 65, HEIGHT//2 + ROAD_WIDTH//2 + 10, 10, 10)
    pygame.draw.ellipse(screen, (0, 100, 0) if ew_light != "green" else GREEN, green_light)

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
                pygame.draw.line(screen, vehicle.color, pos, end_pos, 1)
        
        # Draw vehicle ID and state
        font = pygame.font.SysFont('Arial', 10)
        id_text = font.render(f"{id(vehicle) % 1000}", True, BLACK)
        screen.blit(id_text, (pos[0] - 10, pos[1] - 20))
        
        # Draw collision detection area
        if vehicle.stopped_for_collision:
            pygame.draw.circle(screen, (255, 0, 0, 128), pos, 25, width=1)

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
    font = pygame.font.SysFont('Arial', 16)
    
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
    pygame.draw.rect(screen, (240, 240, 240, 200), (5, 5, 200, 110), border_radius=5)
    pygame.draw.rect(screen, BLACK, (5, 5, 200, 110), width=1, border_radius=5)
    
    # Draw stats
    for i, text in enumerate(stats_text):
        text_surface = font.render(text, True, BLACK)
        screen.blit(text_surface, (10, 10 + i * 18))
    
    return waiting_count, moving_count, arrived_count, avg_satisfaction

def draw_debug_info(ns_light, ew_light, active_vehicles, spawn_schedule, current_tick, episode_length, lane_counts):
    """Draw debug information"""
    screen = get_screen()
    font = pygame.font.SysFont('Arial', 14)
    debug_text = [
        f"NS Light: {ns_light}",
        f"EW Light: {ew_light}",
        f"Active vehicles: {len(active_vehicles)}",
        f"Vehicles to spawn: {len(spawn_schedule)}",
        f"Tick: {current_tick}/{episode_length}",
        f"Press D to toggle debug mode",
        f"Press S to toggle slow mode"
    ]
    
    # Draw a background for debug text
    pygame.draw.rect(screen, (240, 240, 240, 200), (WIDTH - 210, 5, 205, 120), border_radius=5)
    pygame.draw.rect(screen, BLACK, (WIDTH - 210, 5, 205, 120), width=1, border_radius=5)
    
    for i, text in enumerate(debug_text):
        text_surface = font.render(text, True, BLACK)
        screen.blit(text_surface, (WIDTH - 200, 10 + i * 20))
    
    # Draw lane occupancy
    lane_text = [f"{lane}: {count}/4" for lane, count in lane_counts.items()]
    for i, text in enumerate(lane_text):
        text_surface = font.render(text, True, BLACK)
        screen.blit(text_surface, (WIDTH - 100, 130 + i * 20)) 