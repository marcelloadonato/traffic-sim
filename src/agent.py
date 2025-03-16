import random
from src.config import LANES, INTERMEDIATE_POSITIONS, WIDTH, HEIGHT

class Vehicle:
    def __init__(self, route, position, vehicle_type="car", position_threshold=100):
        self.route = route
        self.position = position
        self.vehicle_type = vehicle_type
        self.position_time = 0
        self.position_threshold = position_threshold
        self.state = "moving"  # Start in moving state
        self.stopped_for_collision = False
        self.satisfaction = 10.0
        self.commute_time = 0
        self.destination = None
        self.waiting_time = 0
        self.queue_position = 0
        self.last_state = None
        self.log_counter = 0
        
        # Set size and speed based on vehicle type
        if vehicle_type == "truck":
            self.size = 30
            self.base_speed = 2
            self.speed = 2
        elif vehicle_type == "van":
            self.size = 25
            self.base_speed = 3
            self.speed = 3
        else:  # car
            self.size = 20
            self.base_speed = 4
            self.speed = 4
        
        # Animation and display properties
        self.color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        self.size_multiplier = 1.0 if vehicle_type == "car" else 1.5 if vehicle_type == "truck" else 1.2
        
        # Set initial interpolated position based on starting position
        if position == 'east':
            self.interpolated_position = (WIDTH, HEIGHT//2)
        elif position == 'west':
            self.interpolated_position = (0, HEIGHT//2)
        elif position == 'north':
            self.interpolated_position = (WIDTH//2, 0)
        elif position == 'south':
            self.interpolated_position = (WIDTH//2, HEIGHT)
        else:
            self.interpolated_position = None
        
        # Performance tracking
        self.total_ticks = 0
        self.wait_time = 0
        self.total_wait_time = 0
        self.stop_count = 0
        self.acceleration_changes = 0
        self.last_speed = self.speed
        
        # Movement tracking
        self.movement_history = []
        self.direction_changes = []
        self.interpolation_values = []
        self.movement_vectors = []
        self.route_progression = []
        self.position_time_history = []
        self.last_movement_vector = None
        self.reversal_count = 0
        self.last_interpolated_position = None
    
    def is_at_edge(self):
        """Check if vehicle is at an edge position"""
        return self.position in ['north', 'south', 'east', 'west']
    
    def get_current_coords(self):
        """Get current coordinates based on position"""
        if isinstance(self.position, tuple):
            return self.position
        elif self.position == 'north':
            return (WIDTH//2, 0)
        elif self.position == 'south':
            return (WIDTH//2, HEIGHT)
        elif self.position == 'east':
            return (WIDTH, HEIGHT//2)
        elif self.position == 'west':
            return (0, HEIGHT//2)
        elif self.position == 'intersection':
            return (WIDTH//2, HEIGHT//2)
        return None
    
    def get_next_coords(self, next_pos):
        """Get next coordinates based on next position"""
        if isinstance(next_pos, tuple):
            return next_pos
        elif next_pos == 'north':
            return (WIDTH//2, 0)
        elif next_pos == 'south':
            return (WIDTH//2, HEIGHT)
        elif next_pos == 'east':
            return (WIDTH, HEIGHT//2)
        elif next_pos == 'west':
            return (0, HEIGHT//2)
        elif next_pos == 'intersection':
            return (WIDTH//2, HEIGHT//2)
        return None
    
    def is_behind(self, other_vehicle):
        """Check if this vehicle is behind another vehicle"""
        if not self.interpolated_position or not other_vehicle.interpolated_position:
            return False
        
        # Get current direction based on route
        current_idx = self.route.index(self.position)
        if current_idx >= len(self.route) - 1:
            return False
        
        next_pos = self.route[current_idx + 1]
        next_coords = self.get_next_coords(next_pos)
        if not next_coords:
            return False
        
        # Calculate direction vector
        dx = next_coords[0] - self.interpolated_position[0]
        dy = next_coords[1] - self.interpolated_position[1]
        
        # Get distance to other vehicle
        other_dx = other_vehicle.interpolated_position[0] - self.interpolated_position[0]
        other_dy = other_vehicle.interpolated_position[1] - self.interpolated_position[1]
        
        # Check if other vehicle is in our path and close enough to matter
        if abs(dx) > abs(dy):  # Moving horizontally
            if abs(other_dy) > 30:  # Not in same lane
                return False
            if dx > 0:  # Moving right
                return other_dx > 0 and other_dx < 100
            else:  # Moving left
                return other_dx < 0 and other_dx > -100
        else:  # Moving vertically
            if abs(other_dx) > 30:  # Not in same lane
                return False
            if dy > 0:  # Moving down
                return other_dy > 0 and other_dy < 100
            else:  # Moving up
                return other_dy < 0 and other_dy > -100
    
    def _determine_route(self):
        """Create a complete route from start to destination with proper waypoints."""
        route = [self.start_position]
        
        if self.start_position != self.destination:
            # Add pre-intersection waypoints (approach)
            route_key = f'{self.start_position}_to_intersection'
            if route_key in INTERMEDIATE_POSITIONS:
                route.extend(INTERMEDIATE_POSITIONS[route_key])
            
            # Add the intersection marker
            route.append('intersection')
            
            # Add precise waypoints through the intersection based on turn type
            if self.start_position == 'north':
                if self.destination == 'south':
                    # Straight path (north to south)
                    route.extend([
                        (WIDTH//2, HEIGHT//2 - 20),  # Enter intersection
                        (WIDTH//2, HEIGHT//2),       # Center
                        (WIDTH//2, HEIGHT//2 + 20)   # Exit intersection
                    ])
                elif self.destination == 'east':
                    # Right turn (north to east)
                    route.extend([
                        (WIDTH//2, HEIGHT//2 - 20),  # Enter intersection
                        (WIDTH//2 + 10, HEIGHT//2 - 10),  # Curve point
                        (WIDTH//2 + 20, HEIGHT//2)   # Exit intersection
                    ])
                elif self.destination == 'west':
                    # Left turn (north to west)
                    route.extend([
                        (WIDTH//2, HEIGHT//2 - 20),   # Enter intersection
                        (WIDTH//2 - 10, HEIGHT//2 - 10),  # Curve point
                        (WIDTH//2 - 20, HEIGHT//2)    # Exit intersection
                    ])
            elif self.start_position == 'south':
                if self.destination == 'north':
                    # Straight path (south to north)
                    route.extend([
                        (WIDTH//2, HEIGHT//2 + 20),  # Enter intersection
                        (WIDTH//2, HEIGHT//2),       # Center
                        (WIDTH//2, HEIGHT//2 - 20)   # Exit intersection
                    ])
                elif self.destination == 'west':
                    # Right turn (south to west)
                    route.extend([
                        (WIDTH//2, HEIGHT//2 + 20),   # Enter intersection
                        (WIDTH//2 - 10, HEIGHT//2 + 10),  # Curve point
                        (WIDTH//2 - 20, HEIGHT//2)    # Exit intersection
                    ])
                elif self.destination == 'east':
                    # Left turn (south to east)
                    route.extend([
                        (WIDTH//2, HEIGHT//2 + 20),   # Enter intersection
                        (WIDTH//2 + 10, HEIGHT//2 + 10),  # Curve point
                        (WIDTH//2 + 20, HEIGHT//2)    # Exit intersection
                    ])
            elif self.start_position == 'east':
                if self.destination == 'west':
                    # Straight path (east to west)
                    route.extend([
                        (WIDTH//2 + 20, HEIGHT//2),  # Enter intersection
                        (WIDTH//2, HEIGHT//2),       # Center
                        (WIDTH//2 - 20, HEIGHT//2)   # Exit intersection
                    ])
                elif self.destination == 'north':
                    # Right turn (east to north)
                    route.extend([
                        (WIDTH//2 + 20, HEIGHT//2),   # Enter intersection
                        (WIDTH//2 + 10, HEIGHT//2 - 10),  # Curve point
                        (WIDTH//2, HEIGHT//2 - 20)    # Exit intersection
                    ])
                elif self.destination == 'south':
                    # Left turn (east to south)
                    route.extend([
                        (WIDTH//2 + 20, HEIGHT//2),   # Enter intersection
                        (WIDTH//2 + 10, HEIGHT//2 + 10),  # Curve point
                        (WIDTH//2, HEIGHT//2 + 20)    # Exit intersection
                    ])
            elif self.start_position == 'west':
                if self.destination == 'east':
                    # Straight path (west to east)
                    route.extend([
                        (WIDTH//2 - 20, HEIGHT//2),  # Enter intersection
                        (WIDTH//2, HEIGHT//2),       # Center
                        (WIDTH//2 + 20, HEIGHT//2)   # Exit intersection
                    ])
                elif self.destination == 'south':
                    # Right turn (west to south)
                    route.extend([
                        (WIDTH//2 - 20, HEIGHT//2),   # Enter intersection
                        (WIDTH//2 - 10, HEIGHT//2 + 10),  # Curve point
                        (WIDTH//2, HEIGHT//2 + 20)    # Exit intersection
                    ])
                elif self.destination == 'north':
                    # Left turn (west to north)
                    route.extend([
                        (WIDTH//2 - 20, HEIGHT//2),   # Enter intersection
                        (WIDTH//2 - 10, HEIGHT//2 - 10),  # Curve point
                        (WIDTH//2, HEIGHT//2 - 20)    # Exit intersection
                    ])
            
            # Add post-intersection waypoints (exit)
            route_key = f'intersection_to_{self.destination}'
            if route_key in INTERMEDIATE_POSITIONS:
                route.extend(INTERMEDIATE_POSITIONS[route_key])
        
        # Add final destination
        route.append(self.destination)
        
        # Print route for debugging
        if len(route) > 3:
            print(f"Route: {route}")
        
        return route
    
    def update(self, light_state, vehicles=None):
        """Update vehicle state and position"""
        self.total_ticks += 1
        
        # Check if we've reached our destination
        if self.position == self.destination:
            if self.is_at_edge():
                self.state = "arrived"
                return True
        
        # Get current position index in route
        try:
            current_idx = self.route.index(self.position)
            if current_idx >= len(self.route) - 1:
                return False
            
            # Get next position
            next_pos = self.route[current_idx + 1]
            
            # Get current and next coordinates
            current_coords = self.get_current_coords()
            next_coords = self.get_next_coords(next_pos)
            
            if not current_coords or not next_coords:
                return False
            
            # Check if we need to stop
            should_stop = False
            
            # Stop at red or yellow light if approaching intersection
            if self.position in ['north', 'south', 'east', 'west'] and next_pos == 'intersection':
                ns_light, ew_light = light_state
                if ((self.position in ['north', 'south'] and ns_light in ["red", "yellow"]) or
                    (self.position in ['east', 'west'] and ew_light in ["red", "yellow"])):
                    should_stop = True
                    self.state = "waiting"
                    self.waiting_time += 1
                    self.speed = 0
                    return False
            
            # Check for vehicles ahead if provided
            if not should_stop and vehicles:
                for other_vehicle in vehicles:
                    if other_vehicle != self and other_vehicle.state != "arrived":
                        if self.is_behind(other_vehicle):
                            should_stop = True
                            self.state = "waiting"
                            self.waiting_time += 1
                            self.speed = 0
                            return False
            
            # Update position if not stopped
            if not should_stop:
                self.state = "moving"
                self.waiting_time = 0
                
                # Update position time
                self.position_time += self.speed
                
                # Calculate progress
                progress = min(self.position_time / self.position_threshold, 1.0)
                
                # Calculate new interpolated position
                new_x = current_coords[0] + (next_coords[0] - current_coords[0]) * progress
                new_y = current_coords[1] + (next_coords[1] - current_coords[1]) * progress
                
                # Store new interpolated position
                self.interpolated_position = (new_x, new_y)
                
                # Move to next position when threshold is reached
                if progress >= 1.0:
                    self.position = next_pos
                    self.position_time = 0
                    
                    # Check for arrival at destination
                    if self.position == self.destination and self.is_at_edge():
                        self.state = "arrived"
                        return True
                    
                    return True
            
            return False
            
        except ValueError as e:
            return False
    
    def check_collision_ahead(self):
        """This will be set by the simulation to check for collisions"""
        return False  # Default implementation
    
    def _should_stop_at_red(self, light_state):
        """Determine if this vehicle should stop at a red light based on its route."""
        if self.position in ['north', 'south']:
            # North-South traffic should stop on red light
            return True
        elif self.position in ['east', 'west']:
            # East-West traffic should stop on red light
            return True
        return False  # Default case (e.g., in intersection already)
    
    def at_intersection(self):
        """Check if vehicle is at the intersection."""
        return self.position == "intersection"
    
    def update_metrics(self):
        """Update vehicle performance metrics"""
        self.total_ticks += 1
        
        if self.state == "waiting":
            self.wait_time += 1
            self.total_wait_time += 1
            if self.speed > 0:
                self.stop_count += 1
            self.speed = 0
        else:
            self.wait_time = 0
            self.speed = self.base_speed
            
        # Track acceleration changes
        if self.speed != self.last_speed:
            self.acceleration_changes += 1
        self.last_speed = self.speed 

    def get_movement_analysis(self):
        """Get analysis of movement patterns and anomalies"""
        return {
            'total_reversals': self.reversal_count,
            'direction_changes': self.direction_changes,
            'movement_history': self.movement_history,
            'interpolation_values': self.interpolation_values,
            'route_progression': self.route_progression,
            'position_time_history': self.position_time_history
        } 