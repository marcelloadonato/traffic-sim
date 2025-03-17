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
        
        # Define lane width and safe distance
        LANE_WIDTH = 40  # Width of a single lane
        SAFE_DISTANCE = 80  # Reduced from 150 to allow closer following
        
        # Check if vehicles are in different lanes
        if abs(dx) > abs(dy):  # Moving horizontally
            if abs(other_dy) > LANE_WIDTH:
                return False  # Different lanes
            if dx > 0:  # Moving right
                return other_dx > 0 and other_dx < SAFE_DISTANCE
            else:  # Moving left
                return other_dx < 0 and other_dx > -SAFE_DISTANCE
        else:  # Moving vertically
            if abs(other_dx) > LANE_WIDTH:
                return False  # Different lanes
            if dy > 0:  # Moving down
                return other_dy > 0 and other_dy < SAFE_DISTANCE
            else:  # Moving up
                return other_dy < 0 and other_dy > -SAFE_DISTANCE
    
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
    
    def update(self, simulation):
        """Update the vehicle's state and position"""
        # Get current traffic light states
        ns_light = simulation.traffic_lights['ns']
        ew_light = simulation.traffic_lights['ew']
        
        # Check if we need to stop for a red light
        should_stop_for_light = False
        if self.position in ['north', 'south'] and ns_light == 'red':
            should_stop_for_light = True
        elif self.position in ['east', 'west'] and ew_light == 'red':
            should_stop_for_light = True
        
        # Check if we need to stop for other vehicles
        should_stop_for_vehicle = False
        for other in simulation.vehicles:
            if other != self and other.is_ahead(self) and self.distance_to(other) < 50:
                should_stop_for_vehicle = True
                break
        
        # Update state based on conditions
        if should_stop_for_light or should_stop_for_vehicle:
            self.state = "waiting"
            self.speed = 0
        else:
            self.state = "moving"
            self.speed = self.base_speed
        
        # Update position time and check for position change
        if self.state == "moving":
            self.position_time += self.speed
            
            # Check if we've reached the next position
            if self.position_time >= self.position_threshold:
                self.position_time = 0
                
                # Get current route index
                current_idx = self.route.index(self.position)
                
                # Move to next position if available
                if current_idx + 1 < len(self.route):
                    self.position = self.route[current_idx + 1]
                else:
                    # Reached destination
                    self.state = "arrived"
                    self.speed = 0
        
        # Update commute time
        self.commute_time += 1
    
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