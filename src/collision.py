import math
import torch
from config import WIDTH, HEIGHT, ROAD_WIDTH, LANES
from shared import DEVICE

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
        
        # If vehicle is waiting at the light, pull up to the intersection
        if vehicle.state == "waiting" and vehicle.position_time >= vehicle.position_threshold:
            return LANES[vehicle.position]['in']
        
        # Calculate position along the queue
        if progress < 0.5:  # First half of movement - use queue positions
            queue_idx = min(int(progress * 8), len(queue_positions) - 1)
            return queue_positions[queue_idx]
        else:  # Second half - approach the intersection entrance
            # Interpolate between last queue position and intersection entrance
            last_queue = queue_positions[-1]
            intersection = LANES[vehicle.position]['in']
            t = (progress - 0.5) * 2  # Scale 0.5-1.0 to 0-1
            return (
                last_queue[0] + (intersection[0] - last_queue[0]) * t,
                last_queue[1] + (intersection[1] - last_queue[1]) * t
            )
    
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
                if prev_pos == 'north':
                    return (WIDTH//2, HEIGHT//2 - 40)
                elif prev_pos == 'south':
                    return (WIDTH//2, HEIGHT//2 + 40)
                elif prev_pos == 'east':
                    return (WIDTH//2 + 40, HEIGHT//2)
                else:  # west
                    return (WIDTH//2 - 40, HEIGHT//2)
            
            # Middle third - center of intersection
            elif progress < 0.66:
                return (WIDTH//2, HEIGHT//2)
            
            # Last third - exiting intersection
            else:
                if next_pos == 'north':
                    return (WIDTH//2, HEIGHT//2 - 40)
                elif next_pos == 'south':
                    return (WIDTH//2, HEIGHT//2 + 40)
                elif next_pos == 'east':
                    return (WIDTH//2 + 40, HEIGHT//2)
                else:  # west
                    return (WIDTH//2 - 40, HEIGHT//2)
        
        # Default intersection position
        return (WIDTH//2, HEIGHT//2)
    
    # Default fallback
    return (WIDTH//2, HEIGHT//2)

def get_vehicle_direction(vehicle):
    """Determine the direction a vehicle should face based on its current position and next position"""
    # If at a cardinal direction (north, south, east, west), determine direction based on destination
    if vehicle.position in ['north', 'south', 'east', 'west']:
        if vehicle.position == 'north':
            return 'down'
        elif vehicle.position == 'south':
            return 'up'
        elif vehicle.position == 'east':
            return 'left'
        elif vehicle.position == 'west':
            return 'right'
    
    # If in the intersection or moving between positions, determine direction based on current and next position
    current_idx = vehicle.route.index(vehicle.position)
    if current_idx < len(vehicle.route) - 1:
        next_pos = vehicle.route[current_idx + 1]
        
        # If next position is a tuple, compare coordinates
        if isinstance(vehicle.position, tuple) and isinstance(next_pos, tuple):
            curr_x, curr_y = vehicle.position
            next_x, next_y = next_pos
            
            if next_x > curr_x:
                return 'right'
            elif next_x < curr_x:
                return 'left'
            elif next_y > curr_y:
                return 'down'
            else:
                return 'up'
        
        # If next position is a cardinal direction, determine based on that
        if next_pos == 'north':
            return 'up'
        elif next_pos == 'south':
            return 'down'
        elif next_pos == 'east':
            return 'right'
        elif next_pos == 'west':
            return 'left'
    
    # Default to current direction if can't determine
    return 'right'  # Default direction

def check_collision(vehicle, next_position, active_vehicles):
    """Check if moving to next_position would cause a collision with another vehicle using GPU acceleration"""
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
    
    # Convert positions to tensors for GPU acceleration
    next_pos_tensor = torch.tensor(next_pos_coords, device=DEVICE)
    current_pos_tensor = torch.tensor(current_pos_coords, device=DEVICE)
    
    # Create tensors for all other vehicle positions
    other_positions = []
    for other in active_vehicles:
        if other == vehicle:
            continue  # Skip self
            
        # Skip vehicles not in the same lane or not ahead of us
        if other.position != next_position and other.position != vehicle.position:
            continue
            
        other_pos = get_vehicle_position(other)
        other_positions.append(other_pos)
    
    if not other_positions:
        return False
    
    # Convert other positions to tensor
    other_pos_tensor = torch.tensor(other_positions, device=DEVICE)
    
    # Calculate distances using GPU
    distances = torch.sqrt(torch.sum((next_pos_tensor - other_pos_tensor) ** 2, dim=1))
    
    # Check for collisions (distance < min_distance)
    min_distance = 25
    collision_mask = distances < min_distance
    
    # Check if any collisions are ahead of us in our direction of travel
    if torch.any(collision_mask):
        for i, is_collision in enumerate(collision_mask):
            if is_collision:
                other_pos = other_positions[i]
                if vehicle.start_position == 'north' and other_pos[1] < current_pos_coords[1]:
                    return True
                elif vehicle.start_position == 'south' and other_pos[1] > current_pos_coords[1]:
                    return True
                elif vehicle.start_position == 'east' and other_pos[0] > current_pos_coords[0]:
                    return True
                elif vehicle.start_position == 'west' and other_pos[0] < current_pos_coords[0]:
                    return True
    
    return False  # No collision 