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
    
    def update_vehicles(self):
        """Update the state of all vehicles in the simulation"""
        # Update light state
        light_state = (self.ns_light, self.ew_light)
        
        # List to store vehicles to remove
        vehicles_to_remove = []
        
        # Update each vehicle
        for vehicle in self.active_vehicles:
            try:
                # Check if vehicle has arrived at destination
                if vehicle.state == "arrived":
                    vehicles_to_remove.append(vehicle)
                    continue
                
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
                
                # Check if we need to stop
                should_stop = False
                
                # Stop at red or yellow light if approaching intersection
                if vehicle.position in ['north', 'south', 'east', 'west'] and next_pos == 'intersection':
                    ns_light, ew_light = light_state
                    if ((vehicle.position in ['north', 'south'] and ns_light in ["red", "yellow"]) or
                        (vehicle.position in ['east', 'west'] and ew_light in ["red", "yellow"])):
                        should_stop = True
                        vehicle.state = "waiting"
                        vehicle.waiting_time += 1
                        vehicle.speed = 0
                        continue
                
                # Check for vehicles ahead
                if not should_stop:
                    for other_vehicle in self.active_vehicles:
                        if other_vehicle != vehicle and other_vehicle.state != "arrived":
                            if vehicle.is_behind(other_vehicle):
                                should_stop = True
                                vehicle.state = "waiting"
                                vehicle.waiting_time += 1
                                vehicle.speed = 0
                                break
                
                # Update position if not stopped
                if not should_stop:
                    vehicle.state = "moving"
                    vehicle.waiting_time = 0
                    
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
        
        # Starting position with lane offset
        if start == 'north':
            route.extend([start, (WIDTH//2 + LANE_OFFSET, 50), (WIDTH//2 + LANE_OFFSET, 100)])
        elif start == 'south':
            route.extend([start, (WIDTH//2 - LANE_OFFSET, HEIGHT-50), (WIDTH//2 - LANE_OFFSET, HEIGHT-100)])
        elif start == 'east':
            route.extend([start, (WIDTH-50, HEIGHT//2 - LANE_OFFSET), (WIDTH-100, HEIGHT//2 - LANE_OFFSET)])
        elif start == 'west':
            route.extend([start, (50, HEIGHT//2 + LANE_OFFSET), (100, HEIGHT//2 + LANE_OFFSET)])
        
        # Add intersection approach with lane offset
        if start == 'north':
            route.extend([(WIDTH//2 + LANE_OFFSET, HEIGHT//2 - 100), (WIDTH//2 + LANE_OFFSET, HEIGHT//2 - 50)])
        elif start == 'south':
            route.extend([(WIDTH//2 - LANE_OFFSET, HEIGHT//2 + 100), (WIDTH//2 - LANE_OFFSET, HEIGHT//2 + 50)])
        elif start == 'east':
            route.extend([(WIDTH//2 + 100, HEIGHT//2 - LANE_OFFSET), (WIDTH//2 + 50, HEIGHT//2 - LANE_OFFSET)])
        elif start == 'west':
            route.extend([(WIDTH//2 - 100, HEIGHT//2 + LANE_OFFSET), (WIDTH//2 - 50, HEIGHT//2 + LANE_OFFSET)])
        
        # Add intersection waypoint with offset based on turn
        if (start == 'north' and end == 'west') or (start == 'east' and end == 'south'):
            route.extend([
                'intersection',
                (WIDTH//2 - 25, HEIGHT//2 - 25),  # Smooth turn point
                (WIDTH//2 - 50, HEIGHT//2 + LANE_OFFSET),  # Exit point with proper lane
                (WIDTH//2 - 100, HEIGHT//2 + LANE_OFFSET)  # Past intersection
            ])
        elif (start == 'north' and end == 'east') or (start == 'west' and end == 'south'):
            route.extend([
                'intersection',
                (WIDTH//2 + 25, HEIGHT//2 - 25),  # Smooth turn point
                (WIDTH//2 + 50, HEIGHT//2 - LANE_OFFSET),  # Exit point with proper lane
                (WIDTH//2 + 100, HEIGHT//2 - LANE_OFFSET)  # Past intersection
            ])
        elif (start == 'south' and end == 'west') or (start == 'east' and end == 'north'):
            route.extend([
                'intersection',
                (WIDTH//2 - 25, HEIGHT//2 + 25),  # Smooth turn point
                (WIDTH//2 - 50, HEIGHT//2 + LANE_OFFSET),  # Exit point with proper lane
                (WIDTH//2 - 100, HEIGHT//2 + LANE_OFFSET)  # Past intersection
            ])
        elif (start == 'south' and end == 'east') or (start == 'west' and end == 'north'):
            route.extend([
                'intersection',
                (WIDTH//2 + 25, HEIGHT//2 + 25),  # Smooth turn point
                (WIDTH//2 + 50, HEIGHT//2 - LANE_OFFSET),  # Exit point with proper lane
                (WIDTH//2 + 100, HEIGHT//2 - LANE_OFFSET)  # Past intersection
            ])
        elif start == 'north' and end == 'south':
            route.extend([
                'intersection',
                (WIDTH//2 + LANE_OFFSET, HEIGHT//2),  # Keep right through intersection
                (WIDTH//2 + LANE_OFFSET, HEIGHT//2 + 25),  # Exit point
                (WIDTH//2 + LANE_OFFSET, HEIGHT//2 + 50),  # Past intersection
                (WIDTH//2 + LANE_OFFSET, HEIGHT//2 + 100)  # Further past intersection
            ])
        elif start == 'south' and end == 'north':
            route.extend([
                'intersection',
                (WIDTH//2 - LANE_OFFSET, HEIGHT//2),  # Keep right through intersection
                (WIDTH//2 - LANE_OFFSET, HEIGHT//2 - 25),  # Exit point
                (WIDTH//2 - LANE_OFFSET, HEIGHT//2 - 50),  # Past intersection
                (WIDTH//2 - LANE_OFFSET, HEIGHT//2 - 100)  # Further past intersection
            ])
        elif start == 'east' and end == 'west':
            route.extend([
                'intersection',
                (WIDTH//2, HEIGHT//2 - LANE_OFFSET),  # Keep right through intersection
                (WIDTH//2 - 25, HEIGHT//2 - LANE_OFFSET),  # Exit point
                (WIDTH//2 - 50, HEIGHT//2 - LANE_OFFSET),  # Past intersection
                (WIDTH//2 - 100, HEIGHT//2 - LANE_OFFSET)  # Further past intersection
            ])
        elif start == 'west' and end == 'east':
            route.extend([
                'intersection',
                (WIDTH//2, HEIGHT//2 + LANE_OFFSET),  # Keep right through intersection
                (WIDTH//2 + 25, HEIGHT//2 + LANE_OFFSET),  # Exit point
                (WIDTH//2 + 50, HEIGHT//2 + LANE_OFFSET),  # Past intersection
                (WIDTH//2 + 100, HEIGHT//2 + LANE_OFFSET)  # Further past intersection
            ])
        
        # Add exit path with proper lane offset
        if end == 'north':
            route.extend([(WIDTH//2 - LANE_OFFSET, 100), (WIDTH//2 - LANE_OFFSET, 50), (WIDTH//2 - LANE_OFFSET, 0)])
        elif end == 'south':
            route.extend([(WIDTH//2 + LANE_OFFSET, HEIGHT-100), (WIDTH//2 + LANE_OFFSET, HEIGHT-50), (WIDTH//2 + LANE_OFFSET, HEIGHT)])
        elif end == 'east':
            route.extend([(WIDTH-100, HEIGHT//2 + LANE_OFFSET), (WIDTH-50, HEIGHT//2 + LANE_OFFSET), (WIDTH, HEIGHT//2 + LANE_OFFSET)])
        elif end == 'west':
            route.extend([(100, HEIGHT//2 - LANE_OFFSET), (50, HEIGHT//2 - LANE_OFFSET), (0, HEIGHT//2 - LANE_OFFSET)])
        
        return route

    def create_test_vehicle(self):
        """Create a single test vehicle moving from east to west"""
        # Set test mode flag
        self.test_mode = True
        
        # Clear any existing vehicles
        self.active_vehicles = []
        self.removed_vehicles = []
        
        # Create a simple route from east to west
        route = [
            'east',
            (WIDTH-100, HEIGHT//2),
            (WIDTH-50, HEIGHT//2),
            (WIDTH//2 + 50, HEIGHT//2),
            'intersection',
            (WIDTH//2 - 50, HEIGHT//2),
            (50, HEIGHT//2),
            (0, HEIGHT//2),
            'west'
        ]
        
        # Create the test vehicle with very slow movement settings
        test_vehicle = Vehicle(
            route=route,
            position='east',
            vehicle_type="car",
            position_threshold=200  # Much higher threshold for slower movement
        )
        test_vehicle.destination = 'west'
        test_vehicle.interpolated_position = None
        test_vehicle.id = "TEST_VEHICLE"
        
        # Set initial interpolated position
        test_vehicle.interpolated_position = (WIDTH, HEIGHT//2)
        
        # Override speed settings for test vehicle with very slow speed
        test_vehicle.base_speed = 1  # Very slow speed
        test_vehicle.speed = 1
        test_vehicle.last_speed = 1
        
        # Add vehicle to simulation
        self.active_vehicles.append(test_vehicle)
        print("\n=== Test Vehicle Created ===")
        print(f"Starting Position: east")
        print(f"Destination: west")
        print(f"Route: {route}")
        print(f"Initial Interpolated Position: {test_vehicle.interpolated_position}")
        print(f"Position Threshold: {test_vehicle.position_threshold}")
        print(f"Base Speed: {test_vehicle.base_speed}")
        print("=========================\n")
        
        return test_vehicle

    def run_test_mode(self):
        """Run simulation in test mode with a single vehicle"""
        # Create test vehicle
        test_vehicle = self.create_test_vehicle()
        
        # Set initial light states
        self.ns_light = "red"
        self.ew_light = "green"
        
        # Track previous values for change detection
        prev_state = None
        prev_position = None
        prev_route_index = None
        prev_interpolated = None
        last_logged_tick = -10  # Ensure first tick is logged
        
        print("\n=== Initial Route ===")
        for i, point in enumerate(test_vehicle.route):
            print(f"Point {i}: {point}")
        print("===================\n")
        
        while self.running and test_vehicle in self.active_vehicles:
            # Handle events
            self.handle_events()
            
            # Update traffic lights
            self.update_traffic_lights()
            
            # Store pre-update interpolated position
            pre_update_pos = test_vehicle.interpolated_position
            
            # Update vehicles
            self.update_vehicles()
            
            # Get current route index
            current_route_index = test_vehicle.route.index(test_vehicle.position)
            
            # Calculate movement delta if we have both positions
            if pre_update_pos and test_vehicle.interpolated_position:
                delta_x = test_vehicle.interpolated_position[0] - pre_update_pos[0]
                delta_y = test_vehicle.interpolated_position[1] - pre_update_pos[1]
            else:
                delta_x = delta_y = 0
                
            # Detect significant position changes or state changes
            position_changed = (prev_interpolated != test_vehicle.interpolated_position)
            route_point_changed = (prev_route_index != current_route_index)
            state_changed = (prev_state != test_vehicle.state)
            
            # Log on significant changes or regular intervals
            should_log = (
                self.current_tick - last_logged_tick >= 10 or  # Regular interval
                route_point_changed or                         # Route point change
                state_changed or                              # State change
                (abs(delta_x) > 50 or abs(delta_y) > 50)     # Large position change
            )
            
            if should_log:
                print(f"\n=== Movement Analysis at Tick {self.current_tick} ===")
                print(f"Current Route Point: {test_vehicle.position}")
                print(f"Route Index: {current_route_index}")
                if current_route_index < len(test_vehicle.route) - 1:
                    print(f"Next Route Point: {test_vehicle.route[current_route_index + 1]}")
                
                print(f"\nInterpolation Details:")
                print(f"Previous Position: {pre_update_pos}")
                print(f"Current Position: {test_vehicle.interpolated_position}")
                print(f"Movement Delta: dx={delta_x:.2f}, dy={delta_y:.2f}")
                print(f"Position Time: {test_vehicle.position_time}")
                print(f"Progress: {(test_vehicle.position_time / test_vehicle.position_threshold):.2%}")
                
                if route_point_changed:
                    print(f"\n!!! Route Point Changed !!!")
                    print(f"Previous Point: {prev_position}")
                    print(f"New Point: {test_vehicle.position}")
                
                if abs(delta_x) > 50 or abs(delta_y) > 50:
                    print(f"\n!!! Large Position Change Detected !!!")
                    print(f"Delta X: {delta_x:.2f}")
                    print(f"Delta Y: {delta_y:.2f}")
                
                print("=" * 40)
                last_logged_tick = self.current_tick
            
            # Update previous values
            prev_state = test_vehicle.state
            prev_position = test_vehicle.position
            prev_route_index = current_route_index
            prev_interpolated = test_vehicle.interpolated_position
            
            # Draw everything
            self.draw(None)
            
            # Control simulation speed
            clock = get_clock()
            clock.tick(30)
            
            # Increment tick
            self.current_tick += 1
            
            # End test if vehicle arrives
            if test_vehicle.state == "arrived":
                print("\n=== Test Complete ===")
                print(f"Total Ticks: {self.current_tick}")
                print(f"Final Route Point: {test_vehicle.position}")
                print(f"Final Interpolated Position: {test_vehicle.interpolated_position}")
                print(f"Final State: {test_vehicle.state}")
                print("===================\n")
                break 