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
                if route_idx > 0 and vehicle.route[route_idx-1] in LANES:
                    entry_point = LANES[vehicle.route[route_idx-1]]['in']
                else:
                    # If no valid previous position, use first waypoint
                    entry_point = next_waypoints[0]
                    segment_progress = 0  # Stay at first waypoint
                target = next_waypoints[0]
            else:
                # Later segments: between waypoints
                entry_point = next_waypoints[segment_idx-1]
                # For the last segment, ensure we move towards the exit point
                if segment_idx >= len(next_waypoints) - 1:
                    # Find the next non-tuple position (should be exit direction)
                    exit_direction = None
                    for i in range(route_idx + 1, len(vehicle.route)):
                        if isinstance(vehicle.route[i], str) and vehicle.route[i] != 'intersection':
                            exit_direction = vehicle.route[i]
                            break
                    
                    if exit_direction and exit_direction in LANES:
                        target = LANES[exit_direction]['in']
                    else:
                        target = next_waypoints[-1]
                else:
                    target = next_waypoints[segment_idx]
            
            # Linear interpolation between points
            return (
                entry_point[0] + (target[0] - entry_point[0]) * segment_progress,
                entry_point[1] + (target[1] - entry_point[1]) * segment_progress
            )
        else:
            # If no waypoints found, try to use entry and exit points
            prev_pos = vehicle.route[route_idx-1] if route_idx > 0 else None
            next_pos = vehicle.route[route_idx+1] if route_idx + 1 < len(vehicle.route) else None
            
            if prev_pos in LANES and next_pos in LANES:
                entry = LANES[prev_pos]['in']
                exit = LANES[next_pos]['in']
                progress = min(vehicle.position_time / vehicle.position_threshold, 1.0)
                return (
                    entry[0] + (exit[0] - entry[0]) * progress,
                    entry[1] + (exit[1] - entry[1]) * progress
                )
            else:
                # Ultimate fallback - use center of intersection
                return (WIDTH//2, HEIGHT//2)
    
    # Handle intermediate positions (tuples)
    elif isinstance(vehicle.position, tuple):
        return vehicle.position
    
    # Default fallback
    return (WIDTH//2, HEIGHT//2)

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
    # Get current vehicle position
    x, y = get_vehicle_position(vehicle)
    
    # Define safe distances
    SAFE_DISTANCE_SAME_LANE = 50  # Increased from default to ensure more space between vehicles
    SAFE_DISTANCE_INTERSECTION = 40  # Safe distance in intersection
    
    # Check if vehicle is at intersection
    is_at_intersection = vehicle.position == 'intersection'
    
    # Check if vehicle is approaching intersection
    is_approaching = vehicle.position in ['north', 'south', 'east', 'west']
    
    # Get next position in route
    route_idx = vehicle.route.index(vehicle.position)
    next_pos = vehicle.route[route_idx + 1] if route_idx + 1 < len(vehicle.route) else None
    
    # Check traffic light state if approaching intersection
    if is_approaching and next_pos == 'intersection':
        # Get light states
        ns_light, ew_light = light_state
        # Check if light is red or yellow for this direction
        if ((vehicle.position in ['north', 'south'] and ns_light in ["red", "yellow"]) or
            (vehicle.position in ['east', 'west'] and ew_light in ["red", "yellow"])):
            # Get queue positions for this lane
            queue_positions = LANES[vehicle.position]['queue']
            if queue_positions:
                # Get the last queue position (closest to intersection)
                last_queue = queue_positions[-1]
                
                # Calculate distance to the last queue position
                if vehicle.position in ['north', 'south']:
                    distance_to_queue = abs(y - last_queue[1])
                else:
                    distance_to_queue = abs(x - last_queue[0])
                
                # Stop if we're close enough to the queue position
                if distance_to_queue < SAFE_DISTANCE_SAME_LANE:
                    vehicle.stopped_for_collision = True
                    return True
    
    # Check for vehicles ahead in the same lane or approaching the same intersection point
    for other in other_vehicles:
        if other != vehicle and other.state != "arrived":
            # Get other vehicle's position
            other_x, other_y = get_vehicle_position(other)
            
            # Calculate distance between vehicles
            dx = x - other_x
            dy = y - other_y
            distance = (dx * dx + dy * dy) ** 0.5
            
            # Check if vehicles are in the same lane
            same_lane = vehicle.position == other.position
            
            # Check if they're approaching the same intersection point
            approaching_same_intersection = (
                is_approaching and 
                other.position == 'intersection' and 
                next_pos == 'intersection'
            )
            
            # Check if they're both in the intersection
            both_in_intersection = (
                is_at_intersection and 
                other.position == 'intersection'
            )
            
            # Determine required safe distance based on situation
            required_distance = SAFE_DISTANCE_SAME_LANE if same_lane else SAFE_DISTANCE_INTERSECTION
            
            # Additional check for vehicles in front
            if same_lane:
                # For north-south lanes
                if vehicle.position in ['north', 'south']:
                    # Check if other vehicle is ahead (using y-coordinate)
                    if (vehicle.position == 'north' and other_y < y) or \
                       (vehicle.position == 'south' and other_y > y):
                        if abs(dy) < SAFE_DISTANCE_SAME_LANE and abs(dx) < 20:  # 20px lateral tolerance
                            vehicle.stopped_for_collision = True
                            return True
                # For east-west lanes
                elif vehicle.position in ['east', 'west']:
                    # Check if other vehicle is ahead (using x-coordinate)
                    if (vehicle.position == 'east' and other_x > x) or \
                       (vehicle.position == 'west' and other_x < x):
                        if abs(dx) < SAFE_DISTANCE_SAME_LANE and abs(dy) < 20:  # 20px lateral tolerance
                            vehicle.stopped_for_collision = True
                            return True
            
            # Stop if too close to another vehicle in intersection
            if (approaching_same_intersection or both_in_intersection) and distance < required_distance:
                vehicle.stopped_for_collision = True
                return True
    
    vehicle.stopped_for_collision = False
    return False 