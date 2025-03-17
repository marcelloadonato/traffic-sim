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
        try:
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
            
            # Add log counter for debug output
            self.log_counter = 0
            
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
            try:
                self.rl_agent = TrafficRLAgent(self)
                self.training_in_progress = False
            except Exception as e:
                print(f"Warning: Failed to initialize RL agent: {e}")
                self.rl_agent = None
                self.training_in_progress = False
            
            # Initialize tensors for GPU acceleration
            try:
                self.vehicle_positions = torch.zeros((MAX_VEHICLES_PER_LANE * 4, 2), device=DEVICE)
                self.vehicle_states = torch.zeros((MAX_VEHICLES_PER_LANE * 4, 4), device=DEVICE)
                self.light_states = torch.zeros(2, device=DEVICE)
            except Exception as e:
                print(f"Warning: Failed to initialize tensors: {e}")
                self.vehicle_positions = None
                self.vehicle_states = None
                self.light_states = None
            
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
            
        except Exception as e:
            print(f"Error initializing Simulation: {e}")
            raise
    
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
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return
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
        except pygame.error as e:
            if "display Surface quit" in str(e):
                self.running = False
                return
            else:
                raise
    
    def get_light_state(self):
        """Get the current state of the traffic lights"""
        return (self.ns_light, self.ew_light)
    
    def update_vehicles(self):
        """Update the state of all vehicles in the simulation"""
        vehicles_to_remove = []
        light_state = self.get_light_state()
        
        for vehicle in self.active_vehicles:
            try:
                # Get current position index in route
                current_idx = vehicle.route.index(vehicle.position)
                if current_idx >= len(vehicle.route) - 1:
                    continue
                
                # Get next position
                next_pos = vehicle.route[current_idx + 1]
                
                # Get current and next coordinates
                current_coords = vehicle.get_current_coords()
                next_coords = vehicle.get_next_coords(next_pos)
                
                if not current_coords or not next_coords:
                    continue
                
                # Skip all checks if vehicle is in intersection
                if vehicle.position == 'intersection':
                    vehicle.state = "moving"
                    vehicle.waiting_time = 0
                    vehicle.speed = vehicle.base_speed
                    
                    # Use a smaller threshold in the intersection for faster movement
                    intersection_threshold = 50  # Half the normal threshold
                    
                    # Update position time
                    vehicle.position_time += vehicle.speed
                    
                    # Calculate progress
                    progress = min(vehicle.position_time / intersection_threshold, 1.0)
                    
                    # Calculate new interpolated position
                    new_x = current_coords[0] + (next_coords[0] - current_coords[0]) * progress
                    new_y = current_coords[1] + (next_coords[1] - current_coords[1]) * progress
                    
                    # Store new interpolated position
                    vehicle.interpolated_position = (new_x, new_y)
                    
                    # Move to next position when threshold is reached
                    if progress >= 1.0:
                        vehicle.position = next_pos
                        vehicle.position_time = 0
                        
                        # Check for arrival at destination
                        if vehicle.position == vehicle.destination and vehicle.is_at_edge():
                            vehicle.state = "arrived"
                            vehicles_to_remove.append(vehicle)
                    continue
                
                # Check if we need to stop
                should_stop = False
                
                # Stop at red light if approaching intersection
                if vehicle.position in ['north', 'south', 'east', 'west'] and next_pos == 'intersection':
                    ns_light, ew_light = light_state
                    if ((vehicle.position in ['north', 'south'] and ns_light == "red") or
                        (vehicle.position in ['east', 'west'] and ew_light == "red")):
                        # Only stop for red lights, not yellow
                        should_stop = True
                        vehicle.state = "waiting"
                        vehicle.waiting_time += 1
                        vehicle.speed = 0
                        continue
                
                # Check for vehicles ahead
                if not should_stop:
                    for other_vehicle in self.active_vehicles:
                        if other_vehicle != vehicle and other_vehicle.state != "arrived":
                            # Skip collision check if other vehicle is in intersection
                            if other_vehicle.position == 'intersection':
                                continue
                            if vehicle.is_behind(other_vehicle):
                                # Only stop if very close to the vehicle ahead
                                dx = vehicle.interpolated_position[0] - other_vehicle.interpolated_position[0]
                                dy = vehicle.interpolated_position[1] - other_vehicle.interpolated_position[1]
                                distance = (dx * dx + dy * dy) ** 0.5
                                if distance < 50:  # Reduced from 80
                                    should_stop = True
                                    vehicle.state = "waiting"
                                    vehicle.waiting_time += 1
                                    vehicle.speed = 0
                                    break
                
                # Update position if not stopped
                if not should_stop:
                    vehicle.state = "moving"
                    vehicle.waiting_time = 0
                    vehicle.speed = vehicle.base_speed
                    
                    # Update position time
                    vehicle.position_time += vehicle.speed
                    
                    # Calculate progress
                    progress = min(vehicle.position_time / vehicle.position_threshold, 1.0)
                    
                    # Calculate new interpolated position
                    new_x = current_coords[0] + (next_coords[0] - current_coords[0]) * progress
                    new_y = current_coords[1] + (next_coords[1] - current_coords[1]) * progress
                    
                    # Store new interpolated position
                    vehicle.interpolated_position = (new_x, new_y)
                    
                    # Move to next position when threshold is reached
                    if progress >= 1.0:
                        vehicle.position = next_pos
                        vehicle.position_time = 0
                        
                        # Check for arrival at destination
                        if vehicle.position == vehicle.destination and vehicle.is_at_edge():
                            vehicle.state = "arrived"
                            vehicles_to_remove.append(vehicle)
            
            except Exception as e:
                print(f"Error updating vehicle {id(vehicle) % 1000}: {str(e)}")
                vehicles_to_remove.append(vehicle)
                continue
        
        # Remove completed vehicles
        for vehicle in vehicles_to_remove:
            if vehicle in self.active_vehicles:
                self.active_vehicles.remove(vehicle)
                self.removed_vehicles.append(vehicle)
        
        # Only spawn random vehicles if not in test mode
        if not hasattr(self, 'test_mode') or not self.test_mode:
            if len(self.active_vehicles) < MAX_VEHICLES_PER_LANE * 4 and random.random() < 0.1:
                spawn_edge = random.choice(['north', 'south', 'east', 'west'])
                possible_destinations = ['north', 'south', 'east', 'west']
                possible_destinations.remove(spawn_edge)
                destination = random.choice(possible_destinations)
                route = self.create_route(spawn_edge, destination)
                
                if route:
                    # Create new vehicle with improved settings
                    vehicle = Vehicle(
                        route=route,
                        position=spawn_edge,
                        vehicle_type=random.choice(["car", "van", "truck"]),
                        position_threshold=100  # Consistent threshold for smooth movement
                    )
                    vehicle.destination = destination
                    
                    # Set initial interpolated position based on spawn edge
                    if spawn_edge == 'east':
                        vehicle.interpolated_position = (WIDTH, HEIGHT//2)
                    elif spawn_edge == 'west':
                        vehicle.interpolated_position = (0, HEIGHT//2)
                    elif spawn_edge == 'north':
                        vehicle.interpolated_position = (WIDTH//2, 0)
                    elif spawn_edge == 'south':
                        vehicle.interpolated_position = (WIDTH//2, HEIGHT)
                    
                    # Set appropriate speeds for vehicle type
                    if vehicle.vehicle_type == "truck":
                        vehicle.base_speed = 2
                        vehicle.speed = 2
                    elif vehicle.vehicle_type == "van":
                        vehicle.base_speed = 3
                        vehicle.speed = 3
                    else:  # car
                        vehicle.base_speed = 4
                        vehicle.speed = 4
                    
                    # Initialize movement state
                    vehicle.state = "moving"
                    vehicle.position_time = 0
                    
                    self.active_vehicles.append(vehicle)
    
    def draw(self, data_recorder):
        """Draw the current simulation state"""
        try:
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
        except pygame.error as e:
            if "display Surface quit" in str(e):
                self.running = False
                return
            else:
                raise
    
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
        
        # Only spawn new vehicles if not in test mode
        if not hasattr(self, 'test_mode') or not self.test_mode:
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
        """Get traffic counts by direction"""
        north_count = sum(1 for v in self.active_vehicles if v.position == 'north')
        south_count = sum(1 for v in self.active_vehicles if v.position == 'south')
        east_count = sum(1 for v in self.active_vehicles if v.position == 'east')
        west_count = sum(1 for v in self.active_vehicles if v.position == 'west')
        
        return {
            'north': north_count,
            'south': south_count,
            'east': east_count,
            'west': west_count
        }
    
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
        """Calculate average wait time for vehicles"""
        if not self.active_vehicles:
            return 0
        
        # Calculate average time vehicles spend in "waiting" state
        wait_times = [v.wait_time for v in self.active_vehicles if hasattr(v, 'wait_time')]
        return sum(wait_times) / max(len(wait_times), 1)
    
    def get_traffic_flow(self):
        """Calculate traffic flow (vehicles per minute)"""
        # Use number of vehicles processed in the last minute
        ticks_per_minute = 60 * 60  # Assuming 60 FPS
        recent_ticks = min(self.current_tick, ticks_per_minute)
        
        if recent_ticks == 0:
            return 0
        
        # Count vehicles that were removed in the last minute
        recent_vehicles = len(self.removed_vehicles)
        
        # Convert to vehicles per minute
        return (recent_vehicles / recent_ticks) * ticks_per_minute
    
    def get_queue_length(self):
        """Calculate current queue length at intersections"""
        # Count vehicles in waiting state
        return sum(1 for v in self.active_vehicles if v.state == "waiting")
    
    def get_vehicle_density(self):
        """Calculate vehicle density (vehicles per lane)"""
        # Count total active vehicles divided by number of lanes
        num_lanes = 4  # North, South, East, West
        return len(self.active_vehicles) / num_lanes if num_lanes > 0 else 0
    
    def get_avg_speed(self):
        """Calculate average vehicle speed"""
        if not self.active_vehicles:
            return 0
        
        # Use position_threshold as a proxy for speed (lower = faster)
        speeds = [40 / max(v.position_threshold, 1) * 60 for v in self.active_vehicles]  # pixels per second
        return sum(speeds) / len(speeds)
    
    def get_stops_per_vehicle(self):
        """Calculate average number of stops per vehicle"""
        if not self.active_vehicles and not self.removed_vehicles:
            return 0
        
        # Use a placeholder calculation
        total_vehicles = len(self.active_vehicles) + len(self.removed_vehicles)
        waiting_vehicles = sum(1 for v in self.active_vehicles if v.state == "waiting")
        
        # Approximate stops per vehicle
        return waiting_vehicles / total_vehicles if total_vehicles > 0 else 0
    
    def get_fuel_efficiency(self):
        """Calculate fuel efficiency (higher is better)"""
        # Base efficiency starts at 100%
        base_efficiency = 100
        
        # Reduce efficiency for each vehicle that's waiting (stopped)
        waiting_penalty = 2  # % per waiting vehicle
        waiting_vehicles = sum(1 for v in self.active_vehicles if v.state == "waiting")
        
        # Calculate efficiency
        efficiency = max(0, base_efficiency - (waiting_vehicles * waiting_penalty))
        
        return efficiency
    
    def get_metrics(self):
        """Get metrics for the dashboard"""
        # Calculate metrics
        avg_wait_time = self.get_avg_wait_time()
        traffic_flow = self.get_traffic_flow()
        queue_length = self.get_queue_length()
        vehicle_density = self.get_vehicle_density()
        avg_speed = self.get_avg_speed()
        stops_per_vehicle = self.get_stops_per_vehicle()
        fuel_efficiency = self.get_fuel_efficiency()
        
        # Return as dictionary
        return {
            'avg_wait_time': avg_wait_time,
            'traffic_flow': traffic_flow,
            'queue_length': queue_length,
            'vehicle_density': vehicle_density,
            'avg_speed': avg_speed,
            'stops_per_vehicle': stops_per_vehicle,
            'fuel_efficiency': fuel_efficiency
        }
    
    def create_route(self, start, end):
        """Create a route from start edge to end edge with proper lane offsets"""
        route = []
        
        # Define lane offsets (positive = right side of road in direction of travel)
        LANE_OFFSET = 15  # pixels from center
        
        # Add starting position
        route.append(start)
        
        # Add intersection approach point
        if start == 'north':
            route.append((WIDTH//2 + LANE_OFFSET, HEIGHT//2 - 100))
        elif start == 'south':
            route.append((WIDTH//2 - LANE_OFFSET, HEIGHT//2 + 100))
        elif start == 'east':
            route.append((WIDTH//2 + 100, HEIGHT//2 - LANE_OFFSET))
        elif start == 'west':
            route.append((WIDTH//2 - 100, HEIGHT//2 + LANE_OFFSET))
        
        # Add intersection marker
        route.append('intersection')
        
        # Add intersection exit point
        if end == 'north':
            route.append((WIDTH//2 - LANE_OFFSET, HEIGHT//2 - 100))
        elif end == 'south':
            route.append((WIDTH//2 + LANE_OFFSET, HEIGHT//2 + 100))
        elif end == 'east':
            route.append((WIDTH//2 + 100, HEIGHT//2 + LANE_OFFSET))
        elif end == 'west':
            route.append((WIDTH//2 - 100, HEIGHT//2 - LANE_OFFSET))
        
        # Add destination
        route.append(end)
        
        return route

    def create_test_vehicles(self):
        """Create four test vehicles moving in opposite directions (east-west and north-south)"""
        # Create east-bound vehicle
        east_route = self.create_route('west', 'east')
        east_vehicle = Vehicle(
            route=east_route,
            position='west',
            vehicle_type="car",
            position_threshold=100
        )
        east_vehicle.destination = 'east'
        east_vehicle.interpolated_position = (0, HEIGHT//2 + 15)  # +15 for right lane
        east_vehicle.base_speed = 2
        east_vehicle.speed = 2
        east_vehicle.state = "moving"
        east_vehicle.position_time = 0
        
        # Create west-bound vehicle
        west_route = self.create_route('east', 'west')
        west_vehicle = Vehicle(
            route=west_route,
            position='east',
            vehicle_type="car",
            position_threshold=100
        )
        west_vehicle.destination = 'west'
        west_vehicle.interpolated_position = (WIDTH, HEIGHT//2 - 15)  # -15 for left lane
        west_vehicle.base_speed = 2
        west_vehicle.speed = 2
        west_vehicle.state = "moving"
        west_vehicle.position_time = 0
        
        # Create north-bound vehicle
        north_route = self.create_route('south', 'north')
        north_vehicle = Vehicle(
            route=north_route,
            position='south',
            vehicle_type="car",
            position_threshold=100
        )
        north_vehicle.destination = 'north'
        north_vehicle.interpolated_position = (WIDTH//2 + 15, HEIGHT)  # +15 for right lane
        north_vehicle.base_speed = 2
        north_vehicle.speed = 2
        north_vehicle.state = "moving"
        north_vehicle.position_time = 0
        
        # Create south-bound vehicle
        south_route = self.create_route('north', 'south')
        south_vehicle = Vehicle(
            route=south_route,
            position='north',
            vehicle_type="car",
            position_threshold=100
        )
        south_vehicle.destination = 'south'
        south_vehicle.interpolated_position = (WIDTH//2 - 15, 0)  # -15 for left lane
        south_vehicle.base_speed = 2
        south_vehicle.speed = 2
        south_vehicle.state = "moving"
        south_vehicle.position_time = 0
        
        # Add vehicles to simulation
        self.active_vehicles.extend([east_vehicle, west_vehicle, north_vehicle, south_vehicle])
        
        return east_vehicle, west_vehicle, north_vehicle, south_vehicle

    def run_test_mode(self):
        """Run simulation in test mode with two vehicles"""
        # Create test vehicles
        east_vehicle, west_vehicle, north_vehicle, south_vehicle = self.create_test_vehicles()
        
        # Set initial light states to green for east-west
        self.ns_light = "red"
        self.ew_light = "green"
        self.light_timer = 50  # Start with 50 ticks for green
        self.test_mode = True  # Mark as test mode
        
        # Track vehicle states
        last_logged_tick = -10
        
        print("\n=== Starting Test ===")
        print("Initial States:")
        print(f"East Vehicle: pos={east_vehicle.position}, state={east_vehicle.state}")
        print(f"West Vehicle: pos={west_vehicle.position}, state={west_vehicle.state}")
        print(f"North Vehicle: pos={north_vehicle.position}, state={north_vehicle.state}")
        print(f"South Vehicle: pos={south_vehicle.position}, state={south_vehicle.state}")
        print("===================\n")
        
        while True:
            # Update light timer and states
            self.light_timer -= 1
            if self.light_timer <= 0:
                # Switch lights
                if self.ns_light == "red" and self.ew_light == "green":
                    self.ew_light = "yellow"
                    self.light_timer = 3  # Yellow for 3 ticks
                elif self.ns_light == "red" and self.ew_light == "yellow":
                    self.ns_light = "green"
                    self.ew_light = "red"
                    self.light_timer = 50  # Green for 50 ticks
                elif self.ns_light == "green" and self.ew_light == "red":
                    self.ns_light = "yellow"
                    self.light_timer = 3  # Yellow for 3 ticks
                elif self.ns_light == "yellow" and self.ew_light == "red":
                    self.ns_light = "red"
                    self.ew_light = "green"
                    self.light_timer = 50  # Green for 50 ticks
            
            # Store pre-update positions for movement tracking
            pre_east_pos = east_vehicle.interpolated_position if east_vehicle in self.active_vehicles else None
            pre_west_pos = west_vehicle.interpolated_position if west_vehicle in self.active_vehicles else None
            pre_north_pos = north_vehicle.interpolated_position if north_vehicle in self.active_vehicles else None
            pre_south_pos = south_vehicle.interpolated_position if south_vehicle in self.active_vehicles else None
            
            # Update vehicles
            self.update_vehicles()
            
            # Calculate movement deltas
            if east_vehicle in self.active_vehicles and pre_east_pos:
                east_delta_x = east_vehicle.interpolated_position[0] - pre_east_pos[0]
                east_delta_y = east_vehicle.interpolated_position[1] - pre_east_pos[1]
            else:
                east_delta_x = east_delta_y = 0
            
            if west_vehicle in self.active_vehicles and pre_west_pos:
                west_delta_x = west_vehicle.interpolated_position[0] - pre_west_pos[0]
                west_delta_y = west_vehicle.interpolated_position[1] - pre_west_pos[1]
            else:
                west_delta_x = west_delta_y = 0
            
            if north_vehicle in self.active_vehicles and pre_north_pos:
                north_delta_x = north_vehicle.interpolated_position[0] - pre_north_pos[0]
                north_delta_y = north_vehicle.interpolated_position[1] - pre_north_pos[1]
            else:
                north_delta_x = north_delta_y = 0
            
            if south_vehicle in self.active_vehicles and pre_south_pos:
                south_delta_x = south_vehicle.interpolated_position[0] - pre_south_pos[0]
                south_delta_y = south_vehicle.interpolated_position[1] - pre_south_pos[1]
            else:
                south_delta_x = south_delta_y = 0
            
            # Log status every 10 ticks or on significant changes
            should_log = (
                self.current_tick - last_logged_tick >= 10 or
                abs(east_delta_x) > 10 or abs(east_delta_y) > 10 or
                abs(west_delta_x) > 10 or abs(west_delta_y) > 10 or
                abs(north_delta_x) > 10 or abs(north_delta_y) > 10 or
                abs(south_delta_x) > 10 or abs(south_delta_y) > 10 or
                (east_vehicle in self.active_vehicles and east_vehicle.state == "waiting") or
                (west_vehicle in self.active_vehicles and west_vehicle.state == "waiting") or
                (north_vehicle in self.active_vehicles and north_vehicle.state == "waiting") or
                (south_vehicle in self.active_vehicles and south_vehicle.state == "waiting")
            )
            
            if should_log:
                print(f"\n=== Tick {self.current_tick} ===")
                print(f"Light States: NS={self.ns_light}, EW={self.ew_light}, Timer={self.light_timer}")
                if east_vehicle in self.active_vehicles:
                    print(f"East Vehicle:")
                    print(f"Position: {east_vehicle.position}")
                    print(f"State: {east_vehicle.state}")
                    print(f"Coordinates: {east_vehicle.interpolated_position}")
                    print(f"Movement: dx={east_delta_x:.2f}, dy={east_delta_y:.2f}")
                    print(f"Progress: {(east_vehicle.position_time / east_vehicle.position_threshold * 100):.2f}%\n")
                
                if west_vehicle in self.active_vehicles:
                    print(f"West Vehicle:")
                    print(f"Position: {west_vehicle.position}")
                    print(f"State: {west_vehicle.state}")
                    print(f"Coordinates: {west_vehicle.interpolated_position}")
                    print(f"Movement: dx={west_delta_x:.2f}, dy={west_delta_y:.2f}")
                    print(f"Progress: {(west_vehicle.position_time / west_vehicle.position_threshold * 100):.2f}%\n")
                
                if north_vehicle in self.active_vehicles:
                    print(f"North Vehicle:")
                    print(f"Position: {north_vehicle.position}")
                    print(f"State: {north_vehicle.state}")
                    print(f"Coordinates: {north_vehicle.interpolated_position}")
                    print(f"Movement: dx={north_delta_x:.2f}, dy={north_delta_y:.2f}")
                    print(f"Progress: {(north_vehicle.position_time / north_vehicle.position_threshold * 100):.2f}%\n")
                
                if south_vehicle in self.active_vehicles:
                    print(f"South Vehicle:")
                    print(f"Position: {south_vehicle.position}")
                    print(f"State: {south_vehicle.state}")
                    print(f"Coordinates: {south_vehicle.interpolated_position}")
                    print(f"Movement: dx={south_delta_x:.2f}, dy={south_delta_y:.2f}")
                    print(f"Progress: {(south_vehicle.position_time / south_vehicle.position_threshold * 100):.2f}%")
                
                print("========================================")
                last_logged_tick = self.current_tick
            
            # Increment tick counter
            self.current_tick += 1
            
            # Check if all vehicles have completed their routes
            if not self.active_vehicles:
                print("\n=== Test Complete ===")
                print("All vehicles have completed their routes")
                break

    def create_test_vehicles(self):
        """Create four test vehicles moving in opposite directions (east-west and north-south)"""
        # Create east-bound vehicle
        east_route = self.create_route('west', 'east')
        east_vehicle = Vehicle(
            route=east_route,
            position='west',
            vehicle_type="car",
            position_threshold=100
        )
        east_vehicle.destination = 'east'
        east_vehicle.interpolated_position = (0, HEIGHT//2 + 15)  # +15 for right lane
        east_vehicle.base_speed = 2
        east_vehicle.speed = 2
        east_vehicle.state = "moving"
        east_vehicle.position_time = 0
        
        # Create west-bound vehicle
        west_route = self.create_route('east', 'west')
        west_vehicle = Vehicle(
            route=west_route,
            position='east',
            vehicle_type="car",
            position_threshold=100
        )
        west_vehicle.destination = 'west'
        west_vehicle.interpolated_position = (WIDTH, HEIGHT//2 - 15)  # -15 for left lane
        west_vehicle.base_speed = 2
        west_vehicle.speed = 2
        west_vehicle.state = "moving"
        west_vehicle.position_time = 0
        
        # Create north-bound vehicle
        north_route = self.create_route('south', 'north')
        north_vehicle = Vehicle(
            route=north_route,
            position='south',
            vehicle_type="car",
            position_threshold=100
        )
        north_vehicle.destination = 'north'
        north_vehicle.interpolated_position = (WIDTH//2 + 15, HEIGHT)  # +15 for right lane
        north_vehicle.base_speed = 2
        north_vehicle.speed = 2
        north_vehicle.state = "moving"
        north_vehicle.position_time = 0
        
        # Create south-bound vehicle
        south_route = self.create_route('north', 'south')
        south_vehicle = Vehicle(
            route=south_route,
            position='north',
            vehicle_type="car",
            position_threshold=100
        )
        south_vehicle.destination = 'south'
        south_vehicle.interpolated_position = (WIDTH//2 - 15, 0)  # -15 for left lane
        south_vehicle.base_speed = 2
        south_vehicle.speed = 2
        south_vehicle.state = "moving"
        south_vehicle.position_time = 0
        
        # Add vehicles to simulation
        self.active_vehicles.extend([east_vehicle, west_vehicle, north_vehicle, south_vehicle])
        
        return east_vehicle, west_vehicle, north_vehicle, south_vehicle 