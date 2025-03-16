import random
import pygame
import numpy as np
import torch
from src.config import WIDTH, HEIGHT, BUILDING_COLORS, DEBUG_MODE, SLOW_MODE, EPISODE_LENGTH, WHITE, BLACK, LANES, SPEED_SLIDER, TRAINING_SLIDER, MAX_VEHICLES_PER_LANE, ROAD_WIDTH
from src.visualization import draw_buildings, draw_road, draw_traffic_lights, draw_vehicle, draw_debug_info
from src.vehicle_spawner import generate_vehicle_spawn_schedule, spawn_vehicles
from src.collision import check_collision, get_vehicle_position
from src.shared import get_screen, get_clock
from src.rl_agent import TrafficRLAgent
from src.agent import Vehicle

# Check if CUDA is available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

"""
Traffic Simulation with Reinforcement Learning

Key Components:
- set_traffic_lights: RL agent decides light states here
- update_vehicles: Handles vehicle movement and state changes
- handle_events: Processes user input and simulation controls
- tutorial_mode: Educational mode with step-by-step explanations
"""

class Simulation:
    def __init__(self):
        # Initialize buildings
        self.buildings = []
        # Tutorial mode settings
        self.tutorial_mode = False
        self.tutorial_step = 0
        self.tutorial_messages = [
            "Vehicles spawn and move toward the intersection.",
            "RL agent observes waiting vehicles and picks a light state.",
            "Reward reflects commute time and satisfaction—watch it evolve!"
        ]
        # Manual control mode
        self.manual_mode = False
        # Traffic generation mode
        self.traffic_mode = "Random"  # Default mode
        # Current simulation mode
        self.simulation_mode = "RL"  # Default mode
        
        # Generate buildings in each quadrant
        self._generate_buildings()
        
        # Initialize traffic counts
        self.traffic_counts = {
            'north': 0,
            'south': 0,
            'east': 0,
            'west': 0
        }
        
        # Initialize simulation state
        self.reset()
        self.episode_ended = False
        self.current_fps = SPEED_SLIDER['default_fps']
        self.current_training_steps = TRAINING_SLIDER['default_steps']
        self.slider_dragging = False
        self.training_slider_dragging = False
        
        # Initialize RL agent
        self.rl_agent = TrafficRLAgent(self)
        self.training_in_progress = False
        
        # Initialize tensors for GPU acceleration
        self.vehicle_positions = torch.zeros((MAX_VEHICLES_PER_LANE * 4, 2), device=DEVICE)  # For all possible vehicles
        self.vehicle_states = torch.zeros((MAX_VEHICLES_PER_LANE * 4, 4), device=DEVICE)  # [waiting, moving, arrived, satisfaction]
        self.light_states = torch.zeros(2, device=DEVICE)  # [ns_light, ew_light]
        
        # Add metrics tracking
        self.last_arrived_count = 0
        self.last_flow_update = 0
        self.total_lanes = 4  # 2 lanes in each direction
        
        self.vehicles = []
        self.current_tick = 0
        self.ns_light = "red"
        self.ew_light = "green"
        self.light_timer = 0
        self.light_duration = 100
        self.spawn_probability = 0.1
        self.max_vehicles = MAX_VEHICLES_PER_LANE * 4
    
    def _generate_buildings(self):
        """Helper method to generate buildings in all four quadrants"""
        # Define quadrant boundaries
        quadrants = [
            # (x_min, x_max, y_min, y_max)
            (50, WIDTH//2 - 100//2 - 80, 50, HEIGHT//2 - 100//2 - 80),  # Northwest
            (WIDTH//2 + 100//2 + 30, WIDTH - 100, 50, HEIGHT//2 - 100//2 - 80),  # Northeast
            (50, WIDTH//2 - 100//2 - 80, HEIGHT//2 + 100//2 + 30, HEIGHT - 100),  # Southwest
            (WIDTH//2 + 100//2 + 30, WIDTH - 100, HEIGHT//2 + 100//2 + 30, HEIGHT - 100)  # Southeast
        ]
        
        # Generate buildings for each quadrant
        for x_min, x_max, y_min, y_max in quadrants:
            for _ in range(5):
                x = random.randint(x_min, x_max)
                y = random.randint(y_min, y_max)
                width = random.randint(40, 100)
                height = random.randint(40, 100)
                color = random.choice(BUILDING_COLORS)
                self.buildings.append((x, y, width, height, color))
    
    def reset(self):
        """Reset the simulation to its initial state"""
        self.active_vehicles = []
        self.removed_vehicles = []
        self.spawn_schedule = generate_vehicle_spawn_schedule()
        self.ns_light = "red"
        self.ew_light = "green"
        self.light_timer = 0
        self.light_duration = 100
        self.current_tick = 0
        self.running = True
        self.episode_ended = False
        self.light_change_count = 0  # Track number of light changes per episode
    
    def set_data_recorder(self, data_recorder):
        """Set the data recorder for the simulation"""
        self.data_recorder = data_recorder
        data_recorder.set_simulation(self)  # Set the simulation reference
    
    def get_avg_commute_time(self):
        """Get average commute time of completed vehicles"""
        if not self.removed_vehicles:
            return 0
        return sum(v.commute_time for v in self.removed_vehicles) / len(self.removed_vehicles)
    
    def get_avg_satisfaction(self):
        """Get average satisfaction of all vehicles"""
        all_vehicles = self.active_vehicles + self.removed_vehicles
        if not all_vehicles:
            return 0
        return sum(v.satisfaction for v in all_vehicles) / len(all_vehicles)
    
    def get_waiting_vehicles(self):
        """Get number of waiting vehicles per direction"""
        waiting = {'north': 0, 'south': 0, 'east': 0, 'west': 0}
        for vehicle in self.active_vehicles:
            if vehicle.state == "waiting" and vehicle.position in waiting:
                waiting[vehicle.position] += 1
        return waiting
    
    def update_traffic_lights(self):
        """Update traffic light states with yellow transitions"""
        # Update NS light
        if self.ns_light == "yellow":
            self.light_timer -= 1
            if self.light_timer <= 0:
                self.ns_light = "red"
                self.light_timer = 0
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_light_change()
        
        # Update EW light
        if self.ew_light == "yellow":
            self.light_timer -= 1
            if self.light_timer <= 0:
                self.ew_light = "red"
                self.light_timer = 0
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_light_change()
    
    def set_traffic_lights(self, action):
        """Set traffic lights based on action with yellow transitions"""
        # Only change lights if they're not in yellow transition
        if self.ns_light == "yellow" or self.ew_light == "yellow":
            return
            
        if action == 0:  # NS green
            if self.ns_light != "green":
                # Start yellow transition for current green light
                if self.ew_light == "green":
                    self.ew_light = "yellow"
                    self.light_timer = 3  # 3 ticks of yellow
                # Set NS to green after yellow transition
                self.ns_light = "green"
                self.light_timer = 0
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_light_change()
        
        elif action == 1:  # EW green
            if self.ew_light != "green":
                # Start yellow transition for current green light
                if self.ns_light == "green":
                    self.ns_light = "yellow"
                    self.light_timer = 3  # 3 ticks of yellow
                # Set EW to green after yellow transition
                self.ew_light = "green"
                self.light_timer = 0
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_light_change()
    
    def handle_events(self):
        """Handle user input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_d:
                    global DEBUG_MODE
                    DEBUG_MODE = not DEBUG_MODE
                elif event.key == pygame.K_s:
                    global SLOW_MODE
                    SLOW_MODE = not SLOW_MODE
                elif event.key == pygame.K_e:
                    if not self.episode_ended:
                        self.episode_ended = True
                        if hasattr(self, 'data_recorder'):
                            self.data_recorder.end_episode(self.light_change_count)
                elif event.key == pygame.K_n:
                    if self.episode_ended:
                        self.reset()
                elif event.key == pygame.K_c and self.tutorial_mode:
                    self.tutorial_step += 1
                elif self.manual_mode:
                    if event.key == pygame.K_SPACE:
                        # Only change lights if they're not in yellow transition
                        if self.ns_light != "yellow" and self.ew_light != "yellow":
                            # Start yellow transition for current green light
                            if self.ns_light == "green":
                                self.ns_light = "yellow"
                                self.light_timer = 3
                            elif self.ew_light == "green":
                                self.ew_light = "yellow"
                                self.light_timer = 3
                            # Set the other light to green
                            if self.ns_light == "yellow":
                                self.ew_light = "green"
                            else:
                                self.ns_light = "green"
                            if hasattr(self, 'data_recorder'):
                                self.data_recorder.record_light_change()
    
    def update_vehicles(self):
        """Update the state of all vehicles in the simulation"""
        # Update light state
        light_state = (self.ns_light, self.ew_light)
        
        # List to store vehicles to remove
        vehicles_to_remove = []
        
        # Update each vehicle
        for vehicle in self.active_vehicles:
            # Get current position index in route
            try:
                current_idx = vehicle.route.index(vehicle.position)
                
                # Get current and next positions for interpolation
                current_pos = vehicle.position
                next_pos = None if current_idx >= len(vehicle.route) - 1 else vehicle.route[current_idx + 1]
                
                # Convert string positions to coordinates
                current_coords = current_pos
                if isinstance(current_pos, str):
                    if current_pos == 'north':
                        current_coords = (WIDTH//2, 0)
                    elif current_pos == 'south':
                        current_coords = (WIDTH//2, HEIGHT)
                    elif current_pos == 'east':
                        current_coords = (WIDTH, HEIGHT//2)
                    elif current_pos == 'west':
                        current_coords = (0, HEIGHT//2)
                    elif current_pos == 'intersection':
                        # Use the previous position to determine intersection entry point
                        if current_idx > 0 and isinstance(vehicle.route[current_idx - 1], tuple):
                            current_coords = vehicle.route[current_idx - 1]
                        else:
                            current_coords = (WIDTH//2, HEIGHT//2)
                
                next_coords = next_pos
                if isinstance(next_pos, str):
                    if next_pos == 'north':
                        next_coords = (WIDTH//2, 0)
                    elif next_pos == 'south':
                        next_coords = (WIDTH//2, HEIGHT)
                    elif next_pos == 'east':
                        next_coords = (WIDTH, HEIGHT//2)
                    elif next_pos == 'west':
                        next_coords = (0, HEIGHT//2)
                    elif next_pos == 'intersection':
                        # Use the next waypoint after intersection to determine direction
                        if current_idx + 2 < len(vehicle.route):
                            next_coords = vehicle.route[current_idx + 2]
                        else:
                            next_coords = current_coords
                
                # Check if vehicle has reached the edge of the map
                if isinstance(current_coords, tuple):
                    x, y = current_coords
                    # Only remove if we've reached the destination and are at the edge
                    if vehicle.position == vehicle.destination and vehicle.is_at_edge():
                        vehicles_to_remove.append(vehicle)
                        continue
                
                # Check for collisions with other vehicles
                should_stop = check_collision(vehicle, self.active_vehicles, light_state)
                
                # Update vehicle state if no collision
                if not should_stop and isinstance(current_coords, tuple) and isinstance(next_coords, tuple):
                    # Calculate interpolated position
                    vehicle.position_time += 1
                    progress = min(vehicle.position_time / vehicle.position_threshold, 1.0)
                    
                    # Linear interpolation between current and next position
                    interpolated_x = current_coords[0] + (next_coords[0] - current_coords[0]) * progress
                    interpolated_y = current_coords[1] + (next_coords[1] - current_coords[1]) * progress
                    
                    # Store interpolated position for drawing
                    vehicle.interpolated_position = (interpolated_x, interpolated_y)
                    vehicle.state = "moving"
                    
                    # Move to next position when threshold is reached
                    if vehicle.position_time >= vehicle.position_threshold:
                        vehicle.position = next_pos
                        vehicle.position_time = 0
                        
                        # If we're exiting the intersection, ensure we maintain position
                        if vehicle.position in ['north', 'south', 'east', 'west']:
                            vehicle.interpolated_position = LANES[vehicle.position]['out']
                            vehicle.state = "moving"  # Keep moving state for proper award calculation
                        else:
                            vehicle.interpolated_position = None
                elif should_stop:
                    vehicle.state = "waiting"
                    # Maintain the current position when stopped
                    if isinstance(current_coords, tuple):
                        vehicle.interpolated_position = current_coords
                    # Reset position time to ensure we stay in place
                    vehicle.position_time = 0
            
            except (ValueError, IndexError) as e:
                # If there's an error with the route, remove the vehicle
                vehicles_to_remove.append(vehicle)
                continue
        
        # Remove vehicles that have reached the edge
        for vehicle in vehicles_to_remove:
            if vehicle in self.active_vehicles:
                self.active_vehicles.remove(vehicle)
        
        # Spawn new vehicles only at edges
        if len(self.active_vehicles) < MAX_VEHICLES_PER_LANE * 4 and random.random() < 0.1:
            spawn_edge = random.choice(['north', 'south', 'east', 'west'])
            possible_destinations = ['north', 'south', 'east', 'west']
            possible_destinations.remove(spawn_edge)
            destination = random.choice(possible_destinations)
            route = self.create_route(spawn_edge, destination)
            
            if route:
                vehicle = Vehicle(
                    route=route,
                    position=spawn_edge,
                    vehicle_type=random.choice(["car", "van", "truck"]),
                    position_threshold=40
                )
                vehicle.destination = destination  # Add the destination attribute
                vehicle.interpolated_position = None
                self.active_vehicles.append(vehicle)
                print(f"Spawned vehicle from {spawn_edge} to {destination} at tick {self.current_tick}")
    
    def draw(self, data_recorder):
        """Draw the current simulation state"""
        screen = get_screen()
        screen.fill(WHITE)
        
        # Draw buildings
        draw_buildings(self.buildings)
        
        # Draw road and traffic lights
        draw_road()
        draw_traffic_lights(self.ns_light, self.ew_light)
        
        # Draw vehicles
        for vehicle in self.active_vehicles:
            draw_vehicle(vehicle, DEBUG_MODE)
        
        # Draw debug info if debug mode is enabled
        if DEBUG_MODE:
            # Calculate lane occupancy
            lane_counts = {}
            for vehicle in self.active_vehicles:
                if vehicle.position in ['north', 'south', 'east', 'west']:
                    lane_counts[vehicle.position] = lane_counts.get(vehicle.position, 0) + 1
            
            draw_debug_info(self.ns_light, self.ew_light, self.active_vehicles, 
                          self.spawn_schedule, self.current_tick, EPISODE_LENGTH, lane_counts)
        
        # Force display update
        pygame.display.flip()
    
    def update_simulation(self):
        """Update the simulation for one step without drawing (used by RL)"""
        if not self.episode_ended:
            # Update simulation state
            self.update_traffic_lights()
            
            # Only spawn new vehicles if not in test mode
            if not hasattr(self, 'test_mode') or not self.test_mode:
                # Spawn new vehicles if needed
                spawn_vehicles(self.current_tick, self.spawn_schedule, self.active_vehicles, self)
            
            # Update vehicles
            self.update_vehicles()
            
            # Record data if data recorder exists
            if hasattr(self, 'data_recorder'):
                waiting_count = sum(1 for v in self.active_vehicles if v.state == "waiting")
                moving_count = sum(1 for v in self.active_vehicles if v.state == "moving")
                arrived_count = len(self.removed_vehicles)
                avg_satisfaction = self.get_avg_satisfaction()
                
                self.data_recorder.record_tick(
                    self.current_tick,
                    f"NS:{self.ns_light},EW:{self.ew_light}",
                    waiting_count,
                    moving_count,
                    arrived_count,
                    avg_satisfaction
                )
            
            # Increment tick counter
            self.current_tick += 1
            
            # Check if episode should end
            if self.current_tick >= EPISODE_LENGTH or (not self.active_vehicles and not self.spawn_schedule):
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.end_episode(self.light_change_count)
                self.episode_ended = True
                print("Episode ended automatically")
    
    def get_observation(self):
        """Get the current observation state for the RL agent using GPU acceleration"""
        # Update vehicle states tensor
        for i, vehicle in enumerate(self.active_vehicles):
            if i >= MAX_VEHICLES_PER_LANE * 4:
                break
            self.vehicle_states[i] = torch.tensor([
                1.0 if vehicle.state == "waiting" else 0.0,
                1.0 if vehicle.state == "moving" else 0.0,
                1.0 if vehicle.state == "arrived" else 0.0,
                vehicle.satisfaction
            ], device=DEVICE)
        
        # Calculate waiting vehicles per direction using GPU
        waiting = torch.zeros(4, device=DEVICE)  # [north, south, east, west]
        for i, vehicle in enumerate(self.active_vehicles):
            if i >= MAX_VEHICLES_PER_LANE * 4:
                break
            if vehicle.state == "waiting":
                if vehicle.position == "north":
                    waiting[0] += 1
                elif vehicle.position == "south":
                    waiting[1] += 1
                elif vehicle.position == "east":
                    waiting[2] += 1
                elif vehicle.position == "west":
                    waiting[3] += 1
        
        # Convert to numpy for RL agent
        observation = waiting.cpu().numpy().astype(np.int32)
        return observation
    
    def step(self, data_recorder):
        """Update the simulation state with GPU acceleration"""
        # Handle events
        self.handle_events()
        
        # Update traffic lights based on mode
        if self.simulation_mode == "RL":
            try:
                # Get observation and action from RL agent
                observation = self.get_observation()
                action = self.rl_agent.predict(observation)
                self.set_traffic_lights(action)
            except Exception as e:
                print(f"Error in RL mode: {str(e)}")
                # Fallback to alternating pattern if RL fails
                if self.current_tick % 100 < 50:
                    self.set_traffic_lights(0)  # NS green
                else:
                    self.set_traffic_lights(1)  # EW green
        elif self.manual_mode:
            # Manual control is handled in handle_events
            pass
        else:  # Tutorial mode
            # Tutorial mode uses simple alternating pattern
            if self.current_tick % 100 < 50:
                self.set_traffic_lights(0)  # NS green
            else:
                self.set_traffic_lights(1)  # EW green
        
        # Update traffic light states
        self.update_traffic_lights()
        
        # Spawn new vehicles if needed
        spawn_vehicles(self.current_tick, self.spawn_schedule, self.active_vehicles, self)
        
        # Update vehicles with GPU acceleration
        self.update_vehicles()
        
        # Update current tick
        self.current_tick += 1
        
        # Record data for visualization
        waiting_count = sum(1 for v in self.active_vehicles if v.state == "waiting")
        moving_count = sum(1 for v in self.active_vehicles if v.state == "moving")
        arrived_count = len(self.removed_vehicles)
        avg_satisfaction = self.get_avg_satisfaction()
        
        if hasattr(self, 'data_recorder'):
            data_recorder.record_tick(self.current_tick, f"NS:{self.ns_light},EW:{self.ew_light}", 
                                    waiting_count, moving_count, arrived_count, avg_satisfaction)
        
        # Draw everything
        self.draw(data_recorder)
        
        # Control simulation speed using the fps value
        clock = get_clock()
        if SLOW_MODE:
            clock.tick(5)  # Even slower for debugging
        else:
            clock.tick(20)  # Reduced default speed
    
    def set_traffic_mode(self, mode):
        """Set the traffic generation mode"""
        self.traffic_mode = mode
        # Reset traffic counts when mode changes
        self.traffic_counts = {direction: 0 for direction in self.traffic_counts}
        
    def get_traffic_counts(self):
        """Get current traffic counts by direction"""
        # Initialize counts
        counts = {
            'north': 0,
            'south': 0,
            'east': 0,
            'west': 0
        }
        
        # Count vehicles in each direction
        for vehicle in self.active_vehicles:
            if vehicle.position in counts:
                counts[vehicle.position] += 1
        
        # Update traffic counts
        self.traffic_counts = counts
        return self.traffic_counts
    
    def set_mode(self, mode):
        """Set the simulation mode (RL, Manual, or Tutorial)"""
        self.simulation_mode = mode
        self.tutorial_mode = (mode == "Tutorial")
        self.manual_mode = (mode == "Manual")
        
        # Reset tutorial step when entering tutorial mode
        if self.tutorial_mode:
            self.tutorial_step = 0
            
    def draw_tutorial_message(self):
        """Draw the current tutorial message"""
        if self.tutorial_step < len(self.tutorial_messages):
            message = self.tutorial_messages[self.tutorial_step]
            font = pygame.font.Font(None, 36)
            text = font.render(message, True, WHITE)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT - 50))
            get_screen().blit(text, text_rect)
            
            # Draw instruction
            instruction = "Press SPACE to continue"
            instruction_font = pygame.font.Font(None, 24)
            instruction_text = instruction_font.render(instruction, True, WHITE)
            instruction_rect = instruction_text.get_rect(center=(WIDTH//2, HEIGHT - 20))
            get_screen().blit(instruction_text, instruction_rect)
    
    def get_avg_wait_time(self):
        """Calculate average wait time for vehicles at intersections"""
        if not self.active_vehicles:
            return 0
        wait_times = [v.wait_time for v in self.active_vehicles if v.state == "waiting"]
        return sum(wait_times) / len(wait_times) if wait_times else 0
    
    def get_traffic_flow(self):
        """Calculate traffic flow rate (vehicles per minute)"""
        current_tick = self.current_tick
        if current_tick - self.last_flow_update >= 60:  # Update every minute
            arrived_diff = len(self.removed_vehicles) - self.last_arrived_count
            flow_rate = (arrived_diff * 60) / (current_tick - self.last_flow_update)
            self.last_arrived_count = len(self.removed_vehicles)
            self.last_flow_update = current_tick
            return flow_rate
        return 0
    
    def get_queue_length(self):
        """Calculate current queue length at intersections"""
        return sum(1 for v in self.active_vehicles if v.state == "waiting")
    
    def get_vehicle_density(self):
        """Calculate vehicle density (vehicles per lane)"""
        return len(self.active_vehicles) / self.total_lanes
    
    def get_avg_speed(self):
        """Calculate average vehicle speed"""
        if not self.active_vehicles:
            return 0
        speeds = [v.speed for v in self.active_vehicles if v.state == "moving"]
        return sum(speeds) / len(speeds) if speeds else 0
    
    def get_stops_per_vehicle(self):
        """Calculate average number of stops per vehicle"""
        if not self.active_vehicles:
            return 0
        total_stops = sum(v.stop_count for v in self.active_vehicles)
        return total_stops / len(self.active_vehicles)
    
    def get_fuel_efficiency(self):
        """Calculate fuel efficiency based on acceleration/deceleration patterns"""
        if not self.active_vehicles:
            return 0
        efficiency_scores = []
        for v in self.active_vehicles:
            if v.state == "moving":
                # Penalize frequent acceleration/deceleration
                smoothness = 1.0 - (v.acceleration_changes / max(1, v.total_ticks))
                efficiency_scores.append(smoothness * 100)
        return sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0
    
    def get_metrics(self):
        """Get all metrics in a dictionary format"""
        return {
            'avg_wait_time': self.get_avg_wait_time(),
            'traffic_flow': self.get_traffic_flow(),
            'queue_length': self.get_queue_length(),
            'vehicle_density': self.get_vehicle_density(),
            'avg_speed': self.get_avg_speed(),
            'stops_per_vehicle': self.get_stops_per_vehicle(),
            'fuel_efficiency': self.get_fuel_efficiency()
        }
    
    def create_route(self, start, end):
        """Create a route from start edge to end edge"""
        route = []
        
        # Starting position
        if start == 'north':
            route.extend([start, (WIDTH//2, 50), (WIDTH//2, 100)])
        elif start == 'south':
            route.extend([start, (WIDTH//2, HEIGHT-50), (WIDTH//2, HEIGHT-100)])
        elif start == 'east':
            route.extend([start, (WIDTH-50, HEIGHT//2), (WIDTH-100, HEIGHT//2)])
        elif start == 'west':
            route.extend([start, (50, HEIGHT//2), (100, HEIGHT//2)])
        
        # Add intersection approach
        if start == 'north':
            route.extend([(WIDTH//2, HEIGHT//2 - 100), (WIDTH//2, HEIGHT//2 - 50)])
        elif start == 'south':
            route.extend([(WIDTH//2, HEIGHT//2 + 100), (WIDTH//2, HEIGHT//2 + 50)])
        elif start == 'east':
            route.extend([(WIDTH//2 + 100, HEIGHT//2), (WIDTH//2 + 50, HEIGHT//2)])
        elif start == 'west':
            route.extend([(WIDTH//2 - 100, HEIGHT//2), (WIDTH//2 - 50, HEIGHT//2)])
        
        # Add intersection waypoint
        route.append('intersection')
        
        # Add intersection exit based on turn type
        if (start == 'north' and end == 'west') or (start == 'east' and end == 'south'):
            route.extend([
                (WIDTH//2 - 25, HEIGHT//2 - 25),
                (WIDTH//2 - 50, HEIGHT//2),
                (WIDTH//2 - 100, HEIGHT//2)  # Additional point past intersection
            ])
        elif (start == 'north' and end == 'east') or (start == 'west' and end == 'south'):
            route.extend([
                (WIDTH//2 + 25, HEIGHT//2 - 25),
                (WIDTH//2 + 50, HEIGHT//2),
                (WIDTH//2 + 100, HEIGHT//2)  # Additional point past intersection
            ])
        elif (start == 'south' and end == 'west') or (start == 'east' and end == 'north'):
            route.extend([
                (WIDTH//2 - 25, HEIGHT//2 + 25),
                (WIDTH//2 - 50, HEIGHT//2),
                (WIDTH//2 - 100, HEIGHT//2)  # Additional point past intersection
            ])
        elif (start == 'south' and end == 'east') or (start == 'west' and end == 'north'):
            route.extend([
                (WIDTH//2 + 25, HEIGHT//2 + 25),
                (WIDTH//2 + 50, HEIGHT//2),
                (WIDTH//2 + 100, HEIGHT//2)  # Additional point past intersection
            ])
        elif start == 'north' and end == 'south':
            route.extend([
                (WIDTH//2, HEIGHT//2),
                (WIDTH//2, HEIGHT//2 + 50),
                (WIDTH//2, HEIGHT//2 + 100)  # Additional point past intersection
            ])
        elif start == 'south' and end == 'north':
            route.extend([
                (WIDTH//2, HEIGHT//2),
                (WIDTH//2, HEIGHT//2 - 50),
                (WIDTH//2, HEIGHT//2 - 100)  # Additional point past intersection
            ])
        elif start == 'east' and end == 'west':
            route.extend([
                (WIDTH//2, HEIGHT//2),
                (WIDTH//2 - 50, HEIGHT//2),
                (WIDTH//2 - 100, HEIGHT//2)  # Additional point past intersection
            ])
        elif start == 'west' and end == 'east':
            route.extend([
                (WIDTH//2, HEIGHT//2),
                (WIDTH//2 + 50, HEIGHT//2),
                (WIDTH//2 + 100, HEIGHT//2)  # Additional point past intersection
            ])
        
        # Add exit path
        if end == 'north':
            route.extend([(WIDTH//2, 100), (WIDTH//2, 50), end])
        elif end == 'south':
            route.extend([(WIDTH//2, HEIGHT-100), (WIDTH//2, HEIGHT-50), end])
        elif end == 'east':
            route.extend([(WIDTH-100, HEIGHT//2), (WIDTH-50, HEIGHT//2), end])
        elif end == 'west':
            route.extend([(100, HEIGHT//2), (50, HEIGHT//2), end])
        
        return route

    def create_test_vehicle(self):
        """Create a single test vehicle moving from east to west"""
        # Set test mode flag
        self.test_mode = True
        
        # Clear any existing vehicles
        self.active_vehicles = []
        self.removed_vehicles = []
        
        # Create a route from east to west
        route = self.create_route('east', 'west')
        
        # Create the test vehicle
        test_vehicle = Vehicle(
            route=route,
            position='east',
            vehicle_type="car",
            position_threshold=40
        )
        test_vehicle.destination = 'west'
        test_vehicle.interpolated_position = None
        test_vehicle.id = "TEST_VEHICLE"  # Special ID for tracking
        
        # Add vehicle to simulation
        self.active_vehicles.append(test_vehicle)
        print("\n=== Test Vehicle Created ===")
        print(f"Starting Position: east")
        print(f"Destination: west")
        print(f"Route: {route}")
        print("=========================\n")
        
        return test_vehicle

    def run_test_mode(self):
        """Run simulation in test mode with a single vehicle"""
        # Create test vehicle
        test_vehicle = self.create_test_vehicle()
        
        # Set initial light states
        self.ns_light = "red"
        self.ew_light = "green"
        
        while self.running and test_vehicle in self.active_vehicles:
            # Handle events
            self.handle_events()
            
            # Update traffic lights
            self.update_traffic_lights()
            
            # Update vehicles
            self.update_vehicles()
            
            # Print vehicle state
            print(f"\nTick {self.current_tick}:")
            print(f"Position: {test_vehicle.position}")
            print(f"State: {test_vehicle.state}")
            if hasattr(test_vehicle, 'interpolated_position'):
                print(f"Interpolated Position: {test_vehicle.interpolated_position}")
            print(f"Traffic Lights - NS: {self.ns_light}, EW: {self.ew_light}")
            
            # Draw everything
            self.draw(None)
            
            # Control simulation speed
            clock = get_clock()
            clock.tick(5)  # Slow speed for observation
            
            # Increment tick
            self.current_tick += 1 