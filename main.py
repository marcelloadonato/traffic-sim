# main.py
import pygame
import random
import math
import pandas as pd
import matplotlib.pyplot as plt
import os
from agent import Vehicle

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Traffic Simulation MVP")
clock = pygame.time.Clock()

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

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

# Traffic light states
NS_LIGHT = "green"  # North-South light (green, yellow, red)
EW_LIGHT = "red"    # East-West light (red, yellow, green)
NS_YELLOW_COUNTDOWN = 0
EW_YELLOW_COUNTDOWN = 0

# Road dimensions
ROAD_WIDTH = 100
LANE_WIDTH = 40
LANE_MARKER_WIDTH = 5
LANE_MARKER_LENGTH = 30
LANE_MARKER_GAP = 20

# Lane positions for different directions - add more intermediate positions
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

# Add intermediate positions for smoother movement
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

# Vehicle spawn queue and active vehicles
spawn_queue = []
active_vehicles = []
removed_vehicles = []  # Track vehicles that have reached their destination

# Vehicle colors - for visual variety
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

# Data collection for RL
class DataRecorder:
    def __init__(self):
        self.episode_data = []
        self.current_episode = 1
        self.tick_data = []
        self.episode_summaries = []
        
    def record_tick(self, tick, light_state, waiting_count, moving_count, arrived_count, avg_satisfaction):
        """Record data for a single simulation tick"""
        self.tick_data.append({
            'episode': self.current_episode,
            'tick': tick,
            'light_state': light_state,
            'waiting_vehicles': waiting_count,
            'moving_vehicles': moving_count,
            'arrived_vehicles': arrived_count,
            'avg_satisfaction': avg_satisfaction
        })
        
    def record_vehicle_completion(self, vehicle):
        """Record data when a vehicle completes its journey"""
        self.episode_data.append({
            'episode': self.current_episode,
            'vehicle_id': id(vehicle),
            'vehicle_type': vehicle.vehicle_type,
            'start_position': vehicle.start_position,
            'destination': vehicle.destination,
            'commute_time': vehicle.commute_time,
            'final_satisfaction': vehicle.satisfaction
        })
        
    def end_episode(self):
        """End the current episode and calculate summary statistics"""
        if not self.episode_data:
            return
            
        # Calculate episode summary
        avg_commute = sum(v['commute_time'] for v in self.episode_data) / len(self.episode_data)
        avg_satisfaction = sum(v['final_satisfaction'] for v in self.episode_data) / len(self.episode_data)
        total_vehicles = len(self.episode_data)
        
        # Store summary
        self.episode_summaries.append({
            'episode': self.current_episode,
            'avg_commute_time': avg_commute,
            'avg_satisfaction': avg_satisfaction,
            'total_vehicles': total_vehicles,
            'reward': -0.1 * avg_commute + avg_satisfaction  # Example reward function
        })
        
        # Save data to files
        self.save_data()
        
        # Prepare for next episode
        self.current_episode += 1
        self.episode_data = []
        self.tick_data = []
        
    def save_data(self):
        """Save collected data to CSV files"""
        # Save episode data
        if self.episode_data:
            pd.DataFrame(self.episode_data).to_csv(f'data/episode_{self.current_episode}_vehicles.csv', index=False)
        
        # Save tick data
        if self.tick_data:
            pd.DataFrame(self.tick_data).to_csv(f'data/episode_{self.current_episode}_ticks.csv', index=False)
        
        # Save episode summaries
        if self.episode_summaries:
            pd.DataFrame(self.episode_summaries).to_csv('data/episode_summaries.csv', index=False)
            
    def plot_learning_curve(self):
        """Generate a plot showing reward over episodes"""
        if not self.episode_summaries:
            return
            
        df = pd.DataFrame(self.episode_summaries)
        plt.figure(figsize=(10, 6))
        plt.plot(df['episode'], df['reward'], 'b-')
        plt.title('Reward per Episode')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.grid(True)
        plt.savefig('data/learning_curve.png')
        plt.close()

# Initialize data recorder
data_recorder = DataRecorder()

# Generate random buildings
buildings = []
# Northwest quadrant
for _ in range(5):
    x = random.randint(50, WIDTH//2 - ROAD_WIDTH//2 - 80)
    y = random.randint(50, HEIGHT//2 - ROAD_WIDTH//2 - 80)
    width = random.randint(40, 100)
    height = random.randint(40, 100)
    color = random.choice(BUILDING_COLORS)
    buildings.append((x, y, width, height, color))

# Northeast quadrant
for _ in range(5):
    x = random.randint(WIDTH//2 + ROAD_WIDTH//2 + 30, WIDTH - 100)
    y = random.randint(50, HEIGHT//2 - ROAD_WIDTH//2 - 80)
    width = random.randint(40, 100)
    height = random.randint(40, 100)
    color = random.choice(BUILDING_COLORS)
    buildings.append((x, y, width, height, color))

# Southwest quadrant
for _ in range(5):
    x = random.randint(50, WIDTH//2 - ROAD_WIDTH//2 - 80)
    y = random.randint(HEIGHT//2 + ROAD_WIDTH//2 + 30, HEIGHT - 100)
    width = random.randint(40, 100)
    height = random.randint(40, 100)
    color = random.choice(BUILDING_COLORS)
    buildings.append((x, y, width, height, color))

# Southeast quadrant
for _ in range(5):
    x = random.randint(WIDTH//2 + ROAD_WIDTH//2 + 30, WIDTH - 100)
    y = random.randint(HEIGHT//2 + ROAD_WIDTH//2 + 30, HEIGHT - 100)
    width = random.randint(40, 100)
    height = random.randint(40, 100)
    color = random.choice(BUILDING_COLORS)
    buildings.append((x, y, width, height, color))

def generate_vehicle_spawn_schedule(total_vehicles=20, max_ticks=1000):
    """Generate a spawn schedule for vehicles with different start and end points"""
    schedule = []
    
    # All possible combinations of start and destination
    directions = ['north', 'south', 'east', 'west']
    
    for i in range(total_vehicles):
        # Pick random spawn tick
        spawn_tick = random.randint(0, max_ticks // 2)
        
        # Pick random start and destination (must be different)
        start = random.choice(directions)
        destination = random.choice([d for d in directions if d != start])
        
        # Add to schedule
        schedule.append({
            'spawn_tick': spawn_tick,
            'start': start,
            'destination': destination
        })
    
    # Sort by spawn tick
    schedule.sort(key=lambda x: x['spawn_tick'])
    return schedule

# Generate vehicle spawn schedule
spawn_schedule = generate_vehicle_spawn_schedule(20, 1000)

def spawn_vehicles(current_tick):
    """Check if any vehicles should spawn this tick"""
    # Check spawn schedule
    vehicles_to_spawn = [v for v in spawn_schedule if v['spawn_tick'] == current_tick]
    
    # Check if there's room in the queue (limit 4 vehicles per lane)
    lane_counts = {}
    for vehicle in active_vehicles:
        if vehicle.position in LANES:
            lane_counts[vehicle.position] = lane_counts.get(vehicle.position, 0) + 1
    
    for vehicle_info in vehicles_to_spawn[:]:
        lane = vehicle_info['start']
        # Only spawn if there are fewer than 4 vehicles in this lane
        if lane_counts.get(lane, 0) < 4:
            # Create the vehicle
            vehicle = Vehicle(vehicle_info['start'], vehicle_info['destination'])
            vehicle.color = random.choice(VEHICLE_COLORS)
            vehicle.start_position = vehicle_info['start']  # Store original starting point
            
            # Add to active vehicles
            active_vehicles.append(vehicle)
            spawn_schedule.remove(vehicle_info)
            lane_counts[lane] = lane_counts.get(lane, 0) + 1
            
            # Debug print
            print(f"Spawned vehicle from {vehicle_info['start']} to {vehicle_info['destination']} at tick {current_tick}")
            print(f"Route: {vehicle.route}")
        # If lane is full, leave in schedule for later

def draw_buildings():
    """Draw buildings in the city"""
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

def draw_traffic_lights():
    """Draw two traffic lights - one for NS and one for EW"""
    # North-South traffic light (right side of intersection)
    # Traffic light pole
    pygame.draw.rect(screen, BLACK, (WIDTH//2 + ROAD_WIDTH//2 + 10, HEIGHT//2 - ROAD_WIDTH//2 - 60, 10, 60))
    
    # Traffic light housing
    light_box = pygame.Rect(WIDTH//2 + ROAD_WIDTH//2 + 5, HEIGHT//2 - ROAD_WIDTH//2 - 100, 20, 50)
    pygame.draw.rect(screen, BLACK, light_box)
    
    # Red light
    red_light = pygame.Rect(WIDTH//2 + ROAD_WIDTH//2 + 10, HEIGHT//2 - ROAD_WIDTH//2 - 95, 10, 10)
    pygame.draw.ellipse(screen, (100, 0, 0) if NS_LIGHT != "red" else RED, red_light)
    
    # Yellow light
    yellow_light = pygame.Rect(WIDTH//2 + ROAD_WIDTH//2 + 10, HEIGHT//2 - ROAD_WIDTH//2 - 80, 10, 10)
    pygame.draw.ellipse(screen, (100, 100, 0) if NS_LIGHT != "yellow" else YELLOW, yellow_light)
    
    # Green light
    green_light = pygame.Rect(WIDTH//2 + ROAD_WIDTH//2 + 10, HEIGHT//2 - ROAD_WIDTH//2 - 65, 10, 10)
    pygame.draw.ellipse(screen, (0, 100, 0) if NS_LIGHT != "green" else GREEN, green_light)
    
    # East-West traffic light (bottom side of intersection)
    # Traffic light pole
    pygame.draw.rect(screen, BLACK, (WIDTH//2 - ROAD_WIDTH//2 - 60, HEIGHT//2 + ROAD_WIDTH//2 + 10, 60, 10))
    
    # Traffic light housing
    light_box = pygame.Rect(WIDTH//2 - ROAD_WIDTH//2 - 100, HEIGHT//2 + ROAD_WIDTH//2 + 5, 50, 20)
    pygame.draw.rect(screen, BLACK, light_box)
    
    # Red light
    red_light = pygame.Rect(WIDTH//2 - ROAD_WIDTH//2 - 95, HEIGHT//2 + ROAD_WIDTH//2 + 10, 10, 10)
    pygame.draw.ellipse(screen, (100, 0, 0) if EW_LIGHT != "red" else RED, red_light)
    
    # Yellow light
    yellow_light = pygame.Rect(WIDTH//2 - ROAD_WIDTH//2 - 80, HEIGHT//2 + ROAD_WIDTH//2 + 10, 10, 10)
    pygame.draw.ellipse(screen, (100, 100, 0) if EW_LIGHT != "yellow" else YELLOW, yellow_light)
    
    # Green light
    green_light = pygame.Rect(WIDTH//2 - ROAD_WIDTH//2 - 65, HEIGHT//2 + ROAD_WIDTH//2 + 10, 10, 10)
    pygame.draw.ellipse(screen, (0, 100, 0) if EW_LIGHT != "green" else GREEN, green_light)

def get_vehicle_position(vehicle):
    """Get the position coordinates for a vehicle based on its position value and progress"""
    # If at a lane entrance/exit
    if vehicle.position in LANES:
        # If just spawned, use the out position (edge of screen)
        if vehicle.commute_time < 5:
            return LANES[vehicle.position]['out']
        
        # If approaching intersection, use queue positions based on position_time
        queue_positions = LANES[vehicle.position]['queue']
        progress = min(vehicle.position_time / vehicle.position_threshold, 1.0)
        
        # Calculate position along the queue
        if progress < 0.5:  # First half of movement - use queue positions
            queue_idx = min(int(progress * 8), len(queue_positions) - 1)
            return queue_positions[queue_idx]
        else:  # Second half - approach the intersection entrance
            return LANES[vehicle.position]['in']
    
    # If at the intersection
    elif vehicle.position == 'intersection':
        # Get previous and next positions in route
        route_idx = vehicle.route.index('intersection')
        prev_pos = vehicle.route[route_idx - 1] if route_idx > 0 else None
        next_pos = vehicle.route[route_idx + 1] if route_idx < len(vehicle.route) - 1 else None
        
        # Calculate progress through intersection
        progress = min(vehicle.position_time / vehicle.position_threshold, 1.0)
        
        # If we know where we're coming from and going to
        if prev_pos and next_pos:
            # First third - entering intersection
            if progress < 0.33:
                key = f"{prev_pos}_to_intersection"
                if key in INTERMEDIATE_POSITIONS and INTERMEDIATE_POSITIONS[key]:
                    idx = min(int(progress * 6), len(INTERMEDIATE_POSITIONS[key]) - 1)
                    return INTERMEDIATE_POSITIONS[key][idx]
            
            # Middle third - center of intersection
            elif progress < 0.66:
                return (WIDTH//2, HEIGHT//2)
            
            # Last third - exiting intersection
            else:
                key = f"intersection_to_{next_pos}"
                if key in INTERMEDIATE_POSITIONS and INTERMEDIATE_POSITIONS[key]:
                    idx = min(int((progress - 0.66) * 6), len(INTERMEDIATE_POSITIONS[key]) - 1)
                    return INTERMEDIATE_POSITIONS[key][idx]
        
        # Default intersection position
        return (WIDTH//2, HEIGHT//2)
    
    # Default fallback
    return (WIDTH//2, HEIGHT//2)

def get_vehicle_direction(vehicle):
    """Determine the direction the vehicle should face based on start and destination"""
    if vehicle.position in LANES:
        return LANES[vehicle.position]['direction']
    elif vehicle.position == 'intersection':
        # When in intersection, use the destination to determine direction
        if vehicle.destination == 'north':
            return 'up'
        elif vehicle.destination == 'south':
            return 'down'
        elif vehicle.destination == 'east':
            return 'right'
        else:  # west
            return 'left'
    else:
        return 'down'  # Default

def check_collision(vehicle, next_position):
    """Check if moving to next_position would cause a collision with another vehicle"""
    # Get the actual coordinates for the next position
    next_pos_coords = None
    
    if next_position == 'intersection':
        # For intersection, use the entry point based on where the vehicle is coming from
        if vehicle.position == 'north':
            next_pos_coords = (WIDTH//2, HEIGHT//2 - 40)
        elif vehicle.position == 'south':
            next_pos_coords = (WIDTH//2, HEIGHT//2 + 40)
        elif vehicle.position == 'east':
            next_pos_coords = (WIDTH//2 + 40, HEIGHT//2)
        elif vehicle.position == 'west':
            next_pos_coords = (WIDTH//2 - 40, HEIGHT//2)
        else:
            next_pos_coords = (WIDTH//2, HEIGHT//2)
    elif next_position in LANES:
        next_pos_coords = LANES[next_position]['in']
    else:
        return False  # Unknown position, assume no collision
    
    # Get current vehicle's position coordinates
    current_pos_coords = get_vehicle_position(vehicle)
    
    # Check distance to all other vehicles
    min_distance = 25  # Minimum distance between vehicles
    
    for other in active_vehicles:
        if other == vehicle:
            continue  # Skip self
            
        # Skip vehicles not in the same lane or not ahead of us
        if other.position != next_position and other.position != vehicle.position:
            continue
            
        # Get other vehicle's position
        other_pos = get_vehicle_position(other)
        
        # Calculate distance
        distance = math.sqrt((next_pos_coords[0] - other_pos[0])**2 + (next_pos_coords[1] - other_pos[1])**2)
        
        # Check if too close
        if distance < min_distance:
            # Only count as collision if the other vehicle is ahead of us in our direction of travel
            if vehicle.start_position == 'north' and other_pos[1] < current_pos_coords[1]:
                return True
            elif vehicle.start_position == 'south' and other_pos[1] > current_pos_coords[1]:
                return True
            elif vehicle.start_position == 'east' and other_pos[0] > current_pos_coords[0]:
                return True
            elif vehicle.start_position == 'west' and other_pos[0] < current_pos_coords[0]:
                return True
    
    return False  # No collision

def update_vehicle(vehicle, ns_light, ew_light):
    """Update a single vehicle with the current light states"""
    # Set the collision detection function
    vehicle.check_collision_ahead = lambda: check_collision(vehicle, 
                                                          vehicle.route[vehicle.route.index(vehicle.position) + 1] 
                                                          if vehicle.route.index(vehicle.position) < len(vehicle.route) - 1 
                                                          else None)
    
    # Determine which light applies to this vehicle
    if vehicle.start_position in ['north', 'south']:
        applicable_light = ns_light
    else:  # east or west
        applicable_light = ew_light
        
    # Update the vehicle with the applicable light
    vehicle.update(applicable_light)

def draw_vehicle(vehicle):
    """Draw a vehicle as a car-like shape instead of a circle"""
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
    if DEBUG_MODE:
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

def draw_stats():
    """Draw simulation statistics"""
    # Calculate stats
    waiting_count = sum(1 for agent in active_vehicles if agent.state == "waiting")
    moving_count = sum(1 for agent in active_vehicles if agent.state == "moving")
    arrived_count = len(removed_vehicles)
    
    # Calculate average satisfaction only if there are vehicles
    if active_vehicles:
        avg_satisfaction = sum(agent.satisfaction for agent in active_vehicles) / len(active_vehicles)
    else:
        avg_satisfaction = 0
    
    # Create font
    font = pygame.font.SysFont('Arial', 16)
    
    # Render stats
    stats_text = [
        f"Waiting: {waiting_count}",
        f"Moving: {moving_count}",
        f"Arrived: {arrived_count}",
        f"Avg Satisfaction: {avg_satisfaction:.1f}/10",
        f"Episode: {data_recorder.current_episode}",
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

# Simulation loop
running = True
NS_LIGHT = "green"  # North-South light starts green
EW_LIGHT = "red"    # East-West light starts red
NS_YELLOW_COUNTDOWN = 0
EW_YELLOW_COUNTDOWN = 0
current_tick = 0
episode_length = 1000  # Length of an episode in ticks

# Debug flags
DEBUG_MODE = True
SLOW_MODE = True  # Slow down simulation for better visibility

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # Save any remaining data
            data_recorder.end_episode()
            data_recorder.plot_learning_curve()
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Toggle lights
                if NS_LIGHT == "green" and EW_LIGHT == "red":
                    NS_LIGHT = "yellow"
                    NS_YELLOW_COUNTDOWN = 30  # 1 second at 30 FPS
                elif NS_LIGHT == "red" and EW_LIGHT == "green":
                    EW_LIGHT = "yellow"
                    EW_YELLOW_COUNTDOWN = 30
            elif event.key == pygame.K_d:  # Toggle debug mode
                DEBUG_MODE = not DEBUG_MODE
                print(f"Debug mode: {'ON' if DEBUG_MODE else 'OFF'}")
            elif event.key == pygame.K_s:  # Toggle slow mode
                SLOW_MODE = not SLOW_MODE
                print(f"Slow mode: {'ON' if SLOW_MODE else 'OFF'}")
    
    # Handle yellow light transitions
    if NS_LIGHT == "yellow":
        NS_YELLOW_COUNTDOWN -= 1
        if NS_YELLOW_COUNTDOWN <= 0:
            NS_LIGHT = "red"
            EW_LIGHT = "green"  # Switch the other light to green
    
    if EW_LIGHT == "yellow":
        EW_YELLOW_COUNTDOWN -= 1
        if EW_YELLOW_COUNTDOWN <= 0:
            EW_LIGHT = "red"
            NS_LIGHT = "green"  # Switch the other light to green
    
    # Spawn new vehicles if needed
    spawn_vehicles(current_tick)
    
    # Update active vehicles and remove those that have reached their destination
    for vehicle in active_vehicles[:]:  # Use a copy for safe iteration
        # Update with the appropriate light for this vehicle's direction
        update_vehicle(vehicle, NS_LIGHT, EW_LIGHT)
        
        # Check if vehicle has arrived at destination
        if vehicle.state == "arrived" or vehicle.position == vehicle.destination:
            # Record data
            data_recorder.record_vehicle_completion(vehicle)
            
            # Remove from active and add to removed
            removed_vehicles.append(vehicle)
            active_vehicles.remove(vehicle)
            
            if DEBUG_MODE:
                print(f"Vehicle completed journey: {vehicle.start_position} -> {vehicle.destination} in {vehicle.commute_time} ticks")
    
    # Draw everything
    screen.fill(WHITE)
    draw_buildings()
    draw_road()
    
    # Draw path indicators for better visibility
    if DEBUG_MODE:
        # Draw dots at all lane positions
        for lane, pos_data in LANES.items():
            pygame.draw.circle(screen, (255, 0, 0), pos_data['in'], 3)
            pygame.draw.circle(screen, (0, 0, 255), pos_data['out'], 3)
            
            # Draw queue positions
            for pos in pos_data['queue']:
                pygame.draw.circle(screen, (0, 100, 0), pos, 2)
        
        # Draw dots at intersection
        pygame.draw.circle(screen, (255, 255, 0), (WIDTH//2, HEIGHT//2), 5)
        
        # Draw intermediate positions
        for key, positions in INTERMEDIATE_POSITIONS.items():
            for pos in positions:
                pygame.draw.circle(screen, (0, 255, 0), pos, 3)
    
    draw_traffic_lights()
    
    # Draw all vehicles
    for vehicle in active_vehicles:
        draw_vehicle(vehicle)
    
    # Draw stats and record data
    waiting_count, moving_count, arrived_count, avg_satisfaction = draw_stats()
    data_recorder.record_tick(current_tick, f"NS:{NS_LIGHT},EW:{EW_LIGHT}", waiting_count, moving_count, arrived_count, avg_satisfaction)
    
    # Draw debug info
    if DEBUG_MODE:
        font = pygame.font.SysFont('Arial', 14)
        debug_text = [
            f"NS Light: {NS_LIGHT}",
            f"EW Light: {EW_LIGHT}",
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
        lane_counts = {}
        for vehicle in active_vehicles:
            if vehicle.position in LANES:
                lane_counts[vehicle.position] = lane_counts.get(vehicle.position, 0) + 1
        
        lane_text = [f"{lane}: {count}/4" for lane, count in lane_counts.items()]
        for i, text in enumerate(lane_text):
            text_surface = font.render(text, True, BLACK)
            screen.blit(text_surface, (WIDTH - 100, 130 + i * 20))
    
    pygame.display.flip()
    
    # Control simulation speed
    if SLOW_MODE:
        clock.tick(10)  # Slower for debugging
    else:
        clock.tick(30)  # Normal speed
    
    # Increment tick counter
    current_tick += 1
    
    # Check if episode should end
    if current_tick >= episode_length or (not active_vehicles and not spawn_schedule):
        # End episode
        data_recorder.end_episode()
        data_recorder.plot_learning_curve()
        
        # Reset for next episode
        current_tick = 0
        active_vehicles = []
        removed_vehicles = []
        spawn_schedule = generate_vehicle_spawn_schedule(20, episode_length)
        NS_LIGHT = "green"
        EW_LIGHT = "red"

pygame.quit() 