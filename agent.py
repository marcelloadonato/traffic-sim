# agent.py
import random
import math

class Vehicle:
    def __init__(self, start, destination):
        """Initialize a vehicle agent."""
        self.position = start          # Current position (e.g., 'north')
        self.start_position = start    # Remember where we started
        self.destination = destination # Target endpoint (e.g., 'south')
        self.route = self._determine_route(start, destination)  # Calculate route
        self.commute_time = 0          # Time taken so far (in ticks)
        self.satisfaction = 10         # Happiness score (max 10)
        self.state = "moving"          # Current state: 'moving', 'waiting', 'arrived'
        
        # Movement timing
        self.position_time = 0         # Time spent at current position
        self.position_threshold = 30   # Ticks to spend at each position
        
        # New attributes for enhanced visualization
        self.color = None              # Will be assigned in main.py
        self.vehicle_type = random.choice(["car", "truck", "van"])  # Vehicle type
        self.size_multiplier = 1.0     # Default size
        
        # Adjust size based on vehicle type
        if self.vehicle_type == "truck":
            self.size_multiplier = 1.4
            self.position_threshold = 40  # Trucks move slower
        elif self.vehicle_type == "van":
            self.size_multiplier = 1.2
            self.position_threshold = 35  # Vans move a bit slower
            
        # Animation attributes
        self.animation_offset = 0      # For small movement animations
        self.waiting_time = 0          # Track continuous waiting time
        
        # Debug info
        print(f"Created vehicle: {start} -> {destination}, Route: {self.route}")
    
    def _determine_route(self, start, destination):
        """Determine the route based on start and destination positions."""
        # For a simple 4-way intersection, the route is straightforward
        # We just need to pass through the intersection
        if start == 'north' and destination == 'south':
            return ['north', 'intersection', 'south']
        elif start == 'south' and destination == 'north':
            return ['south', 'intersection', 'north']
        elif start == 'east' and destination == 'west':
            return ['east', 'intersection', 'west']
        elif start == 'west' and destination == 'east':
            return ['west', 'intersection', 'east']
        elif start == 'north' and destination == 'east':
            return ['north', 'intersection', 'east']
        elif start == 'north' and destination == 'west':
            return ['north', 'intersection', 'west']
        elif start == 'south' and destination == 'east':
            return ['south', 'intersection', 'east']
        elif start == 'south' and destination == 'west':
            return ['south', 'intersection', 'west']
        elif start == 'east' and destination == 'north':
            return ['east', 'intersection', 'north']
        elif start == 'east' and destination == 'south':
            return ['east', 'intersection', 'south']
        elif start == 'west' and destination == 'north':
            return ['west', 'intersection', 'north']
        elif start == 'west' and destination == 'south':
            return ['west', 'intersection', 'south']
        else:
            # Default fallback
            return [start, 'intersection', destination]

    def update(self, light_state):
        """Update vehicle state based on stoplight."""
        self.commute_time += 1
        
        # Update animation offset (small bobbing motion)
        self.animation_offset = math.sin(self.commute_time * 0.2) * 0.5
        
        if self.position == self.destination:
            self.state = "arrived"
            print(f"Vehicle arrived at {self.destination} after {self.commute_time} ticks")
        elif light_state == "red" and self.at_intersection() and self._should_stop_at_red():
            if self.state != "waiting":
                self.state = "waiting"
                self.waiting_time = 0
                print(f"Vehicle waiting at intersection (red light)")
            else:
                self.waiting_time += 1
                
            if self.waiting_time % 5 == 0:  # Decrease satisfaction every 5 ticks
                self.satisfaction = max(0, self.satisfaction - 1)
                print(f"Vehicle satisfaction decreased to {self.satisfaction}")
        elif self.state == "moving" or self.state == "waiting":
            # If was waiting but now can move
            if self.state == "waiting":
                self.state = "moving"
                self.waiting_time = 0
                print(f"Vehicle resumed moving")
            
            # Increment position time
            self.position_time += 1
            
            # Move to next position if we've been at this one long enough
            if self.position_time >= self.position_threshold:
                self.move_one_step()
                self.position_time = 0
                print(f"Vehicle moved to {self.position}")
    
    def _should_stop_at_red(self):
        """Determine if this vehicle should stop at a red light based on its route."""
        # North-South gets a green light when light_state is "green"
        # East-West gets a green light when light_state is "red"
        if self.position == "intersection":
            if self.start_position in ["north", "south"] and self.destination in ["north", "south"]:
                return True  # Stop at red when going north-south
            elif self.start_position in ["east", "west"] and self.destination in ["east", "west"]:
                return False  # East-west can go on red (for them it's green)
            else:
                # Turning traffic
                if self.start_position in ["north", "south"]:
                    return True  # Turning from north/south stops on red
                else:
                    return False  # Turning from east/west can go on red
        return False

    def at_intersection(self):
        """Check if vehicle is at the intersection."""
        return self.position == "intersection"

    def move_one_step(self):
        """Move vehicle one step toward destination."""
        current_position_index = self.route.index(self.position)
        
        # If not at the end of the route
        if current_position_index < len(self.route) - 1:
            # Move to the next position in the route
            self.position = self.route[current_position_index + 1] 