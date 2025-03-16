import math
from config import WIDTH, HEIGHT, ROAD_WIDTH, LANES

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

def check_collision(vehicle, next_position, active_vehicles):
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