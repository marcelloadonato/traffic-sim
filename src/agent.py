import random
from src.config import LANES, INTERMEDIATE_POSITIONS, WIDTH, HEIGHT

class Vehicle:
    def __init__(self, route, position, vehicle_type="car", position_threshold=20):
        self.route = route
        self.position = position  # Starting position (edge of map)
        self.vehicle_type = vehicle_type
        self.position_time = 0
        self.position_threshold = position_threshold
        self.state = "moving"
        self.stopped_for_collision = False
        self.satisfaction = 10.0  # Initial satisfaction
        self.commute_time = 0
        self.destination = None  # Will be set when vehicle is created
        self.waiting_time = 0  # Add waiting_time attribute
        self.queue_position = 0  # Add queue_position attribute
        self.last_state = None  # Add last_state attribute
        self.log_counter = 0  # Add log_counter attribute
        
        # Animation and display properties
        self.interpolated_position = None  # For smooth movement between positions
        self.color = None
        self.size_multiplier = 1.0 if vehicle_type == "car" else 1.5 if vehicle_type == "truck" else 1.2
        
        # Performance metrics
        self.speed = 15  # Reduced base speed
        self.base_speed = 15  # Reduced base speed
        self.last_speed = 15  # Reduced base speed
        self.wait_time = 0
        self.total_wait_time = 0
        self.stop_count = 0
        self.acceleration_changes = 0
        self.total_ticks = 0
        
        # Set size and speed based on vehicle type
        if vehicle_type == "truck":
            self.size = 30
            self.base_speed = 10  # Slower for trucks
            self.speed = 10
        elif vehicle_type == "van":
            self.size = 25
            self.base_speed = 12  # Medium speed for vans
            self.speed = 12
        else:  # car
            self.size = 20
            self.base_speed = 15  # Faster for cars but still reasonable
            self.speed = 15
            
    def is_at_edge(self):
        """Check if vehicle is at an edge position"""
        return self.position in ['north', 'south', 'east', 'west']
        
    def get_edge_coords(self):
        """Get the coordinates for edge positions"""
        if self.position == 'north':
            return (WIDTH//2, 0)
        elif self.position == 'south':
            return (WIDTH//2, HEIGHT)
        elif self.position == 'east':
            return (WIDTH, HEIGHT//2)
        elif self.position == 'west':
            return (0, HEIGHT//2)
        return None
    
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
    
    def update(self, light_state, current_fps=30):
        """Update vehicle state and position"""
        self.total_ticks += 1
        
        # Update speed and track acceleration changes
        if self.state == "moving":
            if self.speed != self.last_speed:
                self.acceleration_changes += 1
            self.last_speed = self.speed
            
            # Update wait time if stopped at intersection
            if self.at_intersection() and self._should_stop_at_red(light_state):
                self.wait_time += 1
                self.total_wait_time += 1
                self.speed = 0  # Ensure we stop completely
            else:
                self.wait_time = 0
                self.speed = self.base_speed
        
        # Track stops
        if self.state == "waiting" and self.last_state != "waiting":
            self.stop_count += 1
            self.speed = 0  # Ensure we stop completely
        
        self.last_state = self.state
        
        self.commute_time += 1
        self.log_counter = (self.log_counter + 1) % 10  # Only log every 10 ticks
        
        # Check if we've reached our destination
        if self.position == self.destination:
            self.state = "arrived"
            self.animation_offset = 0  # Reset animation offset
            if self.log_counter == 0:
                print(f"Vehicle arrived at destination: {self.destination}")
            return True
        
        # Get current position index in route
        current_idx = self.route.index(self.position)
        if current_idx >= len(self.route) - 1:
            return False
        
        # Get next position
        next_pos = self.route[current_idx + 1]
        
        # Check if we need to stop for traffic light
        should_stop = False
        
        # Stop at red or yellow light if approaching intersection
        if self.position in ['north', 'south', 'east', 'west'] and next_pos == 'intersection':
            ns_light, ew_light = light_state
            if ((self.position in ['north', 'south'] and ns_light in ["red", "yellow"]) or
                (self.position in ['east', 'west'] and ew_light in ["red", "yellow"])):
                should_stop = True
                if self.state != "waiting" and self.log_counter == 0:
                    print(f"Vehicle stopped at {ns_light if self.position in ['north', 'south'] else ew_light} light: {self.position}")
                self.state = "waiting"
                self.waiting_time += 1
                self.animation_offset = 0
                self.speed = 0  # Ensure we stop completely
        
        # Stop if there's a collision ahead
        if self.check_collision_ahead():
            should_stop = True
            if not self.stopped_for_collision and self.log_counter == 0:
                print(f"Vehicle stopped for collision: {self.position}")
            self.stopped_for_collision = True
            self.state = "waiting"
            self.waiting_time += 1
            self.animation_offset = 0  # Reset animation when stopping
            self.speed = 0  # Ensure we stop completely
        
        # Update position if we're not stopping
        if not should_stop:
            self.state = "moving"
            self.stopped_for_collision = False
            self.waiting_time = 0
            self.speed = self.base_speed  # Restore normal speed
            
            # Adjust movement speed based on position
            base_threshold = self.position_threshold
            if self.position == 'intersection':
                # Slower movement through intersection
                base_threshold = self.position_threshold * 1.5
                self.speed = self.base_speed * 0.8  # Slower in intersection
            elif isinstance(self.position, tuple):
                # Faster movement between waypoints
                base_threshold = self.position_threshold // 2
            
            self.position_time += 1
            progress = min(self.position_time / base_threshold, 1.0)
            fps_scale = current_fps / 30.0
            
            # Calculate movement based on current speed
            self.animation_offset = int(progress * self.speed * fps_scale)
            
            if self.position_time >= base_threshold:
                self.position = next_pos
                self.position_time = 0
                self.animation_offset = 0
                if self.position in ['north', 'south', 'east', 'west']:
                    self.queue_position = min(self.queue_position + 1, 3)
        
        # Decrease satisfaction while waiting
        if self.state == "waiting":
            if self.waiting_time % 10 == 0:  # Decrease satisfaction every 10 ticks instead of 5
                self.satisfaction = max(0, self.satisfaction - 0.1)  # Decrease by 0.1 instead of 0.2
                if self.log_counter == 0:
                    print(f"Vehicle satisfaction decreased to: {self.satisfaction:.1f}")
        else:
            # Gradually recover satisfaction while moving
            if self.waiting_time % 15 == 0:  # Recover satisfaction every 15 ticks
                self.satisfaction = min(10, self.satisfaction + 0.05)  # Recover by 0.05
                if self.log_counter == 0:
                    print(f"Vehicle satisfaction increased to: {self.satisfaction:.1f}")
        
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