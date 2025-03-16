import random
from src.config import TOTAL_VEHICLES, EPISODE_LENGTH, MAX_VEHICLES_PER_LANE, VEHICLE_COLORS
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

def spawn_vehicles(current_tick, spawn_schedule, active_vehicles):
    """Check if any vehicles should spawn this tick"""
    # Check spawn schedule
    vehicles_to_spawn = [v for v in spawn_schedule if v['spawn_tick'] == current_tick]
    
    # Check if there's room in the queue (limit 4 vehicles per lane)
    lane_counts = {}
    for vehicle in active_vehicles:
        if vehicle.position in ['north', 'south', 'east', 'west']:
            lane_counts[vehicle.position] = lane_counts.get(vehicle.position, 0) + 1
    
    for vehicle_info in vehicles_to_spawn[:]:
        lane = vehicle_info['start']
        # Only spawn if there are fewer than 4 vehicles in this lane
        if lane_counts.get(lane, 0) < MAX_VEHICLES_PER_LANE:
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