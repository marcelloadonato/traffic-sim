import random
from src.config import TOTAL_VEHICLES, EPISODE_LENGTH, MAX_VEHICLES_PER_LANE, VEHICLE_COLORS, WIDTH, HEIGHT
from src.agent import Vehicle

DETERMINISTIC_SPAWNING = True  # or True for fixed patterns

def generate_vehicle_spawn_schedule(total_vehicles=TOTAL_VEHICLES, max_ticks=EPISODE_LENGTH, deterministic=False):
    """Generate a spawn schedule for vehicles with different start and end points"""
    schedule = []
    directions = ['north', 'south', 'east', 'west']
    
    if deterministic:
        # Set random seed to ensure same sequence
        random.seed(42)  # or any fixed number
    
    for i in range(total_vehicles):
        # Pick spawn tick - if deterministic, use fixed pattern
        if deterministic:
            spawn_tick = (i * (max_ticks // 2) // total_vehicles)  # Evenly spread spawns
        else:
            spawn_tick = random.randint(0, max_ticks // 2)
        
        # Pick start and destination (must be different)
        start = random.choice(directions)
        destination = random.choice([d for d in directions if d != start])
        
        schedule.append({
            'spawn_tick': spawn_tick,
            'start': start,
            'destination': destination
        })
    
    if deterministic:
        # Reset random seed
        random.seed()
        
    # Sort by spawn tick
    schedule.sort(key=lambda x: x['spawn_tick'])
    return schedule

def spawn_vehicles(current_tick, spawn_schedule, active_vehicles, simulation):
    """Spawn new vehicles according to schedule with proper spacing"""
    # Minimum distance between spawned vehicles
    MIN_SPAWN_DISTANCE = 80  # Increased minimum distance between spawned vehicles
    
    # Process spawn schedule
    if current_tick in spawn_schedule:
        for spawn_data in spawn_schedule[current_tick]:
            start_pos, end_pos = spawn_data
            
            # Check if there's enough space to spawn
            can_spawn = True
            spawn_coords = get_spawn_coordinates(start_pos)
            
            # Check distance to other vehicles in the same lane
            for vehicle in active_vehicles:
                if vehicle.position == start_pos:
                    vehicle_coords = vehicle.get_current_coords()
                    if vehicle_coords:
                        dx = spawn_coords[0] - vehicle_coords[0]
                        dy = spawn_coords[1] - vehicle_coords[1]
                        distance = (dx * dx + dy * dy) ** 0.5
                        if distance < MIN_SPAWN_DISTANCE:
                            can_spawn = False
                            break
            
            if can_spawn:
                # Create route
                route = simulation.create_route(start_pos, end_pos)
                
                if route:
                    # Create new vehicle with improved settings
                    vehicle = Vehicle(
                        route=route,
                        position=start_pos,
                        vehicle_type=random.choice(["car", "van", "truck"]),
                        position_threshold=50  # Reduced from 80 for smoother movement
                    )
                    vehicle.destination = end_pos
                    
                    # Set initial interpolated position
                    vehicle.interpolated_position = spawn_coords
                    
                    # Set appropriate speeds for vehicle type with increased base speeds
                    if vehicle.vehicle_type == "truck":
                        vehicle.base_speed = 3  # Increased from 2
                        vehicle.speed = 3
                    elif vehicle.vehicle_type == "van":
                        vehicle.base_speed = 4  # Increased from 3
                        vehicle.speed = 4
                    else:  # car
                        vehicle.base_speed = 5  # Increased from 4
                        vehicle.speed = 5
                    
                    # Initialize movement state
                    vehicle.state = "moving"
                    vehicle.position_time = 0
                    
                    active_vehicles.append(vehicle)

def get_spawn_coordinates(position):
    """Get spawn coordinates for a given position"""
    if position == 'north':
        return (WIDTH//2 + 15, 0)  # Offset to right lane
    elif position == 'south':
        return (WIDTH//2 - 15, HEIGHT)  # Offset to right lane
    elif position == 'east':
        return (WIDTH, HEIGHT//2 - 15)  # Offset to right lane
    elif position == 'west':
        return (0, HEIGHT//2 + 15)  # Offset to right lane
    return None 