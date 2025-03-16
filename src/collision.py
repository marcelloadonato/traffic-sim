import pygame
import math
import torch
from src.config import WIDTH, HEIGHT, ROAD_WIDTH, LANES
from src.shared import DEVICE
from src.agent import Vehicle

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
        if len(queue_positions) > 0:
            if progress < 0.5:  # First half of movement - use queue positions
                queue_idx = min(int(progress * len(queue_positions)), len(queue_positions) - 1)
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
        else:
            # Fallback if no queue positions
            start = LANES[vehicle.position]['out']
            end = LANES[vehicle.position]['in']
            return (
                start[0] + (end[0] - start[0]) * progress,
                start[1] + (end[1] - start[1]) * progress
            )
    
    # If at the intersection
    elif vehicle.position == 'intersection':
        # Get current route index and waypoints
        route_idx = vehicle.route.index('intersection')
        
        # Find the next tuple waypoint after 'intersection'
        next_waypoints = []
        for i in range(route_idx + 1, min(route_idx + 4, len(vehicle.route))):
            if isinstance(vehicle.route[i], tuple):
                next_waypoints.append(vehicle.route[i])
        
        # If we have waypoints, use them
        if next_waypoints:
            # Progress through waypoints sequentially
            progress = min(vehicle.position_time / vehicle.position_threshold, 1.0)
            total_waypoints = len(next_waypoints)
            
            # Calculate which segment we're in and the progress within that segment
            segment_idx = min(int(progress * total_waypoints), total_waypoints - 1)
            segment_progress = (progress * total_waypoints) - segment_idx
            segment_progress = max(0, min(1, segment_progress))  # Clamp between 0-1
            
            # Get waypoint coordinates
            if segment_idx == 0:
                # First segment: from entry point to first waypoint
                entry_point = LANES[vehicle.route[route_idx-1]]['in'] if route_idx > 0 and vehicle.route[route_idx-1] in LANES else (WIDTH//2, HEIGHT//2)
                target = next_waypoints[0]
            else:
                # Later segments: between waypoints
                entry_point = next_waypoints[segment_idx-1]
                target = next_waypoints[segment_idx] if segment_idx < len(next_waypoints) else next_waypoints[-1]
            
            # Linear interpolation between points
            return (
                entry_point[0] + (target[0] - entry_point[0]) * segment_progress,
                entry_point[1] + (target[1] - entry_point[1]) * segment_progress
            )
        else:
            # Fallback if no waypoints found - use center of intersection
            return (WIDTH//2, HEIGHT//2)
    
    # Handle intermediate positions (tuples)
    elif isinstance(vehicle.position, tuple):
        return vehicle.position
    
    # Default fallback
    return (WIDTH//2, HEIGHT//2)

def get_vehicle_direction(vehicle):
    """Determine the direction a vehicle should face based on its current position and next position"""
    # Get current position index in route
    current_idx = vehicle.route.index(vehicle.position)
    
    # If at the last position, use previous position to determine direction
    if current_idx >= len(vehicle.route) - 1:
        if current_idx > 0:
            prev_pos = vehicle.route[current_idx - 1]
            curr_pos = vehicle.position
            
            # Calculate direction from previous to current position
            prev_coords = get_vehicle_position(vehicle)  # Current position coordinates
            curr_coords = prev_coords  # Since we're already at this position
            
            # Determine direction based on the path we just took
            dx = curr_coords[0] - (prev_coords[0] if isinstance(prev_coords, tuple) else 0)
            dy = curr_coords[1] - (prev_coords[1] if isinstance(prev_coords, tuple) else 0)
            
            # Return direction based on the larger component
            if abs(dx) > abs(dy):
                return 'right' if dx > 0 else 'left'
            else:
                return 'down' if dy > 0 else 'up'
        else:
            # Default directions for spawn points if no history
            if vehicle.position == 'north':
                return 'down'
            elif vehicle.position == 'south':
                return 'up'
            elif vehicle.position == 'east':
                return 'left'
            elif vehicle.position == 'west':
                return 'right'
            return 'right'  # Default
    
    # Get next position
    next_pos = vehicle.route[current_idx + 1]
    
    # Get current and next coordinates
    curr_coords = get_vehicle_position(vehicle)
    
    # Get next_coords based on what next_pos is
    if isinstance(next_pos, tuple):
        next_coords = next_pos
    elif next_pos in LANES:
        next_coords = LANES[next_pos]['in']
    elif next_pos == 'intersection':
        # Handle approach to intersection better - get first waypoint in intersection
        route_idx = current_idx + 1  # Index of 'intersection'
        
        # Look for the next waypoint after 'intersection'
        if route_idx + 1 < len(vehicle.route) and isinstance(vehicle.route[route_idx + 1], tuple):
            next_coords = vehicle.route[route_idx + 1]
        else:
            # Fallback - use default entry points
            if vehicle.position == 'north':
                next_coords = (WIDTH//2, HEIGHT//2 - ROAD_WIDTH//4)
            elif vehicle.position == 'south':
                next_coords = (WIDTH//2, HEIGHT//2 + ROAD_WIDTH//4)
            elif vehicle.position == 'east':
                next_coords = (WIDTH//2 + ROAD_WIDTH//4, HEIGHT//2)
            elif vehicle.position == 'west':
                next_coords = (WIDTH//2 - ROAD_WIDTH//4, HEIGHT//2)
            else:
                next_coords = (WIDTH//2, HEIGHT//2)
    else:
        # For other named destinations, use their entry point
        dest_idx = vehicle.route.index(next_pos)
        if dest_idx > 0 and dest_idx < len(vehicle.route) - 1:
            if isinstance(vehicle.route[dest_idx + 1], tuple):
                next_coords = vehicle.route[dest_idx + 1]
            else:
                next_coords = (WIDTH//2, HEIGHT//2)  # Default fallback
        else:
            next_coords = LANES.get(next_pos, {}).get('in', (WIDTH//2, HEIGHT//2))
    
    # Calculate direction vector
    dx = next_coords[0] - curr_coords[0]
    dy = next_coords[1] - curr_coords[1]
    
    # Use the larger difference to determine primary direction,
    # with a preference for maintaining the current direction when close to equal
    if abs(dx) > abs(dy) * 1.2:  # Add a 20% bias to prefer horizontal
        return 'right' if dx > 0 else 'left'
    elif abs(dy) > abs(dx) * 1.2:  # Add a 20% bias to prefer vertical
        return 'down' if dy > 0 else 'up'
    elif vehicle.position in ['north', 'south']:
        # When differences are close and coming from N/S, prefer vertical
        return 'down' if dy > 0 else 'up'
    else:
        # When differences are close and coming from E/W, prefer horizontal
        return 'right' if dx > 0 else 'left'

def check_collision(vehicle, next_position, active_vehicles):
    """Check if moving to next_position would cause a collision with another vehicle using GPU acceleration."""
    if not next_position:
        return False
    
    # Get coordinates for the next position
    next_pos_coords = None
    if next_position == 'intersection':
        route_idx = vehicle.route.index('intersection')
        next_idx = route_idx + 1 if route_idx < len(vehicle.route) - 1 else route_idx
        next_pos_coords = get_vehicle_position(Vehicle(vehicle.start_position, vehicle.destination)) if next_idx == route_idx else vehicle.route[next_idx]
    elif next_position in LANES:
        next_pos_coords = LANES[next_position]['in']
    elif isinstance(next_position, tuple):
        next_pos_coords = next_position
    else:
        return False
    
    # Get current vehicle's position
    current_pos_coords = get_vehicle_position(vehicle)
    
    # Convert to tensors
    next_pos_tensor = torch.tensor(next_pos_coords, device=DEVICE)
    current_pos_tensor = torch.tensor(current_pos_coords, device=DEVICE)
    
    # Check distances to other vehicles
    other_positions = []
    for other in active_vehicles:
        if other == vehicle:
            continue
        if other.position not in [vehicle.position, next_position, 'intersection']:
            continue
        other_pos = get_vehicle_position(other)
        other_positions.append(other_pos)
    
    if not other_positions:
        return False
    
    other_pos_tensor = torch.tensor(other_positions, device=DEVICE)
    distances = torch.sqrt(torch.sum((next_pos_tensor - other_pos_tensor) ** 2, dim=1))
    
    # Adjust minimum distance for smoother flow
    min_distance = 30  # Increased from 25 to reduce false positives
    collision_mask = distances < min_distance
    
    return torch.any(collision_mask) 