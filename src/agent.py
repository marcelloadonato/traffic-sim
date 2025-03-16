import random
from src.config import LANES, INTERMEDIATE_POSITIONS

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
        self.animation_offset = 0
        self.stopped_for_collision = False
        self.vehicle_type = random.choice(["car", "truck", "van"])
        self.size_multiplier = 1.0 if self.vehicle_type == "car" else 1.5 if self.vehicle_type == "truck" else 1.2
        self.color = None  # Will be set by spawner
        self.queue_position = 0  # Track position in queue
        self.log_counter = 0  # For reducing log spam
        self.waiting_time = 0  # Track continuous waiting time
        
        # Adjust timing based on vehicle type
        if self.vehicle_type == "truck":
            self.position_threshold = 80  # Trucks move slower
        elif self.vehicle_type == "van":
            self.position_threshold = 70  # Vans move a bit slower
        
    def _determine_route(self):
        """Determine the route from start to destination"""
        route = [self.start_position]
        
        # Add intermediate positions for smoother movement
        if self.start_position != self.destination:
            # Add intersection
            route.append('intersection')
            
            # Add intermediate positions after intersection
            route_key = f'intersection_to_{self.destination}'
            if route_key in INTERMEDIATE_POSITIONS:
                route.extend(INTERMEDIATE_POSITIONS[route_key])
        
        # Add destination
        route.append(self.destination)
        return route
    
    def update(self, light_state):
        """Update vehicle state and position"""
        self.commute_time += 1
        self.log_counter = (self.log_counter + 1) % 10  # Only log every 10 ticks
        
        # Check if we've reached our destination
        if self.position == self.destination:
            self.state = "arrived"
            if self.log_counter == 0:
                print(f"Vehicle arrived at destination: {self.destination}")
            return
        
        # Get current position index in route
        current_idx = self.route.index(self.position)
        if current_idx >= len(self.route) - 1:
            return
        
        # Get next position
        next_pos = self.route[current_idx + 1]
        
        # Check if we need to stop
        should_stop = False
        
        # Stop at red light if we're at the intersection entrance
        if self.position in ['north', 'south', 'east', 'west']:
            if light_state == "red" and self._should_stop_at_red():
                should_stop = True
                if self.state != "waiting" and self.log_counter == 0:
                    print(f"Vehicle stopped at red light: {self.position}")
                self.state = "waiting"
                self.waiting_time += 1
        
        # Stop if there's a collision ahead
        if self.check_collision_ahead():
            should_stop = True
            if not self.stopped_for_collision and self.log_counter == 0:
                print(f"Vehicle stopped for collision: {self.position}")
            self.stopped_for_collision = True
            self.state = "waiting"
            self.waiting_time += 1
        
        # Update position if we're not stopping
        if not should_stop:
            self.state = "moving"
            self.stopped_for_collision = False
            self.waiting_time = 0
            self.position_time += 1
            
            # Move to next position if we've waited long enough
            if self.position_time >= self.position_threshold:
                self.position = next_pos
                self.position_time = 0
                
                # Update queue position if we're in a lane
                if self.position in ['north', 'south', 'east', 'west']:
                    self.queue_position = min(self.queue_position + 1, 3)
        
        # Decrease satisfaction while waiting
        if self.state == "waiting":
            if self.waiting_time % 5 == 0:  # Decrease satisfaction every 5 ticks
                self.satisfaction = max(0, self.satisfaction - 0.2)  # Decrease by 0.2 every 5 ticks
                if self.log_counter == 0:
                    print(f"Vehicle satisfaction decreased to: {self.satisfaction:.1f}")
    
    def check_collision_ahead(self):
        """This will be set by the simulation to check for collisions"""
        return False  # Default implementation
    
    def _should_stop_at_red(self):
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