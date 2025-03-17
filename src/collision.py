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
        
        # Calculate position along the lane
        progress = min(vehicle.position_time / vehicle.position_threshold, 1.0)
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
        
        # Get previous and next positions
        prev_pos = vehicle.route[route_idx-1] if route_idx > 0 else None
        next_pos = vehicle.route[route_idx+1] if route_idx + 1 < len(vehicle.route) else None
        
        if prev_pos and next_pos and isinstance(prev_pos, tuple) and isinstance(next_pos, tuple):
            # Calculate progress through intersection
            progress = min(vehicle.position_time / 50, 1.0)  # Use 50 ticks for intersection
            
            # Linear interpolation between waypoints
            return (
                prev_pos[0] + (next_pos[0] - prev_pos[0]) * progress,
                prev_pos[1] + (next_pos[1] - prev_pos[1]) * progress
            )
        else:
            # Fallback - use center of intersection
            return (WIDTH//2, HEIGHT//2)
    
    # Handle intermediate positions (tuples)
    elif isinstance(vehicle.position, tuple):
        return vehicle.position
    
    # Default fallback
    return LANES.get(vehicle.position, {}).get('in', (WIDTH//2, HEIGHT//2))

def get_vehicle_direction(vehicle):
    """Determine the direction a vehicle should face based on its current position and next position"""
    # Get current position coordinates
    curr_coords = get_vehicle_position(vehicle)
    
    # Get current position index in route
    current_idx = vehicle.route.index(vehicle.position)
    if current_idx >= len(vehicle.route) - 1:
        return 'right'  # Default direction if at end of route
    
    # Get next position
    next_pos = vehicle.route[current_idx + 1]
    
    # If at intersection, look ahead to next waypoint
    if vehicle.position == 'intersection':
        # Find the next tuple waypoint after 'intersection'
        next_waypoints = []
        for i in range(current_idx + 1, min(current_idx + 4, len(vehicle.route))):
            if isinstance(vehicle.route[i], tuple):
                next_waypoints.append(vehicle.route[i])
        
        if next_waypoints:
            next_coords = next_waypoints[0]
        else:
            # If no waypoints found, use default entry points based on previous position
            prev_pos = vehicle.route[current_idx - 1] if current_idx > 0 else 'north'
            if prev_pos == 'north':
                next_coords = (WIDTH//2, HEIGHT//2 - ROAD_WIDTH//4)
            elif prev_pos == 'south':
                next_coords = (WIDTH//2, HEIGHT//2 + ROAD_WIDTH//4)
            elif prev_pos == 'east':
                next_coords = (WIDTH//2 + ROAD_WIDTH//4, HEIGHT//2)
            else:  # west
                next_coords = (WIDTH//2 - ROAD_WIDTH//4, HEIGHT//2)
    else:
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
    
    # Calculate direction vector (flipped to point in direction of travel)
    dx = curr_coords[0] - next_coords[0]  # Flipped
    dy = curr_coords[1] - next_coords[1]  # Flipped
    
    # Add threshold to prevent jitter
    threshold = 10  # Minimum movement to change direction
    
    # Get previous direction for this vehicle
    prev_dir = get_vehicle_direction.previous.get(id(vehicle), 'right')
    
    # Determine direction based on the larger component and threshold
    if abs(dx) > abs(dy) and abs(dx) > threshold:
        new_dir = 'right' if dx > 0 else 'left'
    elif abs(dy) > threshold:
        new_dir = 'down' if dy > 0 else 'up'
    else:
        # If movement is below threshold, maintain previous direction
        new_dir = prev_dir
    
    # Store the new direction for next time
    get_vehicle_direction.previous[id(vehicle)] = new_dir
    
    return new_dir

# Initialize the previous direction dictionary
get_vehicle_direction.previous = {}

def check_collision(vehicle, other_vehicles, light_state):
    """Check for collisions with other vehicles and traffic lights"""
    # Skip ALL collision checks if vehicle is in the intersection
    if vehicle.position == 'intersection':
        vehicle.stopped_for_collision = False
        return False
    
    # Get current vehicle position
    x, y = get_vehicle_position(vehicle)
    
    # Define safe distances
    SAFE_DISTANCE_SAME_LANE = 50  # Reduced from 80 to allow closer following
    LANE_WIDTH = 40  # Width of a single lane
    
    # Check if vehicle is approaching intersection
    is_approaching = vehicle.position in ['north', 'south', 'east', 'west']
    
    # Get next position in route
    route_idx = vehicle.route.index(vehicle.position)
    next_pos = vehicle.route[route_idx + 1] if route_idx + 1 < len(vehicle.route) else None
    
    # Check traffic light state if approaching intersection
    if is_approaching and next_pos == 'intersection':
        # Get light states
        ns_light, ew_light = light_state
        # Check if light is red for this direction
        if ((vehicle.position in ['north', 'south'] and ns_light == "red") or
            (vehicle.position in ['east', 'west'] and ew_light == "red")):
            
            # Get queue positions for this lane
            queue_positions = LANES[vehicle.position]['queue']
            if queue_positions:
                # Get the last queue position (closest to intersection)
                last_queue = queue_positions[-1]
                intersection_entry = LANES[vehicle.position]['in']
                
                # Calculate distances
                if vehicle.position in ['north', 'south']:
                    distance_to_queue = abs(y - last_queue[1])
                    distance_to_intersection = abs(y - intersection_entry[1])
                else:
                    distance_to_queue = abs(x - last_queue[0])
                    distance_to_intersection = abs(x - intersection_entry[0])
                
                # Only stop if we're not too close to the intersection
                COMMIT_DISTANCE = 30  # Reduced from 50 to allow vehicles to commit later
                
                if distance_to_intersection > COMMIT_DISTANCE:
                    # Stop if we're close enough to the queue position
                    if distance_to_queue < SAFE_DISTANCE_SAME_LANE:
                        vehicle.stopped_for_collision = True
                        return True
    
    # Check for collisions with other vehicles
    for other in other_vehicles:
        if other != vehicle and other.state != "arrived":
            # Skip collision check if other vehicle is in intersection
            if other.position == 'intersection':
                continue
            
            # Get other vehicle's position
            other_x, other_y = get_vehicle_position(other)
            
            # Calculate distance between vehicles
            dx = x - other_x
            dy = y - other_y
            distance = (dx * dx + dy * dy) ** 0.5
            
            # Check if vehicles are in the same lane
            same_lane = False
            if vehicle.position in ['north', 'south'] and other.position in ['north', 'south']:
                same_lane = abs(x - other_x) < LANE_WIDTH
            elif vehicle.position in ['east', 'west'] and other.position in ['east', 'west']:
                same_lane = abs(y - other_y) < LANE_WIDTH
            
            # Only stop for vehicles in the same lane that are too close
            if same_lane and distance < SAFE_DISTANCE_SAME_LANE:
                # Check if other vehicle is ahead in the same direction
                if vehicle.position == 'north' and y > other_y:
                    vehicle.stopped_for_collision = True
                    return True
                elif vehicle.position == 'south' and y < other_y:
                    vehicle.stopped_for_collision = True
                    return True
                elif vehicle.position == 'east' and x < other_x:
                    vehicle.stopped_for_collision = True
                    return True
                elif vehicle.position == 'west' and x > other_x:
                    vehicle.stopped_for_collision = True
                    return True
    
    vehicle.stopped_for_collision = False
    return False 