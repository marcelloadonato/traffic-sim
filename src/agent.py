import random
from src.config import LANES, INTERMEDIATE_POSITIONS, WIDTH, HEIGHT

class Vehicle:
    def __init__(self, start, destination):
        self.start_position = start
        self.destination = destination
        self.position = start
        self.route = self._determine_route()
        self.state = "moving"
        self.commute_time = 0
        self.satisfaction = 10
        self.position_time = 0
        self.position_threshold = 30  # Time to move between positions
        self.animation_offset = 0  # For smooth movement animation
        self.stopped_for_collision = False
        self.vehicle_type = random.choice(["car", "truck", "van"])
        self.size_multiplier = 1.0 if self.vehicle_type == "car" else 1.5 if self.vehicle_type == "truck" else 1.2
        self.color = None  # Will be set by spawner
        self.queue_position = 0  # Track position in queue
        self.log_counter = 0  # For reducing log spam
        self.waiting_time = 0  # Track continuous waiting time
        self.base_speed = 30  # Base speed in pixels per step
        
        # New metrics tracking
        self.stop_count = 0  # Number of times the vehicle has stopped
        self.acceleration_changes = 0  # Number of acceleration/deceleration changes
        self.total_ticks = 0  # Total number of ticks the vehicle has been active
        self.speed = self.base_speed  # Current speed
        self.last_speed = self.base_speed  # Previous speed for tracking changes
        self.wait_time = 0  # Current wait time at intersection
        self.total_wait_time = 0  # Total wait time throughout journey
        
        # Adjust timing based on vehicle type
        if self.vehicle_type == "truck":
            self.position_threshold = 80  # Trucks move slower
            self.base_speed = 20  # Slower base speed for trucks
        elif self.vehicle_type == "van":
            self.position_threshold = 70  # Vans move a bit slower
            self.base_speed = 25  # Slightly slower base speed for vans
        
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
            else:
                self.wait_time = 0
        
        # Track stops
        if self.state == "waiting" and self.last_state != "waiting":
            self.stop_count += 1
        
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
        
        # Check if we need to stop
        should_stop = False
        
        # Stop at red or yellow light if approaching intersection
        if self.position in ['north', 'south', 'east', 'west']:
            if light_state in ["red", "yellow"]:
                should_stop = True
                if self.state != "waiting" and self.log_counter == 0:
                    print(f"Vehicle stopped at {light_state} light: {self.position}")
                self.state = "waiting"
                self.waiting_time += 1
                self.animation_offset = 0
        
        # Stop if there's a collision ahead
        if self.check_collision_ahead():
            should_stop = True
            if not self.stopped_for_collision and self.log_counter == 0:
                print(f"Vehicle stopped for collision: {self.position}")
            self.stopped_for_collision = True
            self.state = "waiting"
            self.waiting_time += 1
            self.animation_offset = 0  # Reset animation when stopping
        
        # Update position if we're not stopping
        if not should_stop:
            self.state = "moving"
            self.stopped_for_collision = False
            self.waiting_time = 0
            
            base_threshold = self.position_threshold
            if self.position == 'intersection' or isinstance(self.position, tuple):
                base_threshold = self.position_threshold // 2  # Faster through intersection
            
            self.position_time += 1
            progress = min(self.position_time / base_threshold, 1.0)
            fps_scale = current_fps / 30.0
            
            movement_speed = self.base_speed * 1.5 if self.position == 'intersection' else self.base_speed
            self.animation_offset = int(progress * movement_speed * fps_scale)
            
            if self.position_time >= base_threshold:
                self.position = next_pos
                self.position_time = 0
                self.animation_offset = 0
                if self.position in ['north', 'south', 'east', 'west']:
                    self.queue_position = min(self.queue_position + 1, 3)
        
        # Decrease satisfaction while waiting
        if self.state == "waiting":
            if self.waiting_time % 5 == 0:  # Decrease satisfaction every 5 ticks
                self.satisfaction = max(0, self.satisfaction - 0.2)  # Decrease by 0.2 every 5 ticks
                if self.log_counter == 0:
                    print(f"Vehicle satisfaction decreased to: {self.satisfaction:.1f}")
        
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