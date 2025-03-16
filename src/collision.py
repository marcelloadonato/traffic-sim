import pygame
import math
import torch
from src.config import WIDTH, HEIGHT, ROAD_WIDTH, LANES
from src.shared import DEVICE

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
        if prev_pos and next_pos and isinstance(prev_pos, str) and isinstance(next_pos, str):
            # Calculate entry and exit points
            entry = LANES[prev_pos]['in']  # Start from the entry point of previous lane
            exit_point = LANES[next_pos]['out']  # End at the exit point of next lane
            
            # Determine if the vehicle is turning or going straight
            is_turning = (
                (prev_pos in ['north', 'south'] and next_pos in ['east', 'west']) or
                (prev_pos in ['east', 'west'] and next_pos in ['north', 'south'])
            )
            
            if is_turning:
                # For turning vehicles, use a curved path through the intersection
                # Calculate control points for the curve based on direction
                if prev_pos == 'north':
                    if next_pos == 'east':
                        control_point = (WIDTH//2 + ROAD_WIDTH//4, HEIGHT//2 - ROAD_WIDTH//4)
                    else:  # west
                        control_point = (WIDTH//2 - ROAD_WIDTH//4, HEIGHT//2 - ROAD_WIDTH//4)
                elif prev_pos == 'south':
                    if next_pos == 'east':
                        control_point = (WIDTH//2 + ROAD_WIDTH//4, HEIGHT//2 + ROAD_WIDTH//4)
                    else:  # west
                        control_point = (WIDTH//2 - ROAD_WIDTH//4, HEIGHT//2 + ROAD_WIDTH//4)
                elif prev_pos == 'east':
                    if next_pos == 'north':
                        control_point = (WIDTH//2 + ROAD_WIDTH//4, HEIGHT//2 - ROAD_WIDTH//4)
                    else:  # south
                        control_point = (WIDTH//2 + ROAD_WIDTH//4, HEIGHT//2 + ROAD_WIDTH//4)
                else:  # west
                    if next_pos == 'north':
                        control_point = (WIDTH//2 - ROAD_WIDTH//4, HEIGHT//2 - ROAD_WIDTH//4)
                    else:  # south
                        control_point = (WIDTH//2 - ROAD_WIDTH//4, HEIGHT//2 + ROAD_WIDTH//4)
                
                # Quadratic Bezier curve calculation
                t = progress
                return (
                    (1-t)**2 * entry[0] + 2*(1-t)*t * control_point[0] + t**2 * exit_point[0],
                    (1-t)**2 * entry[1] + 2*(1-t)*t * control_point[1] + t**2 * exit_point[1]
                )
            else:
                # For straight movement, use linear interpolation
                return (
                    entry[0] + (exit_point[0] - entry[0]) * progress,
                    entry[1] + (exit_point[1] - entry[1]) * progress
                )
        
        # Default intersection position if route information is incomplete
        return (WIDTH//2, HEIGHT//2)
    
    # Handle intermediate positions (tuples)
    elif isinstance(vehicle.position, tuple):
        return vehicle.position
    
    # Default fallback
    return (WIDTH//2, HEIGHT//2)

def get_vehicle_direction(vehicle):
    """Determine the direction a vehicle should face based on its current position and next position"""
    # Get current and next positions
    current_idx = vehicle.route.index(vehicle.position)
    next_pos = vehicle.route[current_idx + 1] if current_idx < len(vehicle.route) - 1 else None
    
    # If no next position, maintain current direction
    if not next_pos:
        return 'right'
    
    # If current position is a cardinal direction
    if vehicle.position in ['north', 'south', 'east', 'west']:
        if vehicle.position == 'north':
            return 'down'
        elif vehicle.position == 'south':
            return 'up'
        elif vehicle.position == 'east':
            return 'left'
        elif vehicle.position == 'west':
            return 'right'
    
    # Get coordinates for current and next positions
    curr_coords = get_vehicle_position(vehicle)
    next_coords = None
    
    if isinstance(next_pos, tuple):
        next_coords = next_pos
    elif next_pos in LANES:
        next_coords = LANES[next_pos]['in']
    elif next_pos == 'intersection':
        # Use the entry point of the intersection based on current position
        if vehicle.position == 'north':
            next_coords = (WIDTH//2, HEIGHT//2 - ROAD_WIDTH//2)
        elif vehicle.position == 'south':
            next_coords = (WIDTH//2, HEIGHT//2 + ROAD_WIDTH//2)
        elif vehicle.position == 'east':
            next_coords = (WIDTH//2 + ROAD_WIDTH//2, HEIGHT//2)
        elif vehicle.position == 'west':
            next_coords = (WIDTH//2 - ROAD_WIDTH//2, HEIGHT//2)
    
    if next_coords:
        # Determine direction based on coordinate differences
        dx = next_coords[0] - curr_coords[0]
        dy = next_coords[1] - curr_coords[1]
        
        # Use the larger difference to determine primary direction
        if abs(dx) > abs(dy):
            return 'right' if dx > 0 else 'left'
        else:
            return 'down' if dy > 0 else 'up'
    
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
    min_distance = 25  # Simple minimum distance to prevent overlap
    collision_mask = distances < min_distance
    
    # If any vehicle is too close, consider it a collision
    return torch.any(collision_mask) 